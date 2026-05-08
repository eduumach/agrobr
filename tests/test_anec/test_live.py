"""Live tests contra ANEC — rodam com `pytest -m integration`.

Detectam quebras upstream:
- cuid 2026 invalidado pelo CMS
- Layout do PDF mudou (fingerprint diverge do baseline conhecido)
- Site fora do ar
- Estrutura `__NEXT_DATA__` mudou

Não rodam em CI default (deselected via `addopts = "-m 'not benchmark and not slow'"`).
Rode manualmente: `pytest tests/test_anec/test_live.py -m integration -v`.
"""

from __future__ import annotations

import pytest

from agrobr.anec import client, parser


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_list_2026_articles_minimum():
    articles = await client.list_articles(2026)
    assert len(articles) >= 4, (
        f"Esperado >=4 artigos em 2026, recebido {len(articles)}. "
        "Possível: cuid mudou, CMS reorganizado, ou site fora."
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_categories_cuid_unchanged():
    from agrobr.anec.models import CATEGORIES_BY_YEAR

    cuid = CATEGORIES_BY_YEAR[2026]
    articles = await client.list_articles(2026)
    assert articles, f"cuid {cuid!r} de 2026 retornou lista vazia"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_fetch_latest_pdf_size():
    pdf_bytes, _, article = await client.fetch_latest_pdf(year=2026, use_cache=False)
    assert len(pdf_bytes) > 100_000, (
        f"PDF de {article.title_en!r} muito pequeno ({len(pdf_bytes)} bytes). "
        "Possível: ANEC publicou versão preview ou layout reduzido."
    )
    assert pdf_bytes.startswith(b"%PDF"), "Magic bytes %PDF ausentes — não é PDF"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_parse_latest_full():
    pdf_bytes, _, _ = await client.fetch_latest_pdf(year=2026, use_cache=False)
    report = parser.parse_anec_pdf(pdf_bytes)

    assert len(report.weekly_shipments) > 0, "weekly_shipments vazio — parser falhou"
    assert report.weekly_shipments["porto"].nunique() >= 15, (
        "menos de 15 portos detectados — possível mudança de layout"
    )
    assert report.weekly_shipments["produto"].nunique() == 6, (
        "número de produtos != 6 — ANEC pode ter mudado o conjunto"
    )
    assert len(report.monthly_shipments) > 0
    assert len(report.fingerprint) == 16


@pytest.mark.integration
@pytest.mark.asyncio
async def test_live_fingerprint_format_stable():
    pdf_bytes, _, _ = await client.fetch_latest_pdf(year=2026, use_cache=False)
    report = parser.parse_anec_pdf(pdf_bytes)

    assert isinstance(report.fingerprint, str)
    assert len(report.fingerprint) == 16
    assert all(c in "0123456789abcdef" for c in report.fingerprint), (
        f"Fingerprint não-hex: {report.fingerprint!r}"
    )
