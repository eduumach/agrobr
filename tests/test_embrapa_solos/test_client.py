from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
async def test_fetch_perfis_calls_paginated():
    with patch("agrobr.embrapa_solos.client.fetch_wfs_paginated", new_callable=AsyncMock) as mock:
        mock.return_value = ([b"page1"], "https://example.com")

        from agrobr.embrapa_solos.client import fetch_perfis

        pages, url = await fetch_perfis()
        assert len(pages) == 1
        assert "embrapa_solos" in str(mock.call_args)


@pytest.mark.asyncio
async def test_fetch_perfis_no_cql():
    with patch("agrobr.embrapa_solos.client.fetch_wfs_paginated", new_callable=AsyncMock) as mock:
        mock.return_value = ([b"page1"], "https://example.com")

        from agrobr.embrapa_solos.client import fetch_perfis

        await fetch_perfis()
        call_kwargs = mock.call_args
        assert "cql" not in call_kwargs.kwargs or call_kwargs.kwargs.get("cql") is None


@pytest.mark.asyncio
async def test_fetch_perfis_geo_no_cql():
    with patch(
        "agrobr.embrapa_solos.client.fetch_wfs", new_callable=AsyncMock, return_value=b"x" * 100
    ):
        from agrobr.embrapa_solos.client import fetch_perfis_geo

        _, url = await fetch_perfis_geo()
        assert "CQL_FILTER" not in url


@pytest.mark.asyncio
async def test_fetch_mapa_solos_calls_paginated():
    with patch("agrobr.embrapa_solos.client.fetch_wfs_paginated", new_callable=AsyncMock) as mock:
        mock.return_value = ([b"page1"], "https://example.com")

        from agrobr.embrapa_solos.client import fetch_mapa_solos

        pages, url = await fetch_mapa_solos()
        assert mock.called
