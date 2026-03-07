# Contrato: desmatamento

Desmatamento consolidado (PRODES) e alertas em tempo real (DETER) por bioma.

## Modos

| `tipo=` | Contrato | Fonte |
|---------|----------|-------|
| `"prodes"` (default) | `DESMATAMENTO_PRODES_V1` | INPE TerraBrasilis |
| `"deter"` | `DESMATAMENTO_DETER_V1` | INPE TerraBrasilis |

## Schema: PRODES

| Coluna | Tipo | Nullable | Unidade | Restrições |
|--------|------|----------|---------|------------|
| `ano` | INTEGER | Não | — | ≥ 2000 |
| `uf` | STRING | Não | — | UF válida |
| `classe` | STRING | Não | — | — |
| `area_km2` | FLOAT | Não | km² | ≥ 0 |
| `satelite` | STRING | Sim | — | — |
| `sensor` | STRING | Sim | — | — |
| `bioma` | STRING | Não | — | Bioma válido |

**PK:** `(ano, uf, classe, bioma)`

## Schema: DETER

| Coluna | Tipo | Nullable | Unidade | Restrições |
|--------|------|----------|---------|------------|
| `data` | DATE | Não | — | Data válida |
| `classe` | STRING | Não | — | — |
| `uf` | STRING | Não | — | UF válida |
| `municipio` | STRING | Sim | — | — |
| `municipio_id` | INTEGER | Sim | — | — |
| `area_km2` | FLOAT | Não | km² | ≥ 0 |
| `satelite` | STRING | Sim | — | — |
| `sensor` | STRING | Sim | — | — |
| `bioma` | STRING | Não | — | Amazônia ou Cerrado |

**PK:** `(data, classe, uf, municipio, bioma)`

## Restrições

- DETER só disponível para **Amazônia** e **Cerrado** (fail-fast com `ValueError`)
- Bioma é normalizado automaticamente (`"cerrado"` → `"Cerrado"`)

## Exemplo

```python
from agrobr import datasets

# PRODES — desmatamento anual consolidado
df = await datasets.desmatamento("Cerrado", tipo="prodes", ano=2023)

# DETER — alertas de desmatamento
df = await datasets.desmatamento("Amazônia", tipo="deter", data_inicio="2024-01-01")

# Com metadados
df, meta = await datasets.desmatamento("Cerrado", return_meta=True)
```
