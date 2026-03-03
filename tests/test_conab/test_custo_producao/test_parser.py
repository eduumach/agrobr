from __future__ import annotations

from io import BytesIO

import pandas as pd
import pytest

from agrobr.conab.custo_producao.parser import (
    PARSER_VERSION,
    _find_header,
    _identify_columns,
    _parse_sheet_info,
    _refine_valor_column,
    items_to_dataframe,
    parse_planilha,
    select_data_sheet,
)
from agrobr.exceptions import ParseError
from agrobr.normalize.numeric import safe_float


def _make_xlsx(rows: list[list], sheet_name: str = "Plan1") -> BytesIO:
    df = pd.DataFrame(rows)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False, header=False)
    buf.seek(0)
    return buf


def _make_multi_sheet_xlsx(sheets: dict[str, list[list]]) -> BytesIO:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        for name, rows in sheets.items():
            df = pd.DataFrame(rows)
            df.to_excel(writer, sheet_name=name, index=False, header=False)
    buf.seek(0)
    return buf


def _sample_xlsx(
    with_coe: bool = True,
    with_cot: bool = False,
    with_ct: bool = False,
) -> BytesIO:
    rows = [
        [
            "CUSTO DE PRODUÇÃO - SOJA - MT - ALTA TECNOLOGIA - SAFRA 2023/24",
            None,
            None,
            None,
            None,
            None,
        ],
        [None, None, None, None, None, None],
        [
            "Item / Especificação",
            "Unidade",
            "Qtd./ha",
            "Preço Unitário (R$)",
            "Valor Total/ha (R$)",
            "Participação (%)",
        ],
        ["I - INSUMOS", None, None, None, None, None],
        ["Sementes", "kg", 60.0, 8.50, 510.00, 13.42],
        ["Fertilizantes de base (MAP)", "kg", 200.0, 4.20, 840.00, 22.11],
        ["Herbicidas (Glifosato)", "L", 3.0, 25.00, 75.00, 1.97],
        ["Inseticidas", "L", 2.0, 45.00, 90.00, 2.37],
        ["Fungicidas", "L", 1.5, 80.00, 120.00, 3.16],
        ["Inoculante", "dose", 2.0, 12.00, 24.00, 0.63],
        ["II - OPERAÇÕES COM MÁQUINAS", None, None, None, None, None],
        ["Preparo do solo", "h/m", 1.5, 180.00, 270.00, 7.11],
        ["Plantio", "h/m", 0.8, 150.00, 120.00, 3.16],
        ["Pulverizações", "h/m", 2.0, 120.00, 240.00, 6.32],
        ["Colheita mecânica", "h/m", 1.0, 350.00, 350.00, 9.21],
        ["III - MÃO DE OBRA", None, None, None, None, None],
        ["Mão de obra temporária", "d/h", 3.0, 80.00, 240.00, 6.32],
    ]
    if with_coe:
        rows.append(["CUSTO OPERACIONAL EFETIVO (COE)", None, None, None, 2879.00, 75.78])
    if with_cot:
        rows.append(["CUSTO OPERACIONAL TOTAL (COT)", None, None, None, 3400.00, 89.47])
    if with_ct:
        rows.append(["CUSTO TOTAL (CT)", None, None, None, 3800.00, 100.00])
    return _make_xlsx(rows)


