"""Regenera os dados vivos do index.html via agrobr (ticker, painel de prova).

Substitui as regiões entre âncoras <!-- agrobr:X --> ... <!-- /agrobr:X -->.
Aborta sem tocar o arquivo se a coleta falhar nos sanity checks.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from typing import Any, cast

import pandas as pd

INDEX = Path(__file__).resolve().parent.parent / "index.html"

PRODUTOS_TICKER = [
    ("soja", "soja"),
    ("milho", "milho"),
    ("boi", "boi gordo"),
    ("cafe", "café"),
    ("trigo", "trigo"),
    ("algodao", "algodão"),
]

MESES_ABREV = {
    1: "jan",
    2: "fev",
    3: "mar",
    4: "abr",
    5: "mai",
    6: "jun",
    7: "jul",
    8: "ago",
    9: "set",
    10: "out",
    11: "nov",
    12: "dez",
}

UNIDADE_DISPLAY = {
    "BRL/sc60kg": "/ sc 60kg",
    "BRL/sc50kg": "/ sc 50kg",
    "BRL/ton": "/ ton",
    "BRL/@": "/ @",
    "BRL/kg": "/ kg",
    "BRL/L": "/ L",
    "cBRL/lb": "¢ / lb",
}


def fmt_brl(valor: float) -> str:
    s = f"{valor:,.2f}"
    return s.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def fmt_data_curta(data: Any) -> str:
    return f"{data.day:02d} {MESES_ABREV[data.month]} {data.year}"


async def coletar() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from agrobr import datasets

    ticker: list[dict[str, Any]] = []
    soja: dict[str, Any] = {}

    for key, label in PRODUTOS_TICKER:
        df = cast(pd.DataFrame, await datasets.preco_diario(key))
        df = df.sort_values("data").reset_index(drop=True)
        if len(df) < 2:
            raise RuntimeError(f"{key}: menos de 2 pregoes ({len(df)})")

        atual = float(df["valor"].iloc[-1])
        anterior = float(df["valor"].iloc[-2])
        if not (0 < atual < 100_000):
            raise RuntimeError(f"{key}: valor implausivel {atual}")

        ticker.append(
            {
                "label": label,
                "valor": atual,
                "var_pct": (atual / anterior - 1) * 100,
                "data": df["data"].iloc[-1],
            }
        )

        if key == "soja":
            serie = df.tail(30)
            soja = {
                "valores": [float(v) for v in serie["valor"]],
                "datas": list(serie["data"]),
                "unidade": str(serie["unidade"].iloc[-1]),
                "total_pregoes": len(df),
            }

    if len(ticker) != len(PRODUTOS_TICKER):
        raise RuntimeError("coleta incompleta do ticker")
    if len(soja.get("valores", [])) < 10:
        raise RuntimeError("serie da soja curta demais para o sparkline")

    return ticker, soja


def render_ticker(ticker: list[dict[str, Any]]) -> str:
    linhas = []
    for item in ticker:
        var = item["var_pct"]
        seta, classe = ("▲", "up") if var >= 0 else ("▼", "down")
        linhas.append(
            f'        <span class="ticker-item"><span class="tk-name">{item["label"]}</span>'
            f'<span class="tk-price">R$ {fmt_brl(item["valor"])}</span>'
            f'<span class="{classe}">{seta} {abs(var):.2f}'.replace(".", ",")
            + "%</span></span>"
        )
    data_ref = fmt_data_curta(max(item["data"] for item in ticker))
    linhas.append(
        f'        <span class="ticker-item"><span class="tk-stamp">'
        f"indicadores CEPEA · {data_ref} · coletados via agrobr</span></span>"
    )
    return "\n".join(linhas)


def render_proof(soja: dict[str, Any]) -> str:
    valores = soja["valores"]
    vmin, vmax = min(valores), max(valores)
    spread = (vmax - vmin) or 1.0
    n = len(valores)

    pontos = []
    for i, v in enumerate(valores):
        x = i * 300 / (n - 1)
        y = 76 - (v - vmin) / spread * 64
        pontos.append(f"{x:.1f},{y:.1f}")
    ultimo_x, ultimo_y = pontos[-1].split(",")

    rows = []
    for data, valor in list(zip(soja["datas"], valores))[-4:]:
        rows.append(
            f"        <div><span>{str(data)[:10]}</span>"
            f'<span class="v">{fmt_brl(valor)}</span></div>'
        )

    unidade = UNIDADE_DISPLAY.get(soja["unidade"], soja["unidade"])
    data_ref = fmt_data_curta(soja["datas"][-1])

    return (
        f'      <div class="proof-price">R$ {fmt_brl(valores[-1])} '
        f'<span class="currency">{unidade}</span></div>\n'
        f'      <div class="proof-meta">soja · indicador CEPEA/ESALQ · {data_ref}</div>\n'
        f'      <svg class="sparkline" viewBox="0 0 300 84" preserveAspectRatio="none" '
        f'aria-label="Últimos {n} pregões da soja">\n'
        f'        <polyline class="spark-path" points="{" ".join(pontos)}"/>\n'
        f'        <circle class="spark-dot" cx="{ultimo_x}" cy="{ultimo_y}" r="3.5"/>\n'
        f"      </svg>\n"
        f'      <div class="proof-rows">\n' + "\n".join(rows) + "\n      </div>"
    )


def render_pregoes(soja: dict[str, Any]) -> str:
    return (
        '<span class="code-line"><span class="cm"># '
        f"{soja['total_pregoes']} pregões · CEPEA → Notícias Agrícolas → cache</span></span>"
    )


def substituir(html: str, tag: str, conteudo: str) -> str:
    padrao = re.compile(
        rf"(<!-- agrobr:{tag} -->).*?(<!-- /agrobr:{tag} -->)",
        re.DOTALL,
    )
    if not padrao.search(html):
        raise RuntimeError(f"ancora agrobr:{tag} nao encontrada no index.html")
    return padrao.sub(rf"\g<1>\n{conteudo}\n        \g<2>", html, count=1)


def main() -> int:
    ticker, soja = asyncio.run(coletar())

    html = INDEX.read_text(encoding="utf-8")
    html = substituir(html, "ticker", render_ticker(ticker))
    html = substituir(html, "proof", render_proof(soja))

    padrao_pregoes = re.compile(
        r"(<!-- agrobr:pregoes -->).*?(<!-- /agrobr:pregoes -->)", re.DOTALL
    )
    html = padrao_pregoes.sub(rf"\g<1>{render_pregoes(soja)}\g<2>", html, count=1)

    INDEX.write_text(html, encoding="utf-8")
    print(f"index.html atualizado: soja R$ {fmt_brl(soja['valores'][-1])} ({soja['datas'][-1]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
