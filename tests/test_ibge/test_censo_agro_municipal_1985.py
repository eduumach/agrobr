from __future__ import annotations

import pandas as pd
import pytest
from typer.testing import CliRunner

from agrobr.cli import app
from agrobr.ibge.censo_municipal_1985 import (
    _DATA_DIR,
    TABELAS_CENSO_MUNICIPAL_1985,
    TEMAS_CENSO_MUNICIPAL_1985,
    TEMAS_DISPONIVEIS,
    _load_csv,
    _load_index,
    _resolve_unidade,
    censo_agro_municipal_1985,
    temas_censo_agro_municipal_1985,
)
from agrobr.models import MetaInfo

runner = CliRunner()


class TestConstantes:
    def test_53_tabelas(self):
        assert len(TABELAS_CENSO_MUNICIPAL_1985) == 53

    def test_reverse_mapping(self):
        for num, tema in TABELAS_CENSO_MUNICIPAL_1985.items():
            assert TEMAS_CENSO_MUNICIPAL_1985[tema] == num

    def test_temas_sorted(self):
        assert sorted(TEMAS_DISPONIVEIS) == TEMAS_DISPONIVEIS

    def test_range_67_119(self):
        assert min(TABELAS_CENSO_MUNICIPAL_1985) == 67
        assert max(TABELAS_CENSO_MUNICIPAL_1985) == 119


class TestIndex:
    def test_53_entries(self):
        index = _load_index()
        assert len(index) == 53

    def test_campos_obrigatorios(self):
        index = _load_index()
        for entry in index.values():
            assert "tema" in entry
            assert "colunas" in entry
            assert isinstance(entry["colunas"], list)
            assert len(entry["colunas"]) > 0

    def test_tab_67_spot_check(self):
        index = _load_index()
        assert index[67]["tema"] == "propriedade_terras"
        assert "estab_total" in index[67]["colunas"]

    def test_tab_111_spot_check(self):
        index = _load_index()
        assert index[111]["tema"] == "colheita_lav_temporaria"
        assert "qtde_1safra" in index[111]["colunas"]


class TestCsvLoader:
    def test_load_existing(self):
        df = _load_csv(67)
        assert len(df) > 0

    def test_nonexistent_raises(self):
        with pytest.raises(FileNotFoundError):
            _load_csv(999)

    def test_separador(self):
        df = _load_csv(67)
        assert "_uf" in df.columns
        assert "_label" in df.columns
        assert "_level" in df.columns
        assert "confianca" in df.columns

    def test_levels(self):
        df = _load_csv(67)
        levels = set(df["_level"].unique())
        assert "municipio" in levels
        assert "total" in levels


class TestUnidadeResolution:
    def test_estab(self):
        assert _resolve_unidade("estab_total") == "estabelecimentos"

    def test_area_ha(self):
        assert _resolve_unidade("area_ha_total") == "hectares"

    def test_inform(self):
        assert _resolve_unidade("inform_1safra") == "informantes"

    def test_num_pessoas(self):
        assert _resolve_unidade("num_pessoas_total") == "pessoas"

    def test_efetivo(self):
        assert _resolve_unidade("efetivo_total") == "cabeças"

    def test_qtde(self):
        assert _resolve_unidade("qtde_1safra") == "toneladas"

    def test_valor(self):
        assert _resolve_unidade("valor_bens_mil_cr") == "mil_cruzeiros"

    def test_val_fallback(self):
        assert _resolve_unidade("val_1") == "unidades"

    def test_exact_nascidos(self):
        assert _resolve_unidade("nascidos") == "cabeças"

    def test_exact_vendidos(self):
        assert _resolve_unidade("vendidos") == "cabeças"

    def test_unknown_fallback(self):
        assert _resolve_unidade("xyz_unknown") == "unidades"


class TestDataDir:
    def test_dir_exists(self):
        assert _DATA_DIR.exists()
        assert _DATA_DIR.is_dir()

    def test_index_exists(self):
        assert (_DATA_DIR / "_index.csv").exists()

    def test_all_53_csvs(self):
        for num in TABELAS_CENSO_MUNICIPAL_1985:
            path = _DATA_DIR / f"tab_{num:03d}.csv"
            assert path.exists(), f"Missing: {path.name}"


