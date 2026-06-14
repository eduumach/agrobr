# SICAR (Cadastro Ambiental Rural)

Dados tabulares de imoveis rurais do CAR via WFS do GeoServer SICAR.

## imoveis

Registros individuais de imoveis rurais (sem geometria).

```python
import agrobr

df = await agrobr.alt.sicar.imoveis("DF")
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| uf | str | Sim | Sigla da UF (ex: "MT", "DF", "BA") |
| municipio | str | Nao | Filtro parcial de municipio (case-insensitive). Mutuamente exclusivo com `cod_municipio` |
| cod_municipio | int | Nao | Codigo IBGE do municipio (ex: 5107925). Mutuamente exclusivo com `municipio` |
| status | str | Nao | AT, PE, SU ou CA |
| tipo | str | Nao | IRU, AST ou PCT |
| area_min | float | Nao | Area minima em hectares |
| area_max | float | Nao | Area maxima em hectares |
| criado_apos | str | Nao | Data minima de criacao (ISO, ex: "2020-01-01") |
| atualizado_apos | str | Nao | Retorna apenas registros com `data_atualizacao` posterior a esta data (ISO, ex: "2026-06-07" ou "2026-06-07T00:00:00"). Indisponivel para SP, RS, PR, SC, RJ, TO (campo nao existe nesses layers WFS) |
| return_meta | bool | Nao | Se True, retorna (DataFrame, MetaInfo) |

### Colunas de retorno

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| cod_imovel | str | Codigo unico do imovel |
| status | str | AT/PE/SU/CA |
| data_criacao | datetime | Data de criacao |
| data_atualizacao | datetime | Ultima atualizacao (nullable) |
| area_ha | float | Area em hectares |
| condicao | str | Condicao do cadastro (nullable) |
| uf | str | Sigla UF |
| municipio | str | Nome do municipio |
| cod_municipio_ibge | int | Codigo IBGE |
| modulos_fiscais | float | Modulos fiscais |
| tipo | str | IRU/AST/PCT |

### Exemplos

```python
# Imoveis ativos em Sorriso-MT
df = await agrobr.alt.sicar.imoveis(
    "MT", municipio="Sorriso", status="AT"
)

# Filtro por codigo IBGE (evita problemas com acentos)
df = await agrobr.alt.sicar.imoveis("PA", cod_municipio=1508159)  # Uruara

# Imoveis grandes (>1000 ha) no DF
df = await agrobr.alt.sicar.imoveis("DF", area_min=1000)

# Cadastros criados apos 2020
df = await agrobr.alt.sicar.imoveis(
    "GO", criado_apos="2020-01-01"
)

# Cadastros atualizados apos uma data (util para sincronizar a base incrementalmente)
df = await agrobr.alt.sicar.imoveis(
    "MG", atualizado_apos="2026-06-07T00:00:00"
)

# Com metadados de proveniencia
df, meta = await agrobr.alt.sicar.imoveis("DF", return_meta=True)
print(meta.records_count, meta.fetch_duration_ms)
```

## resumo

Estatisticas agregadas por UF ou municipio.

```python
df = await agrobr.alt.sicar.resumo("MT")
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| uf | str | Sim | Sigla da UF |
| municipio | str | Nao | Filtro parcial de municipio (case-insensitive). Mutuamente exclusivo com `cod_municipio` |
| cod_municipio | int | Nao | Codigo IBGE do municipio. Mutuamente exclusivo com `municipio` |
| return_meta | bool | Nao | Se True, retorna (DataFrame, MetaInfo) |

### Retorno sem municipio (UF-level)

Usa `resultType=hits` (4 requests rapidos, sem download de dados):

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| total | int | Total de imoveis |
| ativos | int | Imoveis com status AT |
| pendentes | int | Imoveis com status PE |
| suspensos | int | Imoveis com status SU |
| cancelados | int | Imoveis com status CA |

### Retorno com municipio

