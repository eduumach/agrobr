from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from lxml import etree

from agrobr.acervo_fundiario import parser
from agrobr.acervo_fundiario.models import (
    ASSENTAMENTOS_COLUNAS_SAIDA,
    NS_GML,
    NS_MS,
    SIGEF_COLUNAS_SAIDA,
    SNCI_COLUNAS_SAIDA,
)
from agrobr.exceptions import ParseError

GOLDEN = Path(__file__).resolve().parent.parent / "golden_data" / "acervo_fundiario"

EMPTY_GML = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b"<wfs:FeatureCollection"
    b' xmlns:wfs="http://www.opengis.net/wfs"'
    b' xmlns:gml="http://www.opengis.net/gml">'
    b"</wfs:FeatureCollection>"
)

MINIMAL_SIGEF_GML = (
    b'<?xml version="1.0" encoding="UTF-8"?>'
    b"<wfs:FeatureCollection"
    b' xmlns:ms="http://www.omsug.ca/osgis2004"'
    b' xmlns:wfs="http://www.opengis.net/wfs"'
    b' xmlns:gml="http://www.opengis.net/gml">'
    b"<gml:featureMember>"
    b"<ms:certificada_sigef_particular_go>"
    b"<ms:parcela_codigo>abc-123</ms:parcela_codigo>"
    b"<ms:rt>XYZ</ms:rt>"
    b"<ms:art>art-1</ms:art>"
    b"<ms:situacao_informada>REGISTRADA</ms:situacao_informada>"
    b"<ms:codigo_imovel>0001234567890</ms:codigo_imovel>"
    b"<ms:data_submissao>2024-01-15</ms:data_submissao>"
    b"<ms:data_aprovacao>2024-01-16</ms:data_aprovacao>"
    b"<ms:status>CERTIFICADA</ms:status>"
    b"<ms:nome_area>FAZENDA TEST</ms:nome_area>"
    b"<ms:registro_matricula>1234</ms:registro_matricula>"
    b"<ms:registro_data></ms:registro_data>"
    b"<ms:codigo_municipio>5200100</ms:codigo_municipio>"
    b"</ms:certificada_sigef_particular_go>"
    b"</gml:featureMember>"
    b"</wfs:FeatureCollection>"
)


class TestExtractGml2Features:
    def test_extracts_fields(self):
        records = parser._extract_gml2_features(MINIMAL_SIGEF_GML, ["parcela_codigo", "status"])
        assert len(records) == 1
        assert records[0]["parcela_codigo"] == "abc-123"
        assert records[0]["status"] == "CERTIFICADA"

    def test_empty_collection(self):
        records = parser._extract_gml2_features(EMPTY_GML, ["parcela_codigo"])
        assert records == []

    def test_missing_field_not_in_record(self):
        records = parser._extract_gml2_features(
            MINIMAL_SIGEF_GML, ["parcela_codigo", "campo_inexistente"]
        )
        assert "campo_inexistente" not in records[0]
        assert records[0]["parcela_codigo"] == "abc-123"

    def test_empty_element_text_is_none(self):
        records = parser._extract_gml2_features(MINIMAL_SIGEF_GML, ["registro_data"])
        assert records[0].get("registro_data") is None

    def test_invalid_xml_raises(self):
        with pytest.raises(etree.XMLSyntaxError):
            parser._extract_gml2_features(b"not xml", ["campo"])

    def test_uses_correct_namespaces(self):
        assert NS_GML == "http://www.opengis.net/gml"
        assert NS_MS == "http://www.omsug.ca/osgis2004"


class TestParseSigefGml:
    def test_golden_data(self):
        data = (GOLDEN / "sigef_sample" / "response.gml").read_bytes()
        df = parser.parse_sigef_gml(data)
        assert len(df) == 5
        assert list(df.columns) == SIGEF_COLUNAS_SAIDA

    def test_date_columns_are_datetime(self):
        data = (GOLDEN / "sigef_sample" / "response.gml").read_bytes()
        df = parser.parse_sigef_gml(data)
        assert pd.api.types.is_datetime64_any_dtype(df["data_submissao"])
        assert pd.api.types.is_datetime64_any_dtype(df["data_aprovacao"])

    def test_string_columns(self):
        data = (GOLDEN / "sigef_sample" / "response.gml").read_bytes()
        df = parser.parse_sigef_gml(data)
        assert df["codigo_parcela"].dtype == object
        assert df["status"].dtype == object

    def test_empty_gml(self):
        df = parser.parse_sigef_gml(EMPTY_GML)
        assert df.empty
        assert list(df.columns) == SIGEF_COLUNAS_SAIDA

    def test_minimal_gml(self):
        df = parser.parse_sigef_gml(MINIMAL_SIGEF_GML)
        assert len(df) == 1
        assert df.iloc[0]["codigo_parcela"] == "abc-123"
        assert df.iloc[0]["status"] == "CERTIFICADA"

    def test_missing_required_cols_raises(self):
        bad_gml = (
            b'<?xml version="1.0"?>'
            b'<wfs:FeatureCollection xmlns:ms="http://www.omsug.ca/osgis2004"'
            b' xmlns:wfs="http://www.opengis.net/wfs"'
            b' xmlns:gml="http://www.opengis.net/gml">'
            b"<gml:featureMember>"
            b"<ms:test><ms:rt>X</ms:rt></ms:test>"
            b"</gml:featureMember>"
            b"</wfs:FeatureCollection>"
        )
        with pytest.raises(ParseError):
            parser.parse_sigef_gml(bad_gml)


