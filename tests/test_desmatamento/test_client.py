from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from agrobr.desmatamento.client import _build_wfs_url, _uf_to_estado
from agrobr.exceptions import SourceUnavailableError


class TestBuildWfsUrl:
    def test_basic_url(self):
        url = _build_wfs_url("workspace1", "layer1", ["col1", "col2"])
        assert "workspace1/ows" in url
        assert "typeName=workspace1:layer1" in url
        assert "propertyName=col1,col2" in url
        assert "outputFormat=csv" in url

    def test_with_cql_filter(self):
        url = _build_wfs_url("ws", "ly", ["c1"], cql_filter="year=2023")
        assert "CQL_FILTER=" in url

    def test_max_features(self):
        url = _build_wfs_url("ws", "ly", ["c1"], max_features=100)
        assert "maxFeatures=100" in url

    def test_default_max_features(self):
        url = _build_wfs_url("ws", "ly", ["c1"])
        assert "maxFeatures=50000" in url

    def test_output_format_json(self):
        url = _build_wfs_url("ws", "ly", ["c1"], output_format="application/json")
        assert "outputFormat=application/json" in url

    def test_output_format_default_csv(self):
        url = _build_wfs_url("ws", "ly", ["c1"])
        assert "outputFormat=csv" in url


class TestUfToEstado:
    def test_known_uf(self):
        assert _uf_to_estado("MT") is not None

    def test_lowercase_uf(self):
        assert _uf_to_estado("mt") is not None

    def test_unknown_uf(self):
        assert _uf_to_estado("XX") is None

    def test_sp(self):
        result = _uf_to_estado("SP")
        assert result is not None


class TestFetchProdes:
    @pytest.mark.asyncio
    async def test_unsupported_bioma(self):
        with pytest.raises(SourceUnavailableError, match="nao suportado"):
            from agrobr.desmatamento.client import fetch_prodes

            await fetch_prodes("bioma_invalido")

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        from agrobr.desmatamento.client import fetch_prodes

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"x" * 5000
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            content, url = await fetch_prodes("Amazônia")
        assert len(content) >= 5000

    @pytest.mark.asyncio
    async def test_with_ano_and_uf(self):
        from agrobr.desmatamento.client import fetch_prodes

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"x" * 5000
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            content, url = await fetch_prodes("Amazônia", ano=2023, uf="MT")
        assert len(content) >= 5000


class TestFetchDeter:
    @pytest.mark.asyncio
    async def test_unsupported_bioma(self):
        from agrobr.desmatamento.client import fetch_deter

        with pytest.raises(SourceUnavailableError, match="nao suportado"):
            await fetch_deter("bioma_invalido")

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        from agrobr.desmatamento.client import fetch_deter

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"x" * 5000
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            content, url = await fetch_deter(
                "Amazônia", uf="PA", data_inicio="2024-01-01", data_fim="2024-06-01"
            )
        assert len(content) >= 5000

    @pytest.mark.asyncio
    async def test_404_raises(self):
        from agrobr.desmatamento.client import fetch_deter

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.content = b"not found"
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
            pytest.raises(SourceUnavailableError),
        ):
            await fetch_deter("Amazônia")


class TestFetchDeterGeo:
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        from agrobr.desmatamento.client import fetch_deter_geo

        geojson = b'{"type":"FeatureCollection","features":[' + b"x" * 5000 + b"]}"
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = geojson
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            content, url = await fetch_deter_geo("Amazônia")
        assert len(content) >= 5000

    @pytest.mark.asyncio
    async def test_url_max_features_10000(self):
        from agrobr.desmatamento.client import fetch_deter_geo

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"x" * 5000
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            content, url = await fetch_deter_geo("Amazônia")
        assert "maxFeatures=10000" in url

    @pytest.mark.asyncio
    async def test_url_contains_geom_column_amz(self):
        from agrobr.desmatamento.client import fetch_deter_geo

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"x" * 5000
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            _, url = await fetch_deter_geo("Amazônia")
        assert "propertyName=geom," in url

    @pytest.mark.asyncio
    async def test_url_contains_geom_column_cerrado(self):
        from agrobr.desmatamento.client import fetch_deter_geo

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"x" * 5000
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            _, url = await fetch_deter_geo("Cerrado")
        assert "propertyName=st_multi," in url

    @pytest.mark.asyncio
    async def test_url_output_format_json(self):
        from agrobr.desmatamento.client import fetch_deter_geo

        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"x" * 5000
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_response)

        with (
            patch("agrobr.desmatamento.client.httpx.AsyncClient", return_value=mock_client),
            patch(
                "agrobr.desmatamento.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_response,
            ),
        ):
            _, url = await fetch_deter_geo("Amazônia")
        assert "outputFormat=application/json" in url

    @pytest.mark.asyncio
    async def test_unsupported_bioma(self):
        from agrobr.desmatamento.client import fetch_deter_geo

        with pytest.raises(SourceUnavailableError, match="nao suportado"):
            await fetch_deter_geo("bioma_invalido")
