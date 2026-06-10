"""Pytest configuration and fixtures."""

from __future__ import annotations

import sys

import pytest

try:
    import _duckdb

    sys.modules.setdefault("_duckdb._sqltypes", _duckdb._sqltypes)
    sys.modules.setdefault("_duckdb._func", _duckdb._func)
except (ImportError, AttributeError):
    pass


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
    import structlog

    from agrobr.config import reset_config
    from agrobr.http.rate_limiter import RateLimiter

    reset_config()
    RateLimiter.reset()

    from agrobr.utils.warnings import warn_once_reset

    warn_once_reset()
    structlog.reset_defaults()


@pytest.fixture
def sample_html_cepea() -> str:
    """HTML mínimo para testes de parsing CEPEA."""
    return """
    <html>
    <head><title>CEPEA - Indicador</title></head>
    <body>
        <div id="content">
            <table class="indicador" id="imagenet-indicador1">
                <tr>
                    <th></th>
                    <th>Valor R$*</th>
                    <th>Var./Dia</th>
                    <th>Var./Mês</th>
                    <th>Valor US$*</th>
                </tr>
                <tr>
                    <td>01/02/2024</td>
                    <td>145,50</td>
                    <td>+0,5%</td>
                    <td>+1,2%</td>
                    <td>28,50</td>
                </tr>
                <tr>
                    <td>31/01/2024</td>
                    <td>144,78</td>
                    <td>-0,3%</td>
                    <td>-0,1%</td>
                    <td>28,30</td>
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