Busca dados e agrega client-side:

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| total | int | Total de imoveis |
| ativos | int | Imoveis com status AT |
| pendentes | int | Imoveis com status PE |
| suspensos | int | Imoveis com status SU |
| cancelados | int | Imoveis com status CA |
| area_total_ha | float | Soma das areas |
| area_media_ha | float | Media das areas |
| modulos_fiscais_medio | float | Media de modulos fiscais |
| por_tipo_IRU | int | Imoveis rurais |
| por_tipo_AST | int | Assentamentos |
| por_tipo_PCT | int | Terras indigenas |

### Exemplos

```python
# Resumo do DF (rapido, sem download)
df = await agrobr.alt.sicar.resumo("DF")

# Resumo de Sorriso-MT (com agregacao)
df = await agrobr.alt.sicar.resumo("MT", municipio="Sorriso")
```

## imoveis_geo

Registros individuais com geometria (poligonos MultiPolygon). Requer `pip install agrobr[geo]`.

```python
import agrobr

gdf = await agrobr.alt.sicar.imoveis_geo("DF")
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| uf | str | Sim | Sigla da UF (ex: "MT", "DF", "BA") |
| municipio | str | Nao | Filtro parcial de municipio (case-insensitive). Mutuamente exclusivo com `cod_municipio` |
| cod_municipio | int | Nao | Codigo IBGE do municipio (ex: 5107925). Mutuamente exclusivo com `municipio` |
| status | str | Nao | AT, PE, SU ou CA |
| tipo | str | Nao | IRU, AST ou PCT |
| area_min | float | Nao | Area minima em hectares |
| area_max | float | Nao | Area maxima em hectares |
| criado_apos | str | Nao | Data minima de criacao (ISO, ex: "2020-01-01") |
| atualizado_apos | str | Nao | Retorna apenas registros com `data_atualizacao` posterior a esta data (ISO, ex: "2026-06-07" ou "2026-06-07T00:00:00"). Indisponivel para SP, RS, PR, SC, RJ, TO (campo nao existe nesses layers WFS) |
| return_meta | bool | Nao | Se True, retorna (GeoDataFrame, MetaInfo) |

### Colunas de retorno

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| cod_imovel | str | Codigo unico do imovel |
| status | str | AT/PE/SU/CA |
| data_criacao | datetime | Data de criacao |
| data_atualizacao | datetime | Ultima atualizacao (nullable) |
| area_ha | float | Area em hectares |
| condicao | str | Condicao do cadastro (nullable) |
| uf | str | Sigla UF |
| municipio | str | Nome do municipio |
| cod_municipio_ibge | int | Codigo IBGE |
| modulos_fiscais | float | Modulos fiscais |
| tipo | str | IRU/AST/PCT |
| geometry | MultiPolygon | Poligono do imovel (EPSG:4326) |

### Exemplos

```python
# Imoveis com geometria no DF
gdf = await agrobr.alt.sicar.imoveis_geo("DF")
gdf.plot()

# Filtrar por municipio (nome)
gdf = await agrobr.alt.sicar.imoveis_geo(
    "MT", municipio="Sorriso", status="AT"
)

# Filtrar por codigo IBGE (evita problemas com acentos)
gdf = await agrobr.alt.sicar.imoveis_geo("PA", cod_municipio=1508159)

# Com metadados
gdf, meta = await agrobr.alt.sicar.imoveis_geo("DF", return_meta=True)
```

### Notas

- Maximo 5.000 features por request (warning se truncado)
- Request unico sem paginacao (volume controlado)
- CRS: EPSG:4326 (WGS84)

## imoveis_geo_stream

Itera sobre os imoveis com geometria de uma UF em batches, sem acumular tudo em
memoria antes de comecar a usar os dados. Requer `pip install agrobr[geo]`.

```python
import agrobr

