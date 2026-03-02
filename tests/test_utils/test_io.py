from __future__ import annotations

import pytest

from agrobr.exceptions import ParseError
from agrobr.utils.io import read_csv_safe


class TestReadCsvSafe:
    def test_utf8_basic(self):
        data = b"col1,col2\n1,2\n3,4"
        df = read_csv_safe(data, source="test")
        assert len(df) == 2
        assert list(df.columns) == ["col1", "col2"]

    def test_latin1_fallback(self):
        data = "col1,col2\nSão Paulo,café\n".encode("latin-1")
        df = read_csv_safe(data, source="test")
        assert len(df) == 1
        assert "São Paulo" in df["col1"].iloc[0]

    def test_kwargs_forwarded_sep(self):
        data = b"col1;col2\n1;2\n3;4"
        df = read_csv_safe(data, source="test", sep=";")
        assert list(df.columns) == ["col1", "col2"]
        assert len(df) == 2

    def test_kwargs_forwarded_dtype(self):
        data = b"id,value\n001,10\n002,20"
        df = read_csv_safe(data, source="test", dtype={"id": str})
        assert df["id"].iloc[0] == "001"

    def test_invalid_data_raises_parse_error(self):
        with pytest.raises(ParseError):
            read_csv_safe(b"", source="test", label="CSV bad")

    def test_custom_label_in_error(self):
        with pytest.raises(ParseError, match="CSV PRODES"):
            read_csv_safe(b"", source="test", label="CSV PRODES")

    def test_parser_version_forwarded(self):
        with pytest.raises(ParseError) as exc_info:
            read_csv_safe(b"", source="test", parser_version=3)
        assert exc_info.value.parser_version == 3
