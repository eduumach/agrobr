"""Defensivos agricolas -- Cadastro Agrofit/MAPA.

Produtos formulados, autorizacoes de uso e produtos tecnicos registrados no Brasil.
Fonte: Portal de Dados Abertos do MAPA (CC-BY).
Cobertura: ~2.8K produtos tecnicos, ~8K formulados, ~267K autorizacoes.
"""

from agrobr.defensivos.api import autorizacoes, formulados, tecnicos

__all__ = ["autorizacoes", "formulados", "tecnicos"]
