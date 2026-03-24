# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- **usda** — commodity `cafe`/`coffee` (Coffee, Green, PSD code `0711100`) adicionada a `PSD_COMMODITIES`, `_COMMODITY_NAMES` e dataset `oferta_demanda_global`
- **imea** — aliases `boi`, `boi_gordo`, `bovinos` para cadeia bovinocultura (ID 2), consistente com nomenclatura canonica da lib

### Fixed
- **cepea** — parser v1: coluna USD (`Valor US$*`) sobrescrevia valor BRL (100% dos precos no cache estavam errados). Reordenado condicionais: `var` antes de `data` (evita `Var./Dia` poluir data_value), exclusao explicita de colunas US$/USD
- **cepea** — parser v1: praca agora populada via dict `PRACAS` (20 produtos mapeados). Antes, `praca=None` hardcoded em todos os indicadores
- **cache** — `_to_row` normaliza `praca=None` para `""` (SQL UNIQUE constraint `NULL != NULL` causava duplicatas). Migration 5 limpa 338 linhas corrompidas com `praca IS NULL`
- **preco_diario** — `drop_duplicates(["data", "produto"])` em `_normalize` garante contrato PK 1 preco por (data, produto). Sem isso, dados mistos CEPEA+cache causavam `ContractViolationError`
- **conab** — parser v1 agora detecta safras year-only (`"Safra 2024"` → `2024/25`). Antes, celulas sem `/` no `if "Safra" in cell` branch eram silenciosamente ignoradas, afetando 6 culturas de inverno (trigo, aveia, canola, centeio, cevada, triticale)
- **conab** — serie historica: `_find_header_row` e `_normalize_safra_header` agora tratam float coercion do pandas (`2024.0` → `"2024"` → `"2024/25"`). Antes, `_YEAR_PATTERN` nao matchava `"2024.0"`
- **mapa_psr** — filtro `cultura` agora e accent-insensitive via `remover_acentos`. Antes, `"cafe"` nao matchava `"CAFE ARABICA"` (silent data loss com 0 registros sem aviso)

## [1.0.4] - 2026-03-22

### Added
- **normalize** — `coordenada_para_municipio(lat, lon)` geocodificação reversa offline. Lookup brute-force contra 5571 centroides IBGE (sub-ms, zero HTTP). Retorna `MunicipioInfo` ou `None` (threshold 1.5° ~167km)

### Fixed
- **funai/ibama/incra/icmbio** — funcoes `_geo()` removem `CQL_FILTER` da request WFS GeoJSON (geoservers gov.br retornam HTTP 500 ou HTML de erro ao combinar `CQL_FILTER` + `BBOX` + `outputFormat=application/json`). Filtros uf/fase/grupo/bioma agora aplicados pos-download no GeoDataFrame. Funcoes CSV nao afetadas
- **incra** — `GEOM_COLUMN` corrigido de `the_geom` para `geom`

## [1.0.3] - 2026-03-22

### Added
- **ibama** — embargos ambientais via WFS (siscom.ibama.gov.br). `embargos()` tabular + `embargos_geo()` GeoDataFrame. Paginacao WFS 2.0 (~89K features, 10K/pagina). Filtros uf/bbox. Dedup por numero_tad. PII excluido. Null geometry warning. Licenca ODbL
- **queimadas** — `focos_geo()` converte lat/lon existente para GeoDataFrame (Point, EPSG:4326). Wrapper sobre `focos()`, sem novo endpoint HTTP
- **funai** — terras indigenas via WFS (geoserver.funai.gov.br). `terras_indigenas()` tabular + `terras_indigenas_geo()` GeoDataFrame. Filtros uf/fase/bbox. ~740 TIs. Licenca CC BY-ND 3.0
- **icmbio** — unidades de conservacao federais via WFS (geoservicos.inde.gov.br). `ucs()` tabular + `ucs_geo()` GeoDataFrame. Filtros uf/grupo/bioma/bbox. 344 UCs. Dados publicos
- **incra** — territorios quilombolas via WFS (cmr.funai.gov.br). `quilombolas()` tabular + `quilombolas_geo()` GeoDataFrame. Filtros uf/fase/bbox. ~426 territorios. Dados publicos
- **mapbiomas_alerta** — alertas de desmatamento via GraphQL (plataforma.alerta.mapbiomas.org). `alertas()` tabular + `alertas_geo()` GeoDataFrame com WKT geometry + `alerta_info()` publico. Auth via token (AGROBR_MAPBIOMAS_ALERTA_TOKEN). Paginacao, filtros data/fonte/bbox. Fonte: livre (citacao)
- **lista_suja** — cadastro de empregadores (trabalho escravo) via PDF do MTE (gov.br/trabalho-e-emprego). `empregadores()` com filtro UF, warning PII automatico. Parser pdfplumber. Fonte: livre (Lei de Acesso a Informacao)
- **ana** — 4 layers ArcGIS REST do SNIRH: hidrografia (620K polylines), pivos_irrigacao (19.9K polygons), demanda_irrigacao (265K polygons), disponibilidade_hidrica (42K polylines). Paginacao automatica. Fonte: livre
- **sfb** — 3 layers ArcGIS REST do Servico Florestal: CNFP florestas publicas (20.8K polygons), concessoes florestais (8 polygons), IFN conglomerados (14.5K points). Fonte: livre

### Improved
- **utils/geo** — `check_geopandas()` extraido de desmatamento/sicar para `utils/geo.py` (dedup 2 copias). `validate_bbox()` canonica com checagem min<max (3 implementacoes inconsistentes consolidadas). `fetch_wfs()` agora aceita `base_delay` para throttle de paginacao e `client` opcional para connection reuse em paginacao
- **utils/geo** — dedup WFS: `build_wfs_url()` centraliza construcao de URL WFS com dispatch automatico v1/v2 (typeNames/count vs typeName/maxFeatures), elimina 4 copias em funai/icmbio/incra/ibama. `parse_wfs_hits()` centraliza parsing de `numberMatched` (2 copias ibama+sicar). `parse_geojson_base()` centraliza boilerplate GeoJSON (json.loads, empty check, truncation warning, null geom, from_features, required cols) — 5 parsers migrados
- **utils/geo** — infra ArcGIS REST compartilhada: `LayerConfig` TypedDict, `build_arcgis_query_url()`, `fetch_arcgis_count()`, `fetch_arcgis_layer()`, `parse_arcgis_tabular()`, `parse_arcgis_geojson()` — reusados por ANA e SFB
- **utils/validation** — `validate_uf()` com `UFS_VALIDAS` (27 UFs reais) substitui 10 copias de `_UF_RE` regex em 6 modulos WFS
- **utils/io** — `concat_csv_pages()` centraliza loop de concat paginado CSV (2 copias ibama+sicar eliminadas)
- **ibama/sicar** — paginacao WFS agora reutiliza conexao HTTP (1 TLS handshake em vez de N)

## [1.0.2] - 2026-03-20

### Improved
- **http** — log hygiene cross-cutting: URLs movidas de info/warning para debug em 25 source clients. Logs de producao mais limpos e sem vazamento de endpoints

### Security
- **b3** — token de autenticacao JWT removido de logs info. `url=download_url` (que continha `?token=...`) substituido por `source="b3", size=N`

## [1.0.1] - 2026-03-19

### Added
- **defensivos** — dados de agrotoxicos registrados no Brasil (Agrofit/MAPA). 3 funcoes: `formulados()`, `autorizacoes()`, `tecnicos()`. Fonte: Portal de Dados Abertos MAPA (CC-BY). Cache Parquet 24h. ~8K formulados, ~267K autorizacoes, ~2.8K tecnicos. Filtros por ingrediente ativo, classe, titular, cultura, organicos. 51 testes, golden data

### Changed
- **deps** — duckdb `>=1.4.4` → `>=1.5.0`. Non-blocking checkpointing, 17% throughput, K-way merge sort, late materialization. Workaround em conftest.py para `_duckdb._sqltypes` coverage+Python 3.14

### Fixed
- **noticias_agricolas/parser** — `parse_indicador()` agora reconhece 3 layouts adicionais do NA: tabelas com coluna `Vencimento` (acucar, acucar_refinado), tabelas com coluna `Estado` (suino), e tabelas sem coluna de data com data no div `Fechamento` (leite). Novo helper `_extract_parent_date()`. Bug pre-existente corrigido: `has_region_col` vazava entre iteracoes de tabela
- **b3/api** — `ajustes(data=)` agora aceita formato ISO (`"2025-03-07"`) alem de BR (`"07/03/2025"`) e `date` object. Antes: ISO string passava direto pro client e causava `ValueError` no `strptime("%d/%m/%Y")`
- **alt/sicar** — `data_atualizacao` removido de `PROPERTY_NAMES` WFS. Campo nao existe em todos os layers estaduais (SP, RS, PR, SC, RJ, TO), causando 400 Bad Request. Parser ja tratava campo ausente via `.get()`. Dedup em `imoveis()`/`imoveis_geo()` simplificado (sort por `cod_imovel` apenas, sem `data_atualizacao` que era all-NaT)
- **bcb/bigquery_client** — `fetch_credito_rural_bigquery()` agora tem timeout de 120s via `asyncio.wait_for()`. Antes: fallback BigQuery podia travar indefinidamente quando OData retornava 500

## [1.0.0] - 2026-03-10

### Added
- **CLI** — `cepea indicador` funcional (era stub). Suporta `--inicio`, `--fim`, `--ultimo`, `--formato`
- **docs** — guia dedicado de snapshots (`docs/guides/snapshots.md`): criação, listagem, uso, delete, modo determinístico CLI vs programático
- **docs** — docstring Google style em `cepea.indicador()` (10 params, inclui `_moeda`, `validate_sanity`, `force_refresh`, `offline`)
- **py.typed** — PEP 561 marker para suporte a type checking em projetos downstream
- **datasets** — 2 novos datasets na camada semântica (32→34): `movimentacao_portuaria` (ANTAQ, single-source, keyword-only, 21 colunas, 6 filtros opcionais, reutiliza `MOVIMENTACAO_PORTUARIA_V1`), `condicao_lavouras` (SEAB/DERAL, 14 culturas PR, normalização condicao vazia→plantio/colheita, contrato `CONDICAO_LAVOURAS_V1`)
- **datasets** — 3 novos datasets na camada semântica (29→32): `oferta_demanda_global` (USDA PSD, long/pivot format, 8 commodities, skip contract quando `pivot=True`, contrato `OFERTA_DEMANDA_GLOBAL_V1`), `comercio_internacional` (UN Comtrade, bilateral global por HS code, 17 produtos, reutiliza `COMERCIO_BILATERAL_V1`), `zoneamento_agricola` (ZARC/MAPA, janelas de plantio por município/cultura/solo, 36 decêndios, keyword-only, contrato `ZONEAMENTO_AGRICOLA_V1`)
- **datasets** — 3 novos datasets ambientais/ESG na camada semântica (26→29): `desmatamento` (INPE, `tipo=` dispatch prodes/deter, 6 biomas, normalização bioma, fail-fast DETER fora Amazônia/Cerrado, reutiliza `DESMATAMENTO_PRODES_V1`/`DESMATAMENTO_DETER_V1`), `uso_do_solo` (MapBiomas, `tipo=` dispatch cobertura/transição, suporte `nivel="municipio"` com skip contract, reutiliza `MAPBIOMAS_COBERTURA_V1`/`MAPBIOMAS_TRANSICAO_V1`), `queimadas` (INPE, focos de calor por satélite, dual-register contrato, reutiliza `FOCOS_QUEIMADAS_V1`)
- **datasets** — 2 novos datasets na camada semântica (24→26): `clima` (INMET→NASA POWER, dual-mode UF mensal + estação diária, contratos `CLIMA_V1`/`CLIMA_ESTACAO_V1`), `futuros_agricolas` (B3, `tipo=` dispatch ajustes/historico/posicoes, 7 contratos agro, reutiliza `AJUSTE_DIARIO_V1`/`POSICOES_ABERTAS_V1`, fail-fast soja_fob+posicoes)
- **datasets** — 3 novos datasets na camada semântica (21→24): `serie_historica_safra` (CONAB, 32 culturas desde 1976/77, contrato `SERIE_HISTORICA_SAFRA_V1`), `preco_atacado` (CONAB CEASA/PROHORT, preços diários hortifrúti, reutiliza `PRECO_ATACADO_V1`), `seguro_rural` (MAPA PSR, apólices e sinistros com `tipo=` dispatch, reutiliza `MAPA_PSR_APOLICES_V1`/`MAPA_PSR_SINISTROS_V1`)
- **datasets** — 3 novos datasets na camada semântica (18→21): `importacao` (ComexStat, mirror de exportacao), `pib_agro` (IBGE SIDRA, PIB agropecuário por setor/trimestre com `precos` na PK), `progresso_safra` (CONAB, progresso semanal semeadura/colheita). Contratos `IMPORTACAO_V1`, `PIB_AGRO_V1` + dual register `progresso_safra` para `CONAB_PROGRESSO_V1`
- **comexstat** — `importacao()` para dados de importação ComexStat (MDIC/SECEX). Mesma interface de `exportacao()`: filtro por produto (NCM), ano, UF, agregação mensal/detalhado, `as_polars`, `return_meta`. Parser refatorado com `_parse_comexstat_csv()` compartilhado (mensagens de erro corretas por fluxo). `_fetch_comexstat()` helper elimina duplicação entre export/import. 10 testes novos (6 API + 4 parser)
- **ZARC** — Zoneamento Agricola de Risco Climatico (janelas de plantio por municipio/cultura/solo). Fonte MAPA/Embrapa via CKAN (CC-BY). `zoneamento()` com filtros cultura/uf/municipio/safra/solo/ciclo, `culturas()`, `safras_disponiveis()`. Session cache para CSVs grandes. 31 testes, golden data
- **utils/io** — `open_excel_safe()` e `read_excel_safe()` helpers com fallback automatico para `python-calamine` (Rust, MIT). Se openpyxl falhar (ex: XLSX com estilos/fills malformados), tenta calamine que ignora estilos e extrai apenas dados. Guard xlrd: se `engine="xlrd"`, nao tenta calamine (re-raise direto). 9 parsers migrados (19 operacoes Excel em 9 arquivos): conab/progresso, abiove, conab/serie_historica, deral (multi-sheet via `open_excel_safe`); alt/anp_diesel, mapbiomas, anda, conab/parsers/v1, conab/custo_producao (single-sheet via `read_excel_safe`)
- **deps** — `python-calamine>=0.3.0` como dependencia core (749KB, zero deps Python, engine Rust para leitura Excel)

