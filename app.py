import dash
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import os
from pathlib import Path

from data_loader import carregar_dados, normalize


# =====================================================================
# Data Load
# =====================================================================
df_bruto = carregar_dados()

DIMENSOES = {
    "raca": {
        "label": "Raça/Cor",
        "coluna": "RACA_DESC",
        "ordem": ["Branca", "Preta", "Parda", "Amarela", "Indígena", "Ignorado"],
    },
    "sexo": {
        "label": "Sexo",
        "coluna": "SEXO_DESC",
        "ordem": ["Masculino", "Feminino", "Ignorado"],
    },
    "faixa_etaria": {
        "label": "Faixa Etária",
        "coluna": "FAIXA_ETARIA",
        "ordem": ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70+", "Ignorado"],
    },
    "forma": {
        "label": "Forma Clínica",
        "coluna": "FORMA_DESC",
        "ordem": ["Pulmonar", "Extrapulmonar", "Pulmonar + Extrapulmonar", "Ignorado"],
    },
}

DATA_MIN = df_bruto["DT_NOTIFIC_DT"].min()
DATA_MAX = df_bruto["DT_NOTIFIC_DT"].max()
UNIDADES_DISPONIVEIS = (
    df_bruto[["ID_UNID_AT", "NOME_UNIDADE", "DISTRITO_UNIDADE"]]
    .drop_duplicates()
    .sort_values("NOME_UNIDADE")
)

BASE_DIR = Path(__file__).resolve().parent
with open(BASE_DIR / "distritos_poa.geojson", encoding="utf-8") as f:
    distrito_poa = json.load(f)
DISTRITOS_MAPA = sorted(
    {feature["properties"]["Distrito"] for feature in distrito_poa["features"]}
)
MAX_CASOS_DISTRITO = (
    df_bruto[df_bruto["DISTRITO_UNIDADE"].isin(DISTRITOS_MAPA)]
    .groupby("DISTRITO_UNIDADE")
    .size()
    .max()
)

# =====================================================================
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY],
    title="PET Digital | Porto Alegre",
)


# =====================================================================
# Funções de cálculo
# =====================================================================
def calcular_metricas(df_filtrado: pd.DataFrame) -> dict:
    total_casos = len(df_filtrado)
    situacoes = df_filtrado["SITUA_ENCE"]
    registrados = situacoes.notna().sum()

    curados = (situacoes == 1).sum()
    cura_pct = round(curados / registrados * 100, 1) if registrados else 0.0
    obitos_tb = (situacoes == 3).sum()
    abandono = situacoes.isin([2, 10]).sum()
    abandono_pct = round(abandono / registrados * 100, 1) if registrados else 0.0
    em_tratamento = situacoes.isna().sum()

    return {
        "cura_pct": cura_pct,
        "curados": int(curados),
        "total_casos": total_casos,
        "em_tratamento": int(em_tratamento),
        "obitos_tb": int(obitos_tb),
        "abandono_pct": abandono_pct,
    }


def montar_figura_mapa(df_filtrado: pd.DataFrame):
    """Mapeia casos pelo distrito da unidade que acompanha cada registro."""
    casos = (
        df_filtrado[df_filtrado["DISTRITO_UNIDADE"].isin(DISTRITOS_MAPA)]
        .groupby("DISTRITO_UNIDADE")
        .size()
        .reset_index(name="Casos")
    )
    todos_distritos = pd.DataFrame({"DISTRITO_UNIDADE": DISTRITOS_MAPA})
    casos = todos_distritos.merge(
        casos,
        on="DISTRITO_UNIDADE",
        how="left",
    ).fillna({"Casos": 0})
    casos["Casos"] = casos["Casos"].astype(int)
    df_mapa = casos.rename(columns={"DISTRITO_UNIDADE": "Distrito"})
    sem_distrito_unidade = int(
        (~df_filtrado["DISTRITO_UNIDADE"].isin(DISTRITOS_MAPA)).sum()
    )

    fig = px.choropleth_map(
        df_mapa,
        geojson=distrito_poa,
        locations="Distrito",
        featureidkey="properties.Distrito",
        color="Casos",
        center={"lat": -30.0346, "lon": -51.2177},
        zoom=10.8,
        opacity=0.72,
        color_continuous_scale="Reds",
        range_color=(0, max(MAX_CASOS_DISTRITO, 1)),
    )
    fig.update_traces(
        hovertemplate="<b>%{location}</b><br>Casos: %{z}<extra></extra>"
    )
    fig.update_layout(
        map_style="carto-positron",
        title={
            "text": (
                "Casos por distrito da unidade de saúde"
                f"<sup> | {sem_distrito_unidade} sem distrito de unidade</sup>"
            ),
            "x": 0.02,
            "xanchor": "left",
        },
        margin={"r": 0, "t": 45, "l": 0, "b": 0},
        coloraxis_colorbar={"title": "Casos", "thickness": 12},
    )
    return fig


