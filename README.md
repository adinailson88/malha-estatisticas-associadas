# Malha Estatisticas Associadas

Repositorio do eixo de estatisticas associadas do ecossistema Malha IA. O objetivo e separar analises descritivas, rankings, associacoes e agregados derivados dos chamados de manutencao predial, sem duplicar a base bruta `CHAMADOS`.

Repositorio-hub de dados: [adinailson88/malha-ia](https://github.com/adinailson88/malha-ia)  
Dashboard previsto: `https://adinailson88.github.io/malha-estatisticas-associadas/`

## Escopo

Este repositorio guarda apenas estatisticas agregadas. A base completa `chamados.json` permanece no hub `malha-ia`.

Linhas vazias do snapshot publico nao entram nas estatisticas. O criterio de linha valida e `ID Chamado` preenchido.

Ficam fora deste repositorio:

1. Classificacao de chamados.
2. Previsao temporal de chamados.
3. Previsao temporal de custos.
4. ODS/ESG.
5. Base bruta completa `CHAMADOS`.

## Componentes

1. `scripts/gerar_estatisticas_associadas.py`: baixa `chamados.json` do hub e gera agregados.
2. `scripts/exportar_dados_csv.py`: converte JSONs agregados em CSVs.
3. `dashboard.html`: painel estatico com estatisticas associadas.
4. `dados/*.json`: snapshots agregados.
5. `dados_csv/*.csv`: tabelas derivadas para auditoria e artigo.
6. `docs/CONTRATO_DADOS.md`: fronteira, tabelas e metodo de geracao.

## Execucao local

```powershell
python scripts\gerar_estatisticas_associadas.py
python scripts\exportar_dados_csv.py
```

Validacao sintatica:

```powershell
python -m py_compile scripts\gerar_estatisticas_associadas.py scripts\exportar_dados_csv.py
```

## API da planilha

Este repositorio nao precisa de API Google Sheets para funcionar no modo leve. Ele importa o JSON publico do hub e gera apenas agregados.

Secret `AUTENTICACAO_GOOGLE` so seria necessario se, no futuro, este repositorio passasse a recalcular estatisticas diretamente da planilha operacional.

## Licenca

Informação insuficiente para verificar.
