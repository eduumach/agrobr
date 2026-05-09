from __future__ import annotations

import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pandas as pd
import pytest


def _make_polygons(n: int, *, base_lon: float = -40.0, base_lat: float = -20.0) -> list[Any]:
    from shapely.geometry import Polygon

    return [
        Polygon(
            [
                (base_lon + i * 0.1, base_lat),
                (base_lon + (i + 1) * 0.1, base_lat),
                (base_lon + (i + 1) * 0.1, base_lat + 1.0),
                (base_lon + i * 0.1, base_lat + 1.0),
            ]
        )
        for i in range(n)
    ]


def _write_synthetic_zip(
    tmp_path: Path,
    *,
    name: str,
    rows: list[dict[str, Any]],
    polygons: list[Any],
) -> Path:
    import geopandas as gpd
    import pyogrio

    shp_dir = tmp_path / f"{name}_layer"
    shp_dir.mkdir(exist_ok=True)
    df = pd.DataFrame(rows)
    gdf = gpd.GeoDataFrame(df, geometry=polygons, crs="EPSG:4674")
    shp_path = shp_dir / f"{name}.shp"
    pyogrio.write_dataframe(gdf, shp_path, encoding="latin1")

    zip_path = tmp_path / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for f in shp_dir.iterdir():
            zf.write(f, f.name)
    return zip_path


@pytest.fixture
def synthetic_sigef_zip(tmp_path: Path) -> Path:
    pytest.importorskip("geopandas")
    rows = [
        {
            "parcela_co": f"abc-{i}",
            "rt": "RT1",
            "art": "A1",
            "situacao_i": "REGISTRADA",
            "codigo_imo": f"IMO{i:03d}",
            "data_submi": "2024-01-15",
            "data_aprov": "2024-01-16",
            "status": "CERTIFICADA",
            "nome_area": f"Fazenda São {i}",
            "registro_m": f"M{i}",
            "registro_d": "",
            "municipio_": 5200100 + i,
            "uf_id": 32,
        }
        for i in range(5)
    ]
    return _write_synthetic_zip(
        tmp_path, name="sigef_es", rows=rows, polygons=_make_polygons(5, base_lon=-40.5)
    )


@pytest.fixture
def synthetic_snci_zip(tmp_path: Path) -> Path:
    pytest.importorskip("geopandas")
    rows = [
        {
            "num_proces": f"P-{i:04d}",
            "sr": "SR-13",
            "num_certif": f"C{i:05d}",
            "data_certi": "2012-06-10",
            "qtd_area_p": 1234.56 + i,
            "cod_profis": f"PROF-{i}",
            "cod_imovel": f"IMO-{i:05d}",
            "nome_imove": f"Sítio Açaí {i}",
            "uf_municip": "GO",
        }
        for i in range(4)
    ]
    return _write_synthetic_zip(
        tmp_path,
        name="snci_go",
        rows=rows,
        polygons=_make_polygons(4, base_lon=-49.0, base_lat=-16.0),
    )


@pytest.fixture
def synthetic_assentamentos_zip(tmp_path: Path) -> Path:
    pytest.importorskip("geopandas")
    rows = [
        {
            "cd_sipra": "MG0001000",
            "uf": "MG",
            "nome_proje": "PA Esperança",
            "municipio": "Uberaba",
            "area_hecta": "1500.00",
            "capacidade": 50,
            "num_famili": 48,
            "fase": 3,
            "data_de_cr": "2010-05-15",
            "forma_obte": "Desapropriação",
            "data_obten": "2009-11-20",
            "area_calc_": 1498.5,
            "sr": "SR-06",
            "descricao_": "Consolidado",
        },
        {
            "cd_sipra": "MG0002000",
            "uf": "MG",
            "nome_proje": "PA União",
            "municipio": "Uberlândia",
            "area_hecta": "800.00",
            "capacidade": 30,
            "num_famili": 28,
            "fase": 2,
            "data_de_cr": "2012-03-10",
            "forma_obte": "Compra e Venda",
            "data_obten": "2011-08-05",
            "area_calc_": 799.2,
            "sr": "SR-06",
            "descricao_": "Em estruturação",
        },
        {
            "cd_sipra": "GO0001000",
            "uf": "GO",
            "nome_proje": "PA Sertão",
            "municipio": "Goiânia",
            "area_hecta": "2000.00",
            "capacidade": 80,
            "num_famili": 75,
            "fase": 4,
            "data_de_cr": "2008-07-20",
            "forma_obte": "Desapropriação",
            "data_obten": "2007-12-15",
            "area_calc_": 1995.8,
            "sr": "SR-04",
            "descricao_": "Consolidado",
        },
        {
            "cd_sipra": "XX0001000",
            "uf": "MB",
            "nome_proje": "PA UF Inválida",
            "municipio": "Indef",
            "area_hecta": "100.00",
            "capacidade": 5,
            "num_famili": 4,
            "fase": 1,
            "data_de_cr": "2020-01-01",
            "forma_obte": "Outros",
            "data_obten": "2019-06-01",
            "area_calc_": 99.5,
            "sr": "SR-XX",
            "descricao_": "Dirty UF data",
        },
    ]
    return _write_synthetic_zip(
        tmp_path, name="assentamentos_brasil", rows=rows, polygons=_make_polygons(4)
    )


@pytest.fixture
def isolated_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    cache_dir = tmp_path / "agrobr_cache"
    cache_dir.mkdir()
    monkeypatch.setenv("AGROBR_CACHE_CACHE_DIR", str(cache_dir))
    yield cache_dir


@pytest.fixture(autouse=True)
def _reset_acervo_state() -> Iterator[None]:
    from agrobr.acervo_fundiario import client
    from agrobr.utils.warnings import warn_once_reset

    client._FETCH_LOCKS.clear()
    warn_once_reset()
    yield
    client._FETCH_LOCKS.clear()
    warn_once_reset()
