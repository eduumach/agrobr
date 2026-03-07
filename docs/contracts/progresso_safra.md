# progresso_safra v1.0

Progresso semanal de semeadura e colheita (CONAB).

## Fontes

| Prioridade | Fonte | Descrição |
|------------|-------|-----------|
| 1 | CONAB | Companhia Nacional de Abastecimento |

## Produtos (culturas)

`algodao`, `arroz`, `feijao_1`, `milho_1`, `milho_2`, `soja`, `trigo`

O parâmetro `produto` do dataset é normalizado via `normalizar_cultura()` para o nome esperado pela API CONAB (ex: `"soja"` → `"Soja"`).

## Schema

| Coluna | Tipo | Nullable | Unidade | Estável |
|--------|------|----------|---------|---------|
| `cultura` | str | ❌ | - | Sim |
| `safra` | str | ❌ | - | Sim |
| `operacao` | str | ❌ | - | Sim |
| `estado` | str | ❌ | - | Sim |
| `semana_atual` | str | ❌ | - | Sim |
| `pct_ano_anterior` | float | ✅ | fração | Sim |
| `pct_semana_anterior` | float | ✅ | fração | Sim |
| `pct_semana_atual` | float | ✅ | fração | Sim |
| `pct_media_5_anos` | float | ✅ | fração | Sim |

**Primary key:** `[cultura, safra, operacao, estado, semana_atual]`

**Constraints:** Valores percentuais entre 0.0 e 1.0 (fração, não %)

## Garantias

- PK única por combinação cultura + safra + operação + estado + semana
- Valores percentuais entre 0.0 e 1.0 (fração, não %)
- Dados semanais publicados pela CONAB
- `estado` é código UF de 2 letras (ex: MT, GO, PR)

## Exemplo

```python
from agrobr import datasets

# Async
df = await datasets.progresso_safra("soja")
df = await datasets.progresso_safra("milho_1", estado="MT", operacao="Semeadura")

# Com metadados
df, meta = await datasets.progresso_safra("soja", return_meta=True)

# Sync
from agrobr.sync import datasets
df = datasets.progresso_safra("soja")
```

## Schema JSON

Disponível em `agrobr/schemas/progresso_safra.json`.

```python
from agrobr.contracts import get_contract
contract = get_contract("progresso_safra")
print(contract.to_json())
```
