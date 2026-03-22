from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.sfb.client import fetch_layer


class TestFetchLayer:
    @pytest.mark.asyncio
    async def test_pagination(self):
        page_content = b'{"features": [{"attributes": {"OBJECTID": 1}}]}'

        with (
            patch(
                "agrobr.utils.geo.fetch_arcgis_count",
                new_callable=AsyncMock,
                return_value=3500,
            ),
            patch(
                "agrobr.utils.geo.fetch_wfs",
                new_callable=AsyncMock,
                return_value=page_content,
            ),
        ):
            pages, url = await fetch_layer("cnfp")

        assert len(pages) == 2
        assert url != ""

    @pytest.mark.asyncio
    async def test_empty_result(self):
        with patch(
            "agrobr.utils.geo.fetch_arcgis_count",
            new_callable=AsyncMock,
            return_value=0,
        ):
            pages, url = await fetch_layer("cnfp")

        assert pages == []
