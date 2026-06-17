# Desmatamento (PRODES/DETER)

Dados de desmatamento do INPE via TerraBrasilis — PRODES (consolidado anual) e DETER (alertas em tempo real).

## `desmatamento.prodes()`

Dados anuais de desmatamento consolidado por poligono.

```python
import agrobr

df = await agrobr.desmatamento.prodes(bioma="Cerrado", ano=2022, uf="MT")
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| `bioma` | `str` | Nao | Bioma: "Amazonia", "Cerrado", "Caatinga", "Mata Atlantica", "Pantanal", "Pampa". Default: "Cerrado" |
| `ano` | `int` | Nao | Ano (ex: 2022). Se None, todos os anos |
| `uf` | `str` | Nao | Filtrar por UF (ex: "MT") |
| `return_meta` | `bool` | Nao | Se True, retorna `(DataFrame, MetaInfo)` |

### Colunas de Retorno

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `ano` | int | Ano do desmatamento |
| `uf` | str | Codigo UF (ex: "MT") |
| `classe` | str | Classe de cobertura (ex: "desmatamento") |
| `area_km2` | float | Area desmatada em km2 |
| `satelite` | str | Satelite utilizado |
| `sensor` | str | Sensor do satelite |
| `bioma` | str | Bioma consultado |

### Biomas Disponiveis (PRODES)

| Bioma | Workspace GeoServer | Layer | Serie Historica |
|-------|--------------------|----|---|
| Amazonia | prodes-amazon-nb | yearly_deforestation_biome | 2000+ |
| Cerrado | prodes-cerrado-nb | yearly_deforestation | 2000+ |
| Caatinga | prodes-caatinga-nb | yearly_deforestation | 2000+ |
| Mata Atlantica | prodes-mata-atlantica-nb | yearly_deforestation | 2000+ |
| Pantanal | prodes-pantanal-nb | yearly_deforestation | 2000+ |
| Pampa | prodes-pampa-nb | yearly_deforestation | 2000+ |

---

## `desmatamento.prodes_geo()`

Dados PRODES com geometria (poligonos). Retorna `GeoDataFrame` com coluna `geometry` (MultiPolygon EPSG:4326).

Requer dependencia opcional: `pip install agrobr[geo]`

```python
import agrobr

gdf = await agrobr.desmatamento.prodes_geo(
    bioma="Cerrado",
    ano=2022,
    uf="MT",
)

# Cruzamento geoespacial com CAR/SICAR
import geopandas as gpd
car = gpd.read_file("imoveis_car.geojson")
desmatamento_em_car = gpd.sjoin(gdf, car)
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| `bioma` | `str` | Nao | Bioma: "Amazonia", "Cerrado", "Caatinga", "Mata Atlantica", "Pantanal", "Pampa". Default: "Cerrado" |
| `ano` | `int` | Nao | Ano (ex: 2022). Se None, todos os anos |
| `uf` | `str` | Nao | Filtrar por UF (ex: "MT") |
| `return_meta` | `bool` | Nao | Se True, retorna `(GeoDataFrame, MetaInfo)` |

### Colunas de Retorno

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `ano` | int | Ano do desmatamento |
| `uf` | str | Codigo UF (ex: "MT") |
| `classe` | str | Classe de cobertura (ex: "desmatamento") |
| `area_km2` | float | Area desmatada em km2 |
| `satelite` | str | Satelite utilizado |
| `sensor` | str | Sensor do satelite |
| `bioma` | str | Bioma consultado |
| `geometry` | geometry | MultiPolygon EPSG:4326 |

### Notas

- Default `maxFeatures=10000` — use filtros (uf, ano) para reduzir volume
- Warning logado automaticamente se a resposta atingir o limite de features (possivel truncamento)
- Coluna de geometria no GeoServer e `geom` para todos os 6 biomas (uniforme)

---

## `desmatamento.deter()`

Alertas diarios de desmatamento em tempo real.

```python
import agrobr

df = await agrobr.desmatamento.deter(
    bioma="Amazônia",
    uf="PA",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
)
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| `bioma` | `str` | Nao | Bioma: "Amazonia", "Cerrado". Default: "Amazonia" |
| `uf` | `str` | Nao | Filtrar por UF (ex: "PA") |
| `data_inicio` | `str` | Nao | Data inicial YYYY-MM-DD |
| `data_fim` | `str` | Nao | Data final YYYY-MM-DD |
| `classe` | `str` | Nao | Filtrar por classe de alerta |
| `return_meta` | `bool` | Nao | Se True, retorna `(DataFrame, MetaInfo)` |

### Colunas de Retorno

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `data` | date | Data do alerta |
| `classe` | str | Tipo de alerta (DESMATAMENTO_CR, DEGRADACAO, MINERACAO, etc.) |
| `uf` | str | Codigo UF |
| `municipio` | str | Nome do municipio |
| `municipio_id` | int | Codigo IBGE do municipio |
| `area_km2` | float | Area em km2 |
| `satelite` | str | Satelite utilizado |
| `sensor` | str | Sensor do satelite |
| `bioma` | str | Bioma consultado |

### Classes DETER

| Classe | Descricao |
|--------|-----------|
| `DESMATAMENTO_CR` | Desmatamento com corte raso |
| `DESMATAMENTO_VEG` | Desmatamento com vegetacao secundaria |
| `DEGRADACAO` | Degradacao florestal |
| `MINERACAO` | Atividade de mineracao |
| `CICATRIZ_DE_QUEIMADA` | Cicatriz de queimada |
| `CS_DESORDENADO` | Corte seletivo desordenado |
| `CS_GEOMETRICO` | Corte seletivo geometrico |

---

## `desmatamento.deter_geo()`

Alertas DETER com geometria (poligonos). Retorna `GeoDataFrame` com coluna `geometry` (MultiPolygon EPSG:4326).

Requer dependencia opcional: `pip install agrobr[geo]`

```python
import agrobr

