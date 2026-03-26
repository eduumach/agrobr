# Docker

Rode o agrobr sem instalar Python localmente.

## Requisitos

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) ou Docker Engine (Linux)

## Build

```bash
docker build -t agrobr .
```

## Uso interativo

```bash
docker run -it --rm agrobr
```

Abre um Python REPL com o agrobr instalado:

```python
>>> from agrobr.sync import cepea
>>> df = cepea.indicador('soja', inicio='2024-01-01')
>>> print(df.head())
```

## CLI

```bash
docker run --rm agrobr agrobr --version
docker run --rm agrobr agrobr cepea indicador boi
docker run --rm agrobr agrobr conab safras soja
```

## Persistir cache

Sem volume mount, o cache DuckDB é perdido quando o container encerra.

```bash
docker run -it --rm -v agrobr-cache:/home/agrobr/.agrobr agrobr
```

O named volume `agrobr-cache` persiste entre execuções.

## Rodar scripts locais

```bash
docker run --rm -v "$(pwd)":/work agrobr python /work/meu_script.py
```

## Extras

Build com extras opcionais via `--build-arg`:

```bash
docker build --build-arg EXTRAS=polars,pdf -t agrobr:extras .
```

### Compatibilidade

| Extra | Docker | Notas |
|---|---|---|
| `pdf` | sim | pdfplumber, puro Python |
| `polars` | sim | Wheels manylinux pre-built |
| `bigquery` | sim | Google Cloud client |
| `browser` | **nao** | Playwright precisa Chromium + system libs nao presentes na imagem |
| `geo` | **incerto** | geopandas/pyogrio pode funcionar (GDAL bundled no wheel). Nao verificado |
| `app` | sim | Streamlit funciona, mas adiciona ~200MB e requer `-p 8501:8501` |
| `dev` | nao usar | Ferramentas de dev (pytest, ruff, mypy) |
| `docs` | nao usar | mkdocs |
| `all` | **nunca** | Inclui dev + docs + browser. Quebra |

## Python version

A imagem default usa Python 3.11. Para outras versoes:

```bash
docker build --build-arg PYTHON_VERSION=3.12 -t agrobr:py312 .
```

Versoes suportadas: 3.11, 3.12, 3.13.

## Variáveis de ambiente

Todas as configuracoes sao customizaveis via env vars:

```bash
docker run -it --rm \
  -e AGROBR_CACHE_CACHE_DIR=/data/cache \
  -e AGROBR_HTTP_TIMEOUT_READ=60 \
  -e AGROBR_HTTP_MAX_RETRIES=5 \
  -v agrobr-data:/data \
  agrobr
```

| Prefixo | Configuracao |
|---|---|
| `AGROBR_CACHE_` | Diretorio de cache, nome do banco DuckDB |
| `AGROBR_HTTP_` | Timeouts, retries, rate limits por fonte |
| `AGROBR_ALERT_` | Webhooks Slack/Discord, SendGrid |

## Limitações

- **`agrobr health` / `agrobr doctor`** retornam `ImportError` no container. Esses modulos sao privados e excluidos do wheel. Mesmo comportamento de `pip install agrobr` do PyPI.
- **Cache efemero** sem volume mount. Use `-v agrobr-cache:/home/agrobr/.agrobr`.
- **Imagem ~400-500MB** (pandas ~100MB + duckdb ~80MB + demais deps core).
- **`agrobr/data/censo_1985/`** — 11MB de CSVs estaticos incluidos na imagem (dados runtime do `ibge.censo_municipal_1985()`).
