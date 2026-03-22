"""MapBiomas Alerta — Alertas de desmatamento.
Fonte: plataforma.alerta.mapbiomas.org (GraphQL, auth via token).
Licenca: Livre (citacao obrigatoria).
"""

from agrobr.mapbiomas_alerta.api import alerta_info, alertas, alertas_geo

__all__ = ["alertas", "alertas_geo", "alerta_info"]
