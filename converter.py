import geopandas as gpd
import unicodedata

def normalize(text):
    return unicodedata.normalize('NFKD', str(text))\
        .encode('ASCII', 'ignore')\
        .decode('ASCII')\
        .upper().strip()

# LER JSON BAIRROS
gdf = gpd.read_file("Bairros_LC12112_16.json")

gdf["NOME"] = gdf["NOME"].apply(normalize)

# MAPA BAIRRO -> DISTRITO
# ==========================================
# MAPEAMENTO COMPLETO BAIRRO -> DISTRITO
# Porto Alegre
# ==========================================
mapa_distritos = {

    # ======================
    # CENTRO SUL
    # ======================
    "CAMAQUA": "CENTRO SUL",
    "CAMPO NOVO": "CENTRO SUL",
    "CAVALHADA": "CENTRO SUL",
    "NONOAI": "CENTRO SUL",
    "TERESOPOLIS": "CENTRO SUL",
    "VILA NOVA": "CENTRO SUL",
    "PRAIA DE BELAS": "CENTRO SUL",
    "AZENHA": "CENTRO SUL",
    "MENINO DEUS": "CENTRO SUL",
    

    # ======================
    # EIXO BALTAZAR
    # ======================
    "COSTA E SILVA": "EIXO BALTAZAR",
    "JARDIM ITU": "EIXO BALTAZAR",
    "JARDIM LEOPOLDINA": "EIXO BALTAZAR",
    "PARQUE SANTA FE": "EIXO BALTAZAR",
    "PASSO DAS PEDRAS": "EIXO BALTAZAR",
    "RUBEM BERTA": "EIXO BALTAZAR",

    # ======================
    # EXTREMO SUL
    # ======================
    "BELEM NOVO": "EXTREMO SUL",
    "BOA VISTA DO SUL": "EXTREMO SUL",
    "EXTREMA": "EXTREMO SUL",
    "CHAPEU DO SOL": "EXTREMO SUL",
    "LAGEADO": "EXTREMO SUL",
    "LAMI": "EXTREMO SUL",
    "PONTA GROSSA": "EXTREMO SUL",
    "SAO CAETANO": "EXTREMO SUL",

    # ======================
    # GLORIA
    # ======================
    "BELEM VELHO": "GLORIA",
    "CASCATA": "GLORIA",
    "GLORIA": "GLORIA",

    # ======================
    # CRUZEIRO
    # ======================
    "MEDIANEIRA": "CRUZEIRO",
    "SANTA TEREZA": "CRUZEIRO",

    # ======================
    # CRISTAL
    # ======================
    "CRISTAL": "CRISTAL",
    

    # ======================
    # HUMAITA / NAVEGANTES
    # ======================
    "ANCHIETA": "HUMAITA/NAVEGANTES",
    "FARRAPOS": "HUMAITA/NAVEGANTES",
    "HUMAITA": "HUMAITA/NAVEGANTES",
    "NAVEGANTES": "HUMAITA/NAVEGANTES",
    "SAO GERALDO": "HUMAITA/NAVEGANTES",

    # ======================
    # ILHAS
    # ======================
    "ARQUIPELAGO": "ILHAS",

    # ======================
    # LOMBA DO PINHEIRO
    # ======================
    "LOMBA DO PINHEIRO": "LOMBA DO PINHEIRO",

    # ======================
    # LESTE
    # ======================
    "BOM JESUS": "LESTE",
    "CHACARA DAS PEDRAS": "LESTE",
    "JARDIM CARVALHO": "LESTE",
    "JARDIM DO SALSO": "LESTE",
    "JARDIM SABARA": "LESTE",
    "MORRO SANTANA": "LESTE",
    "TRES FIGUEIRAS": "LESTE",
    "VILA JARDIM": "LESTE",
    "PETRÓPOLIS": "LESTE",
    "SANTA CECILIA": "LESTE",

    # ======================
    # NORDESTE
    # ======================
    "MARIO QUINTANA": "NORDESTE",

    # ======================
    # NOROESTE
    # ======================
    "BOA VISTA": "NOROESTE",
    "CRISTO REDENTOR": "NOROESTE",
    "HIGIENOPOLIS": "NOROESTE",
    "JARDIM EUROPA": "NOROESTE",
    "JARDIM FLORESTA": "NOROESTE",
    "JARDIM LINDOIA": "NOROESTE",
    "JARDIM SAO PEDRO": "NOROESTE",
    "PASSO DA AREIA": "NOROESTE",
    "SANTA MARIA GORETTI": "NOROESTE",
    "SAO JOAO": "NOROESTE",
    "SAO SEBASTIAO": "NOROESTE",
    "VILA IPIRANGA": "NOROESTE",
    "FLORESTA": "NOROESTE",
    "MOINHOS DE VENTO": "NOROESTE",
    "AUXILIADORA": "NOROESTE",
    "MONTSERRAT": "NOROESTE",
    "RIO BRANCO": "NOROESTE",
    "BELA VISTA": "NOROESTE",

    # ======================
    # NORTE
    # ======================
    "SANTA ROSA DE LIMA": "NORTE",
    "SARANDI": "NORTE",

    # ======================
    # PARTENON
    # ======================
    "CEL. APARICIO BORGES": "PARTENON",
    "PARTENON": "PARTENON",
    "SANTO ANTONIO": "PARTENON",
    "VILA JOAO PESSOA": "PARTENON",
    "VILA SAO JOSE": "PARTENON",
    "AGRONOMIA": "PARTENON",
    "JARDIM BOTÂNICO": "PARTENON",

    # ======================
    # RESTINGA
    # ======================
    "PITINGA": "RESTINGA",
    "RESTINGA": "RESTINGA",

    # ======================
    # SUL
    # ======================
    "ABERTA DOS MORROS": "SUL",
    "ESPIRITO SANTO": "SUL",
    "GUARUJA": "SUL",
    "HIPICA": "SUL",
    "IPANEMA": "SUL",
    "JARDIM ISABEL": "SUL",
    "PEDRA REDONDA": "SUL",
    "SERRARIA": "SUL",
    "SETIMO CEU": "SUL",
    "TRISTEZA": "SUL",
    "VILA CONCEICAO": "SUL",
    "VILA ASSUNCAO": "SUL",

    # N/A
    "CENTRO HISTÓRICO": "CENTRAL",
    "CIDADE BAIXA": "CENTRAL",
    "INDEPENDÊNCIA": "CENTRAL",
    "BOM FIM": "CENTRAL",
    "FARROUPILHA": "CENTRAL",
    "SANTANA": "CENTRAL",
    "FLORESTA": "CENTRAL"
    

}

mapa_distritos = {
    normalize(k): v
    for k, v in mapa_distritos.items()
}

gdf["Distrito"] = gdf["NOME"].map(mapa_distritos)

gdf = gdf.dropna(subset=["Distrito"])

# UNIR GEOMETRIAS
distritos = gdf.dissolve(by="Distrito", as_index=False)

# SALVAR
distritos.to_file("distritos_poa.geojson", driver="GeoJSON")

print("Arquivo criado: distritos_poa.geojson")