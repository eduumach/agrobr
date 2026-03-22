from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.ana.client import fetch_layer


class TestFetchLayer:
    @pytest.mark.asyncio
    async def test_pagination(self):
        page_content = b'{"features": [{"attributes": {"OBJECTID": 1}}]}'

        with (
            patch(
                "agrobr.utils.geo.fetch_arcgis_count",
                new_callable=AsyncMock,
                return_value=1500,
            ),
            patch(
                "agrobr.utils.geo.fetch_wfs",
                new_callable=AsyncMock,
                return_value=page_content,
            ),
        ):
            pages, url = await fetch_layer("pivos_irrigacao")

        assert len(pages) == 2
        assert url != ""

    @pytest.mark.asyncio
    async def test_empty_result(self):
        with patch(
            "agrobr.utils.geo.fetch_arcgis_count",
            new_callable=AsyncMock,
            return_value=0,
        ):
            pages, url = await fetch_layer("pivos_irrigacao")

        assert pages == []

    @pytest.mark.asyncio
    async def test_bbox_passthrough(self):
        bbox = (-50.0, -15.0, -45.0, -10.0)

        with (
            patch(
                "agrobr.utils.geo.fetch_arcgis_count",
                new_callable=AsyncMock,
                return_value=0,
            ) as mock_count,
        ):
            await fetch_layer("pivos_irrigacao", bbox=bbox)

        call_kwargs = mock_count.call_args
        assert call_kwargs[1]["bbox"] == bbox
