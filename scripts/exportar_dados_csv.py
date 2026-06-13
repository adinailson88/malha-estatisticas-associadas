#!/usr/bin/env python3
"""Exporta tabelas JSON agregadas para CSV."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ARQUIVOS = [
    "resumo_geral.json",
    "serie_mensal.json",
    "ranking_campus.json",
    "ranking_categoria.json",
    "ranking_categoria_raiz.json",
    "ranking_criticidade.json",
    "ranking_executor.json",
    "ranking_status.json",
    "matriz_campus_categoria.json",
]


def carregar_tabela(path: Path) -> tuple[list[str], list[list[object]]]:
    dados = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(dados, list) or not dados or not isinstance(dados[0], list):
        raise SystemExit(f"{path} nao contem tabela JSON.")
    return [str(h) for h in dados[0]], dados[1:]


def escrever_csv(headers: list[str], rows: list[list[object]], destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8-sig", newline="") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(headers)
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera CSVs de estatisticas associadas.")
    parser.add_argument("--entrada", default="dados")
    parser.add_argument("--saida", default="dados_csv")
    args = parser.parse_args()

    entrada = Path(args.entrada)
    saida = Path(args.saida)
    total = 0
    for nome in ARQUIVOS:
        origem = entrada / nome
        if not origem.exists():
            print(f"AVISO: {origem} ausente; ignorado.")
            continue
        headers, rows = carregar_tabela(origem)
        destino = saida / f"{origem.stem}.csv"
        escrever_csv(headers, rows, destino)
        total += 1
        print(f"CSV gerado: {destino} ({len(rows)} linhas, {len(headers)} colunas)")
    if not total:
        raise SystemExit("Nenhum CSV gerado.")
    print(f"Total de CSVs gerados: {total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