def _make_format_a_xlsx() -> BytesIO:
    rows = [
        ["CUSTO DE PRODUÇÃO - TOMATE - GO", None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        ["DISCRIMINAÇÃO", None, None, None],
        [None, "R$/ha", None, "(%)"],
        ["I - INSUMOS", None, None, None],
        ["Sementes", 320.00, None, 15.0],
        ["Fertilizantes", 480.00, None, 22.5],
    ]
    return _make_xlsx(rows)


def _make_format_c_xlsx() -> BytesIO:
    rows = [
        ["CUSTO DE PRODUÇÃO - CACAU - BA", None, None, None, None],
        [None, None, None, None, None],
        ["DISCRIMINAÇÃO", "CUSTO POR HA", "CUSTO/kg", "PARTICIPAÇÃO CV(%)", "PARTICIPAÇÃO CT(%)"],
        ["I - INSUMOS", None, None, None, None],
        ["Mudas", 250.00, 2.50, 18.0, 12.0],
        ["Fertilizantes", 400.00, 4.00, 29.0, 19.0],
        ["CUSTO OPERACIONAL EFETIVO (COE)", 1380.00, None, None, None],
    ]
    return _make_xlsx(rows)


def _make_format_d_xlsx() -> BytesIO:
    rows = [
        ["CUSTO DE PRODUÇÃO - ABACAXI - TO", None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        [None, None, None, None],
        ["Produtividade Média: 30.000 kg/ha", None, None, None],
        [None, "A PREÇOS DE:", "Abril/2014", "PARTICI-"],
        ["DISCRIMINAÇÃO", None, None, "PAÇÃO"],
        [None, "R$/ha", "R$/1000 kg", "(%)"],
        ["I - DESPESAS DO CUSTEIO", None, None, None],
        ["Mudas", 1200.00, 40.00, 25.0],
        ["Fertilizantes", 800.00, 26.67, 16.7],
        ["Herbicidas", 300.00, 10.00, 6.3],
        ["CUSTO OPERACIONAL EFETIVO (COE)", 4800.00, None, None],
    ]
    return _make_xlsx(rows)


class TestSafeFloat:
    def test_int(self):
        assert safe_float(10, strip=("R$", "%")) == 10.0

    def test_float(self):
        assert safe_float(3.14, strip=("R$", "%")) == pytest.approx(3.14)

    def test_string_dot(self):
        assert safe_float("3.14", strip=("R$", "%")) == pytest.approx(3.14)

    def test_string_comma(self):
        assert safe_float("3,14", strip=("R$", "%")) == pytest.approx(3.14)

    def test_string_with_currency(self):
        assert safe_float("R$ 510.00", strip=("R$", "%")) == pytest.approx(510.0)

    def test_string_with_percent(self):
        assert safe_float("12.5%", strip=("R$", "%")) == pytest.approx(12.5)

    def test_none(self):
        assert safe_float(None, strip=("R$", "%")) is None

    def test_nan(self):
        assert safe_float(float("nan"), strip=("R$", "%")) is None

    def test_empty_string(self):
        assert safe_float("", strip=("R$", "%")) is None

    def test_dash(self):
        assert safe_float("-", strip=("R$", "%")) is None

    def test_garbage(self):
        assert safe_float("abc", strip=("R$", "%")) is None


class TestFindHeader:
    def test_finds_header_original_format(self):
        rows = [
            ["TITULO", None],
            [None, None],
            ["Item", "Valor Total/ha (R$)"],
            ["Sementes", 510.0],
        ]
        df = pd.DataFrame(rows)
        data_start, headers = _find_header(df)
        assert data_start == 3
        assert "Item" in headers

    def test_raises_on_no_header(self):
        rows = [
            ["blah", "blah"],
            ["foo", "bar"],
        ]
        df = pd.DataFrame(rows)
        with pytest.raises(ParseError):
            _find_header(df)

    def test_find_header_format_a(self):
        xlsx = _make_format_a_xlsx()
        df_raw = pd.read_excel(xlsx, header=None)
        data_start, headers = _find_header(df_raw)
        assert data_start == 8
        assert any("discriminação" in h.lower() for h in headers if h)
        assert any("r$/ha" in h.lower() for h in headers if h)

    def test_find_header_format_c(self):
        xlsx = _make_format_c_xlsx()
        df_raw = pd.read_excel(xlsx, header=None)
        data_start, headers = _find_header(df_raw)
        assert data_start == 3
        assert any("discriminação" in h.lower() for h in headers if h)

    def test_find_header_format_d_multirow(self):
        xlsx = _make_format_d_xlsx()
        df_raw = pd.read_excel(xlsx, header=None)
        data_start, headers = _find_header(df_raw)
        assert data_start == 8
        assert any("discriminação" in h.lower() for h in headers if h)
        assert any("r$/ha" in h.lower() for h in headers if h)
        col_map = _identify_columns(headers)
        assert "item" in col_map
        assert "valor_ha" in col_map

    def test_find_header_prefers_best_candidate(self):
        rows = [
            [None, "A PREÇOS DE:", "data", "PARTICI-"],
            ["DISCRIMINAÇÃO", None, None, "PAÇÃO"],
            [None, "R$/ha", "R$/kg", "(%)"],
            ["Sementes", 100.0, 5.0, 10.0],
        ]
        df = pd.DataFrame(rows)
        data_start, headers = _find_header(df)
        assert data_start == 3
        col_map = _identify_columns(headers)
        assert "item" in col_map
        assert "valor_ha" in col_map


class TestIdentifyColumns:
    def test_full_headers(self):
        headers = [
            "Item / Especificação",
            "Unidade",
            "Qtd./ha",
            "Preço Unitário (R$)",
            "Valor Total/ha (R$)",
            "Participação (%)",
        ]
        mapping = _identify_columns(headers)
        assert "item" in mapping
        assert "unidade" in mapping
        assert "quantidade_ha" in mapping
        assert "preco_unitario" in mapping
        assert "valor_ha" in mapping
        assert "participacao_pct" in mapping

    def test_minimal_headers(self):
        headers = ["Discriminação", "Unid.", "Valor/ha (R$)"]
        mapping = _identify_columns(headers)
        assert "item" in mapping
        assert "valor_ha" in mapping

    def test_custo_por_ha(self):
        headers = ["DISCRIMINAÇÃO", "CUSTO POR HA", "PARTICIPAÇÃO (%)"]
        mapping = _identify_columns(headers)
        assert mapping["valor_ha"] == 1

    def test_custo_slash_kg(self):
        headers = ["DISCRIMINAÇÃO", "CUSTO POR HA", "CUSTO/kg", "PARTICIPAÇÃO (%)"]
        mapping = _identify_columns(headers)
        assert mapping["valor_ha"] == 1
        assert mapping["preco_unitario"] == 2

    def test_guard_no_overwrite(self):
        headers = [
            "DISCRIMINAÇÃO",
            "CUSTO POR HA",
            "CUSTO/kg",
            "PARTICIPAÇÃO CV(%)",
            "PARTICIPAÇÃO CT(%)",
        ]
        mapping = _identify_columns(headers)
        assert mapping["participacao_pct"] == 3


class TestRefineValorColumn:
    def test_no_offset_needed(self):
        rows = [[510.0], [840.0], [75.0]]
        df = pd.DataFrame(rows)
        col_map = {"valor_ha": 0}
        _refine_valor_column(df, 0, col_map)
        assert col_map["valor_ha"] == 0

    def test_merged_offset(self):
        rows = [[None, None, 510.0], [None, None, 840.0]]
        df = pd.DataFrame(rows)
        col_map = {"valor_ha": 0}
        _refine_valor_column(df, 0, col_map)
        assert col_map["valor_ha"] == 2

    def test_no_valor_ha_noop(self):
        df = pd.DataFrame([[1, 2]])
        col_map = {"item": 0}
        _refine_valor_column(df, 0, col_map)
        assert "valor_ha" not in col_map


class TestSelectDataSheet:
    def test_single_sheet(self):
        xlsx = _make_xlsx([["data"]], sheet_name="Plan1")
        assert select_data_sheet(xlsx) == "Plan1"

    def test_skips_indice(self):
        xlsx = _make_multi_sheet_xlsx(
            {
                "Índice": [["indice"]],
                "Dados MT 2024": [["data"]],
            }
        )
        assert select_data_sheet(xlsx) == "Dados MT 2024"

    def test_select_by_uf(self):
        xlsx = _make_multi_sheet_xlsx(
            {
                "Índice": [["indice"]],
                "Tomate GO 2023": [["data"]],
                "Tomate SP 2024": [["data"]],
            }
        )
        assert select_data_sheet(xlsx, uf="GO") == "Tomate GO 2023"

    def test_select_by_safra(self):
        xlsx = _make_multi_sheet_xlsx(
            {
                "Índice": [["indice"]],
                "Tomate GO 2023": [["data"]],
                "Tomate GO 2024": [["data"]],
            }
        )
        assert select_data_sheet(xlsx, safra="2023/24") == "Tomate GO 2024"

    def test_select_latest(self):
        xlsx = _make_multi_sheet_xlsx(
            {
                "Índice": [["indice"]],
                "Sheet A": [["data"]],
                "Sheet B": [["data"]],
            }
        )
        assert select_data_sheet(xlsx) == "Sheet B"

    def test_empty_raises(self):
        xlsx = _make_multi_sheet_xlsx(
            {
                "Índice": [["indice"]],
                "Index": [["indice"]],
            }
        )
        with pytest.raises(ParseError):
            select_data_sheet(xlsx)


class TestParseSheetInfo:
    def test_extracts_uf_and_year(self):
        uf, year = _parse_sheet_info("Tomate GO 2024")
        assert uf == "GO"
        assert year == "2024"

    def test_no_match(self):
        uf, year = _parse_sheet_info("Plan1")
        assert uf is None
        assert year is None

    def test_invalid_uf_ignored(self):
        uf, year = _parse_sheet_info("XX 2024")
        assert uf is None
        assert year == "2024"


class TestParsePlanilha:
    def test_parse_basic(self):
        xlsx = _sample_xlsx()
        items, custo_total = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        assert len(items) > 0
        assert all(i.cultura == "soja" for i in items)
        assert all(i.uf == "MT" for i in items)
        assert all(i.safra == "2023/24" for i in items)

    def test_parse_detects_coe(self):
        xlsx = _sample_xlsx(with_coe=True)
        _, custo_total = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        assert custo_total is not None
        assert custo_total.coe_ha == pytest.approx(2879.0)

    def test_parse_detects_cot_ct(self):
        xlsx = _sample_xlsx(with_coe=True, with_cot=True, with_ct=True)
        _, custo_total = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        assert custo_total is not None
        assert custo_total.coe_ha == pytest.approx(2879.0)
        assert custo_total.cot_ha == pytest.approx(3400.0)
        assert custo_total.ct_ha == pytest.approx(3800.0)

    def test_computes_coe_from_items_if_missing(self):
        xlsx = _sample_xlsx(with_coe=False)
        items, custo_total = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        assert custo_total is not None
        assert custo_total.coe_ha > 0
        coe_categorias = {"insumos", "operacoes", "mao_de_obra"}
        soma = sum(i.valor_ha for i in items if i.categoria in coe_categorias)
        assert custo_total.coe_ha == pytest.approx(soma)

    def test_parse_categories(self):
        xlsx = _sample_xlsx()
        items, _ = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        categories = {i.categoria for i in items}
        assert "insumos" in categories
        assert "operacoes" in categories
        assert "mao_de_obra" in categories

    def test_parse_numeric_values(self):
        xlsx = _sample_xlsx()
        items, _ = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        sementes = [i for i in items if "semente" in i.item.lower()]
        assert len(sementes) == 1
        assert sementes[0].valor_ha == pytest.approx(510.0)
        assert sementes[0].quantidade_ha == pytest.approx(60.0)
        assert sementes[0].preco_unitario == pytest.approx(8.50)

    def test_parse_empty_xlsx_raises(self):
        empty_xlsx = _make_xlsx([])
        with pytest.raises(ParseError):
            parse_planilha(empty_xlsx, "soja", "MT", "2023/24")

    def test_parse_malformed_raises(self):
        bad_xlsx = _make_xlsx([["foo", "bar"], ["baz", "qux"]])
        with pytest.raises(ParseError):
            parse_planilha(bad_xlsx, "soja", "MT", "2023/24")

    def test_cultura_normalization(self):
        xlsx = _sample_xlsx()
        items, _ = parse_planilha(xlsx, cultura="SOJA", uf="mt", safra="2023/24")
        assert all(i.cultura == "soja" for i in items)
        assert all(i.uf == "MT" for i in items)

    def test_tecnologia_propagation(self):
        xlsx = _sample_xlsx()
        items, _ = parse_planilha(
            xlsx, cultura="soja", uf="MT", safra="2023/24", tecnologia="media"
        )
        assert all(i.tecnologia == "media" for i in items)

    def test_parse_format_a_full(self):
        xlsx = _make_format_a_xlsx()
        items, _ = parse_planilha(xlsx, cultura="tomate", uf="GO", safra="2023/24")
        assert len(items) >= 2
        sementes = [i for i in items if "semente" in i.item.lower()]
        assert len(sementes) == 1
        assert sementes[0].valor_ha == pytest.approx(320.0)

    def test_parse_format_c_full(self):
        xlsx = _make_format_c_xlsx()
        items, custo_total = parse_planilha(xlsx, cultura="cacau", uf="BA", safra="2024/25")
        assert len(items) >= 2
        mudas = [i for i in items if "muda" in i.item.lower()]
        assert len(mudas) == 1
        assert mudas[0].valor_ha == pytest.approx(250.0)
        assert custo_total is not None
        assert custo_total.coe_ha == pytest.approx(1380.0)

    def test_parse_format_d_multirow_header(self):
        xlsx = _make_format_d_xlsx()
        items, custo_total = parse_planilha(xlsx, cultura="abacaxi", uf="TO", safra="2013/14")
        assert len(items) >= 3
        mudas = [i for i in items if "muda" in i.item.lower()]
        assert len(mudas) == 1
        assert mudas[0].valor_ha == pytest.approx(1200.0)
        assert custo_total is not None
        assert custo_total.coe_ha == pytest.approx(4800.0)


class TestItemsToDataframe:
    def test_converts_to_dataframe(self):
        xlsx = _sample_xlsx()
        items, _ = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        df = items_to_dataframe(items)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(items)
        assert "cultura" in df.columns
        assert "uf" in df.columns
        assert "safra" in df.columns
        assert "categoria" in df.columns
        assert "item" in df.columns
        assert "valor_ha" in df.columns

    def test_empty_list_returns_empty_df(self):
        df = items_to_dataframe([])
        assert df.empty

    def test_numeric_columns_are_numeric(self):
        xlsx = _sample_xlsx()
        items, _ = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        df = items_to_dataframe(items)
        assert df["valor_ha"].dtype in ("float64", "Float64")

    def test_sorted_output(self):
        xlsx = _sample_xlsx()
        items, _ = parse_planilha(xlsx, cultura="soja", uf="MT", safra="2023/24")
        df = items_to_dataframe(items)
        categories = df["categoria"].tolist()
        seen = set()
        for cat in categories:
            seen.add(cat)
        assert len(seen) >= 2


class TestParserVersion:
    def test_version_is_int(self):
        assert isinstance(PARSER_VERSION, int)
        assert PARSER_VERSION >= 1
