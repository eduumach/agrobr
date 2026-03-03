"""ZARC -- Zoneamento Agricola de Risco Climatico.

Janelas de plantio recomendadas por municipio, cultura, solo e ciclo.
Fonte: MAPA/Embrapa via dados.agricultura.gov.br (CC-BY).
Cobertura: 40+ culturas, todos os municipios, safras 2016/2017 a atual + perene.
"""

from agrobr.zarc.api import culturas, safras_disponiveis, zoneamento

__all__ = ["culturas", "safras_disponiveis", "zoneamento"]
