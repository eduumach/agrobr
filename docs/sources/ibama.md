# IBAMA — Embargos Ambientais

## Visao Geral

| Item | Detalhe |
|------|---------|
| Provedor | IBAMA (Instituto Brasileiro do Meio Ambiente e dos Recursos Naturais Renovaveis) |
| Dados | Termos de embargo por infracoes ambientais (SIFISC) |
| Acesso | Download do dump CSV (dadosabertos.ibama.gov.br) |
| Formato | CSV zipado (~47 MB, ~170 MB descomprimido) com geometrias WKT |
| Autenticacao | Nenhuma |
| Licenca | ODbL (Open Database License) |
| Registros | ~114K termos de embargo, atualizacao mensal |

> O GeoServer WFS do siscom.ibama.gov.br foi desativado pela fonte em 2026.
> O acesso migrou para o dump oficial do SIFISC na plataforma de dados abertos.

## Acesso

| Parametro | Valor |
|-----------|-------|
| URL | `dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/termo_embargo/termo_embargo_csv.zip` |
| Atualizacao | Mensal (Last-Modified no servidor) |
| Filtros | `uf` e `bbox` aplicados client-side apos o download |

## Exemplo de Uso

```python
import asyncio
from agrobr import ibama

async def main():
    # Todos os embargos do Brasil
    df = await ibama.embargos()

    # Filtrar por UF
    df = await ibama.embargos(uf="MT")

    # Com geometria WKT (requer geopandas — extra [geo])
    gdf = await ibama.embargos_geo(uf="RR")
    gdf = await ibama.embargos_geo(bbox=(-56, -16, -54, -14))

    # Com metadados
    df, meta = await ibama.embargos(return_meta=True)

    # Polars
    df = await ibama.embargos(as_polars=True)

asyncio.run(main())
```

## Colunas

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| seq_tad | str | Identificador do termo no SIFISC (vazio em registros do sistema AIE Mob) |
| numero_tad | str | Numero do Termo de Embargo |
| data_embargo | datetime | Data do embargo |
| num_processo | str | Numero do processo administrativo |
| descricao | str | Descricao do embargo/infracao |
| codigo_municipio | str | Codigo IBGE do municipio |
| municipio | str | Municipio |
| uf | str | UF (sigla) |
| latitude / longitude | float | Coordenadas do termo |
| area_embargada_ha | float | Area embargada em hectares |
| nome_imovel | str | Nome do imovel |
| status | str | Status do formulario (Lavrado, Cancelado, ...) |
| cancelado | bool | Termo cancelado |
| data_desembargo | datetime | Data do desembargo (NaT se vigente) |

`embargos_geo` adiciona `geometry` (Polygon/MultiPolygon, EPSG:4326) parseada do WKT
do proprio dump — somente registros com poligono.

## Particularidades

- **PII excluido**: o dump da fonte traz nome e CPF/CNPJ do embargado; o agrobr
  nao expoe esses campos (politica do projeto). Quem precisar deles para
  compliance pode baixar o CSV bruto da fonte.
- **Datas sujas na fonte**: alguns registros tem datas impossiveis (ex.: ano 2925);
  sao preservadas quando sintaticamente validas e viram `NaT` quando nao parseiam.
- **bbox** filtra pelo ponto (lat/lon) do termo, nao por intersecao do poligono.
- **Geo sem filtro**: `embargos_geo()` sem `uf`/`bbox` parseia WKT do Brasil
  inteiro — lento; um warning e emitido.

## Limitacoes

- Geometria presente em parte dos registros (embargos sem poligono ficam fora do geo)
- Download completo (~47 MB) a cada chamada — filtros sao client-side
- ODbL: uso livre com citacao da fonte
