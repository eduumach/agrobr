# importacao v1.0

Importações agrícolas brasileiras por produto, UF e mês.

## Fontes

| Prioridade | Fonte | Descrição |
|------------|-------|-----------|
| 1 | ComexStat | Dados oficiais MDIC por NCM |

## Produtos

`soja`, `milho`, `cafe`, `algodao`, `acucar`, `farelo_soja`, `oleo_soja`

## Schema

| Coluna | Tipo | Nullable | Unidade | Estável |
|--------|------|----------|---------|---------|
| `ano` | int | ❌ | - | Sim |
| `mes` | int | ❌ | - | Sim |
| `produto` | str | ❌ | - | Sim |
| `uf` | str | ✅ | - | Sim |
| `kg_liquido` | float | ✅ | kg | Sim |
| `valor_fob_usd` | float | ✅ | USD | Sim |

**Primary key:** `[ano, mes, produto, uf]`

**Constraints:** `ano >= 1997`, `mes` entre 1 e 12, `kg_liquido >= 0`, `valor_fob_usd >= 0`

## Garantias

- Nomes de coluna nunca mudam (só adicionam)
- `ano` sempre >= 1997
- `mes` entre 1 e 12
- Valores numéricos sempre >= 0

## Exemplo

```python
from agrobr import datasets

# Async
df = await datasets.importacao("soja", ano=2024)
df = await datasets.importacao("soja", ano=2024, uf="SP")

# Com metadados
df, meta = await datasets.importacao("soja", ano=2024, return_meta=True)

# Sync
from agrobr.sync import datasets
df = datasets.importacao("soja", ano=2024)
```

## Schema JSON

Disponível em `agrobr/schemas/importacao.json`.

```python
from agrobr.contracts import get_contract
contract = get_contract("importacao")
print(contract.to_json())
```
