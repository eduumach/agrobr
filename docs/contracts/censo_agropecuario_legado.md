# censo_agropecuario_legado v1.0

Dados do Censo Agropecuario 1995/96 — 6 temas legados obtidos via FTP (XLS).

## Fontes

| Prioridade | Fonte | Descricao |
|------------|-------|-----------|
| 1 | IBGE FTP | Censo Agropecuario 1995/96 via FTP (XLS legado) |

## Temas

`tecnologia`, `pessoal_ocupado`, `maquinas`, `producao_animal`, `valor_producao`, `financeiro`

### Categorias por tema

| Tema | Categorias |
|------|-----------|
| `tecnologia` | assistencia_tecnica, irrigacao, adubos_corretivos, controle_pragas, conservacao_solo, energia_eletrica |
| `pessoal_ocupado` | total, familiar, permanentes, temporarios, parceiros_outra |
| `maquinas` | total_tratores, menos_10cv, 10_50cv, 50_100cv, mais_100cv |
| `producao_animal` | leite_vaca, leite_cabra, la, ovos_galinha |
| `valor_producao` | total, vegetal, vegetal_subtipo, animal, animal_subtipo |
| `financeiro` | investimentos, financiamentos, despesas, receitas |

## Schema

| Coluna | Tipo | Nullable | Descricao |
|--------|------|----------|-----------|
| `ano` | int | N | Sempre 1995 |
| `localidade` | str | S | Localidade (mesorregiao, microrregiao, municipio) |
| `localidade_cod` | int | S | Codigo IBGE (indisponivel nos XLS legados) |
| `tema` | str | N | Tema do censo |
| `categoria` | str | N | Categoria dentro do tema |
| `variavel` | str | N | Nome da variavel |
| `valor` | float64 | S | Valor da variavel |
| `unidade` | str | N | Unidade de medida |
| `fonte` | str | N | Sempre 'ibge_censo_agro_legado' |

## Primary Key

`[ano, tema, categoria, variavel, localidade]`

## Garantias

- Ano sempre 1995 (Censo 1995/96)
- Valores numericos sempre >= 0
- Fonte sempre 'ibge_censo_agro_legado'
- Dados estaticos (update_frequency = never)

## Exemplo

```python
from agrobr import ibge

# Tecnologia por mesorregiao
df = await ibge.censo_agro_legado('tecnologia')

# Pessoal ocupado em Sao Paulo
df = await ibge.censo_agro_legado('pessoal_ocupado', uf='SP')

# Maquinas — nivel municipio
df = await ibge.censo_agro_legado('maquinas', nivel='municipio')

# Com metadados
df, meta = await ibge.censo_agro_legado('tecnologia', return_meta=True)
```

## Niveis Territoriais

| Nivel | Descricao |
|-------|-----------|
| `brasil` | Total (Totais no XLS) |
| `uf` | Mesorregioes (default) |
| `municipio` | Municipios |
