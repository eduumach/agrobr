from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from agrobr.ibge import client

GOLDEN_DIR = Path(__file__).parent.parent / "golden_data" / "ibge" / "censo_agro_efetivo_sample"


class TestTabelasCensoAgro:
    def test_efetivo_rebanho(self):
        assert client.TABELAS_CENSO_AGRO["efetivo_rebanho"]["2017"] == "6907"

    def test_uso_terra(self):
        assert client.TABELAS_CENSO_AGRO["uso_terra"]["2017"] == "6881"

    def test_lavoura_temporaria(self):
        assert client.TABELAS_CENSO_AGRO["lavoura_temporaria"]["2017"] == "6957"

    def test_lavoura_permanente(self):
        assert client.TABELAS_CENSO_AGRO["lavoura_permanente"]["2017"] == "6956"

    def test_preparo_solo(self):
        assert client.TABELAS_CENSO_AGRO["preparo_solo"]["2006"] == "791"
        assert client.TABELAS_CENSO_AGRO["preparo_solo"]["2017"] == "6855"

    def test_adubacao(self):
        assert client.TABELAS_CENSO_AGRO["adubacao"]["2006"] == "1249"
        assert client.TABELAS_CENSO_AGRO["adubacao"]["2017"] == "6848"

    def test_calagem(self):
        assert client.TABELAS_CENSO_AGRO["calagem"]["2006"] == "1245"
        assert client.TABELAS_CENSO_AGRO["calagem"]["2017"] == "6849"

    def test_agrotoxicos(self):
        assert client.TABELAS_CENSO_AGRO["agrotoxicos"]["2006"] == "1459"
        assert client.TABELAS_CENSO_AGRO["agrotoxicos"]["2017"] == "6851"

    def test_praticas_agricolas(self):
        assert client.TABELAS_CENSO_AGRO["praticas_agricolas"]["2006"] == "837"
        assert client.TABELAS_CENSO_AGRO["praticas_agricolas"]["2017"] == "8561"

    def test_irrigacao(self):
        assert client.TABELAS_CENSO_AGRO["irrigacao"]["2006"] == "855"
        assert client.TABELAS_CENSO_AGRO["irrigacao"]["2017"] == "6857"

    def test_efetivo_rebanho_1995(self):
        assert client.TABELAS_CENSO_AGRO["efetivo_rebanho"]["1995"] == "323"

    def test_uso_terra_1995(self):
        assert client.TABELAS_CENSO_AGRO["uso_terra"]["1995"] == "316"

    def test_lavoura_temporaria_1995(self):
        assert client.TABELAS_CENSO_AGRO["lavoura_temporaria"]["1995"] == "497"

    def test_lavoura_permanente_1995(self):
        assert client.TABELAS_CENSO_AGRO["lavoura_permanente"]["1995"] == "509"

    def test_has_10_themes(self):
        assert len(client.TABELAS_CENSO_AGRO) == 10

    def test_all_themes_have_at_least_one_year(self):
        for tema, anos in client.TABELAS_CENSO_AGRO.items():
            assert len(anos) >= 1, f"{tema} has no years"

    def test_all_codes_numeric(self):
        for tema, anos in client.TABELAS_CENSO_AGRO.items():
            for ano, code in anos.items():
                assert code.isdigit(), f"{tema}/{ano} has non-numeric code: {code}"


class TestVariaveisCensoAgro:
    def test_efetivo_has_cabecas(self):
        assert "cabecas" in client.VARIAVEIS_CENSO_AGRO["efetivo_rebanho"]["2017"]
        assert client.VARIAVEIS_CENSO_AGRO["efetivo_rebanho"]["2017"]["cabecas"] == "2209"

    def test_uso_terra_has_area(self):
        assert "area" in client.VARIAVEIS_CENSO_AGRO["uso_terra"]["2017"]
        assert client.VARIAVEIS_CENSO_AGRO["uso_terra"]["2017"]["area"] == "184"

    def test_lavoura_temp_has_producao(self):
        assert "producao" in client.VARIAVEIS_CENSO_AGRO["lavoura_temporaria"]["2017"]

    def test_lavoura_perm_has_producao(self):
        assert "producao" in client.VARIAVEIS_CENSO_AGRO["lavoura_permanente"]["2017"]

    def test_preparo_solo_2017_has_plantio_direto(self):
        assert "plantio_direto" in client.VARIAVEIS_CENSO_AGRO["preparo_solo"]["2017"]

    def test_efetivo_1995_has_cabecas(self):
        assert "cabecas" in client.VARIAVEIS_CENSO_AGRO["efetivo_rebanho"]["1995"]
        assert client.VARIAVEIS_CENSO_AGRO["efetivo_rebanho"]["1995"]["cabecas"] == "105"

    def test_uso_terra_1995_has_area(self):
        assert "area" in client.VARIAVEIS_CENSO_AGRO["uso_terra"]["1995"]
        assert client.VARIAVEIS_CENSO_AGRO["uso_terra"]["1995"]["area"] == "184"

    def test_lavoura_temp_1995_has_producao(self):
        assert "producao" in client.VARIAVEIS_CENSO_AGRO["lavoura_temporaria"]["1995"]
        assert client.VARIAVEIS_CENSO_AGRO["lavoura_temporaria"]["1995"]["producao"] == "214"

    def test_lavoura_perm_1995_has_producao(self):
        assert "producao" in client.VARIAVEIS_CENSO_AGRO["lavoura_permanente"]["1995"]

    def test_each_tema_ano_has_at_least_one_var(self):
        for tema, anos in client.VARIAVEIS_CENSO_AGRO.items():
            for ano, vars_map in anos.items():
                assert len(vars_map) >= 1, f"{tema}/{ano} has no variables"

    def test_all_codes_numeric(self):
        for tema, anos in client.VARIAVEIS_CENSO_AGRO.items():
            for ano, vars_map in anos.items():
                for name, code in vars_map.items():
                    assert code.isdigit(), f"{tema}/{ano}.{name} has non-numeric code: {code}"


