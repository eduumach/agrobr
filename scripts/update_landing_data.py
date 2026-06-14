"""Regenera os dados vivos das landings (PT e EN) via agrobr.

Substitui as regiões entre âncoras <!-- agrobr:X --> ... <!-- /agrobr:X -->
em index.html e en/index.html. Aborta sem tocar os arquivos se a coleta
falhar nos sanity checks.
"""

from __future__ import annotations

import asyncio
import re
import sys
from pathlib import Path
from typing import Any, cast

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

PRODUTOS_TICKER = ["soja", "milho", "boi", "cafe", "trigo", "algodao"]

LOCALES: dict[str, dict[str, Any]] = {
    "pt": {
        "index": ROOT / "index.html",
        "labels": {
            "soja": "soja",
            "milho": "milho",
            "boi": "boi gordo",
            "cafe": "café",
            "trigo": "trigo",
            "algodao": "algodão",
        },
        "meses": {
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
        },
        "data_fmt": "{dia:02d} {mes} {ano}",
        "stamp": "indicadores CEPEA · {data} · coletados via agrobr",
        "proof_meta": "soja · indicador CEPEA/ESALQ · {data}",
        "spark_aria": "Últimos {n} pregões da soja",
        "pregoes": "# {n} pregões · CEPEA → Notícias Agrícolas → cache",
        "decimal": ",",
        "milhar": ".",
        "unidades": {
            "BRL/sc60kg": "/ sc 60kg",
            "BRL/sc50kg": "/ sc 50kg",
            "BRL/ton": "/ ton",
            "BRL/@": "/ @",
            "BRL/kg": "/ kg",
            "BRL/L": "/ L",
            "cBRL/lb": "¢ / lb",
        },
    },
    "en": {
        "index": ROOT / "en" / "index.html",
        "labels": {
            "soja": "soybean",
            "milho": "corn",
            "boi": "live cattle",
            "cafe": "coffee",
            "trigo": "wheat",
            "algodao": "cotton",
        },
        "meses": {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        },
        "data_fmt": "{mes} {dia:02d}, {ano}",
        "stamp": "CEPEA indicators · {data} · fetched via agrobr",
        "proof_meta": "soybean · CEPEA/ESALQ indicator · {data}",
        "spark_aria": "Last {n} soybean trading days",
        "pregoes": "# {n} trading days · CEPEA → Notícias Agrícolas → cache",
        "decimal": ".",
        "milhar": ",",
        "unidades": {
            "BRL/sc60kg": "/ 60kg bag",
            "BRL/sc50kg": "/ 50kg bag",
            "BRL/ton": "/ ton",
            "BRL/@": "/ @ (15kg)",
            "BRL/kg": "/ kg",
            "BRL/L": "/ L",
            "cBRL/lb": "¢ / lb",
        },
    },
}


def fmt_valor(valor: float, loc: dict[str, Any]) -> str:
    s = f"{valor:,.2f}"
    return s.replace(",", "\x00").replace(".", loc["decimal"]).replace("\x00", loc["milhar"])


def fmt_data(data: Any, loc: dict[str, Any]) -> str:
    return str(loc["data_fmt"]).format(dia=data.day, mes=loc["meses"][data.month], ano=data.year)


async def coletar() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from agrobr import datasets

    ticker: list[dict[str, Any]] = []
    soja: dict[str, Any] = {}

    for key in PRODUTOS_TICKER:
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
                "key": key,
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


def render_ticker(ticker: list[dict[str, Any]], loc: dict[str, Any]) -> str:
    linhas = []
    for item in ticker:
        var = item["var_pct"]
        seta, classe = ("▲", "up") if var >= 0 else ("▼", "down")
        var_str = f"{abs(var):.2f}".replace(".", loc["decimal"])
        linhas.append(
            f'        <span class="ticker-item"><span class="tk-name">{loc["labels"][item["key"]]}</span>'
            f'<span class="tk-price">R$ {fmt_valor(item["valor"], loc)}</span>'
            f'<span class="{classe}">{seta} {var_str}%</span></span>'
        )
    data_ref = fmt_data(max(item["data"] for item in ticker), loc)
    stamp = str(loc["stamp"]).format(data=data_ref)
    linhas.append(f'        <span class="ticker-item"><span class="tk-stamp">{stamp}</span></span>')
    return "\n".join(linhas)


def render_proof(soja: dict[str, Any], loc: dict[str, Any]) -> str:
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
            f'<span class="v">{fmt_valor(valor, loc)}</span></div>'
        )

    unidade = loc["unidades"].get(soja["unidade"], soja["unidade"])
    data_ref = fmt_data(soja["datas"][-1], loc)
    meta = str(loc["proof_meta"]).format(data=data_ref)
    aria = str(loc["spark_aria"]).format(n=n)

    return (
        f'      <div class="proof-price">R$ {fmt_valor(valores[-1], loc)} '
        f'<span class="currency">{unidade}</span></div>\n'
        f'      <div class="proof-meta">{meta}</div>\n'
        f'      <svg class="sparkline" viewBox="0 0 300 84" preserveAspectRatio="none" '
        f'aria-label="{aria}">\n'
        f'        <polyline class="spark-path" points="{" ".join(pontos)}"/>\n'
        f'        <circle class="spark-dot" cx="{ultimo_x}" cy="{ultimo_y}" r="3.5"/>\n'
        f"      </svg>\n"
        f'      <div class="proof-rows">\n' + "\n".join(rows) + "\n      </div>"
    )


def render_pregoes(soja: dict[str, Any], loc: dict[str, Any]) -> str:
    texto = str(loc["pregoes"]).format(n=soja["total_pregoes"])
    return f'<span class="code-line"><span class="cm">{texto}</span></span>'


def substituir(html: str, tag: str, conteudo: str) -> str:
    padrao = re.compile(
        rf"(<!-- agrobr:{tag} -->).*?(<!-- /agrobr:{tag} -->)",
        re.DOTALL,
    )
    if not padrao.search(html):
        raise RuntimeError(f"ancora agrobr:{tag} nao encontrada")
    return padrao.sub(rf"\g<1>\n{conteudo}\n        \g<2>", html, count=1)


def atualizar_arquivo(
    loc: dict[str, Any], ticker: list[dict[str, Any]], soja: dict[str, Any]
) -> None:
    index: Path = loc["index"]
    html = index.read_text(encoding="utf-8")
    html = substituir(html, "ticker", render_ticker(ticker, loc))
    html = substituir(html, "proof", render_proof(soja, loc))

    padrao_pregoes = re.compile(
        r"(<!-- agrobr:pregoes -->).*?(<!-- /agrobr:pregoes -->)", re.DOTALL
    )
    html = padrao_pregoes.sub(rf"\g<1>{render_pregoes(soja, loc)}\g<2>", html, count=1)
    index.write_text(html, encoding="utf-8")


def main() -> int:
    ticker, soja = asyncio.run(coletar())
    for nome, loc in LOCALES.items():
        atualizar_arquivo(loc, ticker, soja)
        print(f"{loc['index'].relative_to(ROOT)} ({nome}) atualizado")
    print(f"soja R$ {soja['valores'][-1]:.2f} ({str(soja['datas'][-1])[:10]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
