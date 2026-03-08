# Contrato: zoneamento_agricola

Zoneamento Agrícola de Risco Climático — janelas de plantio por município/cultura/solo (ZARC/MAPA).

## Schema

| Coluna | Tipo | Nullable | Restrições |
|--------|------|----------|------------|
| `cultura` | STRING | Não | Nome normalizado pt-br |
| `safra` | STRING | Não | "YYYY/YYYY" ou "perene" |
| `geocodigo` | STRING | Não | IBGE 7 dígitos |
| `uf` | STRING | Não | Sigla 2 letras |
| `municipio` | STRING | Sim | — |
| `solo_codigo` | INTEGER | Não | Código tipo solo |
| `ciclo_codigo` | INTEGER | Não | Código ciclo cultivar |
| `clima` | STRING | Sim | — |
| `manejo` | STRING | Sim | — |
| `portaria` | STRING | Sim | — |
| `dec1`..`dec36` | INTEGER | Sim | Risco por decêndio (0-5) |

**PK:** `(cultura, safra, geocodigo, solo_codigo, ciclo_codigo)`

As 36 colunas `dec1`..`dec36` representam os 36 decêndios do ano (períodos de 10 dias). Valores de 0 (sem risco) a 5 (risco máximo).

## Exemplo

```python
from agrobr import datasets

# Zoneamento de soja em MT
df = await datasets.zoneamento_agricola(cultura="SOJA", uf="MT")

# Com filtros
df = await datasets.zoneamento_agricola(
    cultura="SOJA", uf="MT", solo=2, ciclo=1, safra="2024/2025"
)

# Sem filtros (retorna tudo disponível)
df = await datasets.zoneamento_agricola()

# Culturas disponíveis (via source API diretamente)
from agrobr import zarc
culturas = zarc.culturas()
```