class TestTemasCensoAgro:
    def test_has_10_themes(self):
        assert len(client.TEMAS_CENSO_AGRO) == 10

    def test_efetivo_in_temas(self):
        assert "efetivo_rebanho" in client.TEMAS_CENSO_AGRO

    def test_uso_terra_in_temas(self):
        assert "uso_terra" in client.TEMAS_CENSO_AGRO

    def test_new_themes_in_temas(self):
        for tema in [
            "preparo_solo",
            "adubacao",
            "calagem",
            "agrotoxicos",
            "praticas_agricolas",
            "irrigacao",
        ]:
            assert tema in client.TEMAS_CENSO_AGRO

    def test_temas_match_tabelas(self):
        assert set(client.TEMAS_CENSO_AGRO) == set(client.TABELAS_CENSO_AGRO.keys())


class TestCensoAgroValidation:
    @pytest.mark.asyncio
    async def test_tema_invalido(self):
        from agrobr.ibge.api import censo_agro

        with pytest.raises(ValueError, match="Tema não suportado"):
            await censo_agro("tema_inexistente")

    @pytest.mark.asyncio
    async def test_ano_invalido(self):
        from agrobr.ibge.api import censo_agro

        with pytest.raises(ValueError, match="Ano .* não disponível"):
            await censo_agro("preparo_solo", ano=2020)


def _build_mock_efetivo(n_ufs=3):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso"), ("52", "Goiás")][:n_ufs]
    species = [("110056", "Bovinos"), ("110062", "Ovinos")]
    for cod_uf, nome_uf in ufs:
        for cod_sp, nome_sp in species:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "24",
                    "MN": "Cabeças",
                    "V": str(1000000 + int(cod_uf) * 100),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "2209",
                    "D2N": "Número de cabeças",
                    "D3C": "2017",
                    "D3N": "2017",
                    "D4C": "46302",
                    "D4N": "Total",
                    "D5C": cod_sp,
                    "D5N": nome_sp,
                    "D6C": "46502",
                    "D6N": "Total",
                }
            )
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1020",
                    "MN": "Unidades",
                    "V": str(50000 + int(cod_uf) * 10),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "10010",
                    "D2N": "Número de estabelecimentos",
                    "D3C": "2017",
                    "D3N": "2017",
                    "D4C": "46302",
                    "D4N": "Total",
                    "D5C": cod_sp,
                    "D5N": nome_sp,
                    "D6C": "46502",
                    "D6N": "Total",
                }
            )
    return pd.DataFrame(rows)


def _build_mock_uso_terra(n_ufs=2):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso")][:n_ufs]
    usos = [
        ("111543", "Lavouras temporárias"),
        ("111544", "Pastagens naturais"),
    ]
    for cod_uf, nome_uf in ufs:
        for cod_uso, nome_uso in usos:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1019",
                    "MN": "Hectares",
                    "V": str(500000 + int(cod_uf) * 100),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "184",
                    "D2N": "Área dos estabelecimentos agropecuários",
                    "D3C": "2017",
                    "D3N": "2017",
                    "D4C": "46302",
                    "D4N": "Total",
                    "D5C": cod_uso,
                    "D5N": nome_uso,
                    "D6C": "46502",
                    "D6N": "Total",
                    "D7C": "113601",
                    "D7N": "Total",
                    "D8C": "41151",
                    "D8N": "Total",
                }
            )
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1020",
                    "MN": "Unidades",
                    "V": str(10000 + int(cod_uf)),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "9587",
                    "D2N": "Número de estabelecimentos agropecuários com área",
                    "D3C": "2017",
                    "D3N": "2017",
                    "D4C": "46302",
                    "D4N": "Total",
                    "D5C": cod_uso,
                    "D5N": nome_uso,
                    "D6C": "46502",
                    "D6N": "Total",
                    "D7C": "113601",
                    "D7N": "Total",
                    "D8C": "41151",
                    "D8N": "Total",
                }
            )
    return pd.DataFrame(rows)


