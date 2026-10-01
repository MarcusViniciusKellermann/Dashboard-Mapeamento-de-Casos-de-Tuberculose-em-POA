# Dashboard de Tuberculose

Dashboard Dash para acompanhamento de casos de tuberculose em Porto Alegre. O mapa agrega os casos pelo distrito da unidade de saúde responsável pelo acompanhamento, não pelo distrito de residência do paciente.

Na evolução mensal, casos e casos em tratamento são agrupados pelo mês de notificação. Curas, abandonos e óbitos são agrupados pelo mês de encerramento (`DT_ENCERRA`) e respeitam a data de corte selecionada.

O ranking abaixo do mapa compara os estabelecimentos do distrito selecionado por casos, óbitos por TB, curas ou casos sem situação de encerramento. Ele não é limitado pela unidade individual escolhida no filtro lateral.

## Execucao local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python prepare_data.py
python app.py
```

Acesse `http://localhost:8050`.

## Dados

O aplicativo usa `planilha_dashboard.csv`, uma versao sanitizada da base original com somente as colunas necessarias para os indicadores. Para atualizar a base a partir da planilha de origem, execute `python prepare_data.py`.

A preparacao exclui registros com `SITUA_ENCE` igual a 4 (obito por outras causas), 5 (transferencia) ou 6 (mudanca de diagnostico). Registros sem situacao de encerramento permanecem na analise. A base atual possui 1.025 registros apos essa regra.

A aplicacao usa `distritos_poa.geojson` para o mapa e a imagem em `assets/PetDigital.png` para a identidade visual.

## Producao

Defina a porta pela variavel `PORT` e execute com `debug=False`:

```powershell
$env:PORT = "8050"
python app.py
```

Nao publique a planilha bruta, que pode conter dados pessoais. Os arquivos de conversao e a base original devem permanecer fora do servidor de producao.