def montar_grafico(df_filtrado: pd.DataFrame, distrito_selecionado: str, dimensao: str):
    """Gráfico de contagem de casos, com a dimensão (eixo X) escolhida no dropdown."""
    if distrito_selecionado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["DISTRITO"] == distrito_selecionado]

    config_dim = DIMENSOES[dimensao]
    coluna = config_dim["coluna"]
    ordem = config_dim["ordem"]

    contagem = (
        df_filtrado[coluna]
        .value_counts()
        .reindex(ordem, fill_value=0)
        .reset_index()
    )
    contagem.columns = [coluna, "Casos"]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=contagem[coluna],
        y=contagem["Casos"],
        marker_color="#167c80",
        hovertemplate="<b>%{x}</b><br>Casos: %{y}<extra></extra>",
    ))

    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        autosize=True,
        margin=dict(l=45, r=20, b=70, t=20),
        xaxis_title=config_dim["label"],
        yaxis_title="Casos",
        font={"family": "Arial, sans-serif", "color": "#25313c"},
        hoverlabel={"bgcolor": "#ffffff", "font_size": 13},
    )
    return fig


METRICAS_ESTABELECIMENTOS = {
    "Casos": "Casos",
    "Curados": "Curados",
    "Abandonos": "Abandonos",
    "Óbitos": "Óbitos",
    "Em tratamento": "Em tratamento",
}

METRICAS_RANKING_UNIDADES = {
    "Casos": "Casos",
    "Óbitos por TB": "Óbitos",
    "Curados": "Curados",
    "Em tratamento": "Em tratamento",
}


def contar_metrica(df_filtrado: pd.DataFrame, metrica: str) -> int:
    if metrica == "Casos":
        return len(df_filtrado)
    if metrica == "Curados":
        return int((df_filtrado["SITUA_ENCE"] == 1).sum())
    if metrica == "Abandonos":
        return int(df_filtrado["SITUA_ENCE"].isin([2, 10]).sum())
    if metrica == "Óbitos":
        return int((df_filtrado["SITUA_ENCE"] == 3).sum())
    if metrica == "Em tratamento":
        return int(df_filtrado["SITUA_ENCE"].isna().sum())
    raise ValueError(f"Métrica desconhecida: {metrica}")


