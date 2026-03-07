# futuros_agricolas

Futuros agrícolas B3 — ajustes diários, histórico e posições abertas.

## Fonte

| Prioridade | Fonte | Descrição |
|------------|-------|-----------|
| 1 | B3 | Bolsa de Valores do Brasil |

## Modos (`tipo=`)

### Ajustes (default)

```python
df = await datasets.futuros_agricolas("boi", data="2025-03-05")
```

### Histórico

```python
df = await datasets.futuros_agricolas("boi", tipo="historico", inicio="2025-01-01", fim="2025-03-05")
```

### Posições abertas

```python
df = await datasets.futuros_agricolas("boi", tipo="posicoes", data="2025-03-05")
```

## Produtos

`boi`, `milho`, `cafe_arabica`, `cafe_conillon`, `etanol`, `soja_cross`, `soja_fob`

> `soja_fob` não possui dados de posições abertas (SOY ausente de `TICKERS_AGRO_OI`).

## Contratos

### `tipo="ajustes"` / `tipo="historico"` → `AJUSTE_DIARIO_V1`

PK: `[data, ticker, vencimento_codigo]`

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `data` | DATE | N |
| `ticker` | STRING | N |
| `descricao` | STRING | Y |
| `vencimento_codigo` | STRING | N |
| `vencimento_mes` | INTEGER | N |
| `vencimento_ano` | INTEGER | N |
| `ajuste_anterior` | FLOAT | Y |
| `ajuste_atual` | FLOAT | Y |
| `variacao` | FLOAT | Y |
| `ajuste_por_contrato` | FLOAT | Y |
| `unidade` | STRING | Y |

### `tipo="posicoes"` → `POSICOES_ABERTAS_V1`

PK: `[data, ticker_completo]`

| Coluna | Tipo | Nullable |
|--------|------|----------|
| `data` | DATE | N |
| `ticker` | STRING | N |
| `descricao` | STRING | Y |
| `ticker_completo` | STRING | N |
| `vencimento_codigo` | STRING | N |
| `vencimento_mes` | INTEGER | N |
| `vencimento_ano` | INTEGER | N |
| `tipo` | STRING | N |
| `posicoes_abertas` | INTEGER | N |
| `variacao_posicoes` | INTEGER | Y |
| `unidade` | STRING | Y |

## Licença

`zona_cinza` — B3 é empresa privada. Dados públicos sem termos claros para acesso programático.
