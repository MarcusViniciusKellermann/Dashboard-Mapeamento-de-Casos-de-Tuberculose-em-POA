import unicodedata
from pathlib import Path

import pandas as pd


CS_RACA = {
    1: "Branca",
    2: "Preta",
    3: "Amarela",
    4: "Parda",
    5: "Indígena",
    9: "Ignorado",
}

CS_SEXO = {
    "M": "Masculino",
    "F": "Feminino",
    "I": "Ignorado",
}

FORMA_TB = {
    1: "Pulmonar",
    2: "Extrapulmonar",
    3: "Pulmonar + Extrapulmonar",
}

COLUNAS_OBRIGATORIAS = {
    "DT_NOTIFIC",
    "DT_ENCERRA",
    "DISTRITO",
    "ID_UNID_AT",
    "CS_RACA",
    "CS_SEXO",
    "FORMA",
    "NU_IDADE_N",
    "SITUA_ENCE",
}
CODIGOS_SITUACAO_EXCLUIDOS = {4, 5, 6}


def normalize(text):
    return (
        unicodedata.normalize("NFKD", str(text))
        .encode("ASCII", "ignore")
        .decode("ASCII")
        .upper()
        .strip()
    )


def mapear_sexo(valor):
    if pd.isna(valor):
        return "Ignorado"
    return CS_SEXO.get(str(valor).strip().upper(), "Ignorado")


def mapear_forma(valor):
    if pd.isna(valor):
        return "Ignorado"
    try:
        return FORMA_TB.get(int(float(valor)), "Ignorado")
    except (ValueError, TypeError):
        return "Ignorado"


def calcular_faixa_etaria(valor):
    if pd.isna(valor):
        return "Ignorado"
    try:
        codigo = str(int(float(valor))).zfill(4)
        unidade = codigo[0]
        numero = int(codigo[1:])
    except (ValueError, TypeError):
        return "Ignorado"

    idade_anos = numero if unidade == "4" else 0
    if idade_anos < 10:
        return "0-9"
    if idade_anos < 20:
        return "10-19"
    if idade_anos < 30:
        return "20-29"
    if idade_anos < 40:
        return "30-39"
    if idade_anos < 50:
        return "40-49"
    if idade_anos < 60:
        return "50-59"
    if idade_anos < 70:
        return "60-69"
    return "70+"


def mapear_raca(valor):
    if pd.isna(valor):
        return "Ignorado"
    try:
        return CS_RACA.get(int(float(valor)), "Ignorado")
    except (ValueError, TypeError):
        return "Ignorado"


def filtrar_casos_dashboard(dados):
    situacoes = pd.to_numeric(dados["SITUA_ENCE"], errors="coerce")
    situacoes_invalidas = dados["SITUA_ENCE"].notna() & situacoes.isna()
    if situacoes_invalidas.any():
        valores = sorted(dados.loc[situacoes_invalidas, "SITUA_ENCE"].astype(str).unique())
        raise ValueError(
            "A coluna SITUA_ENCE contem valores nao numericos: "
            f"{', '.join(valores)}"
        )

    dados = dados.copy()
    dados["SITUA_ENCE"] = situacoes
    return dados.loc[~dados["SITUA_ENCE"].isin(CODIGOS_SITUACAO_EXCLUIDOS)].copy()


BASE_DIR = Path(__file__).resolve().parent