class TestContract:
    def test_registered(self):
        from agrobr.contracts import has_contract

        assert has_contract("censo_agropecuario_municipal_1985")

    def test_13_columns(self):
        from agrobr.contracts.ibge import IBGE_CENSO_AGRO_MUNICIPAL_V1

        assert len(IBGE_CENSO_AGRO_MUNICIPAL_V1.columns) == 13

    def test_primary_key_empty(self):
        from agrobr.contracts.ibge import IBGE_CENSO_AGRO_MUNICIPAL_V1

        assert IBGE_CENSO_AGRO_MUNICIPAL_V1.primary_key == []

    def test_ano_fixed_1985(self):
        from agrobr.contracts.ibge import IBGE_CENSO_AGRO_MUNICIPAL_V1

        ano_col = next(c for c in IBGE_CENSO_AGRO_MUNICIPAL_V1.columns if c.name == "ano")
        assert ano_col.min_value == 1985
        assert ano_col.max_value == 1985

    def test_localidade_cod_nullable(self):
        from agrobr.contracts.ibge import IBGE_CENSO_AGRO_MUNICIPAL_V1

        col = next(c for c in IBGE_CENSO_AGRO_MUNICIPAL_V1.columns if c.name == "localidade_cod")
        assert col.nullable is True

    def test_valor_nullable(self):
        from agrobr.contracts.ibge import IBGE_CENSO_AGRO_MUNICIPAL_V1

        col = next(c for c in IBGE_CENSO_AGRO_MUNICIPAL_V1.columns if c.name == "valor")
        assert col.nullable is True

    def test_effective_from(self):
        from agrobr.contracts.ibge import IBGE_CENSO_AGRO_MUNICIPAL_V1

        assert IBGE_CENSO_AGRO_MUNICIPAL_V1.effective_from == "0.12.0"

    def test_fonte_guarantee(self):
        from agrobr.contracts.ibge import IBGE_CENSO_AGRO_MUNICIPAL_V1

        assert any(
            "ibge_censo_agro_municipal_1985" in g for g in IBGE_CENSO_AGRO_MUNICIPAL_V1.guarantees
        )


