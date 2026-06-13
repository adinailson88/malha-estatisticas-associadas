# Contrato de dados - estatisticas associadas

## Fonte central

O repositorio `adinailson88/malha-ia` permanece como hub central. Este repositorio consome `dados/chamados.json` apenas para gerar estatisticas agregadas.

## Regra de fronteira

`chamados.json` e `chamados.csv` nao devem ser versionados neste repositorio. A base bruta completa fica no hub.

## Arquivos gerados

| Arquivo JSON | Papel |
|---|---|
| `dados/resumo_geral.json` | Indicadores gerais da base |
| `dados/serie_mensal.json` | Chamados e custo total por mes |
| `dados/ranking_campus.json` | Quantidade, custo e confianca media por campus |
| `dados/ranking_categoria.json` | Quantidade, custo e confianca media por categoria |
| `dados/ranking_criticidade.json` | Distribuicao por criticidade atribuida pela IA |
| `dados/ranking_executor.json` | Distribuicao por executor/classificador |
| `dados/ranking_status.json` | Distribuicao por status operacional |
| `dados/matriz_campus_categoria.json` | Associacao entre campus e categoria |
| `dados/manifest_hub.json` | Metadados de geracao e fonte |

## Campos usados do hub

| Campo no hub | Uso |
|---|---|
| `ID Chamado` | Contagem e unicidade |
| `DATA E HORA ABERTURA` | Serie temporal mensal |
| `STATUS` | Ranking de status |
| `CAMPUS` | Ranking e associacao |
| `CATEGORIA COMPLETA` | Ranking e matriz campus x categoria |
| `Valor do chamado` | Custo agregado |
| `Classificacao IA` | Comparacao com categoria original quando aplicavel |
| `Avaliacao (%)` | Confianca media |
| `Executor` | Ranking de executor |
| `Criticidade Atribuida por IA` | Ranking de criticidade |

## Uso esperado

Estas tabelas servem como base para artigo ou relatorio de estatisticas associadas. Elas nao substituem os repositorios preditivos nem o painel ODS/ESG.

## Limitacoes

As estatisticas sao snapshots derivados. Se o hub mudar, e necessario rodar novamente:

```powershell
python scripts\gerar_estatisticas_associadas.py
python scripts\exportar_dados_csv.py
```
