# ZARC (Zoneamento Agricola de Risco Climatico)

Janelas de plantio recomendadas por municipio, cultura, tipo de solo e ciclo do cultivar.

## zoneamento

Consulta a Tabua de Risco ZARC.

```python
import agrobr

df = await agrobr.zarc.zoneamento(cultura="soja", uf="MT", safra="2025/2026")
```

### Parametros

| Parametro | Tipo | Obrigatorio | Descricao |
|-----------|------|-------------|-----------|
| cultura | str | Nao | Nome canonico da cultura (ex: "soja", "milho_1", "trigo") |
| uf | str | Nao | Sigla da UF (ex: "MT", "SP") |
| municipio | int \| str | Nao | Codigo IBGE 7 digitos (int) ou nome parcial (str) |
| safra | str | Nao | "2025/2026" ou "perene" (default: safra mais recente) |
| solo | int | Nao | Codigo tipo de solo (1-3 classico, 11-16 novo 6-AD) |
| ciclo | int | Nao | Codigo ciclo do cultivar (20, 21, 22, 24) |
| as_polars | bool | Nao | Se True, retorna polars DataFrame |
| return_meta | bool | Nao | Se True, retorna (DataFrame, MetaInfo) |

### Colunas de retorno

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| cultura | str | Nome canonico (ex: "soja", "milho_1") |
| safra | str | "2025/2026" ou "perene" |
| geocodigo | str | Codigo IBGE do municipio (7 digitos) |
| uf | str | Sigla UF |
| municipio | str | Nome do municipio |
| solo_codigo | int | Tipo de solo |
| ciclo_codigo | int | Ciclo do cultivar |
| clima | str | Restricao climatica |
| manejo | str | Manejo especifico |
| portaria | str | Numero da portaria MAPA |
| dec1-dec36 | int | Risco por decendio (0/20/30/40) |

### Exemplos

```python
# Soja em Mato Grosso
df = await agrobr.zarc.zoneamento(cultura="soja", uf="MT")

# Municipio especifico por geocodigo
df = await agrobr.zarc.zoneamento(municipio=5107925, safra="2025/2026")

# Busca por nome parcial de municipio
df = await agrobr.zarc.zoneamento(municipio="Sorriso", cultura="soja")

# Filtro por solo e ciclo
df = await agrobr.zarc.zoneamento(cultura="milho_1", solo=2, ciclo=20)

# Culturas perenes
df = await agrobr.zarc.zoneamento(cultura="cafe_arabica", safra="perene")

# Com metadados
df, meta = await agrobr.zarc.zoneamento(cultura="soja", uf="MT", return_meta=True)
print(meta.records_count, meta.fetch_duration_ms)
```

## culturas

Lista de culturas disponiveis no ZARC (nomes canonicos agrobr).

```python
culturas = agrobr.zarc.culturas()
# ['algodao', 'amendoim', 'arroz', 'aveia', 'banana_cavendish', ...]
```

Funcao sincrona (sem await).

## safras_disponiveis

Safras disponiveis no portal CKAN (faz discovery online).

```python
safras = await agrobr.zarc.safras_disponiveis()
# ['2016/2017', '2017/2018', ..., '2025/2026', 'perene']
```

## Uso sincrono

```python
from agrobr import sync

df = sync.zarc.zoneamento(cultura="soja", uf="MT")
culturas = sync.zarc.culturas()
safras = sync.zarc.safras_disponiveis()
```

## Fonte de dados

- **Provedor:** MAPA / Embrapa
- **Portal:** [dados.agricultura.gov.br](https://dados.agricultura.gov.br/dataset/tabua-de-risco-zoneamento-agricola-de-risco-climatico)
- **Licenca:** CC-BY (dados publicos governo federal)
- **Atualizacao:** semanal
