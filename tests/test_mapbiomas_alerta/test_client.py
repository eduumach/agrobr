from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agrobr.exceptions import SourceUnavailableError
from agrobr.mapbiomas_alerta.client import _get_token


class TestGetToken:
    def test_from_param(self):
        assert _get_token("my-token") == "my-token"

    def test_from_env(self):
        with patch.dict(os.environ, {"AGROBR_MAPBIOMAS_ALERTA_TOKEN": "env-token"}):
            assert _get_token() == "env-token"

    def test_missing_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("AGROBR_MAPBIOMAS_ALERTA_TOKEN", None)
            with pytest.raises(SourceUnavailableError):
                _get_token()


class TestFetchAlertas:
    @pytest.mark.asyncio
    async def test_single_page(self):
        from agrobr.mapbiomas_alerta import client

        page_data = {"alerts": [{"alertCode": "A1"}, {"alertCode": "A2"}]}
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
        assert records[0]["alertCode"] == "A1"

    @pytest.mark.asyncio
    async def test_empty_response(self):
        from agrobr.mapbiomas_alerta import client

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"data": {"alerts": []}}
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

        page1_data = {"alerts": [{"alertCode": f"A{i}"} for i in range(100)]}
        page2_data = {"alerts": [{"alertCode": "A100"}]}

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
        mock_resp.json.return_value = {"errors": [{"message": "Auth failed"}]}
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


class TestFetchAlertDateRange:
    @pytest.mark.asyncio
    async def test_returns_date_range(self):
        from agrobr.mapbiomas_alerta import client

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {"alertDateRange": {"minDate": "2020-01-01", "maxDate": "2024-12-31"}}
        }
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "agrobr.mapbiomas_alerta.client.retry_on_status",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            result, url = await client.fetch_alert_date_range()

        assert result["minDate"] == "2020-01-01"
        assert result["maxDate"] == "2024-12-31"


class TestFetchLastPublication:
    @pytest.mark.asyncio
    async def test_returns_publication(self):
        from agrobr.mapbiomas_alerta import client

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {"lastAlertPublication": {"date": "2024-06-24", "alertsCount": 1000}}
        }
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "agrobr.mapbiomas_alerta.client.retry_on_status",
            new_callable=AsyncMock,
            return_value=mock_resp,
        ):
            result, url = await client.fetch_last_publication()

        assert result["date"] == "2024-06-24"
        assert result["alertsCount"] == 1000