### Improved
- **docs** — README: seção "Modo Determinístico" expandida com snapshots (CLI + programático). `docs/index.md`: menção a snapshots na feature list. `mkdocs.yml`: nav entry para guia de snapshots
- **docs** — README, docs/index.md, index.html e mkdocs.yml atualizados com todos os 34 datasets. Tabelas ordenadas alfabeticamente, 35 contract docs no nav mkdocs, 34 dataset cards no index.html. Typos de acentuacao corrigidos (Producao→Produção, carvao→carvão, acai→açaí)
- **CI** — Python 3.13 adicionado a matrix de testes. Classifier `Programming Language :: Python :: 3.13` em pyproject.toml
- **coverage** — benchmark/ excluido do coverage (`omit`). 5093+ testes, 88% cobertura (era 4906/87%). ~190 testes novos: datasets/ (snapshots 49→97%, datasets/ multiple files pushed to 80%+, conab/progresso/client 19→60%+). Dead code `_parse_week_date` removido. Test quality audit: singleton mutation fix, `@requires_pyarrow` guards, weak assertion strengthening
- **inmet/api** — `estacoes()` agora suporta `as_polars`, `return_meta` e `build_source_meta()` (unica source API que nao tinha os 3)
- **conab/api** — `balanco()` e `brasil_total()` agora suportam `return_meta` com overloads tipados e `build_source_meta()`. `safras()` migrado de MetaInfo inline para `build_source_meta()`
- **b3** — `ajustes()` agora usa BVBG-086 ZIP como fonte primaria (endpoint `pesquisapregao/download`, XML streaming com `lxml.etree.iterparse`). Fallback automatico para HTML legado em caso de falha. `parse_ajustes_zip()` com filtragem agro, nested ZIP extraction e wrapping de erros em `ParseError`. URL antiga mantida para fallback
- **constants** — `HTTPSettings.max_concurrent_default`, `max_concurrent_b3`, `max_concurrent_ibge` para concorrencia configuravel por fonte no RateLimiter (default 1 = sem mudanca de comportamento)
- **normalize/numeric** — `parse_numeric_br` canonica para parsing numerico formato BR (ponto=milhar, virgula=decimal). Substitui 3 implementacoes duplicadas em `alt/` parsers
- **normalize/encoding** — `detect_encoding_chain` para deteccao rapida de encoding via probe chain (UTF-8, UTF-8-sig, Windows-1252, ISO-8859-1, chardet fallback). Substitui 2 implementacoes duplicadas em `alt/` parsers
- **utils/result** — `finalize_result` helper com overloads tipados para epilogo polars/return_meta. Substitui ~140 linhas de boilerplate em ibge/ (10x), conab/api.py (3x), cepea/api.py (1x)
- **utils/warnings** — `warn_once(key, message)` helper para warnings de licenca. Elimina 7 flags `_WARNED` globais e `global _WARNED # noqa: PLW0603` boilerplate em 6 modulos (abiove, anda, b3, conab/ceasa, imea, noticias_agricolas). `warn_once_reset()` para testes
- **normalize/numeric** — `safe_float` canonico para conversao numerica com suporte a strip chars, null markers configuraveis, nan_as_none, treat_zero_as_none e heuristica ABIOVE (3 digitos apos ponto = milhar). Substitui 5 implementacoes duplicadas `_safe_float` em anda, abiove, deral, conab/serie_historica, conab/custo_producao. `conab/progresso` mantido como wrapper local `_parse_pct`
- **utils/result** — `build_source_meta()` helper para construcao de MetaInfo em source APIs. Absorve 13 campos repetitivos (`fetched_at`, `fetch_timestamp`, `records_count`, `columns`, etc) com defaults inteligentes. Substitui 34 blocos de ~17 linhas em 19 arquivos (abiove, anda, antaq, b3, bcb, comexstat, comtrade, deral, desmatamento, imea, inmet, mapbiomas, nasa_power, queimadas, usda, alt/antt_pedagio, alt/mapa_psr, alt/anp_diesel, alt/sicar)
- **as_polars** — `as_polars=True` suportado em todas as 51 source APIs (37 migradas neste ciclo + 14 anteriores). Todas usam `finalize_result()` para conversao pandas→polars e epilogo return_meta
- **normalize/dates** — `MESES_PT` dict canonico (26 entries: 12 full + 12 abrev + "marco" sem acento) e `month_to_number()` helper. Substitui 3 dicts duplicados em abiove/models, anda/parser, anp_diesel/parser (~60 linhas)
- **normalize/regions** — `UFS_VALIDAS` frozenset canonico com 27 UFs. Substitui 4 frozensets literais identicos em antt_pedagio, mapa_psr, anp_diesel, sicar (~120 linhas)
- **utils/validation** — `validate_year_uf()` helper para validacao de UF e range de anos. Substitui 2 `_validate_params` identicos + 6 inline UF checks em antt_pedagio, mapa_psr, anp_diesel, sicar
- **utils/io** — `read_csv_safe()` helper para leitura CSV com encoding fallback (utf-8 → latin-1). Substitui 4 blocos try/except em desmatamento (2x), sicar, queimadas
- **utils/html** — `parse_links_from_html()` canonico para extracao de links HTML com filtro regex, dedup e base_url. Substitui 3 implementacoes em anda/client, conab/serie_historica/client, conab/custo_producao/client (~120 linhas)
- **normalize/regions** — `normalizar_bioma()`, `BIOMAS` e `BIOMAS_VALIDOS` canonicos. Substitui 3 implementacoes identicas em desmatamento/models, mapbiomas/models, queimadas/models (~45 linhas). Re-exports mantidos para backward compat. Exportado em `agrobr.normalize` como API publica
- **desmatamento/api** — `normalizar_bioma()` wired nos 4 entry points (`prodes`, `prodes_geo`, `deter`, `deter_geo`). Parametro `bioma` aceita lowercase/sem acento (ex: `"cerrado"` → `"Cerrado"`, `"amazonia"` → `"Amazônia"`)
- **http/retry** — `retry_on_status()` agora captura transport exceptions (`TimeoutException`, `NetworkError`, `RemoteProtocolError`) com retry exponencial. Antes: zero retries para falhas de rede, excecao crua propagava. Agora: retries com backoff identico ao de status codes retriable, `SourceUnavailableError` no exhaustion. 24+ source clients beneficiados automaticamente
- **inmet/client** — HTTP 403 agora levanta `SourceUnavailableError` com mensagem sobre `AGROBR_INMET_TOKEN` em vez de `httpx.HTTPStatusError` generico. `fetch_dados_estacoes_uf` propaga 403 em vez de engolir silenciosamente
- **http/rate_limiter** — `RateLimiter` com concorrencia configuravel via `HTTPSettings.max_concurrent_{source}`. `Semaphore(1)` hardcoded substituido por `Semaphore(config)`. Pattern "burst then pause": N requests simultaneos seguidos de pausa de rate_limit delay. Default 1 (zero mudanca de comportamento para fontes nao configuradas). B3 e IBGE configurados com concorrencia 3
- **b3/api** — `historico()` e `oi_historico()` migrados de while-loop sequencial + `asyncio.sleep(1.0)` para `asyncio.gather()` com lista de weekdays. Rate limiting delegado ao RateLimiter (Semaphore(3) para B3). ~4.4x speedup esperado (22 dias: ~44s → ~10s)
- **inmet/client** — `_get_json()` e `fetch_dados_estacao()` aceitam `http: AsyncClient | None` para reuso de conexao. `fetch_dados_estacoes_uf()` cria shared client para todas as estacoes. Elimina criacao de novo AsyncClient por request
- **nasa_power/client** — `_get_json()` aceita `http: AsyncClient | None`. `fetch_daily()` cria shared client para chunking loop. `RATE_LIMIT_DELAY` e `asyncio.sleep()` removidos (RateLimiter ja enforce delay entre requests)
- **ibge/api** — `lspa()` migrado de for-loop sequencial para `asyncio.gather()` (max 3 sub-produtos em paralelo). ~3x speedup para feijao (3 sub-products)
- **ibge/censo_api** — `censo_agro()` e `_fetch_censo_multi_table()` migrados de for-loops sequenciais para `asyncio.gather()` (2-3 fetches em paralelo)
- **ibge/ helpers** — `resolve_ibge_code()` e `resolve_period()` em `_helpers.py` substituem 13 blocos duplicados (6 ibge_code + 7 period) em api.py, pesquisas_api.py, censo_api.py. `calculate_expiry` padronizado para flat strings em 6 call sites (api.py, censo_api.py). `_UF_CODES` promovido a constante module-level em client.py
- **noticias_agricolas** — adicionado a `sync.py` e `__init__.py` (antes ausente do namespace publico e da API sync)
- **conab/api.py** — early returns de `safras()`, `balanco()` e `brasil_total()` agora passam por `finalize_result()`, respeitando `as_polars` e populando MetaInfo completo em resultados vazios
- **contracts/__init__.py** — `_auto_discover_contracts` removido de `__all__` (funcao privada)
- **export.py** — `_get_version()` substituido por `from agrobr import __version__` direto (elimina funcao wrapper)
- **normalize/crops.py** — `_CULTURAS_SEM_ACENTO` dict pre-construido no module level: `normalizar_cultura()` de O(n) loop para O(1) lookup
- **alt/antt_pedagio** — `except Exception:` substituido por `except httpx.HTTPError:` (fetch) e `except (ParseError, KeyError, ValueError):` (parse/join)
- **alt/sicar** — `except Exception:` substituido por `except httpx.HTTPError:` no pre-flight hit count
- **conab/parsers/v1.py** — `except (ParseError, Exception)` simplificado para `except Exception` (ParseError ja e subclasse)
- **ibge/ module split** — `ibge/api.py` (2025 linhas) dividido em `censo_api.py`, `pesquisas_api.py`, `censo_tables.py` e `_helpers.py`. API publica inalterada via re-exports em `__init__.py`. Dead branch e `import re` removidos. `NIVEL_MAP` extraido como constante compartilhada
- **sync.py** — 23 subclasses stub vazias de `_SyncModule` removidas (258→123 linhas). `_MODULE_CLASSES` dict eliminado, `__getattr__` e `_SyncAlt` instanciam `_SyncModule` diretamente. API publica inalterada
- **cli.py** — `_output_df` helper extrai 6 blocos identicos de formatacao output (json/csv/table)
- **CacheSettings** — 32 campos `ttl_*` e `stale_multiplier` removidos (dead code, nunca lidos). `cache/policies.py::POLICIES` e a fonte unica de TTL
- **Test infrastructure** — `tests/helpers.py` com 3 factories (`make_mock_response`, `make_mock_async_client`, `make_alert_settings`). Elimina `_mock_response` duplicado em 18 arquivos e boilerplate `__aenter__`/`__aexit__` em 23 arquivos. `RETRY_SLEEP` e `make_sleep_tracker()` extraidos de 7 test files duplicados (anda, abiove, bcb, usda, imea, deral, comexstat). 4 fixtures mortas + 3 constantes mortas removidas do conftest.py
- **test_dataset_common** — `ALL_DATASETS` dinamico via `registry.list_datasets()` (18 datasets, era 11 hardcoded). `update_frequency` assertion expandida para `continuous`, `decennial`, `never`
- **test_cache/test_migrations** — 9 cenarios para `cache/migrations.py` (fresh DB, partial upgrade, idempotent, column/index creation). Zero cobertura anterior
- **datasets/ MetaInfo dedup** — `BaseDataset._build_meta()` e `_unpack_result()` em `datasets/base.py`. 18 blocos MetaInfo (~18 linhas cada) colapsados para 1 linha. 20 `isinstance(result, tuple)` patterns substituidos por `_unpack_result()`. `datetime`/`UTC` imports removidos de 14 datasets. ~380 linhas de boilerplate eliminadas
- **37 source APIs** migradas para `finalize_result()`: bcb, b3 (4), inmet (2), nasa_power (2), comexstat, usda, anda, deral, abiove, imea, antaq, comtrade (2), desmatamento (2), queimadas, mapbiomas (2), alt/anp_diesel (2), alt/antt_pedagio (2), alt/mapa_psr (2), alt/sicar (2), conab/ceasa, conab/serie_historica, conab/progresso, conab/custo_producao, ibge/legacy_api, ibge/censo_municipal_1985. Inline `if return_meta` boilerplate eliminado, `as_polars` habilitado em todas
- **4 CONAB sub-modulos** (ceasa, serie_historica, progresso, custo_producao) migrados de `MetaInfo(...)` inline com `datetime.now(UTC)` duplicado para `build_source_meta()` com `utcnow()` unico
- **ibge/legacy_api** — inline `as_polars` handling e `MetaInfo` manual substituidos por `finalize_result()` + `build_source_meta()`. Dead branch `len(df) if not isinstance(df, tuple)` removido
- **ibge/censo_municipal_1985** — `MetaInfo` inline substituido por `build_source_meta()` + `finalize_result()`. Timing via `time.perf_counter()` adicionado
- **test_datasets** — `conftest.py` com `mock_source_meta()` + `make_source()` helpers reutilizaveis. 39 testes novos cobrindo 6 datasets (preco_diario 1→9, producao_anual 1→7, estimativa_safra 1→7, balanco 6, extrativismo_vegetal 5, silvicultura 5). Fallback em cascata testado para 3 datasets multi-source. Testes de normalize, invalid produto, return_meta e SourceUnavailableError
- **cepea/api** — `indicador()` (190→~130 linhas) decomposto em 5 helpers: `_normalize_dates` (conversao str→date + defaults), `_needs_fetch` (gap detection com weekday check), `_warn_stale` (deduplica 2 blocos identicos de stale warning), `_FetchResult` NamedTuple (tipo estruturado para 7 campos de retorno), `_fetch_and_parse` (fetch + dispatch parser CEPEA/NA). Imports `warnings`/`StaleDataWarning` promovidos a top-level
- **ibge/api** — `abate()` (160→~85 linhas) decomposto em 2 helpers: `_detect_abate_columns` (col_map estatico + sniffing dinamico D2C/D3C) e `_merge_cabecas_peso` (split por variavel_cod, merge cabecas/peso, formatting output)
- **conab/progresso/parser** — `parse_progresso_xlsx()` (156→~110 linhas) decomposto em 2 helpers: `_read_xlsx_sheet` (abertura workbook + busca sheet + validacao) e `_build_record` (deduplica 2 blocos identicos de record-building BR/estado)
- **http/settings** — `get_timeout(read=...)` factory com override de read timeout. 26 client modules migrados de inline `httpx.Timeout(...)` + `HTTPSettings()` para `get_timeout()`. Elimina `_settings = HTTPSettings()` e `_get_timeout()` locais
- **URL dedup** — 6 constantes de URL duplicadas em modules substituidas por referencias a `URLS` central (PENTAHO_BASE, FTP_BASE, WFS_BASE, CKAN_BASE, SHLP_BASE, VENDAS_DIESEL_CSV_URL). `SIDRA_BASE` em `ibge/_helpers.py` substitui 18 hardcoded `"https://sidra.ibge.gov.br"`
- **Dead code purge** — 5 modulos mortos removidos (stability.py, telemetry/, aliases.py, utils/logging.py). 15+ classes/funcoes mortas removidas (CacheEntry, HistoryEntry, CacheError, 4 dead Warnings, InvalidationReason, Contract.from_json/from_dict, TICKER_PARA_CONTRATO, data_para_safra, mes_para_numero, numero_para_mes, extrair_uf_municipio, validar_regiao, get_rate_limit, get_client_kwargs, cleanup stub). Constantes mortas: TelemetrySettings, CONFIDENCE_MEDIUM, CacheSettings.offline_mode/cache_max_age_days/history_max_age_days, 5 URLs mortas. AgrobrConfig.timeout_seconds removido
- **Dead cache cleanup** — `cache/history.py` deletado (HistoryManager inteiro, 179 linhas, zero callers, bug latente em `query()`). 8 metodos mortos removidos de `DuckDBStore` (`cache_get`, `cache_set`, `cache_invalidate`, `cache_delete`, `cache_clear`, `history_save`, `history_get`, `indicadores_get_dates`). 3 funcoes mortas de `keys.py` (`parse_cache_key`, `is_legacy_key`, `legacy_key_prefix`). 5 funcoes mortas de `policies.py` (`get_ttl`, `is_expired`, `is_stale_acceptable`, `get_stale_max`, `should_refresh`). `CacheSettings.strict_mode` e `save_to_history` removidos (zero callers apos remocao de `cache_get`/`history_save`). ~400 linhas de producao, ~700 linhas de testes. APIs vivas mantidas: `indicadores_query`/`indicadores_upsert` (CEPEA), `get_store`, `build_cache_key`, `calculate_expiry`, `get_policy`, schema init
- **test_datasets (parte 2)** — 33 testes novos para 5 datasets restantes: pecuaria_municipal (8), abate_trimestral (6), censo_agropecuario (6), censo_agropecuario_legado (6), leite_industrial (7). Cobertura fetch/meta/invalid_produto/kwargs/snapshot/source_fail
- **test_golden** — 7 secoes golden wired: b3 (ajustes HTML + posicoes CSV), comtrade (comercio + mirror), queimadas (focos CSV), desmatamento (4 variants: prodes/deter x csv/geojson), conab_ceasa (precos), conab_progresso (xlsx), mapbiomas (cobertura + transicao). `_assert_dataframe_golden` corrigido para None/NaN (pd.NA nullable int, IEEE 754 NaN). 2 golden dirs reestruturados (conab_progresso, mapbiomas → sub-case + metadata.json)
- **alt/ perf** — 27 `.copy()` desnecessarios removidos de 4 parsers (mapa_psr 9, antt_pedagio/api 10, antt_pedagio/parser 3, anp_diesel 5). 6 mantidos por mutation safety. `_build_vendas_df` em anp_diesel vectorizado: iterrows substituido por `pd.to_numeric`/`.str.map`/`.apply` column-wise. Imports mortos `re`/`date` removidos
- **conab/custo_producao/parser** — multi-format support: `_find_header()` substitui `_find_header_row()` com 2-step detection (single-row scan + 2-row sliding window para headers split). 2-row window usa best-quality selection: avalia todos os candidatos via `_identify_columns` e escolhe o que produz col_map mais completo (bonus para candidatos com ambas colunas obrigatorias item+valor_ha). Corrige culturas especiais (abacaxi, banana, cebola) cujo header split em 3 rows causava false positive no window anterior (keyword "preço" casava em "A PREÇOS DE:" sem mapear valor_ha). `_identify_columns()` expandido com patterns para "custo por ha", "custo/ha", "custo por hectare" (valor_ha) e "custo/{unit}" prefix (preco_unitario). Guards `if key not in mapping` em todas as chaves previnem overwrite (ex: PARTICIPAÇÃO CV ganha sobre CT). `_refine_valor_column()` novo para corrigir offset de merged cells (scan col+1/col+2 por dados numericos). `select_data_sheet()` novo para selecao robusta de sheet de dados (skip Indice/Index, filtro por UF/safra, fallback para ultima sheet). `_parse_sheet_info()` extrai UF e ano do nome da sheet via regex. Suporte a safra "2023/24" expandindo ano curto para 4 digitos. COE/COT patterns expandidos para "custo variavel", "total das despesas de custeio", "custo operacional (". Link regex `.xlsx` → `.xlsx?` para suportar .xls. PARSER_VERSION 1→2
- **conab/custo_producao/api** — `custo_producao()` e `custo_producao_total()` integrados com `select_data_sheet()` e `_parse_sheet_info()` para resolucao automatica de sheet, UF e safra

