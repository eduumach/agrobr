"""Acervo Fundiario — Certificacao fundiaria e assentamentos (INCRA).

Fonte: acervofundiario.incra.gov.br (WFS OGC, sem auth).
Licenca: Vedado uso comercial — classificacao nc.
"""

from agrobr.acervo_fundiario.api import (
    assentamentos,
    assentamentos_geo,
    sigef,
    sigef_geo,
    snci,
    snci_geo,
)

__all__ = [
    "assentamentos",
    "assentamentos_geo",
    "sigef",
    "sigef_geo",
    "snci",
    "snci_geo",
]
