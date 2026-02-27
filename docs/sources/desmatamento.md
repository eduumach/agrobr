# Desmatamento (PRODES/DETER)

## Visao Geral

| Campo | Valor |
|-------|-------|
| **Provedor** | INPE — Instituto Nacional de Pesquisas Espaciais |
| **Programas** | PRODES (anual) e DETER (alertas diarios) |
| **Acesso** | API WFS publica (TerraBrasilis GeoServer) |
| **Formato** | CSV via WFS outputFormat + GeoJSON para geometria |
| **Autenticacao** | Nenhuma |
| **Licenca** | Dados publicos governo federal |
| **Serie Historica** | PRODES: 2000+, DETER: 2016+ (Amazonia), 2020+ (Cerrado) |

## Origem dos Dados

O INPE opera dois sistemas complementares de monitoramento do desmatamento:

- **PRODES**: Mapeamento anual consolidado do desmatamento por corte raso. Usa imagens Landsat (30m) para gerar poligonos de desmatamento com area minima de 6.25 hectares. Resultado oficial usado pelo governo federal.

- **DETER**: Sistema de alertas diarios para acoes de fiscalizacao. Usa imagens de sensores como CBERS-4, AMAZONIA-1 e Landsat com resolucao variavel. Detecta desmatamento, degradacao, mineracao e cicatrizes de queimada.

## Acesso via TerraBrasilis

Os dados sao acessados via GeoServer WFS do TerraBrasilis com `outputFormat=csv` e filtros via `CQL_FILTER`.

### PRODES — Workspaces por Bioma

| Bioma | Workspace | Layer |
|-------|-----------|-------|
| Cerrado | prodes-cerrado-nb | yearly_deforestation |
| Caatinga | prodes-caatinga-nb | yearly_deforestation |
| Mata Atlantica | prodes-mata-atlantica-nb | yearly_deforestation |
| Pantanal | prodes-pantanal-nb | yearly_deforestation |
| Pampa | prodes-pampa-nb | yearly_deforestation |

### DETER — Workspaces por Bioma

| Bioma | Workspace | Layer |
|-------|-----------|-------|
| Amazonia | deter-amz | deter_amz |
| Cerrado | deter-cerrado-nb | deter_cerrado |

## Geometria (deter_geo)

A funcao `deter_geo()` retorna alertas DETER com poligonos de geometria como GeoDataFrame.

| Campo | Valor |
|-------|-------|
| **Coluna de geometria (AMZ)** | `geom` |
| **Coluna de geometria (Cerrado)** | `st_multi` |
| **Formato** | MultiPolygon EPSG:4326 |
| **Volume por feature** | ~1.1 KB com geometria |
| **maxFeatures default** | 10.000 (tabular: 50.000) |
| **outputFormat** | `application/json` (GeoJSON) |

A coluna de geometria e bioma-especifica no GeoServer. O parser normaliza ambas para `geometry` no GeoDataFrame de saida.

## Exemplo de Uso

```python
import agrobr

# PRODES — desmatamento anual consolidado
df_prodes = await agrobr.desmatamento.prodes(
    bioma="Cerrado",
    ano=2022,
    uf="MT",
)

# DETER — alertas em tempo real
df_deter = await agrobr.desmatamento.deter(
    bioma="Amazônia",
    uf="PA",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
)

# Com metadados
df, meta = await agrobr.desmatamento.prodes(
    bioma="Cerrado", ano=2022, return_meta=True
)
print(meta.records_count, meta.fetch_duration_ms)

# DETER com geometria (requer pip install agrobr[geo])
gdf = await agrobr.desmatamento.deter_geo(
    bioma="Amazônia",
    uf="PA",
    data_inicio="2024-01-01",
    data_fim="2024-06-30",
)
```

## Limitacoes

- PRODES nao inclui bioma Amazonia neste modulo (dados PRODES Amazonia Legal tem workspace diferente com estrutura variavel)
- DETER so disponivel para Amazonia e Cerrado
- WFS limita 50.000 features por requisicao — filtrar por estado e/ou ano
- Dados PRODES sao poligonos individuais (granularidade fina) — usar agregacao se necessario
- DETER e sistema de alerta, nao de consolidacao — pode haver sobreposicao
- `deter_geo()` retorna geometria (~10x mais volume que tabular) — usar filtros para reduzir dados

## Cache e Atualizacao

- **PRODES**: TTL 24h (dados consolidados anuais, atualizados ~1x/ano)
- **DETER**: TTL 24h (alertas diarios, atualizados frequentemente)
- Recomendado: usar filtros de estado e ano para reduzir volume de dados

## Links

- [TerraBrasilis](https://terrabrasilis.dpi.inpe.br)
- [PRODES](https://www.obt.inpe.br/OBT/assuntos/programas/amazonia/prodes)
- [DETER](https://www.obt.inpe.br/OBT/assuntos/programas/amazonia/deter)
