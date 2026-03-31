# Acervo Fundiario — SIGEF, SNCI e Assentamentos

## Visao Geral

| Item | Detalhe |
|------|---------|
| Provedor | INCRA (Instituto Nacional de Colonizacao e Reforma Agraria) |
| Dados | Parcelas certificadas (SIGEF/SNCI) + assentamentos |
| Acesso | WFS OGC (MapServer i3geo) |
| Formato | GML2 (tabular e geo) |
| Autenticacao | Nenhuma |
| Licenca | Vedado uso comercial — `nc` |
| Cobertura | 27 UFs (layer por UF) |

## Acesso via WFS

| Parametro | Valor |
|-----------|-------|
| Endpoint | `acervofundiario.incra.gov.br/i3geo/ogc.php` |
| WFS Version | 1.0.0 |
| CRS | EPSG:4326 |

Cada UF e uma layer separada no servidor. O parametro `uf` e obrigatorio.

### Layers

| Tipo | Layer Pattern | Endpoint |
|------|--------------|----------|
| SIGEF particular | `certificada_sigef_particular_{uf}` | `sigef(uf, tipo="particular")` |
| SIGEF publico | `certificada_sigef_publico_{uf}` | `sigef(uf, tipo="publico")` |
| SNCI privado | `imoveiscertificados_privado_{uf}` | `snci(uf, tipo="privado")` |
| SNCI publico | `imoveiscertificados_publico_{uf}` | `snci(uf, tipo="publico")` |
| Assentamentos | `assentamentos_{uf}` | `assentamentos(uf)` |

## Exemplo de Uso

```python
import asyncio
from agrobr import acervo_fundiario

async def main():
    # Parcelas SIGEF particulares em Goias
    df = await acervo_fundiario.sigef("GO")

    # Parcelas SIGEF publicas com metadados
    df, meta = await acervo_fundiario.sigef("SP", tipo="publico", return_meta=True)

    # Certificados SNCI (pre-2013)
    df = await acervo_fundiario.snci("MT", tipo="privado")

    # Assentamentos com bbox
    df = await acervo_fundiario.assentamentos("GO", bbox=(-50, -16, -49, -15))

    # Retorno em Polars
    df_pl = await acervo_fundiario.sigef("GO", as_polars=True)

    # Com geometria (requer geopandas)
    gdf = await acervo_fundiario.sigef_geo("GO")
    gdf = await acervo_fundiario.assentamentos_geo("BA")

asyncio.run(main())
```

## Colunas — SIGEF

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| codigo_parcela | str | Codigo UUID da parcela |
| rt | str | Responsavel tecnico |
| art | str | Anotacao de responsabilidade tecnica |
| situacao | str | Situacao informada (REGISTRADA, etc) |
| codigo_imovel | str | Codigo do imovel rural |
| data_submissao | datetime | Data de submissao |
| data_aprovacao | datetime | Data de aprovacao |
| status | str | Status da certificacao (CERTIFICADA, etc) |
| nome_area | str | Nome da area/fazenda |
| registro_matricula | str | Matricula do registro |
| registro_data | str | Data do registro (nullable) |
| cod_municipio | str | Codigo IBGE do municipio |

## Colunas — SNCI

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| id | str | ID interno |
| num_processo | str | Numero do processo |
| sr | str | Superintendencia Regional |
| num_certificacao | str | Numero da certificacao |
| data_certificacao | datetime | Data da certificacao |
| area_peca_tecnica | float | Area em hectares (peca tecnica) |
| cod_profissional | str | Codigo do profissional credenciado |
| cod_imovel_rural | str | Codigo do imovel rural |
| nome_imovel | str | Nome do imovel |

## Colunas — Assentamentos

| Coluna | Tipo | Descricao |
|--------|------|-----------|
| gid | str | ID interno |
| codigo_sipra | str | Codigo SIPRA do projeto |
| nome_projeto | str | Nome do projeto de assentamento |
| municipio | str | Municipio |
| area_ha | float | Area declarada em hectares |
| capacidade | float | Capacidade de familias |
| num_familias | float | Numero de familias assentadas |
| fase | str | Fase do projeto |
| data_criacao | datetime | Data de criacao (DD/MM/YYYY) |
| forma_obtencao | str | Forma de obtencao (Desapropriacao, etc) |
| data_obtencao | datetime | Data de obtencao |
| area_calc_ha | float | Area calculada em hectares |
| sr | str | Superintendencia Regional (nullable) |
| descricao_fase | str | Descricao da fase (nullable) |

## Limitacoes

- Cada UF e uma layer separada — `uf` e obrigatorio
- Servidor so suporta GML2 (sem CSV, sem GeoJSON)
- Sem paginacao (WFS 1.0.0 MapServer) — UFs grandes podem ser lentas
- Algumas UFs podem ter layers com SRS bugado (ex: DF particular)
- Licenca `nc` — vedado uso comercial