### Changed
- **CLI** — stubs `cache status`/`cache clear` removidos (subcommand `cache` eliminado)
- **CLI** — `config show` não exibe mais AlertSettings (módulo privado)
- **wheel** — `agrobr/health`, `agrobr/alerts` e `agrobr/benchmark` excluídos do wheel distribuído (infra interna)

### Fixed
- **comtrade** — ausente do namespace publico `agrobr.__init__` — `from agrobr import comtrade` falhava com ImportError
- **datasets/silvicultura** — exportado como `silvicultura_dataset` (alias desnecessario, padrao dos outros 33 e sem alias). Corrigido para `silvicultura`
- **b3/parser** — `_parse_bvmf_xml` memory cleanup do `iterparse` fazia `del parent[0]` (filhos do parent) quando a intencao era remover siblings anteriores do parent no nivel do avo. XMLs grandes (BVBG-086, 7-8 MB) crasheavam com `IndexError` quando parent ficava vazio. Corrigido para `grandparent.remove(grandparent[0])`
- **conab/custo_producao/client** — regex `\.xlsx` excluia `.xls` (graos: soja, trigo, algodao, cafe). Corrigido para `\.xlsx?`. Novo: folder crawl lazy para culturas em subpaginas (milho, arroz, feijao) — `_extract_folder_urls()` detecta links de pasta, `_crawl_folder()` busca `.xls` dentro delas com `asyncio.gather()` paralelo, strip `/view`. Zero overhead para culturas com link direto. UF regex hardcoded substituido por `UFS_VALIDAS` canonico
- **sync** — `_get_or_create_event_loop()` corrigido: `except RuntimeError` no outer try engolia o `raise RuntimeError` do nest_asyncio missing. Loop running sem nest_asyncio agora levanta RuntimeError corretamente em vez de fallback silencioso para `get_event_loop()`. Test morto (`test_running_loop_without_nest_asyncio_raises`) reescrito e funcional
- **ibge/client** — `sidrapy.get_table()` agora roda via `asyncio.to_thread()`, desbloqueando o event loop em todas as queries IBGE (pam, lspa, ppm, abate, censo, silvicultura, extracao, leite, pib)
- **http/rate_limiter** — `RateLimiter` detecta troca de event loop e recria Lock/Semaphores automaticamente. Antes crashava em chamadas sequenciais com `asyncio.run()`
- **cache/policies** — timezone mismatch corrigido: `_get_smart_expiry_time()` e 3 funcoes de expiry agora usam UTC consistente com `duckdb_store.py`. `CEPEA_UPDATE_HOUR` renomeado pra `CEPEA_UPDATE_HOUR_BRT` (18) / `CEPEA_UPDATE_HOUR_UTC` (21)
- **utcnow migration** — `datetime.utcnow()` (deprecated Python 3.12+) substituido por `utcnow()` helper (naive UTC) em models.py, fingerprint.py, collector.py, duckdb_store.py. 12 sites `fetched_at=datetime.now()` migrados pra UTC em cepea, conab, ibge (api, pesquisas, censo)
- **conab/parsers/v1** — fallback hardcoded `"2025/26"` removido de `_extract_safra_columns()`. Agora levanta `ParseError` com log estruturado quando nao detecta colunas de safra
- Blocos `if TYPE_CHECKING: pass` mortos removidos de 4 modulos datasets (producao_anual, estimativa_safra, preco_diario, balanco)
- **conab/custo_producao** — URL da pagina de custos tinha path duplicado (`/conab/conab/pt-br/...`) resultando em 404. `BASE_URL` ja continha `/conab`, path literal repetia. Corrigido para `{BASE_URL}/pt-br/...`
- **alt/sicar** — `area_ha` e `modulos_fiscais` falhavam contract validation quando WFS GeoServer retornava valores com formato BR (virgula decimal). `pd.to_numeric` nao parseia `"120,5"` → coerce para NaN → `ContractViolationError`. Fix: `.str.replace(",", ".")` antes de `pd.to_numeric` (vectorizado)
- **normalize/encoding** — `detect_encoding_chain` validava encoding apenas contra sample de 4096 bytes. Bytes invalidos alem do sample (ex: 0x81 na posicao 17.6M do CSV PSR) passavam como windows-1252 no sample mas falhavam no decode completo. Fix: valida encoding contra conteudo completo, windows-1252 cai para iso-8859-1 quando necessario
- **comtrade/api** — `comercio()` default `periodo` corrigido de ano corrente (dados incompletos/vazios) para `year - 1` (ultimo ano completo disponivel)
- **comexstat/api** — `exportacao()` default `ano` corrigido de ano corrente para `utcnow().year - 1`. Import migrado de `datetime.now()` local para `utcnow()` UTC
- **datasets/exportacao** — fallback ABIOVE default `ano` corrigido para `utcnow().year - 1`
- **conab/custo_producao** — 2 `datetime.now(UTC)` restantes em `custo_producao_total()` migrados para `utcnow()`. Import `datetime`/`UTC` removido
- **bcb/client** — `fetch_credito_rural_with_fallback()` agora captura `httpx.HTTPStatusError` (403/404) alem de `SourceUnavailableError`, acionando BigQuery fallback. Antes: HTTP 403 de `raise_for_status()` propagava sem tentar fallback

## [0.12.0] - 2026-02-28

### Added
- **IBGE PEVS Silvicultura** — nova funcao `ibge.silvicultura()` para producao silvicultural
  (eucalipto, pinus, carvao vegetal, madeira). Tabela SIDRA 291 (producao, classificacao c194)
  + tabela 5930 (area plantada, classificacao c734). 14 produtos, 3 especies de area,
  variaveis quantidade_produzida/valor_producao/area. Helpers `produtos_silvicultura()` e
  `especies_silvicultura_area()`. Contrato `ibge.silvicultura` v1.0. Dataset `silvicultura`
  com 8 produtos. Schema JSON. Cache 7d/90d stale. ~57 testes + golden data
- **IBGE PEVS Extracao Vegetal** — nova funcao `ibge.extracao_vegetal()` para producao
  extrativista vegetal (acai, castanha-do-para, erva-mate, palmito, etc). Tabela SIDRA 289
  (classificacao c193). 21 produtos, variaveis quantidade_produzida/valor_producao.
  Helper `produtos_extracao_vegetal()`. Contrato `ibge.extracao_vegetal` v1.0. Dataset
  `extrativismo_vegetal` com 12 produtos. Schema JSON. Cache 7d/90d stale. ~35 testes + golden data
- **IBGE Leite Trimestral** — nova funcao `ibge.leite_trimestral()` para aquisicao e
  industrializacao de leite por UF. Tabela SIDRA 1086. 3 variaveis (leite adquirido,
  industrializado, preco medio) pivotadas em colunas wide. Contrato `ibge.leite_trimestral` v1.0.
  Dataset `leite_industrial`. Schema JSON. Cache 7d/90d stale. ~30 testes + golden data
- **IBGE PIB Agro** — nova funcao `ibge.pib_agro()` para PIB agropecuario trimestral
  (Contas Nacionais Trimestrais). Tabelas SIDRA 1846 (precos correntes) e 6612 (precos reais
  1995). 4 setores (agropecuaria, industria, servicos, pib_total). Sem dataset (macro view).
  Cache 7d/90d stale. ~25 testes + golden data
- **Desmatamento PRODES com geometria** — nova funcao `desmatamento.prodes_geo()` retorna
  `GeoDataFrame` com poligonos MultiPolygon (EPSG:4326) do desmatamento consolidado PRODES.
  Requer `pip install agrobr[geo]`. Todos os 6 biomas suportados (incluindo Amazonia).
  Default `maxFeatures=10000` com warning de truncamento. Mesmos parametros de `prodes()`
  (bioma, ano, uf, return_meta). Sync wrapper automatico. Schema `desmatamento_prodes_geo.json`.
  28 novos testes
- **Desmatamento DETER com geometria** — nova funcao `desmatamento.deter_geo()` retorna
  `GeoDataFrame` com poligonos MultiPolygon (EPSG:4326) dos alertas DETER. Requer
  `pip install agrobr[geo]`. Default `maxFeatures=10000` com warning de truncamento.
  Mesmos parametros de `deter()` (bioma, uf, data_inicio, data_fim, classe, return_meta).
  Sync wrapper automatico. 45 novos testes. Schema `desmatamento_deter_geo.json`
- **SICAR Cadastro Ambiental Rural com geometria** — nova funcao `sicar.imoveis_geo()`
  retorna `GeoDataFrame` com poligonos MultiPolygon (EPSG:4326) dos imoveis rurais.
  Requer `pip install agrobr[geo]`. Mesmos parametros de `imoveis()`. Max 5000 features
  com warning de truncamento. Refator: `_normalize_columns` compartilhado entre
  `parse_imoveis_csv` e `parse_imoveis_geojson`. Schema `sicar_imoveis_geo.json`.
  28 novos testes
