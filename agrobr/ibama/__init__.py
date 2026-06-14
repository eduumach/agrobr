"""IBAMA — Embargos ambientais.
Fonte: dadosabertos.ibama.gov.br (dump CSV do SIFISC com geometrias WKT, sem auth).
Licenca: ODbL.
"""

from agrobr.ibama.api import embargos, embargos_geo

__all__ = ["embargos", "embargos_geo"]
