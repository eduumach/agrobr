# Contrato: comercio_internacional

Comércio internacional bilateral de commodities agrícolas — UN Comtrade.

Reutiliza o contrato `COMERCIO_BILATERAL_V1` (mesmo schema de `comtrade.comercio()`).

## Schema

| Coluna | Tipo | Nullable | Unidade | Restrições |
|--------|------|----------|---------|------------|
| `periodo` | STRING | Não | — | — |
| `ano` | INTEGER | Não | — | >= 1988 |
| `mes` | INTEGER | Sim | — | 1-12 |
| `reporter_iso` | STRING | Não | — | — |
| `reporter` | STRING | Sim | — | — |
| `partner_iso` | STRING | Não | — | — |
| `partner` | STRING | Sim | — | — |
| `fluxo_code` | STRING | Não | — | X ou M |
| `hs_code` | STRING | Não | — | — |
| `produto_desc` | STRING | Sim | — | — |
| `peso_liquido_kg` | FLOAT | Sim | kg | >= 0 |
| `volume_ton` | FLOAT | Sim | ton | >= 0 |
| `valor_fob_usd` | FLOAT | Sim | USD | >= 0 |
| `valor_cif_usd` | FLOAT | Sim | USD | >= 0 |
| `valor_primario_usd` | FLOAT | Sim | USD | >= 0 |

**PK:** `(periodo, reporter_iso, partner_iso, hs_code, fluxo_code)`

## Diferenciação de exportacao/importacao

| | `comercio_internacional` | `exportacao` / `importacao` |
|---|---|---|
| Fonte | UN Comtrade | ComexStat/MDIC |
| Cobertura | Bilateral global (qualquer reporter/partner) | Brasil only |
| Classificação | HS codes | NCM |
| Breakdown | País a país | UF brasileira |

## Exemplo

```python
from agrobr import datasets

# Exportações de soja do Brasil para China
df = await datasets.comercio_internacional("soja", partner="CN")

# Importações dos EUA
df = await datasets.comercio_internacional("milho", reporter="US", fluxo="M")

# Mensal
df = await datasets.comercio_internacional("cafe", freq="M", periodo="2024")

# Com metadados
df, meta = await datasets.comercio_internacional("soja", return_meta=True)
```
