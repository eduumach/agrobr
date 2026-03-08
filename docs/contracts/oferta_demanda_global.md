# Contrato: oferta_demanda_global

Oferta e demanda global de commodities agrícolas — USDA PSD.

## Schema (long format)

| Coluna | Tipo | Nullable | Unidade | Restrições |
|--------|------|----------|---------|------------|
| `commodity_code` | STRING | Não | — | PSD 7-digit code |
| `commodity` | STRING | Não | — | pt-br |
| `country_code` | STRING | Não | — | ISO 2-letter |
| `country` | STRING | Sim | — | — |
| `market_year` | INTEGER | Não | — | >= 1960 |
| `attribute` | STRING | Não | — | English name |
| `attribute_br` | STRING | Sim | — | pt-br name |
| `value` | FLOAT | Sim | 1000 MT / 1000 HA | — |
| `unit` | STRING | Sim | — | — |

**PK:** `(commodity_code, country_code, market_year, attribute)`

## Pivot mode

Quando `pivot=True`, colunas dinâmicas são geradas (uma por attribute). A validação de contrato é skipped nesse caso.

## Exemplo

```python
from agrobr import datasets

# Soja Brasil — long format
df = await datasets.oferta_demanda_global("soja")

# Pivot (attributes como colunas)
df = await datasets.oferta_demanda_global("soja", pivot=True)

# Outro país + ano específico
df = await datasets.oferta_demanda_global("milho", country="US", market_year=2023)

# Com metadados
df, meta = await datasets.oferta_demanda_global("soja", return_meta=True)
```
