# RNC/CultivarWeb — Registro Nacional de Cultivares

> **Licenca:** Dados publicos governo federal (Lei 12.527/2011).
> Classificacao: `livre`

Dados de cultivares registradas e protegidas no Brasil via sistema CultivarWeb
do Ministerio da Agricultura, Pecuaria e Abastecimento (MAPA).

## Visao Geral

| Campo | Valor |
|-------|-------|
| **Operador** | MAPA — Ministerio da Agricultura |
| **Website** | [sistemas.agricultura.gov.br/snpc/cultivarweb](https://sistemas.agricultura.gov.br/snpc/cultivarweb) |
| **Licenca** | `livre` — Dados publicos governo federal |
| **Formato** | CSV (virgula, UTF-8) |
| **Atualizacao** | Continua |
| **Cobertura** | ~37K cultivares registradas, ~5K cultivares protegidas |

## Dados Disponiveis

### Cultivares Registradas

Cultivares com registro ativo ou encerrado no RNC/MAPA.

**Colunas:** `cultivar`, `nome_comum`, `nome_cientifico`, `grupo`, `situacao`,
`nr_formulario`, `nr_registro`, `data_registro`, `data_validade`, `mantenedor`

### Cultivares Protegidas

Cultivares com protecao de propriedade intelectual (SNPC).

**Colunas:** `cultivar`, `nome_cientifico`, `nome_comum`, `nr_processo`, `situacao`,
`nr_certificado`, `inicio_protecao`, `termino_protecao`, `titular`,
`representante_legal`, `melhoristas`

## API

```python
import asyncio
from agrobr import rnc

async def main():
    # Todas as cultivares registradas
    df = await rnc.registradas()

    # Filtrar por especie
    df = await rnc.registradas(especie="soja")

    # Filtrar por mantenedor
    df = await rnc.registradas(mantenedor="Embrapa")

    # Cultivares protegidas
    df = await rnc.protegidas()

    # Filtrar por titular
    df = await rnc.protegidas(titular="Embrapa")

    # Com metadados
    df, meta = await rnc.registradas(return_meta=True)

    # Polars
    df = await rnc.registradas(as_polars=True)

asyncio.run(main())
```

## Notas Tecnicas

- Acesso via 2 POSTs com sessao HTTP (pesquisa vazia + export CSV)
- User-Agent obrigatorio (servidor rejeita requests sem header)
- Datas no formato DD/MM/YYYY (parser converte para datetime)
- Filtros aplicados pos-download via `str.contains()` case-insensitive
- Cache local em CSV com TTL de 24h

## Fonte

- URL: `https://sistemas.agricultura.gov.br/snpc/cultivarweb`
- Formato: CSV (`,`)
- Atualizacao: continua
- Licenca: `livre` — Dados publicos governo federal (Lei 12.527/2011)
