import dash
from dash import Dash, dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import json
import unicodedata

# =====================================
# FUNÇÃO NORMALIZAR
# =====================================
def normalize(text):
    return unicodedata.normalize('NFKD', str(text))\
        .encode('ASCII', 'ignore')\
        .decode('ASCII')\
        .upper()\
        .strip()

# =====================================
# BASE CSV DISTRITOS
# =====================================
df = pd.read_csv("distrito-casos-17.csv")

# limpar colunas
df.columns = df.columns.str.strip()

# normalizar distrito
df["Distrito"] = df["Distrito"].apply(normalize)

# opcional: remover N/A do mapa
#df = df[df["Distrito"] != "N/A"]

# =====================================
# GEOJSON REAL DOS DISTRITOS
# =====================================
with open("distritos_poa.geojson", encoding="utf-8") as f:
    distrito_poa = json.load(f)

# =====================================
# DASH APP
# =====================================
app = Dash(__name__, external_stylesheets=[dbc.themes.MORPH])

# =====================================
# MAPA
# =====================================
fig = px.choropleth_mapbox(
    df,
    geojson=distrito_poa,
    locations="Distrito",
    featureidkey="properties.Distrito",
    color="Casos",

    center={"lat": -30.0346, "lon": -51.2177},
    zoom=10.8,

    opacity=0.72,
    color_continuous_scale="Reds",

    hover_data={
        "Distrito": True,
        "Casos": True,
        "Cura (%)": True
    }
)

fig.update_layout(
    mapbox_style="carto-positron",
    margin={"r":0, "t":0, "l":0, "b":0},
    height=720
)

# =====================================
# LAYOUT
# =====================================
app.layout = dbc.Container([

    html.H2(
        "Dashboard Epidemiológico - Tuberculose por Distrito",
        className="text-center mt-3 mb-3"
    ),

    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id="choropleth-map",
                figure=fig,
                config={"scrollZoom": True}
            )
        ], width=12)
    ])

], fluid=True)

# =====================================
# EXECUTAR
# =====================================
if __name__ == "__main__":
    app.run(debug=True)