def _build_mock_preparo_solo_2006(n_ufs=3):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso"), ("52", "Goiás")][:n_ufs]
    categorias = [
        ("113223", "Aração e/ou gradagem (cultivo convencional)"),
        ("113224", "Cultivo mínimo"),
        ("114631", "Plantio direto na palha"),
    ]
    for cod_uf, nome_uf in ufs:
        for cod_cat, nome_cat in categorias:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1020",
                    "MN": "Unidades",
                    "V": str(8000 + int(cod_uf)),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "183",
                    "D2N": "Número de estabelecimentos agropecuários",
                    "D3C": cod_cat,
                    "D3N": nome_cat,
                }
            )
    return pd.DataFrame(rows)


def _build_mock_preparo_solo_2017(n_ufs=3):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso"), ("52", "Goiás")][:n_ufs]
    var_ids = [
        ("9562", "Não utilizaram"),
        ("9563", "Utilizaram preparo do solo"),
        ("9564", "Cultivo convencional"),
        ("9565", "Cultivo mínimo"),
        ("2016", "Plantio direto na palha"),
        ("2018", "Área com plantio direto na palha"),
    ]
    for cod_uf, nome_uf in ufs:
        for var_id, var_nome in var_ids:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1020",
                    "MN": "Unidades",
                    "V": str(5000 + int(cod_uf) + int(var_id) % 100),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": var_id,
                    "D2N": var_nome,
                    "D3C": "46302",
                    "D3N": "Total",
                    "D4C": "41145",
                    "D4N": "Total",
                    "D5C": "45951",
                    "D5N": "Total",
                    "D6C": "46502",
                    "D6N": "Total",
                }
            )
    return pd.DataFrame(rows)


def _build_mock_classif_2006(categorias, n_ufs=2):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso")][:n_ufs]
    for cod_uf, nome_uf in ufs:
        for cod_cat, nome_cat in categorias:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1020",
                    "MN": "Unidades",
                    "V": str(3000 + int(cod_uf)),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "183",
                    "D2N": "Número de estabelecimentos agropecuários",
                    "D3C": cod_cat,
                    "D3N": nome_cat,
                }
            )
    return pd.DataFrame(rows)


def _build_mock_classif_2017(categorias, n_ufs=2):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso")][:n_ufs]
    var_ids = [("183", "Número de estabelecimentos"), ("184", "Área")]
    for cod_uf, nome_uf in ufs:
        for var_id, var_nome in var_ids:
            for cod_cat, nome_cat in categorias:
                rows.append(
                    {
                        "NC": "3",
                        "NN": "Unidade da Federação",
                        "MC": "1020",
                        "MN": "Unidades",
                        "V": str(4000 + int(cod_uf)),
                        "D1C": cod_uf,
                        "D1N": nome_uf,
                        "D2C": var_id,
                        "D2N": var_nome,
                        "D3C": cod_cat,
                        "D3N": nome_cat,
                    }
                )
    return pd.DataFrame(rows)


def _build_mock_adubacao_2006():
    return _build_mock_classif_2006(
        [
            ("113227", "Usam adubação"),
            ("113228", "Químico nitrogenado"),
        ]
    )


def _build_mock_adubacao_2017():
    return _build_mock_classif_2017(
        [
            ("46546", "Fez adubação"),
            ("46547", "Química"),
            ("46548", "Orgânica"),
        ]
    )


def _build_mock_calagem_2006():
    return _build_mock_classif_2006(
        [
            ("112013", "Fez no ano"),
            ("120834", "Faz mas não precisou no período"),
        ]
    )


def _build_mock_calagem_2017():
    return _build_mock_classif_2017(
        [
            ("46554", "Fez aplicação de calcário e/ou de outro corretivo de acidez"),
            ("46555", "Não fez aplicação"),
        ]
    )


def _build_mock_agrotoxicos_2006():
    return _build_mock_classif_2006(
        [
            ("111611", "Utilizou"),
            ("111612", "Não utilizou"),
        ]
    )


def _build_mock_agrotoxicos_2017():
    return _build_mock_classif_2017(
        [
            ("111611", "Utilizou"),
            ("111612", "Não utilizou"),
        ]
    )


def _build_mock_praticas_agricolas_2006():
    return _build_mock_classif_2006(
        [
            ("112654", "Plantio em nível"),
            ("112677", "Rotação de culturas"),
            ("112764", "Pousio ou descanso de solos"),
        ]
    )


def _build_mock_praticas_agricolas_2017():
    return _build_mock_classif_2017(
        [
            ("112654", "Plantio em nível"),
            ("112677", "Rotação de culturas"),
            ("112764", "Pousio ou descanso de solos"),
        ]
    )


