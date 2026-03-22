# Lista Suja — Cadastro de Empregadores (Trabalho Escravo)

## Visao Geral

| Item | Detalhe |
|------|---------|
| Provedor | Ministerio do Trabalho / Portal da Transparencia |
| Dados | Empregadores flagrados com trabalho escravo |
| Acesso | Download XLSX |
| Formato | Excel (.xlsx) |
| Autenticacao | Nenhuma |
| Licenca | Livre (Lei de Acesso a Informacao) |

## Exemplo de Uso

```python
import asyncio
from agrobr import lista_suja

async def main():
    # Todos os empregadores
    df = await lista_suja.empregadores()

    # Filtrar por UF
    df = await lista_suja.empregadores(uf="PA")

    # Com metadados
    df, meta = await lista_suja.empregadores(return_meta=True)

    # Polars
    df = await lista_suja.empregadores(as_polars=True)

asyncio.run(main())
```

## Colunas

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| empregador | str | Nome do empregador |
| cpf_cnpj | str | CPF ou CNPJ |
| estabelecimento | str | Nome do estabelecimento |
| uf | str | UF |
| municipio | str | Municipio |
| cnae | str | Codigo CNAE |
| data_inclusao | datetime | Data de inclusao na lista |
| trabalhadores_resgatados | int | Numero de trabalhadores resgatados |

## Particularidades

- **PII warning**: emite aviso automatico na primeira chamada (CPF/CNPJ publicos por Lei de Acesso a Informacao)
- **Arquivo unico**: download completo sem paginacao

## Limitacoes

- Contem dados pessoais (CPF/CNPJ) — publicos por lei
- Arquivo unico sem paginacao
