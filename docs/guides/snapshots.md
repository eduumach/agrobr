# Snapshots e Modo Determinístico

Snapshots capturam dados locais em arquivos parquet, permitindo reprodutibilidade total em papers, auditorias e pipelines CI. Nenhum request HTTP é feito durante consultas em modo determinístico.

## Criando um Snapshot

### Programático

```python
from agrobr.snapshots import create_snapshot

# Nome automático (data atual)
info = await create_snapshot()

# Nome customizado + fontes específicas
info = await create_snapshot("2025-Q4", sources=["cepea", "conab", "ibge"])
print(info.name, info.path, info.file_count)
```

### CLI

```bash
# Nome automático
agrobr snapshot create

# Nome customizado com fontes
agrobr snapshot create 2025-Q4 --sources cepea,conab,ibge
```

Os snapshots são salvos em `~/.agrobr/snapshots/<nome>/` com um `manifest.json` e arquivos parquet por fonte/dataset.

## Listando Snapshots

```python
from agrobr.snapshots import list_snapshots

for s in list_snapshots():
    print(f"{s.name} — {s.file_count} arquivos, {s.size_bytes/1024/1024:.1f} MB")
    print(f"  Fontes: {', '.join(s.sources)}")
    print(f"  Criado em: {s.created_at}")
```

```bash
agrobr snapshot list
agrobr snapshot list --json    # saída estruturada
```

## Usando um Snapshot (Modo Determinístico)

### Context Manager (recomendado)

```python
from agrobr import datasets

async with datasets.deterministic("2025-12-31"):
    # Todas as consultas filtram data <= snapshot
    # Usa apenas cache local — sem rede
    df = await datasets.preco_diario("soja")
    df2 = await datasets.producao_anual("milho", ano=2023)
```

O context manager usa `contextvars`, sendo thread-safe e async-safe.

### Decorator

```python
from agrobr import datasets
from agrobr.datasets.deterministic import deterministic_decorator

@deterministic_decorator("2025-12-31")
async def meu_pipeline():
    df = await datasets.preco_diario("soja")
    return df
```

!!! note "Context manager vs CLI"
    O context manager `deterministic()` e o decorator recebem uma **data ISO** (ex: `"2025-12-31"`) e filtram consultas por data.
    O CLI `snapshot use` recebe o **nome do snapshot** e ativa o modo determinístico via configuração global.

### CLI

```bash
agrobr snapshot use 2025-12-31
# Ativa modo determinístico para a sessão
# Voltar ao normal: agrobr config mode normal
```

### Configuração global

```python
from agrobr.config import set_mode

set_mode("deterministic", snapshot="2025-12-31")

# Voltar ao normal
set_mode("normal")
```

## Carregando Dados de um Snapshot

```python
from agrobr.snapshots import load_from_snapshot

df = load_from_snapshot("cepea", "indicador", snapshot_name="2025-Q4")
```

## Removendo Snapshots

```python
from agrobr.snapshots import delete_snapshot

delete_snapshot("2025-Q4")
```

```bash
agrobr snapshot delete 2025-Q4
agrobr snapshot delete 2025-Q4 --force   # sem confirmação
```

## Estrutura no Disco

```
~/.agrobr/snapshots/
  2025-Q4/
    manifest.json          # metadados (nome, data, fontes, versão agrobr)
    cepea/
      indicador.parquet
    conab/
      safras.parquet
      balanco.parquet
    ibge/
      pam.parquet
```

## Boas Práticas

- Crie snapshots após coleta completa dos dados necessários
- Use nomes descritivos (ex: `2025-Q4`, `paper-submission-v2`)
- Em CI, crie o snapshot uma vez e reutilize em todos os jobs
- Combine `deterministic()` com testes para garantir reprodutibilidade
