from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_json(name: str) -> dict[str, Any]:
    path = FIXTURES_DIR / "json" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _load_html(name: str) -> str:
    path = FIXTURES_DIR / "html" / name
    return path.read_text(encoding="utf-8")


@pytest.fixture
def category_2026_p1_payload() -> dict[str, Any]:
    return _load_json("category_2026_p1.json")


@pytest.fixture
def category_2026_p2_payload() -> dict[str, Any]:
    return _load_json("category_2026_p2.json")


@pytest.fixture
def category_empty_payload() -> dict[str, Any]:
    return _load_json("category_empty.json")


@pytest.fixture
def article_w16_payload() -> dict[str, Any]:
    return _load_json("article_w16_2026.json")


@pytest.fixture
def wrapper_min_html() -> str:
    return _load_html("wrapper_min.html")


@pytest.fixture
def no_next_data_html() -> str:
    return _load_html("no_next_data.html")


@pytest.fixture
def malformed_json_html() -> str:
    return _load_html("malformed_json.html")


def make_html(payload: dict[str, Any]) -> str:
    return (
        "<html><body>"
        '<script id="__NEXT_DATA__" type="application/json">'
        + json.dumps(payload)
        + "</script></body></html>"
    )


@pytest.fixture
def html_factory():
    return make_html


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("AGROBR_CACHE_CACHE_DIR", str(tmp_path / "agrobr_cache"))
    return tmp_path / "agrobr_cache"


@pytest.fixture(autouse=True)
def _reset_anec_list_cache():
    from agrobr.anec import client as _client
    from agrobr.anec.api import _parse_cache_clear

    _client._list_cache_clear()
    _parse_cache_clear()
    yield
    _client._list_cache_clear()
    _parse_cache_clear()
