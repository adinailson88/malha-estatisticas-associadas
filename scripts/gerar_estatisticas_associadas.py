#!/usr/bin/env python3
"""Gera estatisticas agregadas a partir do hub malha-ia.

Nao salva a base bruta chamados.json. Apenas produz tabelas agregadas em dados/.
"""

from __future__ import annotations

import argparse
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


URL_CHAMADOS_PADRAO = "https://raw.githubusercontent.com/adinailson88/malha-ia/main/dados/chamados.json"
ARQUIVOS_AGREGADOS = [
    "resumo_geral.json",
    "serie_mensal.json",
    "ranking_campus.json",
    "ranking_categoria.json",
    "ranking_categoria_raiz.json",
    "ranking_criticidade.json",
    "ranking_executor.json",
    "ranking_status.json",
    "matriz_campus_categoria.json",
    "manifest_hub.json",
]


def baixar_json(url: str, timeout: int, tentativas: int = 5) -> list[list[object]]:
    req = Request(url, headers={"User-Agent": "malha-estatisticas-associadas/1.0"})
    ultima_excecao: Exception | None = None
    for tentativa in range(1, tentativas + 1):
        try:
            with urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
            break
        except HTTPError as exc:
            ultima_excecao = exc
            if exc.code not in (429, 500, 502, 503, 504) or tentativa == tentativas:
                raise
        except (URLError, TimeoutError) as exc:
            ultima_excecao = exc
            if tentativa == tentativas:
                raise
        espera = min(60, 2 ** tentativa)
        print(f"AVISO tentativa {tentativa}/{tentativas} falhou para {url}: {ultima_excecao}. Nova tentativa em {espera}s.")
        time.sleep(espera)
    else:
        raise RuntimeError(f"Falha ao baixar {url}: {ultima_excecao}")
    dados = json.loads(raw)
    if not isinstance(dados, list) or not dados:
        raise RuntimeError("JSON de chamados nao esta no formato de tabela.")
    return dados


def falha_transitoria(exc: Exception) -> bool:
    if isinstance(exc, HTTPError):
        return exc.code in (429, 500, 502, 503, 504)
    return isinstance(exc, (URLError, TimeoutError))


def normalizar_header(h: object) -> str:
    texto = str(h or "").strip()
    mapa = {
        "TÍTULO": "TITULO",
        "DATA E HORA ABERTURA": "DATA_ABERTURA",
        "CATEGORIA COMPLETA": "CATEGORIA",
        "Valor do chamado": "VALOR",
        "Classificação IA": "CLASSIFICACAO_IA",
        "Avaliação (%)": "AVALIACAO",
        "Criticidade Atribuída por IA": "CRITICIDADE",
    }
    return mapa.get(texto, texto)


def tabela_para_objetos(tabela: list[list[object]]) -> list[dict[str, object]]:
    headers = [normalizar_header(h) for h in tabela[0]]
    rows: list[dict[str, object]] = []
    for linha in tabela[1:]:
        if not linha:
            continue
        obj = {headers[i]: linha[i] if i < len(linha) else "" for i in range(len(headers))}
        rows.append(obj)
    return rows


def id_preenchido(row: dict[str, object]) -> bool:
    return bool(str(row.get("ID Chamado", "")).strip())


def num(v: object) -> float | None:
    if v in (None, ""):
        return None
    try:
        return float(str(v).replace(",", "."))
    except ValueError:
        return None


def mes_ref(valor: object) -> str:
    texto = str(valor or "").strip()
    if len(texto) < 7:
        return "Sem data"
    return texto[:7]


def categoria_raiz(cat: object) -> str:
    texto = str(cat or "").strip()
    if not texto:
        return "Sem categoria"
    return texto.split(">")[0].strip() or "Sem categoria"


def tabular(headers: list[str], rows: list[list[object]]) -> list[list[object]]:
    return [headers] + rows