gdf = await agrobr.desmatamento.deter_geo(
    bioma="Amazônia",
    uf="PA",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
)

# Cruzamento geoespacial com CAR/SICAR
import geopandas as gpd
car = gpd.read_file("imoveis_car.geojson")
alertas_em_reserva = gpd.sjoin(gdf, car[car["tipo"] == "RESERVA_LEGAL"])
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| `bioma` | `str` | Nao | Bioma: "Amazonia", "Cerrado". Default: "Amazonia" |
| `uf` | `str` | Nao | Filtrar por UF (ex: "PA") |
| `data_inicio` | `str` | Nao | Data inicial YYYY-MM-DD |
| `data_fim` | `str` | Nao | Data final YYYY-MM-DD |
| `classe` | `str` | Nao | Filtrar por classe de alerta |
| `return_meta` | `bool` | Nao | Se True, retorna `(GeoDataFrame, MetaInfo)` |

### Colunas de Retorno

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| `data` | date | Data do alerta |
| `classe` | str | Tipo de alerta (DESMATAMENTO_CR, DEGRADACAO, MINERACAO, etc.) |
| `uf` | str | Codigo UF |
| `municipio` | str | Nome do municipio |
| `municipio_id` | int | Codigo IBGE do municipio |
| `area_km2` | float | Area em km2 |
| `satelite` | str | Satelite utilizado |
| `sensor` | str | Sensor do satelite |
| `bioma` | str | Bioma consultado |
| `geometry` | geometry | MultiPolygon EPSG:4326 |

### Notas

- Default `maxFeatures=10000` — use filtros (uf, data_inicio/data_fim, classe) para reduzir volume
- Warning logado automaticamente se a resposta atingir o limite de features (possivel truncamento)
- Volume aproximado: ~1.1 KB por feature com geometria

---

## `desmatamento.deter_geo_stream()`

Itera os alertas DETER com geometria em batches, sem acumular tudo em memoria nem
esbarrar no teto de `maxFeatures` da chamada unica de `deter_geo()`. Pagina a WFS
via `startIndex`/`count` (WFS 2.0.0). Requer `pip install agrobr[geo]`.

```python
import agrobr

# Processa todos os alertas da Amazonia sem guardar tudo em memoria
total = 0
async for gdf in agrobr.desmatamento.deter_geo_stream(bioma="Amazônia"):
    total += len(gdf)
print(total)
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| `bioma` | `str` | Nao | Bioma: "Amazonia", "Cerrado". Default: "Amazonia" |
| `uf` | `str` | Nao | Filtrar por UF (ex: "PA") |
| `data_inicio` | `str` | Nao | Data inicial YYYY-MM-DD |
| `data_fim` | `str` | Nao | Data final YYYY-MM-DD |
| `classe` | `str` | Nao | Filtrar por classe de alerta (aplicado por batch) |
| `page_size` | `int` | Nao | Features por pagina WFS. Default: 5000 |

Cada item gerado e um `GeoDataFrame` com as mesmas colunas de [`deter_geo()`](#desmatamentodeter_geo).

### Notas

- Sem teto de `maxFeatures`: pagina ate esgotar todos os registros do recorte
- Cada yield contem ate `page_size` features (uma pagina WFS), baixadas sequencialmente com throttle
- Paginas vazias sao ignoradas
- CRS: EPSG:4326 (WGS84)
- Async-only: `agrobr.sync` nao suporta async generators

---

## Uso Sincrono

```python
from agrobr import sync

df = sync.desmatamento.prodes(bioma="Cerrado", ano=2022, uf="MT")
gdf_prodes = sync.desmatamento.prodes_geo(bioma="Cerrado", ano=2022, uf="MT")
df_deter = sync.desmatamento.deter(bioma="Amazônia", uf="PA", data_inicio="2024-01-01")
gdf = sync.desmatamento.deter_geo(bioma="Amazônia", uf="PA", data_inicio="2024-01-01")
```

## Fonte dos Dados

- **PRODES**: Programa de Monitoramento da Floresta Amazonica e demais Biomas Brasileiros por Satelite
- **DETER**: Sistema de Deteccao de Desmatamento em Tempo Real
- **Provedor**: INPE — Instituto Nacional de Pesquisas Espaciais
- **API**: TerraBrasilis GeoServer (WFS)
- **Licenca**: Dados publicos governo federal — uso livre com citacao
