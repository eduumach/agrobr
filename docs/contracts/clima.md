# clima

Dados climáticos mensais por UF ou diários por estação.

## Fontes

| Prioridade | Fonte | Descrição |
|------------|-------|-----------|
| 1 | INMET | Estações automáticas agregadas por UF |
| 2 | NASA POWER | Reanálise satelital por UF (fallback) |

## Modos

### Modo UF (multi-source, fallback automático)

```python
df = await datasets.clima(uf="SP", ano=2024)
```

### Modo Estação (INMET only)

```python
df = await datasets.clima(estacao="A301", inicio="2024-01-01", fim="2024-12-31")
```

## Contrato `CLIMA_V1` (modo UF)

PK: `[mes, uf]`

| Coluna | Tipo | Nullable | INMET | NASA | Unidade |
|--------|------|----------|-------|------|---------|
| `mes` | DATE | N | ✅ | ✅ | — |
| `uf` | STRING | N | ✅ | ✅ | — |
| `precip_acum_mm` | FLOAT | N | ✅ | ✅ | mm |
| `temp_media` | FLOAT | N | ✅ | ✅ | °C |
| `temp_max_media` | FLOAT | N | ✅ | ✅ | °C |
| `temp_min_media` | FLOAT | N | ✅ | ✅ | °C |
| `num_estacoes` | INTEGER | Y | ✅ | — | — |
| `umidade_media` | FLOAT | Y | — | ✅ | % |
| `radiacao_media_mj` | FLOAT | Y | — | ✅ | MJ/m² |
| `vento_medio_ms` | FLOAT | Y | — | ✅ | m/s |
| `fonte` | STRING | N | ✅ | ✅ | — |

## Contrato `CLIMA_ESTACAO_V1` (modo estação)

PK: `[data, estacao]`

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `data` | DATE | N |
| `estacao` | STRING | N |
| `uf` | STRING | Y |
| `temp_media` | FLOAT | Y |
| `temp_max` | FLOAT | Y |
| `temp_min` | FLOAT | Y |
| `precipitacao_mm` | FLOAT | Y |
| `umidade_media` | FLOAT | Y |
| `radiacao_total_kj_m2` | FLOAT | Y |

Validação apenas para `agregacao="diario"`.

## Licença

`livre` — ambas as fontes são públicas e gratuitas.