def montar_grafico_temporal(
    df_filtrado: pd.DataFrame,
    distrito_selecionado: str,
    metrica: str = "Casos",
    altura: int = 300,
    data_corte=None,
):
    """Mostra casos por notificação e desfechos pelo mês de encerramento."""
    if distrito_selecionado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["DISTRITO"] == distrito_selecionado]

    if metrica not in METRICAS_ESTABELECIMENTOS:
        raise ValueError(f"Métrica temporal desconhecida: {metrica}")

    data_corte = pd.to_datetime(data_corte) if data_corte is not None else DATA_MAX
    usa_encerramento = metrica in {"Curados", "Abandonos", "Óbitos"}
    coluna_mes = "MES_ENCERRAMENTO" if usa_encerramento else "MES_NOTIFICACAO"
    dados = df_filtrado.dropna(subset=[coluna_mes]).copy()

    if metrica == "Curados":
        dados = dados[dados["SITUA_ENCE"] == 1]
    elif metrica == "Abandonos":
        dados = dados[dados["SITUA_ENCE"].isin([2, 10])]
    elif metrica == "Óbitos":
        dados = dados[dados["SITUA_ENCE"] == 3]
    elif metrica == "Em tratamento":
        dados = dados[dados["SITUA_ENCE"].isna()]

    if usa_encerramento:
        dados = dados[dados["DT_ENCERRA_DT"] <= data_corte]

    dados["MES"] = dados[coluna_mes]
    meses = pd.date_range(
        start=DATA_MIN.to_period("M").to_timestamp(),
        end=data_corte.to_period("M").to_timestamp(),
        freq="MS",
    )
    serie = dados.groupby("MES").size().reindex(meses, fill_value=0).astype(int)

    fig = go.Figure()
    cores = {
        "Casos": "#167c80",
        "Curados": "#2a9d8f",
        "Abandonos": "#e07a5f",
        "Óbitos": "#c0392b",
        "Em tratamento": "#457b9d",
    }
    fig.add_trace(go.Scatter(
        x=serie.index,
        y=serie,
        mode="lines+markers",
        name=metrica,
        line={"color": cores[metrica], "width": 2},
        marker={"size": 6},
        hovertemplate=(
            f"<b>{metrica}</b><br>"
            "%{x|%b/%Y}<br>Quantidade: %{y}<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=f"Evolução mensal: {metrica}",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        height=altura,
        margin=dict(l=45, r=20, b=55, t=55),
        xaxis_title="Mês de encerramento" if usa_encerramento else "Mês de notificação",
        yaxis_title="Quantidade",
        font={"family": "Arial, sans-serif", "color": "#25313c"},
        hoverlabel={"bgcolor": "#ffffff", "font_size": 13},
    )
    return fig


def montar_ranking_unidades(df_filtrado, metrica="Casos", altura: int = 380):
    if metrica not in METRICAS_ESTABELECIMENTOS.values():
        raise ValueError(f"Métrica de ranking desconhecida: {metrica}")

    contagens = [
        {
            "NOME_UNIDADE": unidade,
            "Quantidade": contar_metrica(grupo, metrica),
        }
        for unidade, grupo in df_filtrado.groupby("NOME_UNIDADE")
    ]
    ranking = pd.DataFrame(contagens)
    if not ranking.empty:
        ranking = (
            ranking[ranking["Quantidade"] > 0]
            .sort_values(["Quantidade", "NOME_UNIDADE"], ascending=[True, True])
            .tail(15)
        )

    fig = px.bar(
        ranking,
        x="Quantidade",
        y="NOME_UNIDADE",
        orientation="h",
        text="Quantidade",
        title=f"Unidades com mais: {metrica.lower()}",
        labels={"NOME_UNIDADE": "Unidade de saúde", "Quantidade": metrica},
        color_discrete_sequence=["#167c80"],
    )
    fig.update_traces(hovertemplate="<b>%{y}</b><br>Quantidade: %{x}<extra></extra>")
    fig.update_layout(
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        height=altura,
        margin=dict(l=20, r=20, b=40, t=55),
        font={"family": "Arial, sans-serif", "color": "#25313c"},
    )
    return fig


# =====================================================================
# Layout
# =====================================================================
app.layout = dbc.Container(
    children=[
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Img(
                        src="/assets/PetDigital.png",
                        style={
                            "height": "64px",
                            "width": "auto",
                            "object-fit": "contain",
                            "margin-bottom": "12px",
                        },
                    ),
                    html.P(
                        "Porto Alegre | Casos registrados na planilha municipal",
                        className="text-muted mb-3",
                    ),
                    dbc.Button(
                        "Todos os distritos",
                        color="primary",
                        id="location-button",
                        size="lg",
                    ),
                ], style={"padding-bottom": "20px"}),

                html.P(
                    "Data de corte para os casos acumulados",
                    style={"margin-top": "20px", "font-weight": "600", "color": "#25313c"},
                ),
                html.Div(
                    className="div-for-dropdown",
                    id="div-date",
                    children=[
                        dcc.DatePickerSingle(
                            id="date-picker",
                            min_date_allowed=DATA_MIN,
                            max_date_allowed=DATA_MAX,
                            initial_visible_month=DATA_MAX,
                            date=DATA_MAX,
                            display_format="DD/MM/YYYY",
                            style={"border": "0px solid black"},
                        )
                    ],
                ),
                html.P(
                    "Unidade acompanhadora (filtrada pelo distrito selecionado)",
                    style={"margin-top": "20px", "font-weight": "600", "color": "#25313c"},
                ),
                dcc.Dropdown(
                    id="unidade-dropdown",
                    options=[
                        {"label": row.NOME_UNIDADE, "value": row.ID_UNID_AT}
                        for row in UNIDADES_DISPONIVEIS.itertuples()
                    ],
                    placeholder="Todas as unidades",
                    clearable=True,
                ),
                dbc.Row([
                    dbc.Col([dbc.Card([
                        dbc.CardBody([
                                html.Span("Taxa de cura", className="metric-label"),
                            html.H3(style={"color": "#167c80"}, id="cura-text"),
                            html.Span("Casos curados", className="text-muted"),
                            html.H5(id="curados-text"),
                        ])
                    ], color="light", outline=True, style={
                        "margin-top": "10px",
                        "border": "1px solid #dce4e8",
                        "box-shadow": "0 2px 8px rgba(26, 45, 58, 0.08)",
                    })], md=4),
                    dbc.Col([dbc.Card([
                        dbc.CardBody([
                                html.Span("Total de casos", className="metric-label"),
                            html.H3(style={"color": "#167c80"}, id="total-casos-text"),
                            html.Span("Em tratamento", className="text-muted"),
                            html.H5(id="em-tratamento-text"),
                        ])
                    ], color="light", outline=True, style={
                        "margin-top": "10px",
                        "border": "1px solid #dce4e8",
                        "box-shadow": "0 2px 8px rgba(26, 45, 58, 0.08)",
                    })], md=4),
                    dbc.Col([dbc.Card([
                        dbc.CardBody([
                                html.Span("Óbitos por tuberculose", className="metric-label"),
                            html.H3(style={"color": "#c0392b"}, id="obitos-text"),
                            html.Span("Abandono", className="text-muted"),
                            html.H5(id="abandono-text"),
                        ])
                    ], color="light", outline=True, style={
                        "margin-top": "10px",
                        "border": "1px solid #dce4e8",
                        "box-shadow": "0 2px 8px rgba(26, 45, 58, 0.08)",
                    })], md=4),
                ]),

                html.Div([
                        html.P("Detalhamento dos casos", className="section-label"),
                    dcc.Dropdown(
                        id="dimensao-dropdown",
                        options=[{"label": v["label"], "value": k} for k, v in DIMENSOES.items()],
                        value="raca",
                        style={"margin-top": "10px"},
                    ),
                        dcc.Graph(id="etnia-graph"),
                    html.P("Indicador da evolução mensal", className="section-label"),
                    dcc.Dropdown(
                        id="temporal-metrica-dropdown",
                        options=[{"label": metrica, "value": metrica} for metrica in METRICAS_ESTABELECIMENTOS],
                        value="Casos",
                        clearable=False,
                    ),
                    dcc.Graph(id="temporal-graph"),
                ], id="div-grafico"),

            ], md=5, style={"padding": "25px", "background-color": "#f5f8fa"}),

            dbc.Col([
                dcc.Loading(
                    id="loading-1",
                    type="default",
                    children=[
                        dcc.Graph(
                            id="choropleth-map",
                            style={"height": "100vh", "width": "100%", "margin-right": "10px"},
                            config={"scrollZoom": True},
                        ),
                        html.P(
                            "Ranking de unidades de saúde no distrito selecionado",
                            className="section-label",
                            style={"margin": "24px 12px 8px"},
                        ),
                        dcc.Dropdown(
                            id="ranking-metrica-dropdown",
                            options=[
                                {"label": label, "value": value}
                                for label, value in METRICAS_RANKING_UNIDADES.items()
                            ],
                            value="Casos",
                            clearable=False,
                            style={"margin": "0 12px 8px"},
                        ),
                        dcc.Graph(
                            id="ranking-unidades-graph",
                            style={"height": "430px", "width": "100%"},
                        ),
                    ],
                ),
            ], md=7),
        ]),
        html.Footer(
            "Fonte: planilha municipal | Período de notificação: "
            f"{DATA_MIN:%d/%m/%Y} a {DATA_MAX:%d/%m/%Y} | "
            f"Registros analisados: {len(df_bruto):,}".replace(",", "."),
            className="text-muted small px-3 pb-3",
        ),
    ],
    fluid=True,
)


