# FUNAI — Terras Indigenas

## Visao Geral

| Item | Detalhe |
|------|---------|
| Provedor | FUNAI (Fundacao Nacional dos Povos Indigenas) |
| Dados | Terras Indigenas poligonais |
| Acesso | WFS OGC (GeoServer) |
| Formato | CSV (tabular) / GeoJSON (geo) |
| Autenticacao | Nenhuma |
| Licenca | CC BY-ND 3.0 |
| Features | ~740 TIs |

## Acesso via WFS

| Parametro | Valor |
|-----------|-------|
| Endpoint | `geoserver.funai.gov.br/geoserver/Funai/ows` |
| WFS Version | 2.0.0 |
| Layer | `Funai:tis_poligonais` |
| CRS | EPSG:4674 |

## Exemplo de Uso

```python
import asyncio
from agrobr import funai

async def main():
    # Todas as TIs
    df = await funai.terras_indigenas()

    # Filtrar por UF
    df = await funai.terras_indigenas(uf="MT")

    # Filtrar por fase
    df = await funai.terras_indigenas(fase="Regularizada")

    # Com geometria (requer geopandas)
    gdf = await funai.terras_indigenas_geo(bbox=(-56, -16, -54, -14))

    # Com metadados
    df, meta = await funai.terras_indigenas(return_meta=True)

asyncio.run(main())
```

## Colunas

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| codigo | int | Codigo da TI |
| nome | str | Nome da TI |
| etnia | str | Etnia predominante |
| municipio | str | Municipio sede |
| uf | str | UF (sigla) |
| area_ha | float | Area em hectares |
| fase | str | Fase do processo |
| modalidade | str | Modalidade da TI |
| data_atualizacao | datetime | Data de atualizacao |

## Fases

Regularizada, Homologada, Declarada, Delimitada, Em Estudo, Encaminhada RI.

## Limitacoes

- Apenas TIs poligonais (pontos e linhas excluidos)
- Dados refletem o estado atual do GeoServer FUNAI
- CC BY-ND 3.0: uso livre com citacao, sem derivados
