from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from agrobr.exceptions import ParseError
from agrobr.ibama.models import COLUNAS_SAIDA, COLUNAS_SAIDA_GEO
from agrobr.ibama.parser import PARSER_VERSION, parse_embargos_csv, parse_embargos_geo

GOLDEN = Path(__file__).parent.parent / "golden_data" / "ibama" / "termo_embargo_sample.csv"


def _golden_bytes() -> bytes:
    return GOLDEN.read_bytes()


class TestParserVersion:
    def test_version_bumped_para_formato_sifisc(self):
        assert PARSER_VERSION >= 2


class TestParseEmbargosCsv:
    def test_golden_valido(self):
        df = parse_embargos_csv(_golden_bytes())

        assert len(df) == 40
        assert list(df.columns) == COLUNAS_SAIDA

    def test_dtypes(self):
        df = parse_embargos_csv(_golden_bytes())

        assert pd.api.types.is_datetime64_any_dtype(df["data_embargo"])
        assert pd.api.types.is_datetime64_any_dtype(df["data_desembargo"])
        assert pd.api.types.is_float_dtype(df["area_embargada_ha"])
        assert pd.api.types.is_float_dtype(df["latitude"])
        assert pd.api.types.is_bool_dtype(df["cancelado"])

    def test_area_decimal_br_convertida(self):
        df = parse_embargos_csv(_golden_bytes())

        areas = df["area_embargada_ha"].dropna()
        assert len(areas) > 0
        assert (areas >= 0).all()
        assert (areas < 1_000_000).all()

    def test_uf_maiuscula(self):
        df = parse_embargos_csv(_golden_bytes())

        ufs = df["uf"].unique()
        assert all(u == u.upper() for u in ufs if u)
        assert len(ufs) > 20

    def test_cancelados_presentes(self):
        df = parse_embargos_csv(_golden_bytes())

        assert df["cancelado"].sum() >= 5

    def test_filtro_uf(self):
        df = parse_embargos_csv(_golden_bytes(), uf="PA")

        assert len(df) > 0
        assert (df["uf"] == "PA").all()

    def test_filtro_bbox(self):
        df_all = parse_embargos_csv(_golden_bytes())
        bbox = (-55.0, -10.0, -45.0, 0.0)
        df = parse_embargos_csv(_golden_bytes(), bbox=bbox)

        assert len(df) < len(df_all)
        assert df["longitude"].between(-55.0, -45.0).all()
        assert df["latitude"].between(-10.0, 0.0).all()

    def test_layout_drift_raises_parse_error(self):
        csv_quebrado = b"COLUNA_A;COLUNA_B\n1;2\n"

        with pytest.raises(ParseError, match="Usecols"):
            parse_embargos_csv(csv_quebrado)


class TestParseEmbargosGeo:
    def test_golden_geo(self):
        gpd = pytest.importorskip("geopandas")

        gdf = parse_embargos_geo(_golden_bytes())

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 24
        assert list(gdf.columns) == COLUNAS_SAIDA_GEO
        assert gdf.crs is not None
        assert gdf.geometry.notna().all()

    def test_geo_filtro_uf_aplicado_antes_do_wkt(self):
        pytest.importorskip("geopandas")

        gdf_all = parse_embargos_geo(_golden_bytes())
        ufs_com_geom = gdf_all["uf"].unique()
        alvo = ufs_com_geom[0]

        gdf = parse_embargos_geo(_golden_bytes(), uf=alvo)
        assert len(gdf) >= 1
        assert (gdf["uf"] == alvo).all()

    def test_geo_vazio_pos_filtro_retorna_colunas(self):
        gpd = pytest.importorskip("geopandas")

        gdf = parse_embargos_geo(_golden_bytes(), bbox=(0.0, 0.0, 1.0, 1.0))

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 0
        assert list(gdf.columns) == COLUNAS_SAIDA_GEO

    def test_geo_wkt_invalido_descartado(self):
        pytest.importorskip("geopandas")

        raw = _golden_bytes().decode("utf-8")
        linhas = raw.split("\n")
        header = linhas[0].split(";")
        geom_idx = header.index("GEOM_AREA_EMBARGADA")

        corrompidas = [linhas[0]]
        trocou = False
        for linha in linhas[1:]:
            campos = linha.split(";")
            if (
                not trocou
                and len(campos) > geom_idx
                and campos[geom_idx].startswith(("POLYGON", "MULTIPOLYGON"))
            ):
                campos[geom_idx] = "WKT_QUEBRADO((1 2)"
                trocou = True
            corrompidas.append(";".join(campos))
        assert trocou

        gdf = parse_embargos_geo("\n".join(corrompidas).encode("utf-8"))
        assert len(gdf) == 23