- **SICAR filtro por codigo IBGE** — novo parametro `cod_municipio` (int) em
  `imoveis()`, `imoveis_geo()` e `resumo()`. Alternativa ao filtro por nome
  (`municipio`) que nao lida com acentos no GeoServer WFS ILIKE. Mutuamente
  exclusivo com `municipio` (ValueError se ambos). `resumo()` refatorado para
  usar `_build_cql_filter` em vez de CQL hardcoded. 9 novos testes
- **Censo Agropecuario Municipal 1985 — Fase 7 completa: core + integracao** (#17) —
  dados municipais do Censo 1985 extraidos via OCR de PDFs do IBGE. 53 CSVs bundled no
  pacote (`agrobr/data/censo_1985/`), modulo `agrobr/ibge/censo_municipal_1985.py` com
  API async (`censo_agro_municipal_1985()`, `temas_censo_agro_municipal_1985()`),
  constantes (53 temas, tab 67-119), loader CSV com melt wide→long, resolucao de
  `localidade_cod` via `municipio_para_ibge()`, unidade por prefixo semantico. Contrato
  `IBGE_CENSO_AGRO_MUNICIPAL_V1` (13 colunas, PK vazio — labels OCR homonimos,
  effective_from 0.12.0). Dataset `censo_agropecuario_municipal_1985` no registry com
  fallback automatico. CLI: `agrobr ibge censo-municipal-1985 <tema>` (--uf, --nivel,
  --formato) e `agrobr ibge temas-municipal-1985`. Schema JSON gerado. 63 testes
  (constantes, index, CSV, unidade, data dir, contrato, validacao, parsing, dataset, CLI).
  22 UFs cobertas (MA/PI/CE/RN excluidas — sem OCR). Docs completos
- **Censo Agropecuario Serie Historica — Bloco 4: CLI e integracao final** (#17) — comandos
  `agrobr ibge censo-historico <tema>` (com `--ano`, `--uf`, `--nivel`, `--formato`) e
  `agrobr ibge temas-historico`. Sync wrapper via `agrobr.sync.ibge` funciona automaticamente
- **Censo Agropecuario Serie Historica — Bloco 3: contrato, dataset e docs** (#17) — contrato
  `IBGE_CENSO_AGRO_HISTORICO_V1` (9 colunas, PK `[ano, tema, categoria, variavel, localidade]`,
  effective_from 0.13.0, fonte='ibge_censo_agro_historico', anos censitarios 1920-2006, nivel max UF).
  Dataset `censo_agropecuario_historico` com 9 temas, update_frequency='never', license='livre'.
  Registrado no registry. 25 novos testes (14 contrato + 11 dataset). Docs: contrato, licenses,
  index, README, CHANGELOG atualizados
- **Censo Agropecuario Serie Historica — Bloco 2: API, parser e testes** (#17) — nova
  funcao `censo_agro_historico()` para serie historica 1920-2006 (ate UF). Parser dedicado
  `_parse_censo_historico_raw()` com deteccao robusta de dimensoes (ano/variavel/categoria),
  unidade por categoria (UNIDADES_CATEGORIAS como fonte primaria, MN so como ultimo
  fallback — corrige Aves=Mil cabecas vs Cabecas). Helper `temas_censo_agro_historico()`.
  3 classes de teste: validacao (9), parsing (22 com mocks), integracao (1). 126 testes
  no arquivo (era 95)
- **Censo Agropecuario Serie Historica — Bloco 1: constantes SIDRA** (#17) — 9 tabelas
  da serie historica (263-283, 1730, 1731) mapeadas com periodos, variaveis,
  classificacoes, categorias, niveis territoriais e unidades. Cobertura: 1920-2006,
  ate Brasil+Regiao+UF. 95 testes cobrindo todas as constantes
- **PAM cacau** — novo produto `cacau` (código SIDRA 40138, "Cacau em amêndoa") em
  `PRODUTOS_PAM` e na whitelist do dataset `producao_anual`
- **MapBiomas cobertura municipal** — novo parametro `nivel="municipio"` em `cobertura()`.
  Chama `fetch_biome_state_municipality()` (~660 MB), parser detecta coluna `municipality`
  automaticamente. Novo parametro `municipio` para filtro por nome (case-insensitive).
  Warning de download pesado via structlog

### Improved
- **Censo Agro Municipal 1985** — melhoria de qualidade dos dados OCR municipais (53 tabelas, 22 UFs).
  Column bleed fix: 525 valores corrigidos (remoção de dígitos vazados de colunas adjacentes).
  Label D→O fix: `\bOE\b→DE`, `\bOO\b→DO` no OCR (e.g. "PLÁCIDO OE CASTRO" → "DE CASTRO").
  Tolerância adaptativa no validador: `absolute_tolerance=5.0` para valores pequenos (<100),
  `sparse_factor=2.0` para tabelas com >60% de células vazias/zero.
  Thresholds de confiança recalibrados: `_load_stats` 70/40→60/30, `generate_confidence_report`
  suspect_rate 0/0.3→0.10/0.40. Revalidação per-parent-group (upgrade-only).
  Distribuição de confiança: alta 5.4%→25.4%, média 62.0%→65.3%, baixa 32.6%→9.3%

### Changed
- **Rate limiter** — `retry_on_status()` agora aplica rate limiting automático em todas as
  fontes. `RateLimiter._get_delay()` busca settings dinamicamente via `getattr(HTTPSettings)`,
  eliminando dict hardcoded. `RateLimiter.acquire()` aceita `str | Fonte`. 32 call sites
  em 21 clients ganham rate limiting sem alteração de código
- **CONAB Custo Produção** — `fetch_custos_page()` agora usa `retry_on_status()` em cada tab
  e fallback, consistente com `download_xlsx()`. Antes era `client.get()` direto sem retry
- **INMET/NASA POWER** — adicionado `follow_redirects=True` ao `httpx.AsyncClient`
- **ComexStat** — docstring documentando SERPRO TLS (cert intermediário Sectigo ausente,
  `verify=False` justificado)
- **CONAB CEASA** — credenciais Pentaho movidas para env vars (`AGROBR_CONAB_CEASA_USER`,
  `AGROBR_CONAB_CEASA_PASS`) com defaults públicos
- **Structlog** — processador `_scrub_sensitive` filtra campos sensíveis (api_key, token,
  password, authorization) e query params sensíveis em URLs nos logs
- **Golden tests** — checksum exclui `parsed_at` (não-determinístico) para estabilidade
- **ANP Diesel** — `format="mixed"` em `pd.to_datetime()` elimina warning `dayfirst` vs ISO
- **Test performance** — test suite reduzido de ~102s para ~43s (58% mais rápido).
  Fixture autouse `_fast_retry` com env vars para retry delays (0.001s) e rate limits (0.001s).
  Benchmark tests excluídos por default (`-m 'not benchmark and not slow'`).
  ANP diesel golden test marcado como `@pytest.mark.slow` (12s de parse xlsx).
  Testes de settings ajustados para verificar consistência em vez de defaults hardcoded
- **Censo Agropecuario 1995/96 — Bloco 1: config SIDRA** (#16) — tabelas, variaveis,
  classificacoes e indices de coluna para 4 temas (efetivo_rebanho, uso_terra,
  lavoura_temporaria, lavoura_permanente) do Censo 1995. Novo dict `_CENSO_MULTI_TABLE`
  para dispatch multi-tabela (logica no Bloco 2). Contrato `min_value` e dataset `min_date`
  atualizados de 2006 para 1995
- **Censo Agropecuario 1995/96 — Bloco 6: API legado + contrato + dataset** (#16) — nova
  funcao `censo_agro_legado()` para 6 temas FTP (tecnologia, pessoal_ocupado, maquinas,
  producao_animal, valor_producao, financeiro). Contrato `IBGE_CENSO_AGRO_LEGADO_V1` com
  ano fixo 1995, 9 colunas, fonte='ibge_censo_agro_legado'. Dataset
  `censo_agropecuario_legado` com update_frequency='never'. Cache TTL 90 dias. Exports em
  `ibge/__init__` e `datasets/__init__`. Testes completos (API, contrato, dataset, cache,
  exports)
- **Censo Agropecuario 1995/96 — Bloco 2: refatoracao + multi-tabela** (#16) — extraido
  `_parse_censo_raw()` e `_empty_censo_df()` de `_fetch_censo_single()`. Novo
  `_fetch_censo_multi_table()` busca N tabelas SIDRA e concatena. `_fetch_censo_single()`
  simplificado para dispatch multi-table vs single-table. Zero regressao (84 testes)
- **Censo Agropecuario 1995/96 — Bloco 3: testes SIDRA 1995** (#16) — 6 mock builders
  para dados 1995, 12 testes novos em `TestCensoAgro1995Mocked` (single-variable, multi-table,
  multi-year, columns, valor, categorias, unidade). Fix: `_parse_censo_raw` com fallback
  `var_map` para SIDRA single-variable (sem dimensao de variavel na resposta). 104 testes
- **Censo Agropecuario 1995/96 — Bloco 5: FTP client + parser** (#16) — novo
  `ftp_client.py` para download de ZIPs legados do FTP IBGE (padrao ANTAQ: retry, timeout
  180s, validacao tamanho, UserAgentRotator). Novo `legacy_parser.py` com parsing de XLS
  (xlrd) para 6 temas FTP (tecnologia, pessoal_ocupado, maquinas, producao_animal,
  valor_producao, financeiro). Deteccao de hierarquia geografica por indentacao
  (totais/mesorregiao/microrregiao/municipio). Config por tema em `_TEMA_COLS`. URL FTP e
  TTL 90 dias em constants.py. 60 testes novos, suite completa 3811 passed

### Fixed
- **Test isolation** — fixture autouse `_reset_global_state` em conftest.py reseta config,
  RateLimiter, HistoryManager e todas as flags `_WARNED` (6 módulos) entre testes.
  Elimina poluição de estado entre testes e garante isolamento correto
- **HistoryManager** — adicionada `reset_history_manager()` para permitir reset do singleton
- **Contracts DATETIME** — `Column.validate()` agora valida colunas DATETIME (antes caiam
  no fallthrough sem type-check). Afeta 2 colunas SICAR (`data_criacao`, `data_atualizacao`)
- **Contracts auto-discovery** — side-effect imports em `datasets/base.py` substituídos por
  `_auto_discover_contracts()` via `pkgutil`. Descobre automaticamente novos módulos de
  contratos sem precisar editar lista manual
- **IBGE LSPA** — contrato `IBGE_LSPA_V1` agora registrado como `lspa` (antes era definido
  mas nunca registrado)
- **Schema orphan** — removido `antaq_movimentacao.json` duplicado (auto-gerado correto é
  `movimentacao_portuaria.json`)
- **PRODES workspace Amazonia** — `PRODES_WORKSPACES["Amazônia"]` apontava para
  `prodes-cerrado-nb` (workspace do Cerrado). Corrigido para `prodes-amazon-nb` com
  layer `yearly_deforestation_biome`
- **PRODES CQL state filter** — filtro por UF enviava apenas nome completo (ex:
  `state='MATO GROSSO'`), mas WFS do TerraBrasilis tem ambos formatos (UF + nome)
  misturados. Novo `_build_state_cql()` gera `(state='MT' OR state='MATO GROSSO')`
- **`_check_geopandas()` mensagem generica** — mensagem de erro hardcoded para
  `deter_geo()` corrigida para mensagem generica que cobre todas as funcoes geo
- **Censo Agro Legado FTP 404 no nivel Brasil** (#16) — `LEGACY_TEMAS` guardava nomes
  com sufixo `Mn` (ex: `Tab_3Mn`), mas o diretorio `Brasil/` no FTP do IBGE so tem
  arquivos sem sufixo (`Tab_3.zip`). Fix: guardar nome base e adicionar `Mn`
  condicionalmente apenas para diretorios de UF
- **Censo Agro 2006 subcategorias perdidas** (#16) — `_parse_censo_raw()` colidia
  quando SIDRA retorna classificacao em D2 e variavel em D3: o `cat_idx=3` sobrescrevia
  a coluna ja reivindicada como `variavel_cod`, mapeando o nome da variavel como
  categoria e ignorando as subcategorias reais. Fix: deteccao de conflito no `cat_idx`
  com fallback para primeira coluna Dx nao reivindicada. Afeta todos os 6 temas 2006
  (preparo_solo, adubacao, calagem, agrotoxicos, praticas_agricolas, irrigacao)
- **PAM/PPM/Censo Agro municipal — fix SIDRA request** — corrige erro "Unidade territorial
  inexistente" ao usar `nivel='municipio'` com filtro de UF. SIDRA espera notacao
  `in N3 {uf_code}` para filtrar municipios por estado, nao o codigo da UF direto.
  Afeta `pam()`, `ppm()` e `censo_agro()`
- **SICAR ContractViolationError** — `data_criacao` nullable=True no contrato (dados reais
  do GeoServer tem nulls legitimos). Dedup por `cod_imovel` mantendo registro com
  `data_atualizacao` mais recente (resolve duplicatas de paginacao WFS)

### Security
- **Snapshots** — proteção contra path traversal em `create_snapshot()`, `load_from_snapshot()`
  e `delete_snapshot()`. Nomes de snapshot validados por regex whitelist + `Path.resolve().is_relative_to()`.
  Previne `shutil.rmtree` em diretórios arbitrários via nomes como `../../..`
- **RateLimiter** — lock `asyncio.Lock()` agora é lazy (criado no primeiro uso, não no import).
  Evita compartilhamento de primitivas asyncio entre event loops diferentes em testes
- **SICAR** — removido `check_hostname=False` e `verify_mode=CERT_NONE` do SSLContext.
  Certificado Sectigo validado (chain completa). `@SECLEVEL=1` mantido para compatibilidade
  de ciphers do GeoServer
- **B3** — removido `verify=False` do client de ajustes. Certificado GTS validado (ECDSA 256)
- **CONAB** — sanitizado URL interpolada em `page.evaluate()` via `json.dumps()` para
  prevenir JS injection no download headless de XLSX
- **B3** — split de flag `_WARNED` em `_WARNED_AJUSTES` e `_WARNED_POSICOES` para que
  cada funcao emita seu proprio warning de licenca independentemente
- **IBGE** — `retriable_exceptions` restrito a exceções de rede (httpx.TimeoutException,
  NetworkError, ConnectionError, TimeoutError). Evita retry infinito em TypeError/KeyError
- **BCB BigQuery** — sanitização de inputs em `_build_query()` via regex whitelist.
  Previne SQL injection em parâmetros `produto`, `safra_ano`, `uf`
- **BCB OData** — escape de aspas simples em `produto_sicor` no filtro OData `contains()`
- **Desmatamento** — validação regex de UF (`^[A-Z]{2}$`) e datas (`^\d{4}-\d{2}-\d{2}$`)
  nos filtros CQL do DETER e PRODES
- **B3** — `except Exception` restrito a `(httpx.HTTPError, SourceUnavailableError, ParseError)`
  em `historico()` e `oi_historico()`. Bugs de programação não são mais engolidos
- **CEPEA** — `except Exception` restrito a exceções de rede/parse em `indicador()` e `ultimo()`.
  Conversão de indicadores restrita a `(KeyError, ValueError, TypeError)`
- **SICAR** — validação regex de `criado_apos` (`^\d{4}-\d{2}-\d{2}$`) no filtro CQL

## [0.11.3] - 2026-02-24

### Added
- **Censo Agropecuario — 6 novos temas de manejo de solo e irrigacao** (#15) — `preparo_solo`,
  `adubacao`, `calagem`, `agrotoxicos`, `praticas_agricolas`, `irrigacao`. Cada tema com dados de
  2006 (tabelas SIDRA 791/1249/1245/1459/837/855) e 2017 (tabelas 6855/6848/6849/6851/8561/6857).
  Total de temas sobe de 4 para 10. Novo parametro `ano` em `censo_agro()` para filtrar por ano
  censal ou buscar ambos (`ano=None` concatena 2006+2017). Tratamento especial para `preparo_solo`
  2017 onde variaveis SIDRA funcionam como categorias (`_VAR_AS_CATEGORIA`). Helper
  `_fetch_censo_single()` extraido para loop multi-ano. Retrocompativel — temas existentes
  continuam funcionando sem `ano`. 86 testes (era 52). Docs: `api/ibge.md`, `sources/ibge.md`,
  `contracts/censo_agropecuario.md` atualizados

## [0.11.2] - 2026-02-22

### Added
- **Cobertura de testes 80% → 84%** — 157 novos testes (3501 → 3658), 462 linhas adicionais cobertas em 15 módulos. Módulos com maior ganho: telemetry/collector (0%→100%), utils/logging (0%→100%), validators/sanity (59%→100%), mapbiomas/client (39%→100%), desmatamento/client (22%→97%), cache/policies (56%→96%), cache/duckdb_store (83%→94%), validators/structural (18%→85%), http/browser (23%→77%), plugins/__init__ (58%→87%), cepea/parsers/consensus (72%→100%), cepea/parsers/detector (92%→100%)

### Fixed
- **CONAB serie_historica**: URL corrigida — `/conab/conab/pt-br/` duplicado removido (BASE_URL ja inclui `/conab`)
- **MapBiomas**: URLs migradas de GCS (`storage.googleapis.com`, 404) para Dataverse (`data.mapbiomas.org/api/access/datafile/`). File IDs: BIOME_STATE=457, BIOME_STATE_MUNICIPALITY=254
- **SICAR**: SSLContext customizado com `@SECLEVEL=1` para contornar TLS handshake failure do `geoserver.car.gov.br` (servidor usa cipher suite legado)
- **ANTT Pedagio**: slugs CKAN atualizados — `fluxo-de-veiculos-nas-pracas-de-pedagio` → `volume-trafego-praca-pedagio`, `cadastro-de-pracas-de-pedagio` → `praca-de-pedagio`. Parser de pracas ajustado para colunas renomeadas (`latitude`/`longitude` → `lat`/`lon`). Parser V2 ajustado para novo layout CSV: `_parse_date_v2` aceita DD/MM/YYYY, `volume_total` como candidate de volume, `tipo_de_veiculo` usado direto quando presente (fallback para `EIXOS_TIPO_MAP`)
- **ANP Diesel**: `vendas_diesel` migrado de XLS pivot table (quebrado) para CSV dados abertos. Fonte: `vendas-oleo-diesel-tipo-m3-2013-2025.csv` — formato long, flat, semicolon-delimited. Removidos helpers `_parse_vendas_wide`/`_parse_vendas_long`/`_is_month_column`

## [0.11.1] - 2026-02-21

### Changed
- **URLs centralizadas em `constants.py`** — 18 clients migrados de URLs hardcoded locais
  (`BASE_URL = "https://..."`) para `URLS[Fonte.XXX]["chave"]` importado de `agrobr.constants`.
  Dominio ou endpoint muda em UM lugar so. Clients afetados: abiove, anda, antaq, bcb, b3,
  comexstat, comtrade, deral, desmatamento, imea, inmet, mapbiomas, nasa_power, queimadas,
  usda, conab/serie_historica, conab/custo_producao, conab/progresso
- **Timeouts centralizados** — 3 clients (anda, inmet, nasa_power) migrados de
  `httpx.Timeout(connect=10.0, read=X, ...)` hardcoded para `HTTPSettings()` com override
  de `read` onde necessario. Todos os 25 clients agora usam `HTTPSettings`
- **Magic numbers substituidos por constantes nomeadas** — 19 thresholds de tamanho minimo
  (`< 50`, `< 100`, `< 500`, `< 1_000`, `< 5_000`) substituidos por `MIN_WFS_SIZE`,
  `MIN_CSV_SIZE`, `MIN_HTML_SIZE`, `MIN_ZIP_SIZE`, `MIN_XLSX_SIZE`, `MIN_HTML_PAGE_SIZE`
  em 16 clients. Ajuste de threshold agora requer edicao em UM lugar so

### Added
- `Fonte.COMTRADE` no StrEnum + URLs (base, auth, guest) + `rate_limit_comtrade` no HTTPSettings
- `URLS[Fonte.B3]["arquivos"]` — endpoint `arquivos.b3.com.br` centralizado
- `URLS[Fonte.DERAL]["downloads"]` — endpoint de downloads centralizado
- 6 constantes de tamanho minimo em `constants.py`: `MIN_WFS_SIZE` (50), `MIN_CSV_SIZE` (100),
  `MIN_HTML_SIZE` (500), `MIN_ZIP_SIZE` (500), `MIN_XLSX_SIZE` (1000), `MIN_HTML_PAGE_SIZE` (5000)

## [0.11.0] - 2026-02-21

### Fixed
- **CEPEA/NA — parser failure em soft block (#14)** — `cepea.indicador("soja")` e
  `datasets.preco_diario("soja")` falhavam com `ParseError` quando Noticias Agricolas
  retornava pagina de consent/challenge (~10KB sem tabela) em vez dos dados (~75KB com
  tabela). Tres mudancas: (1) `FetchResult(html, source)` NamedTuple no client CEPEA
  identifica explicitamente a fonte do HTML ("cepea", "browser", "noticias_agricolas"),
  eliminando deteccao fragil por markers no conteudo (`"noticiasagricolas" in html`);
  (2) `_validate_html_has_data()` no client NA rejeita respostas < 20KB sem `<table`
  (soft block) com `SourceUnavailableError`, ativando cache fallback; (3) roteamento
  no `api.py` usa `FetchResult.source` em vez de inspecionar HTML
- **ANP Diesel — normalizar produto** — `"OLEO DIESEL"` / `"ÓLEO DIESEL S10"` agora
  normalizado para `"DIESEL"` / `"DIESEL S10"` no output. Afeta `parse_precos`,
  `_parse_vendas_wide`, `_parse_vendas_long`. Regex `^[OÓ]LEO\s+` strip no produto.
  Filtro `produto=` tambem normaliza antes de comparar. Schema guarantee atualizada.
- **ANP Diesel — normalizar UF** — Coluna `ESTADO` com nome completo (ex: `"MATO GROSSO"`)
  agora convertida para sigla via `normalizar_uf()`. Fallback `or v.upper()` corrigido
  para `or ""` (antes retornava nome completo se normalizar_uf falhasse). Fix aplicado
  em `parse_precos`, `_parse_vendas_wide`, `_parse_vendas_long`.
- **CONAB Serie Historica — engine Excel** — `parse_serie_historica()` agora detecta
  formato via magic bytes (OLE2 BIFF = xlrd, senao openpyxl). Antes: `pd.ExcelFile()`
  sem engine falhava com `ValueError` para arquivos `.xls` reais da CONAB. Commit
  `38f5112` adicionou xlrd como dep mas nao corrigiu este parser.
- **Queimadas — fallback historico** — `fetch_focos_mensal()` agora tenta em cascata:
  `.csv` mensal (2024+) → `.zip` mensal (2023) → `.zip` anual (2003-2022). Antes:
  HTTP 404 para qualquer mes <2024 sem fallback. INPE migrou CSVs historicos para
  formato ZIP e dados pre-2023 so disponiveis como ZIP anual. Filtro por mes aplicado
  na api quando fonte e anual.

### Added
- **SICAR — Cadastro Ambiental Rural** — Novo namespace `agrobr/alt/sicar/` para dados do
  Cadastro Ambiental Rural (CAR) via GeoServer WFS (OGC 2.0.0, CSV sem geometria, sem auth).
  Funcoes: `sicar.imoveis(uf, municipio, status, tipo, area_min, area_max, criado_apos)` para
  registros individuais de imoveis rurais e `sicar.resumo(uf, municipio)` para estatisticas
  agregadas (total, por status, area, modulos fiscais, por tipo). Pagination transparente
  (resultType=hits + startIndex/count=10000), progressive delay apos pagina 5, timeout 180s.
  CQL_FILTER server-side para municipio (ILIKE), status, tipo, area range, data criacao.
  Contrato `SICAR_IMOVEIS_V1` (11 colunas, PK cod_imovel). Schema JSON, golden data (DF + MT).
  114 novos testes (models, client, parser, api). Sync wrapper via `agrobr.sync.alt.sicar`.
  Docs: `api/sicar.md`, `sources/sicar.md`
- **Dataset semantico `cadastro_rural`** — `datasets.cadastro_rural(uf, municipio, status, tipo,
  area_min, area_max, criado_apos)` na camada semantica. Wraps `sicar.imoveis()` com validacao
  de contrato, return_meta, modo deterministico e fallback pattern. Registrado no registry com
  contrato `SICAR_IMOVEIS_V1`. 10 novos testes.
- **ANTT Pedagio — Fluxo de Veiculos em Pracas de Pedagio** — Novo namespace `agrobr/alt/antt_pedagio/`
  para dados de fluxo de veiculos em pracas de pedagio rodoviario (ANTT Dados Abertos, CC-BY).
  Funcoes: `antt_pedagio.fluxo_pedagio(ano, ano_inicio, ano_fim, uf, apenas_pesados)` para
  trafego mensal com filtros por UF/concessionaria/rodovia/tipo de veiculo e
  `antt_pedagio.pracas_pedagio(uf, rodovia)` para cadastro georreferenciado (200+ pracas).
  CSV bulk 2010-2025 (16 arquivos), schema V1 (2010-2023) com categorias texto e V2 (2024+)
  com eixos numerico, encoding Windows-1252 com fallback automatico, join com cadastro de
  pracas para enriquecimento geografico (rodovia, UF, municipio).
  Contratos `ANTT_PEDAGIO_FLUXO_V1` (10 colunas) e `ANTT_PEDAGIO_PRACAS_V1` (9 colunas).
  Schemas JSON, golden data. 117 novos testes (models, client, parser, api). Sync wrapper
  via `agrobr.sync.alt.antt_pedagio`. Docs: `api/antt_pedagio.md`, `sources/antt_pedagio.md`
- **MAPA PSR — Seguro Rural** — Novo namespace `agrobr/alt/mapa_psr/` para dados de
  apolices e sinistros do seguro rural brasileiro (SISSER/MAPA, CC-BY). Funcoes:
  `mapa_psr.sinistros(cultura, uf, ano, evento)` para indenizacoes pagas e
  `mapa_psr.apolices(cultura, uf, ano)` para todas as apolices com subvencao federal.
  CSV bulk 2006+ (3 periodos), encoding auto-detect, PII removido automaticamente.
  Contratos `MAPA_PSR_SINISTROS_V1` (17 colunas) e `MAPA_PSR_APOLICES_V1` (18 colunas).
  Schemas JSON, golden data. 104 novos testes (models, client, parser, api). Sync wrapper
  via `agrobr.sync.alt.mapa_psr`. Docs: `api/mapa_psr.md`, `sources/mapa_psr.md`
- **ANP Diesel — Precos + Volumes** — Novo namespace `agrobr/alt/anp_diesel/` para dados de
  precos de revenda e volumes de venda de diesel da ANP. Funcoes:
  `anp_diesel.precos_diesel(uf, municipio, produto, nivel, agregacao)` para precos
  semanais/mensais por municipio/UF/Brasil e `anp_diesel.vendas_diesel(uf)` para volumes
  mensais por UF. XLSX bulk 2013+ (openpyxl), cache por periodo do arquivo.
  Contratos `ANP_DIESEL_PRECOS_V1` (8 colunas) e `ANP_DIESEL_VENDAS_V1` (5 colunas).
  Schemas JSON, golden data. 103 novos testes (models, client, parser, api). Sync wrapper
  via `agrobr.sync.alt.anp_diesel`. Docs: `api/anp_diesel.md`, `sources/anp_diesel.md`
- **UN Comtrade — Trade Mirror** — Novo modulo `comtrade/` para dados de comercio
  internacional bilateral via UN Comtrade API. Funcoes: `comtrade.comercio()` (dados
  bilaterais por HS code/pais/periodo) e `comtrade.trade_mirror()` (compara exportacoes
  do reporter vs importacoes do parceiro, calcula discrepancias peso/valor/ratio).
  Guest mode (sem API key) + `AGROBR_COMTRADE_API_KEY` para rate limit maior.
  Chunking automatico para periodos > 12 meses. 17 produtos agro mapeados por HS code.
  Contratos `COMERCIO_BILATERAL_V1` e `TRADE_MIRROR_V1`. Golden data (comercio + mirror).
  70 novos testes. Sync wrapper. Docs: `api/comtrade.md`, `sources/comtrade.md`
- **ANTAQ — Movimentacao Portuaria** — Novo modulo `antaq/` para dados de movimentacao
  portuaria de carga do Estatistico Aquaviario (ANTAQ). Funcao `antaq.movimentacao(ano)`
  baixa ZIP bulk anual (~80MB), extrai e faz join de 3 tabelas (Atracacao + Carga + Mercadoria).
  Filtros: tipo_navegacao, natureza_carga, mercadoria, porto, uf, sentido.
  Encoding UTF-8-sig, separador `;`, decimal brasileiro (`,`). Historico desde 2010.
  Contrato `MOVIMENTACAO_PORTUARIA_V1` com 21 colunas. Schema JSON, golden data.
  72 novos testes (client, parser, models, api). Sync wrapper. Docs: `sources/antaq.md`
- **B3 Posicoes em Aberto (Open Interest)** — Novas funcoes `b3.posicoes_abertas()` e
  `b3.oi_historico()` para dados de open interest diario de futuros e opcoes agro
  (BGI, CCM, ETH, ICF, SJC). CSV publico via `arquivos.b3.com.br` (2-step: token + download).
  Parser filtra segmento AGRIBUSINESS, classifica futuro/opcao, enriquece com descricao e unidade.
  Contrato `POSICOES_ABERTAS_V1` com PK `[data, ticker_completo]`, 11 colunas. Schema JSON,
  golden data (518 linhas agro, 2025-12-19), 61 novos testes. Docs: `api/b3.md`, `sources/b3.md`
  atualizados
- **BCB/SICOR dimensoes ocultas** — Expoe 5 dimensoes que a API retorna mas eram ignoradas:
  programa, fonte de recurso, tipo de seguro, modalidade e atividade. Cada dimensao gera
  duas colunas: codigo (`cd_programa`) e nome legivel (`programa`). Dicionarios hardcoded
  com fallback `"Desconhecido ({code})"` + log warning para codigos novos. Enriquecimento
  no parser (PARSER_VERSION=2). Novos parametros `programa` e `tipo_seguro` para filtro
  client-side. Nova agregacao `agregacao="programa"`. Contract v1.1 com 11 novas colunas
  nullable (nao quebra consumidores v1.0). Schema JSON regenerado. 87 novos testes
  (models, parser, api). Suite: 2778 passed, 0 failed

### Changed
- `credito_rural` contract bump v1.0 → v1.1 (minor — novas colunas nullable)
- `PARSER_VERSION` bump 1 → 2 (novas colunas + enriquecimento)
- Golden data `custeio_sample/expected.json` atualizado com 20 colunas (era 15)

## [0.10.1] - 2026-02-16

### Fixed
- **DuckDB thread-safety** — `DuckDBStore` agora usa `threading.Lock` em todos os
  métodos que acessam a conexão. `get_store()` usa double-checked locking. Corrige
  segfault/deadlock quando múltiplas threads compartilham o singleton (ex: MCP server
  despachando requests para threads diferentes)
- **Parser NA semanal** — `_parse_date` aceita formato semanal `'09 - 13/02/2026'`
  (média CEPEA semanal). Registros semanais marcados com `anomalies=["media_semanal"]`
  e `meta["tipo"]="media_semanal"`. Antes: linhas ignoradas com warning
  `parse_row_failed`
- **ANDA ano errado** — `fetch_entregas_pdf` agora retorna `tuple[bytes, int]` com
  `ano_real` extraído do texto do link (não da URL de upload que contém o ano do
  upload, não dos dados). Corrige parser buscando header "2026" em PDF de dados 2025

### Changed
- `integration_tests.yml` — timeout global adicionado
- `pyproject.toml` — `pytest-timeout` adicionado como dependência de teste
- 3 testes de thread-safety no DuckDB store (`test_threaded_reads`,
  `test_threaded_writes`, `test_threaded_indicadores` — 5 threads × 10-20 ops cada)
- Suite: 2719 passed, 0 failed (era 2660+)

## [0.10.0] - 2026-02-15

### Added
- **CONAB CEASA/PROHORT (Precos de Atacado Hortifruti)** — Nova fonte: precos diarios de atacado
  de 48 produtos (20 frutas, 28 hortalicas) em 43 CEASAs do Brasil. Modulo `agrobr/conab/ceasa/`
  com client (Pentaho CDA REST API, JSON), parser (pivot 48x43 -> long-form, datas por header,
  mapeamento posicional CEASAs), models (48 produtos, 43 CEASAs, UF map, categorias).
  API publica `conab.ceasa_precos()` com filtros por produto/ceasa, `conab.ceasa_produtos()`,
  `conab.lista_ceasas()`, `conab.ceasa_categorias()`. Contrato `PRECO_ATACADO_V1` com
  PK `[data, produto, ceasa]`. Schema JSON, golden data (Pentaho real), 70 testes. Warning
  zona_cinza na primeira chamada. Docs: `sources/conab.md`, licenses atualizado
- **B3 Futuros Agro** — Nova fonte: ajustes diarios de futuros agricolas (boi gordo, milho,
  cafe arabica, cafe conillon, etanol, soja cross, soja FOB). Modulo `agrobr/b3/` com client
  (HTML parse de `www2.bmf.com.br`, encoding iso-8859-1), parser (tabela `tblDadosAjustes`,
  carry-forward de ticker, numeros BR), models (7 contratos, month codes, unidades).
  API publica `b3.ajustes()` com filtro por contrato, `b3.historico()` para serie temporal,
  `b3.contratos()`. Contrato `AJUSTE_DIARIO_V1` com PK `[data, ticker, vencimento_codigo]`.
  Schema JSON, golden data (dia util + weekend), 71 testes. Warning zona_cinza na primeira
  chamada. Sync wrapper. Docs: `api/b3.md`, `sources/b3.md`, licenses atualizado
- **IBGE Censo Agropecuário (Censo Agro 2017)** — Nova pesquisa no módulo IBGE:
  4 temas (efetivo_rebanho, uso_terra, lavoura_temporaria, lavoura_permanente) via tabelas
  SIDRA 6907/6881/6957/6956. API pública `ibge.censo_agro()` com filtros por tema/UF/nível
  e `ibge.temas_censo_agro()`. Dataset `censo_agropecuario` com contrato `ibge.censo_agro v1.0`,
  schema JSON, golden data. Long format (variável/valor por linha). Cache 30 dias.
  52 testes. Docs: `api/ibge.md`, `sources/ibge.md`, `contracts/censo_agropecuario.md`, licenses
  atualizado
- **IBGE Abate Trimestral**: abate bovino, suíno e frango por UF desde 1997 — 54 testes, contrato, golden data
- **IBGE PPM — Pesquisa da Pecuária Municipal (roadmap 2.8)** — Nova pesquisa no módulo IBGE:
  efetivo de rebanhos (10 espécies, tabela SIDRA 3939) e produção de origem animal (6 produtos,
  tabela 74). API pública `ibge.ppm()` com filtros por espécie/ano/UF/nível e `ibge.especies_ppm()`.
  Dataset `pecuaria_municipal` com contrato `IBGE_PPM_V1`, schema JSON, golden data. Cache 7 dias.
  60 testes. Docs: `api/ibge.md`, `sources/ibge.md`, `contracts/pecuaria_municipal.md`, licenses
  atualizado
- **CONAB Progresso de Safra (roadmap 2.0.5)** — Nova fonte: progresso semanal de plantio
  e colheita por cultura x UF. Modulo `agrobr/conab/progresso/` com client (Plone CMS
  pagination, XLSX download via sub-links), parser (block-based state machine para XLSX
  com blocos repetidos por cultura/operacao), models (6 culturas, 27 UFs, normalizacao
  estado→UF). API publica `conab.progresso_safra()` com filtros por cultura/estado/operacao
  e `conab.semanas_disponiveis()` para listar semanas. Contrato `CONAB_PROGRESSO_V1` com
  PK `[cultura, safra, operacao, estado, semana_atual]`. Golden data, 67 testes. Docs:
  `api/conab_progresso.md`, `sources/conab_progresso.md`, licenses atualizado
- **MapBiomas (roadmap 2.7)** — Nova fonte: cobertura e uso da terra por municipio/ano
  (1985-presente). Modulo `agrobr/mapbiomas/` com client (download XLSX do Google Cloud
  Storage), parser (multi-sheet com classes de cobertura MapBiomas Collection 9), models
  (classes de cobertura, biomas, transicoes). API publica `mapbiomas.cobertura()` com
  filtros por municipio/UF/bioma/classe/ano e `mapbiomas.transicao()`. Contrato
  `MAPBIOMAS_COBERTURA_V1`. Golden data, 66 testes. Docs: `api/mapbiomas.md`,
  `sources/mapbiomas.md`, licenses atualizado
- **Desmatamento PRODES/DETER (roadmap 2.2)** — Nova fonte: dados de desmatamento via
  TerraBrasilis GeoServer (WFS). Modulo `agrobr/desmatamento/` com client (WFS+CSV, CQL_FILTER
  por UF/ano/data), parser (PRODES anual + DETER alertas), models (workspaces por bioma,
  classes DETER, mapeamento UF/estado). API publica `desmatamento.prodes()` (5 biomas: Cerrado,
  Caatinga, Mata Atlantica, Pantanal, Pampa) e `desmatamento.deter()` (Amazonia, Cerrado)
  com filtros por bioma/UF/ano/classe e suporte a `return_meta`. Contratos
  `DESMATAMENTO_PRODES_V1` e `DESMATAMENTO_DETER_V1`. Schemas JSON, golden data (PRODES 10
  registros x 9 UFs, DETER 10 registros x 5 UFs x 4 classes), 56 testes. Export em
  `__init__.py` e sync wrapper. Docs: `api/desmatamento.md`, `sources/desmatamento.md`,
  licenses atualizado
- **Queimadas/INPE (roadmap 2.1)** — Nova fonte: focos de calor detectados por satelite via
  BDQueimadas/INPE. Modulo `agrobr/queimadas/` com client (CSV diario/mensal), parser
  (UTF-8 + latin-1 fallback), models (6 biomas, 27 UFs, 13 satelites), API publica
  `queimadas.focos()` com filtros por UF/bioma/satelite e suporte a `return_meta`.
  Contrato `FOCOS_QUEIMADAS_V1` com PK `[data, lat, lon, satelite, hora_gmt]`.
  Schema JSON, golden data (8 registros x 6 biomas), 43 testes. Export em `__init__.py`
  e sync wrapper. Docs: `api/queimadas.md`, `sources/queimadas.md`, licenses atualizado
- **Schemas JSON formais (roadmap 1.2)** — Contratos Python agora geram schemas JSON em
  `agrobr/schemas/`. 8 contratos com primary_key, min/max constraints, validação automática
  via `_validate_contract()` em todos os 8 datasets. Novos contratos: `credito_rural`,
  `exportacao`, `fertilizante`, `custo_producao`. Registry centralizado com
  `register_contract()` / `get_contract()` / `validate_dataset()`. 60 testes dedicados.
  `Contract.to_json()` / `from_json()` para serialização roundtrip
- **Normalização transversal (roadmap 1.3)** — Dois novos módulos em `agrobr/normalize/`:
  - `municipalities.py` — Mapeamento nome→código IBGE para 5571 municípios brasileiros.
    Busca accent/case insensitive. `municipio_para_ibge()`, `ibge_para_municipio()`,
    `buscar_municipios()`. Dados da API IBGE Localidades (livre para uso)
  - `crops.py` — Dicionário unificado de 140+ variantes→35 culturas canônicas.
    `normalizar_cultura()` resolve "SOJA", "soja em grão", "soybean" → "soja".
    `listar_culturas()`, `is_cultura_valida()`. Substitui aliases dispersos
  - 464 testes novos (100 municípios x 3 variações + culturas). Total suite: 2128 testes
- **Politica de versionamento datasets (roadmap 1.4)** — `docs/contracts/semver.md` expandido
  com tabela detalhada de bump rules (major/minor/patch), principio de `schema_version`
  independente de `lib_version`, criterios de breaking change para datasets
- **Metadados no registry (roadmap 1.9)** — `DatasetInfo` expandido com `source_url`,
  `source_institution`, `min_date`, `unit`, `license`. 8 datasets preenchidos com metadados
  reais (instituição, URL, licença, data mínima, unidade). Registry ganha
  `describe(name)` e `describe_all()` para exibição formatada
- **Testes de integracao formalizados (roadmap 1.8)** — Distinção clara entre unit/golden
  (todo push), integration (cron semanal) e benchmark (manual). Markers `@pytest.mark.integration`
  e `@pytest.mark.benchmark` registrados em `pyproject.toml`. CI padrao exclui ambos:
  `pytest -m "not integration and not benchmark"`
- **CI health check semanal (roadmap 1.5)** — `.github/workflows/integration_tests.yml`:
  cron segunda 08:00 UTC, `pytest -m integration --tb=short --timeout=120`, issue automatica
  com label `source-changed` em caso de falha, alertas Discord/Slack, artefato de resultados
  (30 dias). Nao bloqueia release — apenas alerta
- **Cobertura CLI/alerts/health** — 107 testes novos: `test_cli.py` (51), `test_alerts/test_notifier.py` (17),
  `test_health/test_checker.py` (15), `test_health/test_reporter.py` (24). Total suite: 1640 testes. Closes #11
- **Golden tests com dados reais** para 5 fontes: BCB, IBGE, ComexStat, DERAL, ABIOVE
  (substituindo dados sintéticos). Script `scripts/update_golden.py` expandido com
  captura automatizada para 6 fontes (5 novas + CEPEA existente). Closes #10
- **Audit de licenças** — `docs/licenses.md` com tabela completa das 13 fontes,
  classificação (`livre`, `nc`, `zona_cinza`, `restrito`) e URLs dos termos
- **Aviso CC BY-NC 4.0** no módulo CEPEA (docstrings em `__init__.py` e `api.py`)
  e na documentação (`docs/sources/cepea.md`)
- **Avisos de licença** nos módulos IMEA (`restrito`), Notícias Agrícolas
  (`restrito`, deprecação pendente), ANDA e ABIOVE (`zona_cinza`, autorização
  solicitada fev/2026)
- **Runtime warnings** — `warnings.warn()` no primeiro uso de IMEA e Notícias
  Agrícolas alertando sobre restrições de redistribuição
- **Warning box no README** apontando para `docs/licenses.md`
- **Cache key versionada** — `build_cache_key()` em `agrobr/cache/keys.py`:
  formato `{dataset}|{params_hash}|v{lib_version}|sv{schema_version}`,
  garante invalidação automática entre versões da lib e mudanças de schema
- **Cache versionado completo** — migração automática de keys legacy para formato
  versionado (`legacy_cache_migrated`), strict mode via `AGROBR_CACHE_STRICT=1`
  (rejeita cache de versão divergente), `parse_cache_key()` / `is_legacy_key()`
  / `legacy_key_prefix()` em `cache/keys.py`. 16 testes novos (migração, strict,
  concorrência 3 threads)
- **HTTP settings centralizados** — `agrobr/http/settings.py` com `get_timeout()`,
  `get_rate_limit()`, `get_client_kwargs()`. `rate_limit_default` (1 req/s) no
  `HTTPSettings`. Env vars `AGROBR_HTTP_TIMEOUT_*` e `AGROBR_HTTP_RATE_LIMIT_*`
  configuram tudo. 14 testes novos

### Fixed
- **Pydantic `class Config` → `model_config`** — 4 Settings classes em `constants.py`
  migradas de `class Config` (deprecated) para `model_config = SettingsConfigDict(...)`.
  Elimina 4 `PydanticDeprecatedSince20` warnings em toda importação do agrobr
- **MapBiomas sync wrapper** — `_SyncMapBiomas` adicionado ao `sync.py`. Antes:
  `from agrobr.sync import mapbiomas` lançava `ImportError`
- **Warnings zona_cinza ANDA/ABIOVE** — `_WARNED` + `warnings.warn()` adicionados
  em `anda/api.py` e `abiove/api.py` (padrão já existente em B3, CEASA, IMEA, NA)
- **Schemas JSON desatualizados** — `generate_json_schemas()` regenerou 19 schemas
  (3 novos: mapbiomas_cobertura, mapbiomas_transicao, conab_progresso; 16 atualizados)
- **Pre-commit limpo** — SIM117 (nested `with` combinados), mypy `untyped-decorator`
  no cli.py, erros pré-existentes em `scripts/` e `examples/` corrigidos (27 erros mypy)
- **Parser ABIOVE** — suporte a formato single-sheet multi-seção (meses na coluna 1,
  seções por produto: grão, farelo, óleo, milho, total). Layout novo de 2024/2025.
- **Parser DERAL** — suporte a formato multi-produto por sheet (sheets nomeadas por
  data: "Atual", "Anterior", "10-02-2025"). Layout atual do PC.xls com tabela
  Condição/Fase por cultura em cada sheet.
- **7 clients legados migrados para `retry_on_status()`** — deral, imea, usda,
  abiove, bcb, comexstat, anda. ~445 linhas de retry duplicado removidas.
  Timeout/ConnectError propagam imediatamente (sem retry).
- **`indicadores_upsert` 7x mais rápido** — temp table + INSERT SELECT
  substitui INSERT row-by-row. 10k: 34s→4.8s, 50k: 187s→25.9s.
  Scaling agora linear (ratio 50k/10k ≈ 5.4x).

### Changed
- Retry loops dos 7 clients restantes migrados para `http/retry.py` centralizado
  (todos 13 clients agora usam `retry_on_status()`)
- `indicadores_upsert` usa chunks de 5000 via temp table `_ind_staging`
  com fallback row-by-row para isolamento de erros

## [0.9.0] - 2026-02-11

### Added
- **1529 testes** (era 949), cobertura **~75%** (era 57.5%) — atualizado para 1640 no Unreleased
- **Golden tests** para todas as 13 fontes de dados (era 2/13)
- **Benchmark de escalabilidade** — memory, volume, cache, async, rate limiting, sync, golden
- **Suporte a token INMET** — `AGROBR_INMET_TOKEN` via env var
- `retry_on_status()` e `retry_async()` centralizados em `http/retry.py`
- **Retry-After header** respeitado em respostas HTTP 429
- **Testes de resiliência HTTP** para todos os 13 clients (timeout, 429, 500, 403, resposta vazia)
- **Testes de API pública**: `cepea.indicador()`/`ultimo()`, `conab.safras()`/`balanco()`/`brasil_total()`/`levantamentos()`
- Pre-commit hooks atualizados (ruff v0.15, mypy v1.19)

### Fixed
- **Cache DuckDB** — `history_entries.id` sem autoincrement: histórico permanente nunca salvava dados
- **normalize/dates** — `normalizar_safra()` não fazia strip no input
- **6 clients sem retry para HTTP 429**: inmet, nasa_power, conab_custo, conab_serie, conab main, ibge
- **Graceful degradation silenciosa** trocada por `SourceUnavailableError` quando retry esgota
- **except Exception genérico** em `duckdb_store.py` restringido para exceções específicas
- **INMET** — endpoint `/estacao/dados/` atualizado para `/estacao/` (API mudou)
- **INMET** — tratamento de HTTP 204 (No Content) retorna DataFrame vazio

### Changed
- Retry loops de 5 clients migrados para `http/retry.py` centralizado
- Testes de datasets refatorados: 98 funções duplicadas → 27 parametrizadas (115 cenários)
- mypy override para `tests.*` (`ignore_errors = true`, strict mantido no core)

### Known Issues
- 4 golden tests com dados sintéticos (INMET, USDA, NA, ANDA) — `needs_real_data`
  (BCB, IBGE, ComexStat, DERAL, ABIOVE migrados para dados reais na issue #10)
- ~~DuckDB 1.4.4 incompatível com coverage no Python 3.14~~ (resolvido: bump 1.5.0 + workaround conftest.py)

## [0.8.0] - 2026-02-09

### Added
- **ABIOVE** (`agrobr.abiove`) — Exportação do complexo soja
  - `abiove.exportacao()` — Volume e receita mensal de grão, farelo, óleo e milho
  - Parser Excel com detecção dinâmica de header
- **USDA PSD** (`agrobr.usda`) — Estimativas internacionais de oferta/demanda
  - `usda.psd()` — Dados PSD por commodity/país/ano via API FAS OpenData v2
  - Suporte a pivot, filtro por atributos, mapeamento PT-BR
  - Requer API key gratuita (api.data.gov)
- **IMEA** (`agrobr.imea`) — Cotações e indicadores Mato Grosso
  - `imea.cotacoes()` — Preços, progresso de safra, comercialização (6 cadeias)
  - API REST pública (api1.imea.com.br), sem autenticação
- **DERAL** (`agrobr.deral`) — Condição das lavouras Paraná
  - `deral.condicao_lavouras()` — Condição semanal (boa/média/ruim) + progresso plantio/colheita
  - Parser Excel (PC.xls) com detecção dinâmica de abas e produtos
- **CONAB série histórica** (`agrobr.conab.serie_historica`) — Sub-módulo de safras 2010+
  - `conab.serie_historica()` — Série histórica de safras por UF com filtros
  - Parser Excel com detecção dinâmica de header row
- **BCB BigQuery fallback** — `pip install agrobr[bigquery]`
  - Base dos Dados como fallback quando API OData retorna 500
  - `asyncio.to_thread()` para wrapping do SDK síncrono
- **5 novos datasets semânticos** (camada semântica):
  - `datasets.credito_rural()` — BCB/SICOR com fallback BigQuery
  - `datasets.exportacao()` — ComexStat → ABIOVE (fallback automático)
  - `datasets.fertilizante()` — ANDA (entregas por UF)
  - `datasets.custo_producao()` — CONAB custos de produção
  - Total: 8 datasets (era 4)
- 949 testes passando (era ~804)

### Fixed
- **BCB/SICOR** — Endpoints atualizados para API reestruturada (~2024)
  - `CusteioMunicipio` → `CusteioRegiaoUFProduto`
  - `InvestimentoMunicipio` → `InvestRegiaoUFProduto`
  - `ComercializacaoMunicipio` → `ComercRegiaoUFProduto`
  - `industrializacao` removida (sem endpoint equivalente)
- **BCB parser** — `COLUNAS_MAP` expandido para colunas da API nova (`VlCusteio`→`valor`, `nomeUF`→`uf`, `AreaCusteio`→`area_financiada`, etc.)
- **BCB parser** — Limpeza de aspas embarcadas em `nomeProduto` (`"\"SOJA\""` → `soja`)

### Changed
- **BCB client** — Server-side filter via `contains()` (unico operador suportado pelo Olinda v2); filtragem por ano/UF client-side
- **BCB client** — `MAX_RETRIES` 4→6, `timeout.read` 60→120s, `User-Agent` header adicionado
- **13 fontes** integradas (era 8): +ABIOVE, +USDA PSD, +IMEA, +DERAL, +Notícias Agrícolas
- `agrobr/constants.py` — Fonte enum +4, URLS +4, CacheSettings +4 TTLs, HTTPSettings +4 rate limits
- `agrobr/sync.py` — 4 novas classes _SyncModule (abiove, deral, imea, usda)
- `agrobr/http/rate_limiter.py` — 4 novas entradas no delays dict

## [0.7.1] - 2026-02-07

### Added
- **NASA POWER** (`agrobr.nasa_power`) — Dados climaticos globais como substituto do INMET
  - `nasa_power.clima_ponto()` — Dados diarios/mensais por coordenada (lat/lon)
  - `nasa_power.clima_uf()` — Dados climaticos por UF (ponto central)
  - 7 parametros agroclimaticos: temp (media/max/min), precipitacao, umidade, radiacao, vento
  - API REST pura (NASA LaRC), sem autenticacao, cobertura global desde 1981
  - Chunking automatico para periodos > 365 dias
  - 34 testes unitarios (models, parser, api)
- **NASAPowerCollector** no agrobr-collector (substitui INMETCollector)
- **Alertas automaticos** — health_check.yml e structure_monitor.yml enviam alertas Discord/Slack quando fontes degradam
- **Health checks reais** — CONAB (HTTP HEAD), IBGE (SIDRA API query com validacao de dados)
- **NASA POWER cache policy** dedicada (TTL 7d, stale 30d) em `policies.py`
- **Notebook demo** (`examples/agrobr_demo.ipynb`) — 14 secoes cobrindo todas as fontes, MetaInfo, fallback, cache, pipeline com graficos e modo async
- **Landing page** atualizada — text-shadow para legibilidade, copyright 2026, icone monocromatico, botao Colab no CTA

### Changed
- INMET desabilitado no collector (config.yaml `enabled: false`) — API dados retornando 404
- Docs atualizados: INMET referencia NASA POWER como alternativa
- `docs/index.md` atualizado com 8 fontes (era 3), NASA POWER no uso rapido
- `alert_on_anomaly` habilitado por padrao em `constants.py`
- `CacheSettings.ttl_nasa_power` corrigido de 24h para 7d (consistente com `policies.py`)
- `SOURCE_POLICY_MAP` corrigido: NASA_POWER aponta para `"nasa_power"` (era `"bcb"`)

### Fixed
- **sync.py** — `_SyncNasaPower` adicionado (nasa_power nao funcionava no modo sincrono)
- **Notebook cell 17** — PAM defensivo: detecta `"producao"` ou `"Quantidade produzida"` (SIDRA rename)
- **README** — Colab badge corrigido de `demo_colab.ipynb` para `agrobr_demo.ipynb`
- **cepea/client.py** — Variavel nao usada `produto_key` removida (ruff lint)

## [0.7.0] - 2026-02-07

### Added
- **INMET** (`agrobr.inmet`) — Dados meteorologicos de 600+ estacoes automaticas
  - `inmet.estacoes()` — Listar estacoes por tipo e UF
  - `inmet.estacao()` — Dados horarios/diarios de uma estacao
  - `inmet.clima_uf()` — Clima mensal agregado por UF
- **BCB/SICOR** (`agrobr.bcb`) — Credito rural por municipio e cultura
  - `bcb.credito_rural()` — Dados de credito de custeio por safra
- **ComexStat** (`agrobr.comexstat`) — Exportacoes brasileiras por NCM
  - `comexstat.exportacao()` — Exportacoes mensais com 19 produtos mapeados
  - Filtro por NCM usa prefix match (subposicoes capturadas automaticamente)
- **ANDA** (`agrobr.anda`) — Entregas de fertilizantes por UF/mes
  - `anda.entregas()` — Dados de entregas de fertilizantes
  - Parser suporta multiplas orientacoes de tabela PDF + layout "Principais Indicadores"
  - Requer `pip install agrobr[pdf]` (pdfplumber)
- **CONAB custo_producao** (`agrobr.conab.custo_producao`) — Custos de producao por hectare
  - `conab.custo_producao()` — Dados detalhados de custo por cultura/UF/safra
  - `conab.custo_producao_total()` — Totais COE/COT/CT

### Fixed
- **ComexStat**: NCM algodao corrigido de `52010000` (inexistente) para prefixo `520100` (captura `52010020` + `52010090`)
- **ComexStat**: `verify=False` no httpx para contornar certificado SSL invalido do `balanca.economia.gov.br`
- **ComexStat**: Filtro NCM no parser mudou de match exato (`==`) para prefix match (`str.startswith()`)
- **ANDA**: URL atualizada de `/estatisticas/` para `/recursos/` (reorganizacao do site)
- **ANDA**: Parser expandido com `_expand_newline_cells()` e `_parse_indicadores()` para PDFs com meses/valores concatenados
- **INMET**: User-Agent header adicionado ao client HTTP (previne 403 Forbidden)
- **custo_producao**: URLs migradas de `conab.gov.br` para `gov.br/conab/` com scraping multi-tab (3 abas de planilhas)
- **custo_producao**: `parse_links_from_html()` reescrito com BeautifulSoup + dedup de URLs

### Known Issues
- **INMET**: API de dados (`/estacao/dados/`) retornando 404 em todos endpoints — API fora do ar externamente
- **BCB/SICOR**: API OData retornando 503 Service Unavailable — indisponibilidade temporaria
- **custo_producao**: Graos (soja, milho, cafe, algodao) nao disponiveis como xlsx no gov.br — conteudo carregado via JavaScript dinamico

## [0.6.3] - 2026-02-06

### Fixed
- `__version__` atualizado para `0.6.3` (estava travado em `0.6.0` desde o v0.6.0)
- `.gitignore` corrompido — linhas garbled reescritas, adicionados roadmap v4 e insights
- README: parâmetro inexistente `periodo=` corrigido para `inicio=` na API CEPEA
- README: `cepea.produtos()` agora com `await` (função é async)
- `ruff>=0.14.0` corrigido para `ruff>=0.4.0` (versão 0.14 não existe)
- `site_url` corrigido no mkdocs.yml e pyproject.toml (era `agrobr.dev`, agora aponta para GitHub Pages)
- Testes CEPEA API marcados como `@pytest.mark.integration` (chamavam API real sem mock)

### Changed
- `playwright` movido de dependência core para extra `[browser]` (~50MB a menos no install padrão)
- Notícias Agrícolas client reescrito — Playwright removido, agora usa httpx puro (página é server-side rendered, não precisa de JS)
- `docs/sources/` (4 páginas órfãs) adicionadas ao nav do mkdocs.yml
- `docs/index.md` reescrito — agora reflete estado atual do projeto (datasets, 20 indicadores, features v0.6)
- Documentação atualizada: 20 produtos CEPEA, LSPA aliases, algodão cBRL/lb, troubleshooting sem Playwright
- Arquivo `nul` (artefato Windows) removido do repositório

## [0.6.2] - 2026-02-05

### Fixed
- URLs do Notícias Agrícolas corrigidas para milho, boi, café, algodão e trigo (retornavam 404)
- Unidade do algodão corrigida de `BRL/@` para `cBRL/lb` (centavos de real por libra-peso)
- Parser trigo ajustado para tabela com 4 colunas (Data, Região, R$/t, Variação)
- `wait_for_selector("table.cot-fisicas")` substituído por `wait_for_selector("table td")` — classe CSS não existe mais no site
- IBGE LSPA aceita nomes genéricos de produto (`milho` → `milho_1` + `milho_2`, `feijao` → `feijao_1` + `feijao_2` + `feijao_3`)
- Playwright cleanup no Windows — `atexit` handler evita `ValueError: I/O operation on closed pipe`
- Circuit breaker no CEPEA httpx — pula tentativa direta (403 Cloudflare) por 10min após primeira falha, eliminando ~2s de latência

### Added
- 11 novos produtos CEPEA via Notícias Agrícolas: arroz, açúcar cristal, açúcar refinado, etanol hidratado, etanol anidro, frango congelado, frango resfriado, suíno, leite, laranja indústria, laranja in natura
- Total de 20 indicadores CEPEA/ESALQ disponíveis via fallback Notícias Agrícolas
- Parser v2 com suporte a tabelas multi-região (trigo: Paraná + RS)
- Aliases LSPA: `milho`, `feijao`, `amendoim`, `batata` expandem para sub-safras automaticamente

## [0.6.1] - 2026-02-05

### Fixed
- Playwright graceful degradation — import com try/except, não crasha em Python 3.14+
- Parser Notícias Agrícolas levanta `ParseError` ao invés de retornar lista vazia silenciosamente
- Cache fallback automático com `StaleDataWarning` quando todas as fontes falham

## [0.6.0] - 2026-02-05

### Added
- **Camada Semântica** - 4 datasets padronizados com fallback automático entre fontes
  - `datasets.preco_diario()` - Preços diários (CEPEA → cache)
  - `datasets.producao_anual()` - Produção anual (IBGE PAM → CONAB)
  - `datasets.estimativa_safra()` - Estimativas safra corrente (CONAB → IBGE LSPA)
  - `datasets.balanco()` - Balanço oferta/demanda (CONAB)
  - `datasets.list_datasets()` / `datasets.list_products()` / `datasets.info()`
- **Contratos Públicos** - Garantias formais de schema versionado
  - Documentação em `docs/contracts/` para cada dataset
  - Colunas estáveis, tipos só alargam, breaking changes só em major
- **Modo Determinístico Aprimorado** - Context manager async com contextvars
  - `async with datasets.deterministic("2025-12-31"):` - Isolado por task
  - `@deterministic_decorator("2025-12-31")` - Decorator para funções
  - `is_deterministic()` / `get_snapshot()` - Verificar estado atual
- **Hierarquia de Exceções Expandida**
  - `NetworkError` - Erros de rede (timeout, HTTP error, DNS)
  - `ContractViolationError` - DataFrame não atende contrato do dataset
- **MetaInfo Expandido** - Novos campos de proveniência
  - `dataset` - Nome do dataset
  - `contract_version` - Versão do contrato
  - `snapshot` - Data de corte (modo determinístico)
- **Documentação Avançada**
  - `docs/advanced/reproducibility.md` - Guia de reprodutibilidade
  - `docs/advanced/pipelines.md` - Integração Airflow, Prefect, Dagster
- **Notebook Demo** - Google Colab com exemplos executáveis

### Changed
- `agrobr.sync.datasets` - API síncrona para datasets
- README atualizado com seção de datasets e status das fontes

## [0.5.0] - 2026-02-04

### Added
- **Plugin System** - Arquitetura extensível para fontes e validadores
  - `SourcePlugin` - Interface para novas fontes de dados
  - `ParserPlugin` - Interface para parsers customizados
  - `ExporterPlugin` - Interface para exportadores customizados
  - `ValidatorPlugin` - Interface para validadores customizados
  - `register()`, `get_plugin()`, `list_plugins()` - Gerenciamento de plugins
- **API Stability Decorators** - Marcadores de estabilidade de API
  - `@stable(since="x.y.z")` - Marca API como estável
  - `@experimental(since="x.y.z")` - Marca API como experimental
  - `@deprecated(since, removed_in, replacement)` - Marca API como deprecated
  - `@internal` - Marca API como interna (não pública)
  - `list_stable_apis()`, `list_experimental_apis()`, `list_deprecated_apis()`
- **SLA Documentado** - Contratos de nível de serviço por fonte
  - `SourceSLA` - Definição de SLA com tier, freshness, latency, availability
  - `CEPEA_SLA` - Tier CRITICAL, atualização diária 18h, 99% uptime
  - `CONAB_SLA` - Tier STANDARD, atualização mensal, 98% uptime
  - `IBGE_SLA` - Tier STANDARD, varia por pesquisa
  - `get_sla()`, `list_slas()`, `get_sla_summary()`
- **Certificação de Qualidade** - Sistema de certificação de dados
  - `QualityLevel` - GOLD, SILVER, BRONZE, UNCERTIFIED
  - `QualityCheck` - Check individual com status e detalhes
  - `QualityCertificate` - Certificado completo com score e validade
  - `certify(df)` - Executa checks (completeness, duplicates, schema, freshness, range)
  - `quick_check(df)` - Retorna (level, score) rapidamente

## [0.4.0] - 2026-02-04

### Added
- **Modo Determinístico** - Reprodutibilidade absoluta para backtests
  - `agrobr.set_mode("deterministic", snapshot="2025-01-01")`
  - `agrobr.configure()` para opções globais
  - `agrobr.get_config()` para consultar configuração atual
  - `agrobr.reset_config()` para resetar ao padrão
- **Sistema de Snapshots** - Gerenciamento de versões de dados
  - `create_snapshot()` - Cria snapshot dos dados atuais
  - `load_from_snapshot()` - Carrega dados de um snapshot
  - `list_snapshots()` / `delete_snapshot()` - Gerenciamento
  - CLI: `agrobr snapshot create/list/delete/use`
- **Export Auditável** - Formatos com metadados de proveniência
  - `export_parquet()` - Parquet com metadata embutido
  - `export_csv()` - CSV com arquivo sidecar .meta.json
  - `export_json()` - JSON com metadados opcionais
  - `verify_export()` - Verificação de integridade

## [0.3.0] - 2026-02-04

### Added
- **Stability Contracts** - Garantias formais de schema para todas as fontes
  - `CEPEA_INDICADOR_V1` - Contrato para indicadores de preço CEPEA
  - `CONAB_SAFRA_V1` - Contrato para dados de safra CONAB
  - `CONAB_BALANCO_V1` - Contrato para balanço oferta/demanda CONAB
  - `IBGE_PAM_V1` - Contrato para dados PAM do IBGE
  - `IBGE_LSPA_V1` - Contrato para dados LSPA do IBGE
  - `contract.validate(df)` - Validação automática contra contrato
  - `contract.to_markdown()` - Documentação automática
- **Validação Semântica** - Verificações avançadas de qualidade
  - Validação de preços positivos
  - Validação de faixas de produtividade por cultura
  - Detecção de anomalias em variação diária (>20%)
  - Consistência de sequência de datas
  - Consistência de áreas (colhida <= plantada)
  - Validação de formato de safra
  - `validate_semantic(df)` - Executa todas as regras
  - `get_validation_summary(df)` - Resumo das violações
- **Benchmark Suite** - Ferramentas para medição de performance
  - `benchmark_async()` / `benchmark_sync()` - Benchmark de funções
  - `run_api_benchmarks()` - Benchmark das APIs
  - `run_contract_benchmarks()` - Benchmark de validação de contratos
  - `run_semantic_benchmarks()` - Benchmark de validação semântica

### Changed
- Changelog reestruturado seguindo Keep a Changelog

## [0.2.0] - 2026-02-04

### Added
- **`agrobr doctor`** - Comando CLI para diagnóstico do sistema
  - Verificação de conectividade das fontes
  - Estatísticas do cache (tamanho, registros, por fonte)
  - Status de configuração
  - Output JSON (`--json`) e formatado Rich
- **Parâmetro `return_meta`** - Suporte a data lineage em todas as APIs
  - `cepea.indicador(return_meta=True)` retorna `(DataFrame, MetaInfo)`
  - `conab.safras(return_meta=True)` retorna `(DataFrame, MetaInfo)`
  - `ibge.pam(return_meta=True)` retorna `(DataFrame, MetaInfo)`
  - `ibge.lspa(return_meta=True)` retorna `(DataFrame, MetaInfo)`
- **Classe `MetaInfo`** - Metadados de proveniência e rastreabilidade
  - Informações da fonte (nome, URL, método)
  - Timing (duração fetch, duração parse)
  - Status do cache (from_cache, cache_key, expires_at)
  - Integridade do conteúdo (hash SHA256, tamanho)
  - Versões (agrobr, parser, schema, python)
  - `to_dict()` / `to_json()` para serialização
  - `verify_hash(df)` para verificação de integridade
- **Documentação** - Guias de proveniência e resiliência
  - `docs/sources/cepea.md` - Documentação da fonte CEPEA
  - `docs/sources/conab.md` - Documentação da fonte CONAB
  - `docs/sources/ibge.md` - Documentação da fonte IBGE
  - `docs/advanced/resilience.md` - Documentação de resiliência

### Changed
- `MetaInfo` exportado do pacote principal

## [0.1.2] - 2026-02-04

### Changed
- **Smart TTL** para cache CEPEA - expira às 18:00 (horário de atualização CEPEA)
- Reduz requests desnecessários em ~90%

## [0.1.1] - 2026-02-04

### Fixed
- Browser fallback desabilitado para CEPEA (Cloudflare bloqueia)
- CEPEA agora vai direto para Notícias Agrícolas, evitando timeout

## [0.1.0] - 2026-02-04

### Added
- **CEPEA**: Indicadores de preços agrícolas (soja, milho, boi, café, algodão, trigo)
  - Fallback automático para Notícias Agrícolas quando CEPEA bloqueado
  - Acumulação progressiva de histórico no DuckDB
- **CONAB**: Dados de safras e balanço oferta/demanda
  - Parser para planilhas XLSX do boletim de safras
  - Suporte a todos os produtos principais (soja, milho, arroz, feijão, etc.)
- **IBGE**: Integração com API SIDRA
  - PAM (Produção Agrícola Municipal) - dados anuais
  - LSPA (Levantamento Sistemático) - estimativas mensais
- **Cache**: Sistema de cache com DuckDB
  - Separação entre cache volátil e histórico permanente
  - TTL configurável por fonte
  - Acumulação progressiva de dados
- **HTTP**: Cliente robusto com resiliência
  - Retry com exponential backoff
  - Rate limiting por fonte
  - User-agent rotativo
  - Fallback para Playwright quando necessário
- **CLI**: Interface de linha de comando completa
  - Comandos para CEPEA, CONAB e IBGE
  - Exportação em CSV, JSON e Parquet
- **Validação**: Sistema de validação multinível
  - Pydantic v2 para validação de tipos
  - Validação estatística (sanity checks)
  - Fingerprinting de layout para detecção de mudanças
- **Monitoramento**: Health checks e alertas
  - Health check por fonte
  - Alertas multi-canal (Slack, Discord, Email)
  - Monitoramento de estrutura
- **Suporte Polars**: Todas as APIs suportam `as_polars=True`
- **Testes**: 96 testes passando (~80% cobertura)
- **CI/CD**: GitHub Actions configurados
  - Testes automatizados
  - Health check diário
  - Monitoramento de estrutura

### Technical Details
- Python 3.11+ required
- Async-first design com sync wrapper
- Type hints completos
- Logging estruturado com structlog

[Unreleased]: https://github.com/bruno-portfolio/agrobr/compare/v1.0.4...HEAD
[1.0.4]: https://github.com/bruno-portfolio/agrobr/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/bruno-portfolio/agrobr/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/bruno-portfolio/agrobr/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/bruno-portfolio/agrobr/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.12.0...v1.0.0
[0.12.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.11.3...v0.12.0
[0.11.3]: https://github.com/bruno-portfolio/agrobr/compare/v0.11.2...v0.11.3
[0.11.2]: https://github.com/bruno-portfolio/agrobr/compare/v0.11.1...v0.11.2
[0.11.1]: https://github.com/bruno-portfolio/agrobr/compare/v0.11.0...v0.11.1
[0.11.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.10.1...v0.11.0
[0.10.1]: https://github.com/bruno-portfolio/agrobr/compare/v0.10.0...v0.10.1
[0.10.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.9.0...v0.10.0
[0.9.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.7.1...v0.8.0
[0.7.1]: https://github.com/bruno-portfolio/agrobr/compare/v0.7.0...v0.7.1
[0.7.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.6.3...v0.7.0
[0.6.3]: https://github.com/bruno-portfolio/agrobr/compare/v0.6.2...v0.6.3
[0.6.2]: https://github.com/bruno-portfolio/agrobr/compare/v0.6.1...v0.6.2
[0.6.1]: https://github.com/bruno-portfolio/agrobr/compare/v0.6.0...v0.6.1
[0.6.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/bruno-portfolio/agrobr/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/bruno-portfolio/agrobr/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/bruno-portfolio/agrobr/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/bruno-portfolio/agrobr/releases/tag/v0.1.0