class TestParseSnciGml:
    def test_golden_data(self):
        data = (GOLDEN / "snci_sample" / "response.gml").read_bytes()
        df = parser.parse_snci_gml(data)
        assert len(df) == 5
        assert list(df.columns) == SNCI_COLUNAS_SAIDA

    def test_area_is_float(self):
        data = (GOLDEN / "snci_sample" / "response.gml").read_bytes()
        df = parser.parse_snci_gml(data)
        assert pd.api.types.is_float_dtype(df["area_peca_tecnica"])

    def test_date_strips_time_suffix(self):
        data = (GOLDEN / "snci_sample" / "response.gml").read_bytes()
        df = parser.parse_snci_gml(data)
        assert pd.api.types.is_datetime64_any_dtype(df["data_certificacao"])
        assert df["data_certificacao"].notna().all()

    def test_empty_gml(self):
        df = parser.parse_snci_gml(EMPTY_GML)
        assert df.empty
        assert list(df.columns) == SNCI_COLUNAS_SAIDA


class TestParseAssentamentosGml:
    def test_golden_data(self):
        data = (GOLDEN / "assentamentos_sample" / "response.gml").read_bytes()
        df = parser.parse_assentamentos_gml(data)
        assert len(df) == 5
        assert list(df.columns) == ASSENTAMENTOS_COLUNAS_SAIDA

    def test_numeric_columns(self):
        data = (GOLDEN / "assentamentos_sample" / "response.gml").read_bytes()
        df = parser.parse_assentamentos_gml(data)
        assert pd.api.types.is_float_dtype(df["area_ha"])
        assert pd.api.types.is_float_dtype(df["area_calc_ha"])

    def test_dd_mm_yyyy_dates(self):
        data = (GOLDEN / "assentamentos_sample" / "response.gml").read_bytes()
        df = parser.parse_assentamentos_gml(data)
        assert pd.api.types.is_datetime64_any_dtype(df["data_criacao"])
        assert pd.api.types.is_datetime64_any_dtype(df["data_obtencao"])
        assert df["data_criacao"].notna().all()

    def test_empty_gml(self):
        df = parser.parse_assentamentos_gml(EMPTY_GML)
        assert df.empty
        assert list(df.columns) == ASSENTAMENTOS_COLUNAS_SAIDA


class TestTruncationWarning:
    def test_warning_logged_when_at_max(self):
        features = []
        for i in range(5):
            features.append(
                f"<gml:featureMember><ms:t>"
                f"<ms:parcela_codigo>p{i}</ms:parcela_codigo>"
                f"<ms:codigo_imovel>c{i}</ms:codigo_imovel>"
                f"<ms:status>CERTIFICADA</ms:status>"
                f"<ms:rt>X</ms:rt><ms:art>A</ms:art>"
                f"<ms:situacao_informada>R</ms:situacao_informada>"
                f"<ms:data_submissao>2024-01-01</ms:data_submissao>"
                f"<ms:data_aprovacao>2024-01-01</ms:data_aprovacao>"
                f"<ms:nome_area>N</ms:nome_area>"
                f"<ms:registro_matricula>1</ms:registro_matricula>"
                f"<ms:registro_data></ms:registro_data>"
                f"<ms:codigo_municipio>1</ms:codigo_municipio>"
                f"</ms:t></gml:featureMember>"
            )
        gml = (
            '<?xml version="1.0"?>'
            "<wfs:FeatureCollection"
            ' xmlns:ms="http://www.omsug.ca/osgis2004"'
            ' xmlns:wfs="http://www.opengis.net/wfs"'
            ' xmlns:gml="http://www.opengis.net/gml">'
            + "".join(features)
            + "</wfs:FeatureCollection>"
        ).encode()

        from unittest.mock import patch

        with patch("agrobr.acervo_fundiario.parser.MAX_FEATURES_SIGEF", 5):
            df = parser.parse_sigef_gml(gml)
            assert len(df) == 5
