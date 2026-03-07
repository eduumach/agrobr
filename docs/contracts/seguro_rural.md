# seguro_rural v1.0

Seguro rural — apólices e sinistros do PSR (MAPA).

## Fontes

| Prioridade | Fonte | Descrição |
|------------|-------|-----------|
| 1 | MAPA PSR | Programa de Subvenção ao Prêmio do Seguro Rural |

## Produtos

100+ culturas dinâmicas do PSR (validação delegada à source).

## Tipo de dados

O dataset suporta dois tipos de consulta via parâmetro `tipo`:

- `tipo="apolices"` (default) — todas as apólices com subvenção federal
- `tipo="sinistros"` — sinistros comunicados

Cada tipo tem seu próprio contrato (`mapa_psr_apolices` e `mapa_psr_sinistros`).

## Schema — Apólices

| Coluna | Tipo | Nullable | Unidade | Estável |
|--------|------|----------|---------|---------|
| `nr_apolice` | str | ❌ | - | Sim |
| `ano_apolice` | int | ❌ | - | Sim |
| `uf` | str | ❌ | - | Sim |
| `municipio` | str | ✅ | - | Sim |
| `cd_ibge` | str | ✅ | - | Sim |
| `cultura` | str | ❌ | - | Sim |
| `classificacao` | str | ✅ | - | Sim |
| `area_total` | float | ✅ | ha | Sim |
| `valor_premio` | float | ✅ | BRL | Sim |
| `valor_subvencao` | float | ✅ | BRL | Sim |
| `valor_limite_garantia` | float | ✅ | BRL | Sim |
| `valor_indenizacao` | float | ✅ | BRL | Sim |
| `evento` | str | ✅ | - | Sim |
| `produtividade_estimada` | float | ✅ | - | Sim |
| `produtividade_segurada` | float | ✅ | - | Sim |
| `nivel_cobertura` | float | ✅ | - | Sim |
| `taxa` | float | ✅ | - | Sim |
| `seguradora` | str | ✅ | - | Sim |

## Schema — Sinistros

| Coluna | Tipo | Nullable | Unidade | Estável |
|--------|------|----------|---------|---------|
| `nr_apolice` | str | ❌ | - | Sim |
| `ano_apolice` | int | ❌ | - | Sim |
| `uf` | str | ❌ | - | Sim |
| `municipio` | str | ✅ | - | Sim |
| `cd_ibge` | str | ✅ | - | Sim |
| `cultura` | str | ❌ | - | Sim |
| `classificacao` | str | ✅ | - | Sim |
| `evento` | str | ❌ | - | Sim |
| `area_total` | float | ✅ | ha | Sim |
| `valor_indenizacao` | float | ❌ | BRL | Sim |
| `valor_premio` | float | ✅ | BRL | Sim |
| `valor_subvencao` | float | ✅ | BRL | Sim |
| `valor_limite_garantia` | float | ✅ | BRL | Sim |
| `produtividade_estimada` | float | ✅ | - | Sim |
| `produtividade_segurada` | float | ✅ | - | Sim |
| `nivel_cobertura` | float | ✅ | - | Sim |
| `seguradora` | str | ✅ | - | Sim |

## Garantias

- `uf` é código UF válido
- Valores monetários em BRL
- Dados desde 2006 (início do PSR)
- Sinistros: `valor_indenizacao` sempre > 0, `evento` sempre preenchido
- Apólices: `valor_indenizacao` pode ser null/0

## Exemplo

```python
from agrobr import datasets

# Apólices (default)
df = await datasets.seguro_rural()
df = await datasets.seguro_rural("soja", uf="MT", ano=2023)

# Sinistros
df = await datasets.seguro_rural(tipo="sinistros")
df = await datasets.seguro_rural(tipo="sinistros", evento="SECA")

# Com metadados
df, meta = await datasets.seguro_rural(return_meta=True)

# Sync
from agrobr.sync import datasets
df = datasets.seguro_rural()
```

## Schema JSON

```python
from agrobr.contracts import get_contract
# Apólices
contract = get_contract("mapa_psr_apolices")
# Sinistros
contract = get_contract("mapa_psr_sinistros")
```
