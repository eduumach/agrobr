"""SICAR — Cadastro Ambiental Rural (CAR) via WFS.

Fonte: Sistema Nacional de Cadastro Ambiental Rural (SICAR/SFB).
Dados abertos via GeoServer WFS (OGC), sem autenticacao.
Licenca: CC-BY (dados abertos governo federal).
"""

from agrobr.alt.sicar.api import diff_imoveis, imoveis, imoveis_geo, imoveis_geo_stream, resumo

__all__ = ["diff_imoveis", "imoveis", "imoveis_geo", "imoveis_geo_stream", "resumo"]
