from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx


def make_mock_response(
    status_code: int = 200,
    *,
    text: str | None = None,
    content: bytes | None = None,
    json_data: dict | list | None = None,
    headers: dict | None = None,
    url: str = "https://test.agrobr.dev/mock",
    charset_encoding: str | None = None,
) -> MagicMock:
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code

    if text is not None:
        resp.text = text
    if content is not None:
        resp.content = content
    if json_data is not None:
        resp.json.return_value = json_data

    if headers is not None:
        resp.headers = headers
    elif charset_encoding is not None:
        resp.headers = {"content-type": f"text/html; charset={charset_encoding}"}
    else:
        resp.headers = {}

    resp.url = url

    if charset_encoding is not None:
        resp.charset_encoding = charset_encoding

    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"HTTP {status_code}", request=MagicMock(), response=resp
        )

    return resp


def make_mock_async_client() -> AsyncMock:
    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    return client


def make_alert_settings(
    *,
    enabled: bool = True,
    slack_webhook: str | None = None,
    discord_webhook: str | None = None,
    sendgrid_api_key: str | None = None,
    email_from: str = "alerts@agrobr.dev",
    email_to: list[str] | None = None,
    discord_embed_char_limit: int = 3900,
) -> MagicMock:
    settings = MagicMock()
    settings.enabled = enabled
    settings.slack_webhook = slack_webhook
    settings.discord_webhook = discord_webhook
    settings.sendgrid_api_key = sendgrid_api_key
    settings.email_from = email_from
    settings.email_to = email_to if email_to is not None else []
    settings.discord_embed_char_limit = discord_embed_char_limit
    return settings