class TestValidation:
    async def test_tema_invalido(self):
        with pytest.raises(ValueError, match="inválido"):
            await censo_agro_municipal_1985("nao_existe")

    async def test_tema_valido(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        assert len(df) > 0

    async def test_filtro_uf(self):
        df = await censo_agro_municipal_1985("propriedade_terras", uf="SP")
        assert set(df["uf"].unique()) == {"SP"}

    async def test_filtro_nivel(self):
        df = await censo_agro_municipal_1985("propriedade_terras", nivel="municipio")
        assert set(df["nivel"].unique()) == {"municipio"}

    async def test_uf_invalida(self):
        with pytest.raises(ValueError, match="inválida"):
            await censo_agro_municipal_1985("propriedade_terras", uf="XX")

    async def test_nivel_invalido(self):
        with pytest.raises(ValueError, match="inválido"):
            await censo_agro_municipal_1985("propriedade_terras", nivel="pais")

    async def test_uf_sem_dados(self):
        with pytest.raises(ValueError, match="não tem dados"):
            await censo_agro_municipal_1985("inseminacao_ordenha", uf="AP")

    async def test_temas_helper(self):
        temas = await temas_censo_agro_municipal_1985()
        assert len(temas) == 53
        assert temas == sorted(temas)


class TestParsing:
    async def test_schema_output(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        expected_cols = [
            "ano",
            "uf",
            "uf_cod",
            "localidade",
            "localidade_cod",
            "nivel",
            "tema",
            "categoria",
            "variavel",
            "valor",
            "unidade",
            "confianca",
            "fonte",
        ]
        assert df.columns.tolist() == expected_cols

    async def test_unidade_semantica(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        unidades = set(df["unidade"].unique())
        assert "estabelecimentos" in unidades
        assert "hectares" in unidades

    async def test_confianca_values(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        assert set(df["confianca"].unique()).issubset({"alta", "media", "baixa"})

    async def test_nivel_values(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        assert set(df["nivel"].unique()).issubset(
            {"total", "mesorregiao", "microrregiao", "municipio"}
        )

    async def test_uf_cod(self):
        df = await censo_agro_municipal_1985("propriedade_terras", uf="SP")
        assert (df["uf_cod"] == 35).all()

    async def test_localidade_cod_resolved(self):
        df = await censo_agro_municipal_1985("propriedade_terras", nivel="municipio")
        resolved_pct = df["localidade_cod"].notna().mean()
        assert resolved_pct > 0.5, f"Apenas {resolved_pct:.1%} resolvidos"

    async def test_valor_numerico(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        assert df["valor"].dtype == "float64"
        valid = df["valor"].dropna()
        assert (valid >= 0).all()

    async def test_return_meta(self):
        result = await censo_agro_municipal_1985("propriedade_terras", return_meta=True)
        assert isinstance(result, tuple)
        df, meta = result
        assert isinstance(meta, MetaInfo)
        assert meta.records_count == len(df)

    async def test_val_n_columns(self):
        df = await censo_agro_municipal_1985("condicao_legal_terras")
        variavel_set = set(df["variavel"].unique())
        assert "val_1" in variavel_set
        assert all(v.startswith("val_") for v in variavel_set)

    async def test_ano_always_1985(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        assert (df["ano"] == 1985).all()

    async def test_fonte_constante(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        assert (df["fonte"] == "ibge_censo_agro_municipal_1985").all()

    async def test_categoria_geral(self):
        df = await censo_agro_municipal_1985("propriedade_terras")
        assert (df["categoria"] == "geral").all()


class TestDataset:
    def test_info_name(self):
        from agrobr.datasets.censo_agropecuario_municipal_1985 import (
            CENSO_AGROPECUARIO_MUNICIPAL_1985_INFO,
        )

        assert CENSO_AGROPECUARIO_MUNICIPAL_1985_INFO.name == "censo_agropecuario_municipal_1985"

    def test_53_products(self):
        from agrobr.datasets.censo_agropecuario_municipal_1985 import (
            CENSO_AGROPECUARIO_MUNICIPAL_1985_INFO,
        )

        assert len(CENSO_AGROPECUARIO_MUNICIPAL_1985_INFO.products) == 53

    def test_frequency_never(self):
        from agrobr.datasets.censo_agropecuario_municipal_1985 import (
            CENSO_AGROPECUARIO_MUNICIPAL_1985_INFO,
        )

        assert CENSO_AGROPECUARIO_MUNICIPAL_1985_INFO.update_frequency == "never"

    def test_registered_in_registry(self):
        from agrobr.datasets.registry import get_dataset

        ds = get_dataset("censo_agropecuario_municipal_1985")
        assert ds is not None
        assert ds.info.name == "censo_agropecuario_municipal_1985"

    async def test_fetch_via_dataset(self):
        from agrobr.datasets.censo_agropecuario_municipal_1985 import (
            censo_agropecuario_municipal_1985,
        )

        df = await censo_agropecuario_municipal_1985("propriedade_terras", uf="SP")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert set(df["uf"].unique()) == {"SP"}

    async def test_fetch_with_meta(self):
        from agrobr.datasets.censo_agropecuario_municipal_1985 import (
            censo_agropecuario_municipal_1985,
        )

        result = await censo_agropecuario_municipal_1985("propriedade_terras", return_meta=True)
        assert isinstance(result, tuple)
        df, meta = result
        assert isinstance(meta, MetaInfo)
        assert meta.dataset == "censo_agropecuario_municipal_1985"
        assert meta.records_count == len(df)


class TestCLI:
    def test_temas_command(self):
        result = runner.invoke(app, ["ibge", "temas-municipal-1985"])
        assert result.exit_code == 0
        assert "Censo Agropecuario Municipal 1985" in result.output
        assert "propriedade_terras" in result.output

    def test_censo_command_csv(self):
        result = runner.invoke(
            app,
            [
                "ibge",
                "censo-municipal-1985",
                "propriedade_terras",
                "--uf",
                "SP",
                "--formato",
                "csv",
            ],
        )
        assert result.exit_code == 0
        assert "ano" in result.output
        assert "SP" in result.output

    def test_tema_invalido_exit_1(self):
        result = runner.invoke(app, ["ibge", "censo-municipal-1985", "nao_existe"])
        assert result.exit_code == 1
        assert "Erro" in result.output
