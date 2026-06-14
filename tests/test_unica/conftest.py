from __future__ import annotations

import pytest

from agrobr.unica import api, client


@pytest.fixture(autouse=True)
def _reset_unica_caches():
    client._pdf_cache = None
    api._parsed_cache = None
    yield
    client._pdf_cache = None
    api._parsed_cache = None