async for gdf in agrobr.alt.sicar.imoveis_geo_stream("MT"):
    print(len(gdf))
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| uf | str | Sim | Sigla da UF (ex: "MT", "DF", "BA") |
| municipio | str | Nao | Filtro parcial de municipio (case-insensitive). Mutuamente exclusivo com `cod_municipio` |
| cod_municipio | int | Nao | Codigo IBGE do municipio (ex: 5107925). Mutuamente exclusivo com `municipio` |
| status | str | Nao | AT, PE, SU ou CA |
| tipo | str | Nao | IRU, AST ou PCT |
| area_min | float | Nao | Area minima em hectares |
| area_max | float | Nao | Area maxima em hectares |
| criado_apos | str | Nao | Data minima de criacao (ISO, ex: "2020-01-01") |
| atualizado_apos | str | Nao | Retorna apenas registros com `data_atualizacao` posterior a esta data (ISO, ex: "2026-06-07" ou "2026-06-07T00:00:00"). Indisponivel para SP, RS, PR, SC, RJ, TO (campo nao existe nesses layers WFS) |

Cada item gerado e um `GeoDataFrame` com as mesmas colunas de [`imoveis_geo`](#imoveis_geo).

### Exemplos

```python
# Acumula o total de imoveis de Sorriso-MT sem guardar tudo em memoria
total = 0
async for gdf in agrobr.alt.sicar.imoveis_geo_stream("MT", municipio="Sorriso"):
    total += len(gdf)
print(total)
```

### Notas

- Sem limite de `max_features`: pagina ate esgotar todos os registros da UF
- Cada yield contem ate `GEO_BATCH_SIZE * 10.000` features (`GEO_BATCH_SIZE` paginas de 10.000 baixadas em paralelo via `asyncio.gather`; default `GEO_BATCH_SIZE=1`)
- Deduplica `cod_imovel` entre batches
- CRS: EPSG:4326 (WGS84)
- Async-only: `agrobr.sync` nao suporta async generators

## diff_imoveis

Compara dois snapshots de [`imoveis()`](#imoveis) ou [`imoveis_geo()`](#imoveis_geo) (mesma UF/filtros,
capturados em momentos diferentes) e identifica o que mudou entre eles, usando `cod_imovel` como
chave. E a forma recomendada de sincronizar a base nas UFs sem `data_atualizacao`
(SP, RS, PR, SC, RJ, TO — ver `atualizado_apos` em [`imoveis`](#imoveis)).

```python
import agrobr

anterior = await agrobr.alt.sicar.imoveis("SP")
# ... dias depois ...
atual = await agrobr.alt.sicar.imoveis("SP")

mudancas = agrobr.alt.sicar.diff_imoveis(anterior, atual)
print(mudancas[["cod_imovel", "mudanca", "colunas_alteradas"]])
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| anterior | DataFrame | Sim | Snapshot anterior, com a coluna `cod_imovel` |
| atual | DataFrame | Sim | Snapshot atual, com a coluna `cod_imovel` |

### Retorno

`DataFrame` (ou `GeoDataFrame`, se a entrada tiver `geometry`) com as colunas de `atual`
(registros removidos usam os valores de `anterior`), mais:

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| mudanca | str | "novo", "alterado" ou "removido" |
| colunas_alteradas | list[str] | Colunas que mudaram de valor (vazia para "novo"/"removido") |

Registros sem alteracao entre os dois snapshots nao aparecem no resultado. A coluna `geometry`,
se presente, e ignorada na comparacao (apenas carregada no resultado).

### Notas

- Funcao sincrona e local (sem requests): so compara DataFrames ja carregados em memoria
- Util tambem para auditar diferencas entre execucoes nas UFs com `data_atualizacao`
- Levanta `ValueError` se `cod_imovel` nao estiver presente em `anterior` ou `atual`

## Uso sincrono

```python
from agrobr import sync

df = sync.sicar.imoveis("DF")
gdf = sync.sicar.imoveis_geo("DF")
df = sync.sicar.resumo("MT", municipio="Sorriso")
```

## Fonte de dados

- **Provedor:** Servico Florestal Brasileiro (SFB) / SICAR
- **API:** WFS 2.0.0 (OGC GeoServer)
- **Licenca:** CC-BY (dados abertos governo federal)
- **Atualizacao:** continua (cadastros em tempo real)