def carregar_dados(caminho=None):
    caminho = Path(caminho) if caminho else BASE_DIR / "planilha_dashboard.csv"
    dados = pd.read_csv(caminho, sep=";", usecols=lambda coluna: coluna.strip() in COLUNAS_OBRIGATORIAS)
    dados.columns = dados.columns.str.strip()

    colunas_ausentes = COLUNAS_OBRIGATORIAS - set(dados.columns)
    if colunas_ausentes:
        raise ValueError(
            "A planilha nao contem as colunas obrigatorias: "
            f"{', '.join(sorted(colunas_ausentes))}"
        )

    dados = filtrar_casos_dashboard(dados)
    dados["DISTRITO"] = dados["DISTRITO"].apply(normalize)
    dados["ID_UNID_AT"] = (
        pd.to_numeric(dados["ID_UNID_AT"], errors="coerce")
        .astype("Int64")
        .astype("string")
        .str.zfill(7)
    )
    dados["DT_NOTIFIC_DT"] = pd.to_datetime(
        dados["DT_NOTIFIC"], format="%d/%m/%Y", errors="coerce"
    )
    dados["MES_NOTIFICACAO"] = dados["DT_NOTIFIC_DT"].dt.to_period("M").dt.to_timestamp()
    dados["DT_ENCERRA_DT"] = pd.to_datetime(
        dados["DT_ENCERRA"], format="%d/%m/%Y", errors="coerce"
    )
    dados["MES_ENCERRAMENTO"] = dados["DT_ENCERRA_DT"].dt.to_period("M").dt.to_timestamp()
    dados["RACA_DESC"] = dados["CS_RACA"].apply(mapear_raca)
    dados["SEXO_DESC"] = dados["CS_SEXO"].apply(mapear_sexo)
    dados["FORMA_DESC"] = dados["FORMA"].apply(mapear_forma)
    dados["FAIXA_ETARIA"] = dados["NU_IDADE_N"].apply(calcular_faixa_etaria)

    unidades = pd.read_csv(BASE_DIR / "unidades_saude.csv", sep=";", dtype="string")
    unidades["ID_UNID_AT"] = unidades["ID_UNID_AT"].str.zfill(7)
    localidades = pd.read_csv(
        BASE_DIR / "unidades_saude_com_bairro.csv",
        dtype="string",
    )
    localidades["ID_UNID_AT"] = (
        pd.to_numeric(localidades["ID_UNID_AT"], errors="coerce")
        .astype("Int64")
        .astype("string")
        .str.zfill(7)
    )
    localidades["BAIRRO_NORMALIZADO"] = localidades["BAIRRO"].apply(normalize)
    bairros_distritos = pd.read_csv(
        BASE_DIR / "bairros_distritos.csv",
        sep=";",
        dtype="string",
    )
    localidades = localidades.merge(
        bairros_distritos,
        on="BAIRRO_NORMALIZADO",
        how="left",
        validate="many_to_one",
    )
    distritos_confirmados = pd.read_csv(
        BASE_DIR / "unidades_distritos_confirmados.csv",
        sep=";",
        dtype="string",
    )
    distritos_confirmados["ID_UNID_AT"] = distritos_confirmados["ID_UNID_AT"].str.zfill(7)
    localidades = localidades.merge(
        distritos_confirmados,
        on="ID_UNID_AT",
        how="left",
        validate="one_to_one",
        suffixes=("", "_CONFIRMADO"),
    )
    localidades["DISTRITO_UNIDADE"] = localidades["DISTRITO_UNIDADE_CONFIRMADO"].fillna(
        localidades["DISTRITO_UNIDADE"]
    )
    localidades = localidades[
        ["ID_UNID_AT", "BAIRRO", "FONTE_BAIRRO", "DISTRITO_UNIDADE"]
    ]
    unidades = unidades.merge(
        localidades,
        on="ID_UNID_AT",
        how="left",
        validate="one_to_one",
    )
    unidades["BAIRRO"] = unidades["BAIRRO"].fillna("Não informado")
    unidades["FONTE_BAIRRO"] = unidades["FONTE_BAIRRO"].fillna("Não informado")
    unidades["DISTRITO_UNIDADE"] = unidades["DISTRITO_UNIDADE"].fillna("Não classificado")
    dados = dados.merge(unidades, on="ID_UNID_AT", how="left", validate="many_to_one")
    dados["NOME_UNIDADE"] = dados["NOME_UNIDADE"].fillna(
        dados["ID_UNID_AT"].map(lambda codigo: f"Unidade não identificada ({codigo})")
    )
    dados["BAIRRO"] = dados["BAIRRO"].fillna("Não informado")
    dados["DISTRITO_UNIDADE"] = dados["DISTRITO_UNIDADE"].fillna("Não classificado")
    return dados
