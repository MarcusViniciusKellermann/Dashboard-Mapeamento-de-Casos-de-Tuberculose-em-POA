from pathlib import Path

import pandas as pd

from data_loader import COLUNAS_OBRIGATORIAS, filtrar_casos_dashboard


BASE_DIR = Path(__file__).resolve().parent
entrada = BASE_DIR / "planilha_tb_com_distrito.csv"
saida = BASE_DIR / "planilha_dashboard.csv"

dados = pd.read_csv(
    entrada,
    sep=";",
    usecols=lambda coluna: coluna.strip() in COLUNAS_OBRIGATORIAS,
)
dados.columns = dados.columns.str.strip()
dados = filtrar_casos_dashboard(dados)
dados.to_csv(saida, sep=";", index=False)

print(f"Arquivo sanitizado criado: {saida} ({len(dados)} casos incluidos)")
