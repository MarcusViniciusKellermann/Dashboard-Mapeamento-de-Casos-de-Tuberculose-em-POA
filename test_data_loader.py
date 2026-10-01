import unittest

import pandas as pd

from data_loader import (
    carregar_dados,
    calcular_faixa_etaria,
    filtrar_casos_dashboard,
    mapear_forma,
    mapear_raca,
    mapear_sexo,
)


class DataLoaderTests(unittest.TestCase):
    def test_carrega_base_sanitizada(self):
        dados = carregar_dados()
        self.assertEqual(len(dados), 1025)
        self.assertIn("MES_NOTIFICACAO", dados.columns)
        self.assertIn("DT_ENCERRA_DT", dados.columns)
        self.assertNotIn("NM_PACIENT", dados.columns)

    def test_exclui_obito_outras_causas_transferencia_e_mudanca_diagnostico(self):
        dados = carregar_dados()
        self.assertFalse(dados["SITUA_ENCE"].isin([4, 5, 6]).any())
        self.assertEqual(int(dados["SITUA_ENCE"].isna().sum()), 762)

    def test_filtragem_preserva_demais_situacoes_e_sem_encerramento(self):
        entrada = pd.DataFrame({"SITUA_ENCE": [1, 4, 5, 6, 7, 8, 10, None]})
        resultado = filtrar_casos_dashboard(entrada)
        self.assertEqual(
            resultado["SITUA_ENCE"].dropna().tolist(),
            [1.0, 7.0, 8.0, 10.0],
        )
        self.assertTrue(pd.isna(resultado["SITUA_ENCE"].iloc[-1]))

    def test_unidades_recebem_bairro_e_distrito(self):
        dados = carregar_dados()
        unidade = dados.loc[dados["ID_UNID_AT"] == "2264439"].iloc[0]
        self.assertEqual(unidade["BAIRRO"], "Serraria")
        self.assertEqual(unidade["DISTRITO_UNIDADE"], "SUL")

    def test_codigos_sem_localizacao_continuam_classificados(self):
        dados = carregar_dados()
        sem_localizacao = dados.loc[dados["ID_UNID_AT"] == "2264722"].iloc[0]
        self.assertEqual(sem_localizacao["DISTRITO_UNIDADE"], "Não classificado")

    def test_distritos_confirmados_por_unidade(self):
        dados = carregar_dados().drop_duplicates("ID_UNID_AT").set_index("ID_UNID_AT")
        distritos_esperados = {
            "2237792": "LESTE",
            "2237954": "NORDESTE",
            "2264757": "LOMBA DO PINHEIRO",
            "2265125": "EIXO BALTAZAR",
        }
        for codigo, distrito in distritos_esperados.items():
            with self.subTest(codigo=codigo):
                self.assertEqual(dados.loc[codigo, "DISTRITO_UNIDADE"], distrito)

        self.assertNotIn("7114893", dados.index)

    def test_filtro_territorial_usa_distrito_da_unidade(self):
        import app

        dados = app.obter_dados_filtrados(app.DATA_MAX, "CRUZEIRO")
        self.assertEqual(len(dados), 151)
        self.assertTrue(dados["DISTRITO_UNIDADE"].eq("CRUZEIRO").all())

    def test_grafico_temporal_exibe_apenas_metrica_selecionada(self):
        import app

        for metrica in app.METRICAS_ESTABELECIMENTOS:
            with self.subTest(metrica=metrica):
                figura = app.montar_grafico_temporal(
                    app.df_bruto,
                    "TODOS",
                    metrica,
                )
                self.assertEqual(len(figura.data), 1)
                self.assertEqual(figura.data[0].name, metrica)

    def test_ranking_de_unidades_respeita_distrito_e_metrica(self):
        import app

        distrito = "CRUZEIRO"
        dados = app.obter_dados_ranking_unidades(app.DATA_MAX, distrito)
        unidades_do_distrito = set(
            app.UNIDADES_DISPONIVEIS.loc[
                app.UNIDADES_DISPONIVEIS["DISTRITO_UNIDADE"] == distrito,
                "NOME_UNIDADE",
            ]
        )

        self.assertEqual(len(dados), 151)
        self.assertTrue(dados["DISTRITO_UNIDADE"].eq(distrito).all())

        for metrica in app.METRICAS_RANKING_UNIDADES.values():
            with self.subTest(metrica=metrica):
                figura = app.montar_ranking_unidades(dados, metrica, altura=430)
                unidades_exibidas = set(figura.data[0].y)
                quantidade_exibida = sum(figura.data[0].x)
                self.assertTrue(unidades_exibidas.issubset(unidades_do_distrito))
                self.assertEqual(
                    quantidade_exibida,
                    app.contar_metrica(dados, metrica),
                )

    def test_desfecho_temporal_usa_mes_de_encerramento(self):
        import app

        dados = app.df_bruto
        caso = dados.loc[
            dados["SITUA_ENCE"].isin([2, 10])
            & dados["DT_ENCERRA_DT"].notna()
            & (dados["MES_NOTIFICACAO"] != dados["MES_ENCERRAMENTO"])
        ].iloc[0]
        figura = app.montar_grafico_temporal(
            dados,
            "TODOS",
            "Abandonos",
            data_corte=app.DATA_MAX,
        )
        indice_mes_encerramento = list(figura.data[0].x).index(caso["MES_ENCERRAMENTO"])
        self.assertGreater(figura.data[0].y[indice_mes_encerramento], 0)
        self.assertEqual(figura.layout.xaxis.title.text, "Mês de encerramento")

    def test_mapeamentos_sinan(self):
        self.assertEqual(mapear_raca(4), "Parda")
        self.assertEqual(mapear_sexo("F"), "Feminino")
        self.assertEqual(mapear_forma(3), "Pulmonar + Extrapulmonar")
        self.assertEqual(calcular_faixa_etaria(4047), "40-49")

    def test_data_invalida_eh_nula(self):
        dados = pd.DataFrame({"data": ["31/02/2026"]})
        convertida = pd.to_datetime(dados["data"], format="%d/%m/%Y", errors="coerce")
        self.assertTrue(pd.isna(convertida.iloc[0]))


if __name__ == "__main__":
    unittest.main()
