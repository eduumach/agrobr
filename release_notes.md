# agrobr 0.11.3 — Censo Agro Expansion

## Highlights

- **Censo Agropecuario expandido: 4 → 10 temas** — 6 novos temas de manejo de solo e irrigacao
- **Multi-ano: 2006 + 2017** — novo parametro `ano` em `censo_agro()` para filtrar por ano censal
- **86 testes** (era 52) — cobertura completa dos novos temas e combinacoes multi-ano
- **Retrocompativel** — temas existentes continuam funcionando sem `ano`

## Breaking Changes

Nenhum. API publica mantida.

## Upgrade

```bash
pip install --upgrade agrobr
```

## Added

- **6 novos temas do Censo Agropecuario** (#15):
  - `preparo_solo` — Preparo do solo (tabelas SIDRA 6855/791)
  - `adubacao` — Adubacao (tabelas SIDRA 6848/1249)
  - `calagem` — Calagem (tabelas SIDRA 6849/1245)
  - `agrotoxicos` — Uso de agrotoxicos (tabelas SIDRA 6851/1459)
  - `praticas_agricolas` — Praticas agricolas (tabelas SIDRA 8561/837)
  - `irrigacao` — Irrigacao (tabelas SIDRA 6857/855)

- **Suporte multi-ano (2006 + 2017)**:
  - `censo_agro('preparo_solo', ano=2017)` — apenas 2017
  - `censo_agro('irrigacao', ano=2006)` — apenas 2006
  - `censo_agro('adubacao')` — ambos os anos concatenados

- **Tratamento especial `preparo_solo` 2017** — variaveis SIDRA funcionam como categorias (`_VAR_AS_CATEGORIA`)

- **Helper `_fetch_censo_single()`** extraido para loop multi-ano

## Exemplo

```python
from agrobr import ibge

# Novos temas de manejo de solo
df = await ibge.censo_agro('preparo_solo', ano=2017, uf='SP')
df = await ibge.censo_agro('irrigacao')  # ambos os anos
df = await ibge.censo_agro('adubacao', ano=2006)

# Listar todos os 10 temas
temas = await ibge.temas_censo_agro()
# ['efetivo_rebanho', 'uso_terra', 'lavoura_temporaria', 'lavoura_permanente',
#  'preparo_solo', 'adubacao', 'calagem', 'agrotoxicos', 'praticas_agricolas', 'irrigacao']
```

## Links

- [Documentacao](https://www.agrobr.dev/docs/)
- [PyPI](https://pypi.org/project/agrobr/)
- [Changelog completo](https://github.com/bruno-portfolio/agrobr/blob/main/CHANGELOG.md)
- [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/bruno-portfolio/agrobr/blob/main/examples/agrobr_demo.ipynb)
