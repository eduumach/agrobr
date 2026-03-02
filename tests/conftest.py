"""Pytest configuration and fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _fast_retry(monkeypatch):
    monkeypatch.setenv("AGROBR_HTTP_RETRY_BASE_DELAY", "0.001")
    monkeypatch.setenv("AGROBR_HTTP_RETRY_MAX_DELAY", "0.01")
    from agrobr import constants

    for field in constants.HTTPSettings.model_fields:
        if field.startswith("rate_limit_"):
            monkeypatch.setenv(f"AGROBR_HTTP_{field.upper()}", "0.001")


@pytest.fixture(autouse=True)
def _reset_global_state():
    yield
    from agrobr.config import reset_config
    from agrobr.http.rate_limiter import RateLimiter

    reset_config()
    RateLimiter.reset()

    from agrobr.utils.warnings import warn_once_reset

    warn_once_reset()


@pytest.fixture
def sample_html_cepea() -> str:
    """HTML mínimo para testes de parsing CEPEA."""
    return """
    <html>
    <head><title>CEPEA - Indicador</title></head>
    <body>
        <div id="content">
            <table class="indicador" id="tblIndicador">
                <tr>
                    <th>Data</th>
                    <th>Valor (R$/sc 60kg)</th>
                    <th>Variação</th>
                </tr>
                <tr>
                    <td>01/02/2024</td>
                    <td>145,50</td>
                    <td>+0,5%</td>
                </tr>
                <tr>
                    <td>31/01/2024</td>
                    <td>144,78</td>
                    <td>-0,3%</td>
                </tr>
            </table>
        </div>
        <p>Indicador CEPEA/ESALQ</p>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_empty() -> str:
    """HTML sem tabelas para testar erros."""
    return "<html><body><p>No data available</p></body></html>"