def salvar(path: Path, dados: list[list[object]] | dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dados, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def agregados_existentes(saida: Path) -> bool:
    return all((saida / nome).exists() for nome in ARQUIVOS_AGREGADOS)


def ranking(counter: Counter[str], extra: dict[str, dict[str, float]] | None = None) -> list[list[object]]:
    headers = ["Dimensao", "N_chamados", "Valor_total_R$", "Valor_medio_R$", "Confianca_media"]
    rows = []
    for chave, n in counter.most_common():
        info = (extra or {}).get(chave, {})
        total = info.get("valor_total", 0.0)
        conf_soma = info.get("conf_soma", 0.0)
        conf_n = info.get("conf_n", 0.0)
        rows.append([
            chave,
            n,
            round(total, 2),
            round(total / n, 2) if n else 0,
            round(conf_soma / conf_n, 4) if conf_n else "",
        ])
    return tabular(headers, rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera estatisticas associadas agregadas do Malha IA.")
    parser.add_argument("--url", default=URL_CHAMADOS_PADRAO)
    parser.add_argument("--saida", default="dados")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()
    saida = Path(args.saida)

    try:
        tabela = baixar_json(args.url, args.timeout)
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, RuntimeError) as exc:
        if falha_transitoria(exc) and agregados_existentes(saida):
            print(f"AVISO Falha transitória ao baixar chamados do hub: {exc}; mantidos agregados locais existentes.")
            return 0
        raise SystemExit(f"Falha ao baixar chamados do hub: {exc}") from exc

    rows_origem = tabela_para_objetos(tabela)
    rows = [row for row in rows_origem if id_preenchido(row)]

    total_origem = len(rows_origem)
    total = len(rows)
    ids = {str(r.get("ID Chamado", "")).strip() for r in rows if str(r.get("ID Chamado", "")).strip()}
    valores = [num(r.get("VALOR")) or 0.0 for r in rows]
    confiancas = [num(r.get("AVALIACAO")) for r in rows if num(r.get("AVALIACAO")) is not None]
    datas = [str(r.get("DATA_ABERTURA", "")).strip() for r in rows if str(r.get("DATA_ABERTURA", "")).strip()]
    custos_positivos = [v for v in valores if v > 0]

    cont_mes: Counter[str] = Counter()
    cont_campus: Counter[str] = Counter()
    cont_categoria: Counter[str] = Counter()
    cont_categoria_raiz: Counter[str] = Counter()
    cont_status: Counter[str] = Counter()
    cont_executor: Counter[str] = Counter()
    cont_criticidade: Counter[str] = Counter()
    extra_campus: dict[str, dict[str, float]] = defaultdict(lambda: {"valor_total": 0.0, "conf_soma": 0.0, "conf_n": 0.0})
    extra_categoria: dict[str, dict[str, float]] = defaultdict(lambda: {"valor_total": 0.0, "conf_soma": 0.0, "conf_n": 0.0})
    extra_status: dict[str, dict[str, float]] = defaultdict(lambda: {"valor_total": 0.0, "conf_soma": 0.0, "conf_n": 0.0})
    matriz: dict[tuple[str, str], dict[str, float]] = defaultdict(lambda: {"n": 0.0, "valor_total": 0.0})
    serie: dict[str, dict[str, float]] = defaultdict(lambda: {"n": 0.0, "valor_total": 0.0, "conf_soma": 0.0, "conf_n": 0.0})

    for r in rows:
        campus = str(r.get("CAMPUS") or "Sem campus").strip() or "Sem campus"
        categoria = str(r.get("CATEGORIA") or "Sem categoria").strip() or "Sem categoria"
        status = str(r.get("STATUS") or "Sem status").strip() or "Sem status"
        executor = str(r.get("Executor") or "Sem executor").strip() or "Sem executor"
        criticidade = str(r.get("CRITICIDADE") or "Sem criticidade").strip() or "Sem criticidade"
        mes = mes_ref(r.get("DATA_ABERTURA"))
        valor = num(r.get("VALOR")) or 0.0
        conf = num(r.get("AVALIACAO"))

        cont_mes[mes] += 1
        cont_campus[campus] += 1
        cont_categoria[categoria] += 1
        cont_categoria_raiz[categoria_raiz(categoria)] += 1
        cont_status[status] += 1
        cont_executor[executor] += 1
        cont_criticidade[criticidade] += 1

        for extra in (extra_campus[campus], extra_categoria[categoria], extra_status[status]):
            extra["valor_total"] += valor
            if conf is not None:
                extra["conf_soma"] += conf
                extra["conf_n"] += 1

        serie[mes]["n"] += 1
        serie[mes]["valor_total"] += valor
        if conf is not None:
            serie[mes]["conf_soma"] += conf
            serie[mes]["conf_n"] += 1

        item = matriz[(campus, categoria_raiz(categoria))]
        item["n"] += 1
        item["valor_total"] += valor

    resumo = [
        ["Indicador", "Valor"],
        ["Total de chamados validos", total],
        ["Linhas origem no JSON", total_origem],
        ["Linhas vazias ignoradas", total_origem - total],
        ["IDs unicos", len(ids)],
        ["Primeira data", min(datas) if datas else ""],
        ["Ultima data", max(datas) if datas else ""],
        ["Valor total R$", round(sum(valores), 2)],
        ["Valor medio R$", round(sum(valores) / total, 2) if total else 0],
        ["Chamados com valor positivo", len(custos_positivos)],
        ["Confianca media IA", round(sum(confiancas) / len(confiancas), 4) if confiancas else ""],
        ["Campi distintos", len(cont_campus)],
        ["Categorias distintas", len(cont_categoria)],
    ]

    serie_rows = []
    for mes in sorted(serie):
        info = serie[mes]
        n = int(info["n"])
        serie_rows.append([
            mes,
            n,
            round(info["valor_total"], 2),
            round(info["valor_total"] / n, 2) if n else 0,
            round(info["conf_soma"] / info["conf_n"], 4) if info["conf_n"] else "",
        ])

    matriz_rows = []
    for (campus, cat), info in sorted(matriz.items(), key=lambda item: (-item[1]["n"], item[0][0], item[0][1])):
        matriz_rows.append([campus, cat, int(info["n"]), round(info["valor_total"], 2)])

    salvar(saida / "resumo_geral.json", resumo)
    salvar(saida / "serie_mensal.json", tabular(["Mes", "N_chamados", "Valor_total_R$", "Valor_medio_R$", "Confianca_media"], serie_rows))
    salvar(saida / "ranking_campus.json", ranking(cont_campus, extra_campus))
    salvar(saida / "ranking_categoria.json", ranking(cont_categoria, extra_categoria))
    salvar(saida / "ranking_categoria_raiz.json", tabular(["Categoria_raiz", "N_chamados"], cont_categoria_raiz.most_common()))
    salvar(saida / "ranking_criticidade.json", tabular(["Criticidade", "N_chamados"], cont_criticidade.most_common()))
    salvar(saida / "ranking_executor.json", tabular(["Executor", "N_chamados"], cont_executor.most_common()))
    salvar(saida / "ranking_status.json", ranking(cont_status, extra_status))
    salvar(saida / "matriz_campus_categoria.json", tabular(["Campus", "Categoria_raiz", "N_chamados", "Valor_total_R$"], matriz_rows))
    salvar(
        saida / "manifest_hub.json",
        {
            "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
            "fonte": args.url,
            "linhas_origem": total_origem,
            "linhas_validas": total,
            "linhas_ignoradas_vazias": total_origem - total,
            "criterio_linha_valida": "ID Chamado preenchido",
            "observacao": "Base bruta nao foi salva neste repositorio; somente agregados derivados.",
        },
    )

    print(f"Estatisticas geradas em {saida} a partir de {total} chamados validos; {total_origem - total} linhas vazias ignoradas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
