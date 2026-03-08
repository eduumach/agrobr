# Contrato: condicao_lavouras

Condição das lavouras paranaenses — SEAB/DERAL.

## Schema

| Coluna | Tipo | Nullable | Unidade | Restrições |
|--------|------|----------|---------|------------|
| `produto` | STRING | Não | — | Key normalizado DERAL |
| `data` | STRING | Não | — | dd/mm/yyyy |
| `condicao` | STRING | Não | — | boa, media, ruim, plantio, colheita |
| `pct` | FLOAT | Sim | % | 0-100 |
| `plantio_pct` | FLOAT | Sim | % | 0-100 |
| `colheita_pct` | FLOAT | Sim | % | 0-100 |

**PK:** `(produto, data, condicao)`

## Produtos

14 culturas: aveia, cafe, cana, canola, cevada, feijao, feijao_1, feijao_2, mandioca, milho, milho_1, milho_2, soja, trigo.

## Escopo geográfico

Dados cobrem exclusivamente o estado do Paraná (PR).

## Normalização

O dataset normaliza automaticamente linhas de progresso (plantio/colheita) vindas do parser DERAL:
- `condicao=""` + `plantio_pct` presente → `condicao="plantio"`
- `condicao=""` + `colheita_pct` presente → `condicao="colheita"`

## Exemplo

```python
from agrobr import datasets

# Todas as culturas
df = await datasets.condicao_lavouras()

# Apenas soja
df = await datasets.condicao_lavouras("soja")

# Com metadados
df, meta = await datasets.condicao_lavouras(return_meta=True)
```