def _build_mock_irrigacao_2006():
    return _build_mock_classif_2006(
        [
            ("113515", "Inundação"),
            ("113517", "Pivô central"),
            ("113519", "Localizado (gotejamento, microaspersão)"),
        ]
    )


def _build_mock_irrigacao_2017():
    return _build_mock_classif_2017(
        [
            ("45916", "Gotejamento"),
            ("45923", "Pivô central"),
            ("45919", "Inundação"),
        ]
    )


def _build_mock_efetivo_1995(n_ufs=3):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso"), ("52", "Goiás")][:n_ufs]
    species = [("31660", "Bovinos"), ("31666", "Ovinos")]
    for cod_uf, nome_uf in ufs:
        for cod_sp, nome_sp in species:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "24",
                    "MN": "Cabeças",
                    "V": str(800000 + int(cod_uf) * 100),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "105",
                    "D2N": "Efetivo dos rebanhos",
                    "D3C": cod_sp,
                    "D3N": nome_sp,
                    "D4C": "0",
                    "D4N": "Total",
                }
            )
    return pd.DataFrame(rows)


def _build_mock_uso_terra_1995_area(n_ufs=2):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso")][:n_ufs]
    usos = [("31386", "Lavouras temporárias"), ("31387", "Pastagens naturais")]
    for cod_uf, nome_uf in ufs:
        for cod_uso, nome_uso in usos:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1019",
                    "MN": "Hectares",
                    "V": str(400000 + int(cod_uf) * 100),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "184",
                    "D2N": "Área dos estabelecimentos",
                    "D3C": cod_uso,
                    "D3N": nome_uso,
                    "D4C": "0",
                    "D4N": "Total",
                }
            )
    return pd.DataFrame(rows)


def _build_mock_uso_terra_1995_estab(n_ufs=2):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso")][:n_ufs]
    usos = [("31386", "Lavouras temporárias"), ("31387", "Pastagens naturais")]
    for cod_uf, nome_uf in ufs:
        for cod_uso, nome_uso in usos:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1020",
                    "MN": "Unidades",
                    "V": str(8000 + int(cod_uf)),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "183",
                    "D2N": "Número de estabelecimentos",
                    "D3C": cod_uso,
                    "D3N": nome_uso,
                    "D4C": "0",
                    "D4N": "Total",
                }
            )
    return pd.DataFrame(rows)


def _build_mock_lavoura_temp_1995_prod(n_ufs=2):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso")][:n_ufs]
    produtos = [("31627", "Arroz"), ("31631", "Milho")]
    for cod_uf, nome_uf in ufs:
        for cod_prod, nome_prod in produtos:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1021",
                    "MN": "Toneladas",
                    "V": str(500000 + int(cod_uf) * 100),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "214",
                    "D2N": "Quantidade produzida",
                    "D3C": cod_prod,
                    "D3N": nome_prod,
                    "D4C": "0",
                    "D4N": "Total",
                }
            )
    return pd.DataFrame(rows)


def _build_mock_lavoura_temp_1995_estab(n_ufs=2):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso")][:n_ufs]
    produtos = [("31627", "Arroz"), ("31631", "Milho")]
    for cod_uf, nome_uf in ufs:
        for cod_prod, nome_prod in produtos:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1020",
                    "MN": "Unidades",
                    "V": str(5000 + int(cod_uf)),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "151",
                    "D2N": "Número de estabelecimentos",
                    "D3C": cod_prod,
                    "D3N": nome_prod,
                    "D4C": "0",
                    "D4N": "Total",
                }
            )
    return pd.DataFrame(rows)


def _build_mock_lavoura_temp_1995_area(n_ufs=2):
    rows = []
    ufs = [("35", "São Paulo"), ("51", "Mato Grosso")][:n_ufs]
    produtos = [("31627", "Arroz"), ("31631", "Milho")]
    for cod_uf, nome_uf in ufs:
        for cod_prod, nome_prod in produtos:
            rows.append(
                {
                    "NC": "3",
                    "NN": "Unidade da Federação",
                    "MC": "1019",
                    "MN": "Hectares",
                    "V": str(100000 + int(cod_uf) * 10),
                    "D1C": cod_uf,
                    "D1N": nome_uf,
                    "D2C": "216",
                    "D2N": "Área colhida",
                    "D3C": cod_prod,
                    "D3N": nome_prod,
                    "D4C": "0",
                    "D4N": "Total",
                }
            )
    return pd.DataFrame(rows)


