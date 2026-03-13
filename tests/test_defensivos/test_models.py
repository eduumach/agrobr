from __future__ import annotations

from agrobr.defensivos.models import (
    AUTORIZACOES_COLS,
    FORMULADOS_PRODUCT_COLS,
    FORMULADOS_RENAME,
    TECNICOS_COLS,
    TECNICOS_RENAME,
    AutorizacaoUso,
    ProdutoFormulado,
    ProdutoTecnico,
)


def test_produto_formulado_valid():
    p = ProdutoFormulado(
        nr_registro="000189",
        marca_comercial="GRAMOXONE 200",
        ingrediente_ativo="DICLORETO DE PARAQUATE",
        titular="SYNGENTA",
        classe="Herbicida",
        organicos="NAO",
    )
    assert p.nr_registro == "000189"
    assert p.classe == "Herbicida"


def test_autorizacao_uso_valid():
    a = AutorizacaoUso(
        nr_registro="000189",
        marca_comercial="GRAMOXONE 200",
        cultura="ALGODAO",
        praga="Amaranthus spp.",
    )
    assert a.cultura == "ALGODAO"


def test_produto_tecnico_valid():
    t = ProdutoTecnico(
        nr_registro="T00001",
        marca_comercial="GLIFOSATO TECNICO",
        ingrediente_ativo="GLIFOSATO",
        grupo_quimico="Glicina Substituida",
    )
    assert t.grupo_quimico == "Glicina Substituida"


def test_strip_whitespace():
    p = ProdutoFormulado(
        nr_registro="  000189  ",
        marca_comercial="  GRAMOXONE 200  ",
    )
    assert p.nr_registro == "000189"
    assert p.marca_comercial == "GRAMOXONE 200"


def test_empty_string_becomes_none():
    p = ProdutoFormulado(
        nr_registro="000189",
        marca_comercial="GRAMOXONE",
        ingrediente_ativo="  ",
    )
    assert p.ingrediente_ativo is None


def test_rename_maps_consistent_with_column_lists():
    formulados_renamed = set(FORMULADOS_RENAME.values())
    for col in FORMULADOS_PRODUCT_COLS:
        assert col in formulados_renamed, f"{col} missing from FORMULADOS_RENAME values"
    for col in AUTORIZACOES_COLS:
        assert col in formulados_renamed, f"{col} missing from FORMULADOS_RENAME values"

    tecnicos_renamed = set(TECNICOS_RENAME.values())
    for col in TECNICOS_COLS:
        assert col in tecnicos_renamed, f"{col} missing from TECNICOS_RENAME values"