# =====================================================================
# Interactivity
# =====================================================================
def obter_dados_filtrados(date, location, unidade=None):
    data_selecionada = pd.to_datetime(date)
    dados = df_bruto[df_bruto["DT_NOTIFIC_DT"] <= data_selecionada]

    if location != "TODOS":
        dados = dados[dados["DISTRITO_UNIDADE"] == location]
    if unidade:
        dados = dados[dados["ID_UNID_AT"] == unidade]
    return dados


def obter_dados_ranking_unidades(date, location):
    return obter_dados_filtrados(date, location)


def opcoes_unidade_por_distrito(distrito):
    unidades = UNIDADES_DISPONIVEIS
    if distrito and distrito != "TODOS":
        distrito_normalizado = normalize(distrito)
        unidades = unidades[
            unidades["DISTRITO_UNIDADE"].apply(normalize) == distrito_normalizado
        ]
    return [
        {"label": row.NOME_UNIDADE, "value": row.ID_UNID_AT}
        for row in unidades.itertuples()
    ]


@app.callback(
    [
        Output("location-button", "children"),
        Output("unidade-dropdown", "options"),
        Output("unidade-dropdown", "value"),
    ],
    [Input("choropleth-map", "clickData"), Input("location-button", "n_clicks")],
)
def update_location(click_data, n_clicks):
    changed_id = [p["prop_id"] for p in dash.callback_context.triggered][0]
    if click_data is not None and changed_id != "location-button.n_clicks":
        distrito = click_data["points"][0]["location"]
        return "{}".format(distrito), opcoes_unidade_por_distrito(distrito), None
    else:
        return "TODOS", opcoes_unidade_por_distrito("TODOS"), None