class TestCensoAgro1995Mocked:
    @pytest.mark.asyncio
    async def test_efetivo_1995_single_variable(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo_1995()
            df = await censo_agro("efetivo_rebanho", ano=1995)
            assert set(df["variavel"].unique()) == {"cabecas"}

    @pytest.mark.asyncio
    async def test_efetivo_1995_ano_value(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo_1995()
            df = await censo_agro("efetivo_rebanho", ano=1995)
            assert set(df["ano"].unique()) == {1995}

    @pytest.mark.asyncio
    async def test_efetivo_1995_categorias(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo_1995()
            df = await censo_agro("efetivo_rebanho", ano=1995)
            categorias = set(df["categoria"].unique())
            assert "Bovinos" in categorias
            assert "Ovinos" in categorias

    @pytest.mark.asyncio
    async def test_efetivo_1995_unidade(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo_1995()
            df = await censo_agro("efetivo_rebanho", ano=1995)
            assert (df["unidade"] == "cabeças").all()

    @pytest.mark.asyncio
    async def test_uso_terra_1995_multi_table(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _build_mock_uso_terra_1995_area(),
                _build_mock_uso_terra_1995_estab(),
            ]
            df = await censo_agro("uso_terra", ano=1995)
            assert mock.call_count == 2
            variaveis = set(df["variavel"].unique())
            assert "area" in variaveis
            assert "estabelecimentos" in variaveis

    @pytest.mark.asyncio
    async def test_lavoura_temp_1995_multi_table(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _build_mock_lavoura_temp_1995_prod(),
                _build_mock_lavoura_temp_1995_estab(),
                _build_mock_lavoura_temp_1995_area(),
            ]
            df = await censo_agro("lavoura_temporaria", ano=1995)
            assert mock.call_count == 3
            variaveis = set(df["variavel"].unique())
            assert len(variaveis) == 3
            assert "producao" in variaveis
            assert "estabelecimentos" in variaveis
            assert "area_colhida" in variaveis

    @pytest.mark.asyncio
    async def test_1995_output_columns(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo_1995()
            df = await censo_agro("efetivo_rebanho", ano=1995)
            expected = [
                "ano",
                "localidade",
                "localidade_cod",
                "tema",
                "categoria",
                "variavel",
                "valor",
                "unidade",
                "fonte",
            ]
            assert list(df.columns) == expected

    @pytest.mark.asyncio
    async def test_1995_multi_year_default(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _build_mock_efetivo_1995(),
                _build_mock_efetivo(),
            ]
            df = await censo_agro("efetivo_rebanho")
            assert {1995, 2017} == set(df["ano"].unique())

    @pytest.mark.asyncio
    async def test_1995_valor_numerico(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo_1995()
            df = await censo_agro("efetivo_rebanho", ano=1995)
            assert pd.api.types.is_numeric_dtype(df["valor"])
            assert (df["valor"] > 0).all()

    @pytest.mark.asyncio
    async def test_1995_localidade_cod_inteiro(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo_1995()
            df = await censo_agro("efetivo_rebanho", ano=1995)
            assert df["localidade_cod"].dtype == "Int64"

    @pytest.mark.asyncio
    async def test_1995_tema_and_fonte(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo_1995()
            df = await censo_agro("efetivo_rebanho", ano=1995)
            assert (df["tema"] == "efetivo_rebanho").all()
            assert (df["fonte"] == "ibge_censo_agro").all()


class TestCensoAgroMocked:
    @pytest.mark.asyncio
    async def test_efetivo_returns_dataframe(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0

    @pytest.mark.asyncio
    async def test_efetivo_output_columns(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            expected = [
                "ano",
                "localidade",
                "localidade_cod",
                "tema",
                "categoria",
                "variavel",
                "valor",
                "unidade",
                "fonte",
            ]
            assert list(df.columns) == expected

    @pytest.mark.asyncio
    async def test_efetivo_tema_value(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            assert (df["tema"] == "efetivo_rebanho").all()

    @pytest.mark.asyncio
    async def test_efetivo_fonte_value(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            assert (df["fonte"] == "ibge_censo_agro").all()

    @pytest.mark.asyncio
    async def test_efetivo_ano_2017(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho", ano=2017)
            assert (df["ano"] == 2017).all()

    @pytest.mark.asyncio
    async def test_efetivo_categorias(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            categorias = df["categoria"].unique()
            assert "Bovinos" in categorias
            assert "Ovinos" in categorias

    @pytest.mark.asyncio
    async def test_efetivo_variaveis(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            variaveis = df["variavel"].unique()
            assert "cabecas" in variaveis
            assert "estabelecimentos" in variaveis

    @pytest.mark.asyncio
    async def test_efetivo_unidades(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            cabecas = df[df["variavel"] == "cabecas"]
            assert (cabecas["unidade"] == "cabeças").all()
            estab = df[df["variavel"] == "estabelecimentos"]
            assert (estab["unidade"] == "unidades").all()

    @pytest.mark.asyncio
    async def test_efetivo_valor_numerico(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            assert pd.api.types.is_numeric_dtype(df["valor"])
            assert (df["valor"] > 0).all()

    @pytest.mark.asyncio
    async def test_efetivo_localidade_cod_inteiro(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            assert df["localidade_cod"].dtype == "Int64"

    @pytest.mark.asyncio
    async def test_efetivo_return_meta(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            result = await censo_agro("efetivo_rebanho", return_meta=True)
            assert isinstance(result, tuple)
            df, meta = result
            assert isinstance(df, pd.DataFrame)
            assert meta.source == "ibge_censo_agro"

    @pytest.mark.asyncio
    async def test_efetivo_uf_filter(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo(n_ufs=1)
            df = await censo_agro("efetivo_rebanho", ano=2017, uf="SP")
            assert len(df) > 0
            mock.assert_called_once()
            call_kwargs = mock.call_args
            assert call_kwargs.kwargs.get("ibge_territorial_code") == "35"

    @pytest.mark.asyncio
    async def test_uso_terra_returns_dataframe(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_uso_terra()
            df = await censo_agro("uso_terra")
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "uso_terra").all()

    @pytest.mark.asyncio
    async def test_uso_terra_variaveis(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_uso_terra()
            df = await censo_agro("uso_terra")
            variaveis = df["variavel"].unique()
            assert "area" in variaveis
            assert "estabelecimentos" in variaveis

    @pytest.mark.asyncio
    async def test_uso_terra_unidade_area(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_uso_terra()
            df = await censo_agro("uso_terra")
            area = df[df["variavel"] == "area"]
            assert (area["unidade"] == "hectares").all()

    @pytest.mark.asyncio
    async def test_empty_response(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = pd.DataFrame()
            df = await censo_agro("efetivo_rebanho")
            assert isinstance(df, pd.DataFrame)
            assert len(df) == 0

    @pytest.mark.asyncio
    async def test_total_filtered_out(self):
        from agrobr.ibge.api import censo_agro

        mock_df = _build_mock_efetivo(n_ufs=1)
        total_row = mock_df.iloc[0:1].copy()
        total_row["D5C"] = "111197"
        total_row["D5N"] = "Total"
        mock_with_total = pd.concat([total_row, mock_df], ignore_index=True)

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = mock_with_total
            df = await censo_agro("efetivo_rebanho")
            assert "Total" not in df["categoria"].values


class TestCensoAgroNewThemesMocked:
    @pytest.mark.asyncio
    async def test_preparo_solo_2006(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_preparo_solo_2006()
            df = await censo_agro("preparo_solo", ano=2006)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "preparo_solo").all()
            assert (df["ano"] == 2006).all()
            categorias = df["categoria"].unique()
            assert "Plantio direto na palha" in categorias

    @pytest.mark.asyncio
    async def test_preparo_solo_2017_var_as_category(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_preparo_solo_2017()
            df = await censo_agro("preparo_solo", ano=2017)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "preparo_solo").all()
            assert (df["ano"] == 2017).all()
            categorias = df["categoria"].unique()
            assert "Plantio direto na palha" in categorias
            assert "Cultivo convencional" in categorias

    @pytest.mark.asyncio
    async def test_preparo_solo_2017_columns(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_preparo_solo_2017()
            df = await censo_agro("preparo_solo", ano=2017)
            expected = [
                "ano",
                "localidade",
                "localidade_cod",
                "tema",
                "categoria",
                "variavel",
                "valor",
                "unidade",
                "fonte",
            ]
            assert list(df.columns) == expected

    @pytest.mark.asyncio
    async def test_preparo_solo_multi_year(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _build_mock_preparo_solo_2006(),
                _build_mock_preparo_solo_2017(),
            ]
            df = await censo_agro("preparo_solo")
            assert set(df["ano"].unique()) == {2006, 2017}
            assert len(df) > 0

    @pytest.mark.asyncio
    async def test_adubacao_2006(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_adubacao_2006()
            df = await censo_agro("adubacao", ano=2006)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "adubacao").all()
            assert (df["ano"] == 2006).all()

    @pytest.mark.asyncio
    async def test_adubacao_2017(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_adubacao_2017()
            df = await censo_agro("adubacao", ano=2017)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "adubacao").all()

    @pytest.mark.asyncio
    async def test_calagem_2006(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_calagem_2006()
            df = await censo_agro("calagem", ano=2006)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "calagem").all()

    @pytest.mark.asyncio
    async def test_calagem_2017(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_calagem_2017()
            df = await censo_agro("calagem", ano=2017)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "calagem").all()

    @pytest.mark.asyncio
    async def test_agrotoxicos_2006(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_agrotoxicos_2006()
            df = await censo_agro("agrotoxicos", ano=2006)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "agrotoxicos").all()

    @pytest.mark.asyncio
    async def test_agrotoxicos_2017(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_agrotoxicos_2017()
            df = await censo_agro("agrotoxicos", ano=2017)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "agrotoxicos").all()

    @pytest.mark.asyncio
    async def test_praticas_agricolas_2006(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_praticas_agricolas_2006()
            df = await censo_agro("praticas_agricolas", ano=2006)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "praticas_agricolas").all()
            categorias = df["categoria"].unique()
            assert "Plantio em nível" in categorias

    @pytest.mark.asyncio
    async def test_praticas_agricolas_2017(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_praticas_agricolas_2017()
            df = await censo_agro("praticas_agricolas", ano=2017)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "praticas_agricolas").all()

    @pytest.mark.asyncio
    async def test_irrigacao_2006(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_irrigacao_2006()
            df = await censo_agro("irrigacao", ano=2006)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "irrigacao").all()
            categorias = df["categoria"].unique()
            assert "Pivô central" in categorias

    @pytest.mark.asyncio
    async def test_irrigacao_2017(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_irrigacao_2017()
            df = await censo_agro("irrigacao", ano=2017)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "irrigacao").all()
            categorias = df["categoria"].unique()
            assert "Gotejamento" in categorias

    @pytest.mark.asyncio
    async def test_ano_filter_single(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_adubacao_2017()
            df = await censo_agro("adubacao", ano=2017)
            mock.assert_called_once()
            assert (df["ano"] == 2017).all()

    @pytest.mark.asyncio
    async def test_valor_numerico(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_irrigacao_2006()
            df = await censo_agro("irrigacao", ano=2006)
            assert pd.api.types.is_numeric_dtype(df["valor"])

    @pytest.mark.asyncio
    async def test_localidade_cod_inteiro(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_calagem_2017()
            df = await censo_agro("calagem", ano=2017)
            assert df["localidade_cod"].dtype == "Int64"


class TestCensoAgroRetrocompat:
    @pytest.mark.asyncio
    async def test_efetivo_rebanho_still_works(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho")
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "efetivo_rebanho").all()

    @pytest.mark.asyncio
    async def test_uso_terra_still_works(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_uso_terra()
            df = await censo_agro("uso_terra")
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
            assert (df["tema"] == "uso_terra").all()

    @pytest.mark.asyncio
    async def test_efetivo_with_uf_keyword(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo(n_ufs=1)
            df = await censo_agro("efetivo_rebanho", uf="SP")
            assert len(df) > 0

    @pytest.mark.asyncio
    async def test_efetivo_with_ano_none(self):
        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo()
            df = await censo_agro("efetivo_rebanho", ano=None)
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0


class TestTemasCensoAgroFunc:
    @pytest.mark.asyncio
    async def test_returns_list(self):
        from agrobr.ibge.api import temas_censo_agro

        result = await temas_censo_agro()
        assert isinstance(result, list)
        assert len(result) == 10

    @pytest.mark.asyncio
    async def test_contains_all_themes(self):
        from agrobr.ibge.api import temas_censo_agro

        result = await temas_censo_agro()
        assert "efetivo_rebanho" in result
        assert "uso_terra" in result
        assert "lavoura_temporaria" in result
        assert "lavoura_permanente" in result
        assert "preparo_solo" in result
        assert "adubacao" in result
        assert "calagem" in result
        assert "agrotoxicos" in result
        assert "praticas_agricolas" in result
        assert "irrigacao" in result


class TestCensoAgroPolarsSupport:
    @pytest.mark.asyncio
    async def test_as_polars_returns_polars_df(self):
        pytest.importorskip("polars")
        import polars as pl

        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo(n_ufs=1)
            df = await censo_agro("efetivo_rebanho", as_polars=True)
            assert isinstance(df, pl.DataFrame)

    @pytest.mark.asyncio
    async def test_as_polars_with_meta(self):
        pytest.importorskip("polars")
        import polars as pl

        from agrobr.ibge.api import censo_agro

        with patch("agrobr.ibge.client.fetch_sidra", new_callable=AsyncMock) as mock:
            mock.return_value = _build_mock_efetivo(n_ufs=1)
            result = await censo_agro("efetivo_rebanho", as_polars=True, return_meta=True)
            assert isinstance(result, tuple)
            assert isinstance(result[0], pl.DataFrame)


class TestCensoAgroGoldenData:
    def test_golden_data_exists(self):
        assert GOLDEN_DIR.exists()
        assert (GOLDEN_DIR / "metadata.json").exists()
        assert (GOLDEN_DIR / "response.csv").exists()
        assert (GOLDEN_DIR / "expected.json").exists()

    def test_golden_metadata_valid(self):
        meta = json.loads((GOLDEN_DIR / "metadata.json").read_text(encoding="utf-8"))
        assert meta["source"] == "ibge_censo_agro"
        assert meta["table"] == "6907"
        assert meta["tema"] == "efetivo_rebanho"

    def test_golden_response_parseable(self):
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        assert len(df) > 0
        assert "D5N" in df.columns

    def test_golden_expected_format(self):
        expected = json.loads((GOLDEN_DIR / "expected.json").read_text(encoding="utf-8"))
        assert "row_count" in expected
        assert "columns" in expected
        assert "sample_values" in expected
        assert expected["tema"] == "efetivo_rebanho"

    def test_golden_row_count_matches(self):
        expected = json.loads((GOLDEN_DIR / "expected.json").read_text(encoding="utf-8"))
        df = pd.read_csv(GOLDEN_DIR / "response.csv", dtype=str)
        assert len(df) == expected["row_count"]


class TestCensoAgroContract:
    def test_contract_registered(self):
        from agrobr.contracts import get_contract

        contract = get_contract("censo_agropecuario")
        assert contract is not None
        assert contract.name == "ibge.censo_agro"

    def test_contract_validates_valid_df(self):
        from agrobr.contracts import validate_dataset

        df = pd.DataFrame(
            {
                "ano": [2017, 2017, 1995],
                "localidade": ["São Paulo", "São Paulo", "São Paulo"],
                "localidade_cod": [35, 35, 35],
                "tema": ["efetivo_rebanho", "efetivo_rebanho", "efetivo_rebanho"],
                "categoria": ["Bovinos", "Bovinos", "Bovinos"],
                "variavel": ["cabecas", "estabelecimentos", "cabecas"],
                "valor": [10391878.0, 131234.0, 5000000.0],
                "unidade": ["cabeças", "unidades", "cabeças"],
                "fonte": ["ibge_censo_agro", "ibge_censo_agro", "ibge_censo_agro"],
            }
        )
        validate_dataset(df, "censo_agropecuario")

    def test_contract_rejects_negative_values(self):
        from agrobr.contracts import validate_dataset
        from agrobr.exceptions import ContractViolationError

        df = pd.DataFrame(
            {
                "ano": [2017],
                "localidade": ["Test"],
                "localidade_cod": [11],
                "tema": ["efetivo_rebanho"],
                "categoria": ["Bovinos"],
                "variavel": ["cabecas"],
                "valor": [-100.0],
                "unidade": ["cabeças"],
                "fonte": ["ibge_censo_agro"],
            }
        )
        with pytest.raises(ContractViolationError):
            validate_dataset(df, "censo_agropecuario")


class TestCensoAgroDataset:
    def test_dataset_registered(self):
        from agrobr.datasets.registry import list_datasets

        datasets = list_datasets()
        assert "censo_agropecuario" in datasets

    def test_dataset_info(self):
        from agrobr.datasets.censo_agropecuario import CENSO_AGROPECUARIO_INFO

        assert CENSO_AGROPECUARIO_INFO.name == "censo_agropecuario"
        assert CENSO_AGROPECUARIO_INFO.update_frequency == "decennial"

    def test_dataset_products(self):
        from agrobr.datasets.censo_agropecuario import CENSO_AGROPECUARIO_INFO

        assert "efetivo_rebanho" in CENSO_AGROPECUARIO_INFO.products
        assert "uso_terra" in CENSO_AGROPECUARIO_INFO.products
        assert "preparo_solo" in CENSO_AGROPECUARIO_INFO.products
        assert "irrigacao" in CENSO_AGROPECUARIO_INFO.products
        assert len(CENSO_AGROPECUARIO_INFO.products) == 10

    def test_dataset_source(self):
        from agrobr.datasets.censo_agropecuario import CENSO_AGROPECUARIO_INFO

        assert len(CENSO_AGROPECUARIO_INFO.sources) == 1
        assert CENSO_AGROPECUARIO_INFO.sources[0].name == "ibge_censo_agro"


class TestCensoAgroCachePolicy:
    def test_policy_exists(self):
        from agrobr.cache.policies import POLICIES

        assert "ibge_censo_agro" in POLICIES

    def test_policy_ttl_30_days(self):
        from agrobr.cache.policies import POLICIES, TTL

        policy = POLICIES["ibge_censo_agro"]
        assert policy.ttl_seconds == TTL.DAYS_30.value

    def test_policy_stale_90_days(self):
        from agrobr.cache.policies import POLICIES, TTL

        policy = POLICIES["ibge_censo_agro"]
        assert policy.stale_max_seconds == TTL.DAYS_90.value


class TestCensoAgroIntegration:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_efetivo_rebanho_real_api(self):
        from agrobr.ibge.api import censo_agro

        df = await censo_agro("efetivo_rebanho", uf="SP", nivel="uf")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "categoria" in df.columns
        assert (df["tema"] == "efetivo_rebanho").all()
        assert (df["fonte"] == "ibge_censo_agro").all()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_uso_terra_real_api(self):
        from agrobr.ibge.api import censo_agro

        df = await censo_agro("uso_terra", ano=2017, uf="MT", nivel="uf")
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert (df["tema"] == "uso_terra").all()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_efetivo_rebanho_1995_real_api(self):
        from agrobr.ibge.api import censo_agro

        df = await censo_agro("efetivo_rebanho", ano=1995, uf="SP", nivel="uf")
        assert len(df) > 0
        assert (df["ano"] == 1995).all()
        assert "cabecas" in df["variavel"].values
