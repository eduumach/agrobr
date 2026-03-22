# ANA/SNIRH — Agencia Nacional de Aguas

## Visao Geral

| Item | Detalhe |
|------|---------|
| Provedor | ANA (Agencia Nacional de Aguas e Saneamento Basico) |
| Dados | Hidrografia, pivos de irrigacao, demanda de irrigacao, disponibilidade hidrica |
| Acesso | ArcGIS REST API |
| Formato | JSON (tabular) / GeoJSON (geo) |
| Autenticacao | Nenhuma |
| Licenca | Dados publicos |

## Layers

| Layer | Features | Geometria | bbox obrigatorio |
|-------|----------|-----------|------------------|
| `hidrografia` | ~620K polylines | Polyline | Sim |
| `pivos_irrigacao` | ~19.9K polygons | Polygon | Nao |
| `demanda_irrigacao` | ~265K polygons | Polygon | Sim |
| `disponibilidade_hidrica` | ~42K polylines | Polyline | Nao |

## Acesso via ArcGIS REST

| Parametro | Valor |
|-----------|-------|
| Base URL | `https://portal1.snirh.gov.br/server/rest/services/dados_abertos` |
| Paginacao | Automatica (1K features/pagina) |
| Throttle | 2s delay apos 5 paginas |

## Exemplo de Uso

```python
import asyncio
from agrobr import ana

async def main():
    # Hidrografia (bbox obrigatorio — dataset grande)
    df = await ana.hidrografia(bbox=(-50, -20, -48, -18))

    # Com geometria
    gdf = await ana.hidrografia_geo(bbox=(-50, -20, -48, -18))

    # Pivos de irrigacao
    df = await ana.pivos_irrigacao(uf="GO")

    # Pivos com geometria
    gdf = await ana.pivos_irrigacao_geo(uf="SP", bbox=(-50, -22, -48, -20))

    # Demanda de irrigacao (bbox obrigatorio)
    df = await ana.demanda_irrigacao(bbox=(-50, -20, -48, -18))

    # Disponibilidade hidrica
    df = await ana.disponibilidade_hidrica(uf="MG")
    gdf = await ana.disponibilidade_hidrica_geo(bbox=(-46, -20, -44, -18))

    # Com metadados
    df, meta = await ana.pivos_irrigacao(return_meta=True)

    # Polars
    df = await ana.pivos_irrigacao(as_polars=True)

    # Limitar features
    df = await ana.hidrografia(bbox=(-50, -20, -48, -18), max_features=500)

asyncio.run(main())
```

## Colunas por Layer

### hidrografia

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| OBJECTID | int | ID do registro |
| codigo_curso | str | Codigo do curso d'agua |
| nome_rio | str | Nome do rio |
| comprimento_m | float | Comprimento em metros |
| area_m2 | float | Area em metros quadrados |
| nivel_otto | str | Nivel de ottocodificacao |
| codigo_bacia | str | Codigo da bacia |

### pivos_irrigacao

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| OBJECTID | int | ID do registro |
| UF | str | UF (sigla) |
| municipio | str | Municipio |
| area_ha | float | Area em hectares |
| ano_mapeamento | int | Ano do mapeamento |
| lat | float | Latitude |
| lon | float | Longitude |

### demanda_irrigacao

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| OBJECTID | int | ID do registro |
| codigo_bacia | str | Codigo da bacia |
| nivel_otto | str | Nivel de ottocodificacao |
| demanda_m3_s | float | Demanda em m3/segundo |
| demanda_m3_ano | float | Demanda em m3/ano |

### disponibilidade_hidrica

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| OBJECTID | int | ID do registro |
| codigo_curso | str | Codigo do curso d'agua |
| nome_rio | str | Nome do rio |
| q95_l_s | float | Vazao Q95 em litros/segundo |
| qmlt_l_s | float | Vazao media de longo termo em litros/segundo |
| codigo_bacia | str | Codigo da bacia |

## Particularidades

- **bbox obrigatorio**: `hidrografia` e `demanda_irrigacao` requerem bbox (datasets grandes)
- **Paginacao automatica**: 1K features por pagina com connection reuse
- **max_features**: parametro opcional para limitar o total de features retornadas

## Limitacoes

- Hidrografia e demanda de irrigacao exigem bbox (sem filtro retornaria centenas de milhares de features)
- Throttle de 2s apos 5 paginas para nao sobrecarregar o servidor