@app.callback(
    [
        Output("cura-text", "children"),
        Output("curados-text", "children"),
        Output("total-casos-text", "children"),
        Output("em-tratamento-text", "children"),
        Output("obitos-text", "children"),
        Output("abandono-text", "children"),
    ],
    [Input("date-picker", "date"), Input("location-button", "children"),
     Input("unidade-dropdown", "value")],
)
def display_status(date, location, unidade):
    df_filtrado = obter_dados_filtrados(date, location, unidade)
    m = calcular_metricas(df_filtrado)

    return (
        f'{m["cura_pct"]}%',
        f'{m["curados"]:,}'.replace(",", "."),
        f'{m["total_casos"]:,}'.replace(",", "."),
        f'{m["em_tratamento"]:,}'.replace(",", "."),
        f'{m["obitos_tb"]:,}'.replace(",", "."),
        f'{m["abandono_pct"]}%',
    )


@app.callback(
    [Output("etnia-graph", "figure"), Output("temporal-graph", "figure")],
    [Input("dimensao-dropdown", "value"), Input("location-button", "children"),
     Input("date-picker", "date"), Input("unidade-dropdown", "value"),
     Input("temporal-metrica-dropdown", "value")],
)
def plot_graph(dimensao, location, date, unidade, metrica_temporal):
    df_filtrado = obter_dados_filtrados(date, location, unidade)
    return (
        montar_grafico(df_filtrado, "TODOS", dimensao),
        montar_grafico_temporal(
            df_filtrado,
            "TODOS",
            metrica_temporal,
            data_corte=date,
        ),
    )


@app.callback(
    Output("choropleth-map", "figure"),
    Input("date-picker", "date"),
)
def update_map(date):
    return montar_figura_mapa(obter_dados_filtrados(date, "TODOS"))


@app.callback(
    Output("ranking-unidades-graph", "figure"),
    [
        Input("date-picker", "date"),
        Input("location-button", "children"),
        Input("ranking-metrica-dropdown", "value"),
    ],
)
def update_ranking_unidades(date, location, metrica):
    if metrica not in METRICAS_RANKING_UNIDADES.values():
        raise ValueError(f"Métrica de ranking desconhecida: {metrica}")
    dados = obter_dados_ranking_unidades(date, location)
    return montar_ranking_unidades(dados, metrica, altura=430)


# =====================================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8050")),
        debug=False,
    )