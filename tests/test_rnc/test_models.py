from agrobr.rnc.models import (
    _REQUIRED_PROT,
    _REQUIRED_REG,
    DATE_COLS_PROT,
    DATE_COLS_REG,
    PROTEGIDAS_COLS,
    PROTEGIDAS_RENAME,
    REGISTRADAS_COLS,
    REGISTRADAS_RENAME,
)


def test_registradas_rename_maps_to_output_cols():
    output = set(REGISTRADAS_RENAME.values())
    expected = set(REGISTRADAS_COLS)
    assert output == expected


def test_protegidas_rename_maps_to_output_cols():
    output = set(PROTEGIDAS_RENAME.values())
    expected = set(PROTEGIDAS_COLS)
    assert output == expected


def test_required_cols_are_in_rename_keys():
    assert set(REGISTRADAS_RENAME.keys()) >= _REQUIRED_REG
    assert set(PROTEGIDAS_RENAME.keys()) >= _REQUIRED_PROT


def test_date_cols_are_in_output():
    assert all(c in REGISTRADAS_COLS for c in DATE_COLS_REG)
    assert all(c in PROTEGIDAS_COLS for c in DATE_COLS_PROT)


def test_registradas_has_10_columns():
    assert len(REGISTRADAS_COLS) == 10


def test_protegidas_has_11_columns():
    assert len(PROTEGIDAS_COLS) == 11
