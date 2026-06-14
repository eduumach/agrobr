from __future__ import annotations

from agrobr.defensivos.models import (
    AUTORIZACOES_COLS,
    FORMULADOS_PRODUCT_COLS,
    FORMULADOS_RENAME,
    TECNICOS_COLS,
    TECNICOS_RENAME,
)


def test_rename_maps_consistent_with_column_lists():
    formulados_renamed = set(FORMULADOS_RENAME.values())
    for col in FORMULADOS_PRODUCT_COLS:
        assert col in formulados_renamed, f"{col} missing from FORMULADOS_RENAME values"
    for col in AUTORIZACOES_COLS:
        assert col in formulados_renamed, f"{col} missing from FORMULADOS_RENAME values"

    tecnicos_renamed = set(TECNICOS_RENAME.values())
    for col in TECNICOS_COLS:
        assert col in tecnicos_renamed, f"{col} missing from TECNICOS_RENAME values"
