# Fontes de Dados

O agrobr integra dados de 35 fontes de dados agricolas.
Todas as fontes suportam `return_meta=True` para rastreabilidade completa.

## Visao Geral

| Fonte | Tipo | Atualizacao | Cobertura |
|-------|------|-------------|-----------|
| [CEPEA/ESALQ](cepea.md) | Precos | Diaria | Commodities agricolas |
| [CONAB](conab.md) | Safras, custos, serie historica | Mensal | Producao nacional |
| [IBGE/SIDRA](ibge.md) | Estatisticas | Anual/Mensal/Trimestral | Dados oficiais (PAM, LSPA, PPM, Abate, PEVS, Leite, PIB, Censo) |
| [NASA POWER](nasa_power.md) | Climatologia | Diaria | Global, grid 0.5 grau |
| [BCB/SICOR](bcb.md) | Credito rural | Mensal | Cultura/UF (+ BigQuery) |
| [ComexStat](comexstat.md) | Exportacoes | Semanal | NCM/UF |
| [ANDA](anda.md) | Fertilizantes | Mensal | UF/mes |
| [ABIOVE](abiove.md) | Exportacao complexo soja | Mensal | Volume/receita |
| [USDA PSD](usda.md) | Oferta/demanda internacional | Mensal | Commodities globais |
| [IMEA](imea.md) | Cotacoes e indicadores MT | Diaria | Mato Grosso |
| [DERAL](deral.md) | Condicao lavouras PR | Semanal | Parana |
| [INMET](inmet.md) | Meteorologia | Diaria | 600+ estacoes (API fora do ar) |
| [Notícias Agrícolas](noticias_agricolas.md) | Cotações (fallback CEPEA) | Diária | Commodities |
| [Queimadas/INPE](queimadas.md) | Focos de calor | Diária | 6 biomas, 13 satélites |
| [Desmatamento PRODES/DETER](desmatamento.md) | Desmatamento + alertas | Anual/Diária | Amazônia, Cerrado, Pantanal |
| [MapBiomas](mapbiomas.md) | Cobertura e uso da terra | Anual | Municípios (1985-presente) |
| [CONAB Progresso](conab_progresso.md) | Plantio/colheita semanal | Semanal | 6 culturas, 27 UFs |
| [B3 Futuros Agro](b3.md) | Ajustes diarios + posicoes em aberto | Diaria | 7 contratos agricolas |
| [CONAB CEASA](conab_ceasa.md) | Precos atacado hortifruti | Diaria | 48 produtos, 43 CEASAs |
| [UN Comtrade](comtrade.md) | Comercio bilateral + trade mirror | Mensal/Anual | ~200 paises, HS codes |
| [ANTAQ](antaq.md) | Movimentacao portuaria de carga | Anual | Portos brasileiros, 2010+ |
| [ANP Diesel](anp_diesel.md) | Precos revenda + volumes diesel | Semanal/Mensal | UFs, municipios, 2013+ |
| [ANTT Pedagio](antt_pedagio.md) | Fluxo de veiculos em pracas de pedagio | Mensal | 200+ pracas, 2010+ |
| [MAPA PSR](mapa_psr.md) | Apolices e sinistros seguro rural | Anual | 27 UFs, 2006+ |
| [SICAR](sicar.md) | Cadastro Ambiental Rural | Continua | 27 UFs, 7.4M+ imoveis |
| [ZARC](zarc.md) | Zoneamento Agricola de Risco Climatico | Semanal | 40+ culturas, todos municipios |
| [Agrofit/MAPA](defensivos.md) | Agrotoxicos registrados | Continua | ~8K formulados, ~267K autorizacoes |
| [FUNAI Terras Indigenas](funai.md) | Terras indigenas (WFS geo) | Continua | ~740 TIs, todas UFs |
| [ICMBio UCs Federais](icmbio.md) | Unidades de conservacao federais (WFS geo) | Continua | 344 UCs federais |
| [INCRA Quilombolas](incra.md) | Territorios quilombolas (WFS geo) | Continua | ~426 territorios |
| [IBAMA Embargos](ibama.md) | Embargos ambientais (WFS geo) | Continua | ~89K embargos, paginado |
| [MapBiomas Alerta](mapbiomas_alerta.md) | Alertas de desmatamento (GraphQL) | Semanal | Nacional |
| [Lista Suja](lista_suja.md) | Cadastro de trabalho escravo (XLSX) | Semestral | Nacional |
| [ANA/SNIRH](ana.md) | Hidrografia, irrigacao, disponibilidade hidrica (ArcGIS REST) | Variavel | Nacional |
| [SFB](sfb.md) | Florestas publicas, concessoes, IFN (ArcGIS REST) | Anual | Nacional |

## Proveniencia e Rastreabilidade

Toda informacao retornada pelo agrobr pode ser rastreada ate sua origem.
Use o parametro `return_meta=True` para obter metadados completos de proveniencia.

```python
import asyncio
from agrobr import cepea

async def main():
    # Uso basico (sem mudanca)
    df = await cepea.indicador('soja')

    # Com metadados de proveniencia
    df, meta = await cepea.indicador('soja', return_meta=True)

    print(f"Fonte: {meta.source}")
    print(f"URL: {meta.source_url}")
    print(f"Coletado em: {meta.fetched_at}")
    print(f"Do cache: {meta.from_cache}")
    print(f"Registros: {meta.records_count}")

asyncio.run(main())
```

## Estrutura do MetaInfo

O objeto `MetaInfo` contem as seguintes informacoes:

| Campo | Tipo | Descricao |
|-------|------|-----------|
| `source` | str | Nome da fonte (cepea, conab, ibge) |
| `source_url` | str | URL exata acessada |
| `source_method` | str | Metodo de acesso (httpx, cache) |
| `fetched_at` | datetime | Momento da coleta |
| `from_cache` | bool | Se veio do cache local |
| `cache_key` | str | Chave no cache |
| `cache_expires_at` | datetime | Quando o cache expira |
| `records_count` | int | Quantidade de registros |
| `columns` | list | Colunas retornadas |
| `fetch_duration_ms` | int | Tempo de fetch em ms |
| `parse_duration_ms` | int | Tempo de parsing em ms |
| `agrobr_version` | str | Versao do agrobr |
| `parser_version` | int | Versao do parser usado |

## Verificacao de Integridade

O MetaInfo permite verificar integridade dos dados:

```python
# Verifica se DataFrame nao foi alterado
is_valid = meta.verify_hash(df)

# Exporta metadados para auditoria
meta_json = meta.to_json()
meta_dict = meta.to_dict()
```

## Diagnostico

Use o comando `doctor` para verificar saude do sistema:

```bash
agrobr doctor
```

Retorna:
- Status de conectividade das fontes
- Estatisticas do cache
- Ultimas coletas
- Configuracao atual
