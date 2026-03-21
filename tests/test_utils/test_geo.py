from __future__ import annotations

from unittest.mock import patch

import pytest


class TestCheckGeopandas:
    def test_returns_module(self):
        gpd = pytest.importorskip("geopandas")
        from agrobr.utils.geo import check_geopandas

        result = check_geopandas()
        assert result is gpd

    def test_raises_import_error(self):
        from agrobr.utils import geo

        with (
            patch.object(geo, "check_geopandas", side_effect=ImportError("agrobr[geo]")),
            pytest.raises(ImportError, match="agrobr\\[geo\\]"),
        ):
            geo.check_geopandas()
