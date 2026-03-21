# IBAMA — Embargos Ambientais

## Visao Geral

| Item | Detalhe |
|------|---------|
| Provedor | IBAMA (Instituto Brasileiro do Meio Ambiente e dos Recursos Naturais Renovaveis) |
| Dados | Areas embargadas por infraccoes ambientais |
| Acesso | WFS OGC (GeoServer) |
| Formato | CSV (tabular) / GeoJSON (geo) |
| Autenticacao | Nenhuma |
| Licenca | ODbL (Open Database License) |
| Features | ~89K embargos (paginado, 10K/pagina) |

## Acesso via WFS

| Parametro | Valor |
|-----------|-------|
| Endpoint | `siscom.ibama.gov.br/geoserver/wfs` |
| WFS Version | 2.0.0 |
| Layer | `publica:vw_brasil_adm_embargo_a` |
| CRS | EPSG:4674 |
| Paginacao | Sim (count/startIndex) |

## Exemplo de Uso

```python
import asyncio
from agrobr import ibama

async def main():
    # Todos os embargos (paginado automaticamente)
    df = await ibama.embargos()

    # Filtrar por UF
    df = await ibama.embargos(uf="MT")

    # Com geometria (requer geopandas)
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
| numero_tad | str | Numero do Termo de Embargo |
| data_embargo | datetime | Data do embargo |
| uf | str | UF (sigla) |
| municipio | str | Municipio |
| area_desmatada_ha | float | Area desmatada em hectares |
| infracao | str | Descricao da infracao |
| legislacao | str | Base legal |
| status | str | Status do embargo |
| situacao_poligono | str | Situacao do poligono |
| respeita_embargo | str | Se o embargo e respeitado |

## Particularidades

- **PII excluido**: campos `nom_pessoa` e `cpf_cnpj_infrator` nunca sao buscados
- **Null geometry**: alguns embargos nao tem poligono associado (warning emitido)
- **Paginacao**: 89K+ features exigem paginacao automatica (~9 paginas de 10K)
- **Dedup**: registros duplicados por `numero_tad` sao removidos automaticamente

## Limitacoes

- Geometria nula em parte dos registros (embargos antigos sem poligono)
- Dados refletem o estado atual do GeoServer IBAMA (siscom)
- ODbL: uso livre com citacao da fonte
