# extrativismo_vegetal v1.0

Producao extrativista vegetal (acai, castanha-do-para, erva-mate, palmito, etc) por UF ou municipio.

## Fontes

| Prioridade | Fonte | Descricao |
|------------|-------|-----------|
| 1 | IBGE PEVS | Producao da Extracao Vegetal e da Silvicultura |

## Produtos

`acai`, `castanha_para`, `erva_mate`, `palmito`, `pequi_fruto`, `babacu`, `piacava`, `carnauba_cera`, `carvao`, `lenha`, `madeira_tora`, `hevea_coagulado`

## Schema

| Coluna | Tipo | Nullable | Descricao |
|--------|------|----------|-----------|
| `ano` | int | ❌ | Ano de referencia |
| `localidade` | str | ✅ | UF ou municipio |
| `localidade_cod` | int | ✅ | Codigo IBGE |
| `produto` | str | ❌ | Nome do produto |
| `valor` | float64 | ✅ | Valor (Toneladas ou Metros cubicos) |
| `unidade` | str | ❌ | Unidade de medida |
| `fonte` | str | ❌ | Origem dos dados |

## Primary Key

`[ano, produto, localidade]`

## Garantias

- Dados consolidados anuais
- Latencia tipica: Y+1 (dados disponiveis no ano seguinte)
- Serie historica desde 1986

## Exemplo

```python
from agrobr import datasets

# Producao de acai por UF
df = await datasets.extrativismo_vegetal("acai", ano=2023)

# Castanha-do-Para no Amazonas
df = await datasets.extrativismo_vegetal("castanha_para", ano=2023, uf="AM")

# Filtrar por UF
df = await datasets.extrativismo_vegetal("erva_mate", ano=2023, uf="PR")

# Com metadados
df, meta = await datasets.extrativismo_vegetal("acai", ano=2023, return_meta=True)
```

## Schema JSON

Disponivel em `agrobr/schemas/extrativismo_vegetal.json`.

```python
from agrobr.contracts import get_contract
contract = get_contract("extrativismo_vegetal")
print(contract.to_json())
```

## Niveis Territoriais

| Nivel | Descricao |
|-------|-----------|
| `brasil` | Total nacional |
| `uf` | Por Unidade Federativa (default) |
| `municipio` | Por municipio |
