from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.mapbiomas_alerta.client import _get_token


class TestGetToken:
    def test_from_param(self):
        assert _get_token("my-token") == "my-token"

    def test_from_env(self):
        import os

        with patch.dict(os.environ, {"AGROBR_MAPBIOMAS_ALERTA_TOKEN": "env-tok"}):
            assert _get_token() == "env-tok"

    def test_missing_raises(self):
        import os

        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AGROBR_MAPBIOMAS_ALERTA_TOKEN", None)
            with pytest.raises(SourceUnavailableError):
                _get_token()


class TestFetchAlertas:
    @pytest.mark.asyncio
    async def test_single_page(self):
        from agrobr.mapbiomas_alerta import client

        page_data = {
            "alerts": {
                "collection": [{"alertCode": 1}, {"alertCode": 2}],
                "metadata": {"currentPage": 1, "totalCount": 2, "totalPages": 1},
            }
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": page_data}
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "agrobr.mapbiomas_alerta.client.retry_on_status",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            records, url = await client.fetch_alertas(token="tok", limit=100)

        assert len(records) == 2
        assert records[0]["alertCode"] == 1

    @pytest.mark.asyncio
    async def test_empty_response(self):
        from agrobr.mapbiomas_alerta import client

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "alerts": {
                    "collection": [],
                    "metadata": {"currentPage": 1, "totalCount": 0, "totalPages": 0},
                }
            }
        }
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "agrobr.mapbiomas_alerta.client.retry_on_status",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            records, url = await client.fetch_alertas(token="tok")

        assert records == []

    @pytest.mark.asyncio
    async def test_multi_page(self):
        from agrobr.mapbiomas_alerta import client

        page1_data = {
            "alerts": {
                "collection": [{"alertCode": i} for i in range(100)],
                "metadata": {"currentPage": 1, "totalCount": 101, "totalPages": 2},
            }
        }
        page2_data = {
            "alerts": {
                "collection": [{"alertCode": 100}],
                "metadata": {"currentPage": 2, "totalCount": 101, "totalPages": 2},
            }
        }

        mock_resp1 = MagicMock()
        mock_resp1.status_code = 200
        mock_resp1.json.return_value = {"data": page1_data}
        mock_resp1.raise_for_status = MagicMock()

        mock_resp2 = MagicMock()
        mock_resp2.status_code = 200
        mock_resp2.json.return_value = {"data": page2_data}
        mock_resp2.raise_for_status = MagicMock()

        with patch(
            "agrobr.mapbiomas_alerta.client.retry_on_status",
            new_callable=AsyncMock,
            side_effect=[mock_resp1, mock_resp2],
        ):
            records, url = await client.fetch_alertas(token="tok", limit=100)

        assert len(records) == 101

    @pytest.mark.asyncio
    async def test_graphql_error_raises(self):
        from agrobr.mapbiomas_alerta import client

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"errors": [{"message": "Something failed"}]}
        mock_resp.raise_for_status = MagicMock()

        with (
            patch(
                "agrobr.mapbiomas_alerta.client.retry_on_status",
                new_callable=AsyncMock,
                return_value=mock_resp,
            ),
            pytest.raises(SourceUnavailableError, match="GraphQL error"),
        ):
            await client.fetch_alertas(token="tok")

    @pytest.mark.asyncio
    async def test_bounding_box_passthrough(self):
        from agrobr.mapbiomas_alerta import client

        page_data = {
            "alerts": {
                "collection": [{"alertCode": 1}],
                "metadata": {"currentPage": 1, "totalCount": 1, "totalPages": 1},
            }
        }
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": page_data}
        mock_resp.raise_for_status = MagicMock()

        bbox_input = [{"swLat": -10.0, "swLng": -55.0, "neLat": -5.0, "neLng": -50.0}]
        with patch(
            "agrobr.mapbiomas_alerta.client.retry_on_status",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            records, url = await client.fetch_alertas(token="tok", bounding_box=bbox_input)

        assert len(records) == 1


class TestFetchAlertDateRange:
    @pytest.mark.asyncio
    async def test_returns_date_range(self):
        from agrobr.mapbiomas_alerta import client

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "alertDateRange": {
                    "minDetectedAt": "2020-01-15",
                    "maxDetectedAt": "2024-12-31",
                    "minPublishedAt": "2020-02-01",
                    "maxPublishedAt": "2024-12-31",
                }
            }
        }
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "agrobr.mapbiomas_alerta.client.retry_on_status",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            result, url = await client.fetch_alert_date_range()

        assert result["minDetectedAt"] == "2020-01-15"
        assert result["maxDetectedAt"] == "2024-12-31"


class TestFetchLastPublication:
    @pytest.mark.asyncio
    async def test_returns_publication(self):
        from agrobr.mapbiomas_alerta import client

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {"lastAlertPublication": {"publishedAt": "2024-06-24T12:00:00Z", "total": 1000}}
        }
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "agrobr.mapbiomas_alerta.client.retry_on_status",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            result, url = await client.fetch_last_publication()

        assert result["publishedAt"] == "2024-06-24T12:00:00Z"
        assert result["total"] == 1000
