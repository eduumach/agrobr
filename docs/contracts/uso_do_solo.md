# Contrato: uso_do_solo

Cobertura e uso da terra (MapBiomas) — cobertura anual e transições entre classes.

## Modos

| `tipo=` | Contrato | Fonte |
|---------|----------|-------|
| `"cobertura"` (default) | `MAPBIOMAS_COBERTURA_V1` | MapBiomas |
| `"transicao"` | `MAPBIOMAS_TRANSICAO_V1` | MapBiomas |

## Schema: Cobertura

| Coluna | Tipo | Nullable | Unidade | Restrições |
|--------|------|----------|---------|------------|
| `bioma` | STRING | Não | — | Bioma válido |
| `estado` | STRING | Não | — | UF válida |
| `classe_id` | INTEGER | Não | — | Código LULC MapBiomas |
| `classe` | STRING | Não | — | — |
| `nivel_0` | STRING | Sim | — | — |
| `ano` | INTEGER | Não | — | ≥ 1985 |
| `area_ha` | FLOAT | Não | ha | ≥ 0 |

**PK:** `(bioma, estado, classe_id, ano)`

## Schema: Transição

| Coluna | Tipo | Nullable | Unidade | Restrições |
|--------|------|----------|---------|------------|
| `bioma` | STRING | Não | — | Bioma válido |
| `estado` | STRING | Não | — | UF válida |
| `classe_de_id` | INTEGER | Não | — | Código LULC |
| `classe_de` | STRING | Não | — | — |
| `classe_para_id` | INTEGER | Não | — | Código LULC |
| `classe_para` | STRING | Não | — | — |
| `periodo` | STRING | Não | — | Formato YYYY-YYYY |
| `area_ha` | FLOAT | Não | ha | ≥ 0 |

**PK:** `(bioma, estado, classe_de_id, classe_para_id, periodo)`

## Nível municipal

Cobertura suporta `nivel="municipio"` — contrato de PK é ignorado nesse modo (PK não inclui município).

## Exemplo

```python
from agrobr import datasets

# Cobertura por estado
df = await datasets.uso_do_solo(tipo="cobertura", bioma="Cerrado", ano=2022)

# Cobertura por município
df = await datasets.uso_do_solo(tipo="cobertura", nivel="municipio", municipio="Cuiabá")

# Transições entre classes
df = await datasets.uso_do_solo(tipo="transicao", periodo="2020-2021")

# Com metadados
df, meta = await datasets.uso_do_solo(tipo="cobertura", return_meta=True)
```
