"""MapBiomas Alerta — Alertas de desmatamento.
Fonte: plataforma.alerta.mapbiomas.org (GraphQL, acesso publico).
Licenca: Livre (citacao obrigatoria).
"""

from agrobr.mapbiomas_alerta.api import (
    alerta_info,
    alertas,
    alertas_geo,
    alertas_geo_stream,
)

__all__ = ["alertas", "alertas_geo", "alertas_geo_stream", "alerta_info"]
