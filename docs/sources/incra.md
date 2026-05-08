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

    # Filtrar por fase do processo
    df = await incra.quilombolas(fase="TITULADO")

    # Combinar filtros
    df = await incra.quilombolas(uf="BA", fase="TITULADO")

    # Com geometria (requer geopandas)
    gdf = await incra.quilombolas_geo(bbox=(-42, -15, -40, -13))

    # Com metadados
    df, meta = await incra.quilombolas(return_meta=True)

asyncio.run(main())
```

## Filtros

Parametros aceitos por `quilombolas()` e `quilombolas_geo()`:

| Parametro | Tipo | Descricao |
|-----------|------|-----------|
| `uf` | str \| None | Sigla da UF (case-insensitive) |
| `fase` | str \| None | Fase do processo (ver tabela abaixo) |
| `bbox` | tuple\[float, float, float, float\] \| None | (minlon, minlat, maxlon, maxlat) em EPSG:4674 |

### Fases validas

| Valor | Significado |
|-------|-------------|
| `CCDRU` | Concessao de Direito Real de Uso |
| `DECRETO` | Decreto de desapropriacao publicado |
| `PORTARIA` | Portaria de reconhecimento publicada |
| `RTID` | Relatorio Tecnico de Identificacao e Delimitacao |
| `TITULADO` | Territorio com titulo definitivo emitido |
| `TITULO ANULADO` | Titulo anulado por decisao judicial |
| `TITULO PARCIAL` | Titulacao parcial (parte do territorio) |

Valores fora dessa lista levantam `ValueError`.

!!! note "Filtros aplicados client-side"
    Os filtros `uf` e `fase` sao aplicados **depois** do download (o servidor
    CMR/FUNAI nao respeita `CQL_FILTER` nesses campos). O dataset completo
    (~426 territorios) e baixado a cada chamada, independente dos filtros.
    Use `bbox` para reduzir o tamanho da resposta no servidor.

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
- Limite de 1500 features por requisicao. Quando atingido, log
  `incra_quilombolas_truncated` (ou `incra_quilombolas_geo_truncated`) e emitido
- Filtros `uf`/`fase` sao client-side (nao reduzem trafego de rede)
- Algumas datas podem estar ausentes (nullable)
- Campo `familias` e nullable (nem todos os registros tem essa informacao)
- Campo `codigo` (cd_quilomb) e nullable: ~63% dos registros sao territorios em
  pre-cadastro identificados pelo CMR/FUNAI que ainda nao receberam codigo INCRA
  oficial. Use `df["codigo"].notna()` para filtrar apenas territorios cadastrados
- Geometrias invalidas no GeoJSON sao reparadas via `shapely.validation.make_valid`
  com log `incra_quilombolas_geo_repaired`
