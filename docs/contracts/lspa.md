# lspa v1.0

Levantamento Sistemático da Produção Agrícola — estimativas mensais do IBGE.

## Fontes

| Prioridade | Fonte | Descrição |
|------------|-------|-----------|
| 1 | IBGE LSPA | Levantamento Sistemático da Produção Agrícola |

## Schema

| Coluna | Tipo | Nullable | Descrição |
|--------|------|----------|-----------|
| `ano` | int | ❌ | Ano de referência (>= 1974) |
| `mes` | int | ✅ | Mês de referência (1-12) |
| `produto` | str | ❌ | Nome do produto |
| `variavel` | str | ✅ | Variável medida |
| `valor` | float64 | ✅ | Valor da medição |
| `fonte` | str | ❌ | Sempre `ibge_lspa` |

## Primary Key

`[ano, mes, produto]`

## Garantias

- Nomes de colunas nunca mudam (apenas adições)
- `ano` é sempre um ano válido
- `mes` é entre 1 e 12 quando presente
- `fonte` é sempre `ibge_lspa`

## Schema JSON

Disponível em `agrobr/schemas/lspa.json`.

```python
from agrobr.contracts import get_contract
contract = get_contract("lspa")
print(contract.to_json())
```
