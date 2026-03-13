from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.defensivos import client
from agrobr.exceptions import SourceUnavailableError
from tests.helpers import make_mock_async_client, make_mock_response


@pytest.mark.asyncio
async def test_download_formulados_ok():
    content = b"x" * (client.MIN_CSV_FORMULADOS + 1)
    mock_resp = make_mock_response(content=content)
    mock_client = make_mock_async_client()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with (
        patch("agrobr.defensivos.client.httpx.AsyncClient", return_value=mock_client),
        patch("agrobr.defensivos.client.retry_on_status", return_value=mock_resp),
    ):
        result = await client.download_formulados()
        assert len(result) > client.MIN_CSV_FORMULADOS


@pytest.mark.asyncio
async def test_download_formulados_too_small():
    content = b"small"
    mock_resp = make_mock_response(content=content)
    mock_client = make_mock_async_client()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with (
        patch("agrobr.defensivos.client.httpx.AsyncClient", return_value=mock_client),
        patch("agrobr.defensivos.client.retry_on_status", return_value=mock_resp),
        pytest.raises(SourceUnavailableError, match="too small"),
    ):
        await client.download_formulados()


@pytest.mark.asyncio
async def test_download_tecnicos_ok():
    content = b"x" * (client.MIN_CSV_TECNICOS + 1)
    mock_resp = make_mock_response(content=content)
    mock_client = make_mock_async_client()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with (
        patch("agrobr.defensivos.client.httpx.AsyncClient", return_value=mock_client),
        patch("agrobr.defensivos.client.retry_on_status", return_value=mock_resp),
    ):
        result = await client.download_tecnicos()
        assert len(result) > client.MIN_CSV_TECNICOS


@pytest.mark.asyncio
async def test_download_tecnicos_too_small():
    content = b"tiny"
    mock_resp = make_mock_response(content=content)
    mock_client = make_mock_async_client()
    mock_client.get = AsyncMock(return_value=mock_resp)

    with (
        patch("agrobr.defensivos.client.httpx.AsyncClient", return_value=mock_client),
        patch("agrobr.defensivos.client.retry_on_status", return_value=mock_resp),
        pytest.raises(SourceUnavailableError, match="too small"),
    ):
        await client.download_tecnicos()
