# INCRA — Territorios Quilombolas

## Visao Geral

| Item | Detalhe |
|------|---------|
| Provedor | INCRA (Instituto Nacional de Colonizacao e Reforma Agraria) |
| Dados | Territorios quilombolas |
| Acesso | WFS OGC (CMR/FUNAI GeoServer) |
| Formato | CSV (tabular) / GeoJSON (geo) |
| Autenticacao | Nenhuma |
| Licenca | Dados publicos governo federal |
| Features | ~426 territorios |

## Acesso via WFS

| Parametro | Valor |
|-----------|-------|
| Endpoint | `cmr.funai.gov.br/geoserver/ows` |
| WFS Version | 1.0.0 |
| Layer | `CMR-PUBLICO:lim_quilombolas_a` |
| CRS | EPSG:4674 |

O layer e hospedado no servidor CMR da FUNAI, nao no INCRA.

## Exemplo de Uso

```python
import asyncio
from agrobr import incra

async def main():
    # Todos os territorios quilombolas
    df = await incra.quilombolas()

    # Filtrar por UF
    df = await incra.quilombolas(uf="BA")

    # Com geometria (requer geopandas)
    gdf = await incra.quilombolas_geo(bbox=(-42, -15, -40, -13))

    # Com metadados
    df, meta = await incra.quilombolas(return_meta=True)

asyncio.run(main())
```

## Colunas

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| codigo | str | Codigo do territorio |
| nome | str | Nome da comunidade |
| municipio | str | Municipio |
| uf | str | UF (sigla) |
| area_ha | float | Area em hectares |
| familias | Int64 | Numero de familias (nullable) |
| fase | str | Fase do processo |
| titulado | str | "T" (titulado) ou "F" (nao titulado) |
| data_publicacao | datetime | Data de publicacao |
| data_titulo | datetime | Data do titulo (nullable) |

## Limitacoes

- Dados hospedados em servidor FUNAI/CMR, nao INCRA
- Algumas datas podem estar ausentes (nullable)
- Campo `familias` e nullable (nem todos os registros tem essa informacao)
