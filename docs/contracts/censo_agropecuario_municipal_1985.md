# censo_agropecuario_municipal_1985 v1.0

Censo Agropecuario 1985 — dados municipais extraidos via OCR de PDFs do IBGE (22 UFs, 53 temas).

## Fontes

| Prioridade | Fonte | Descricao |
|------------|-------|-----------|
| 1 | IBGE Censo Agro Municipal 1985 | CSVs locais extraidos via OCR de PDFs estaduais |

## Temas

53 temas cobrindo estrutura fundiaria, uso da terra, pessoal, mecanizacao, pecuaria, lavouras e producao:

`propriedade_terras`, `condicao_produtor`, `condicao_legal_terras`, `area_total`, `uso_terra_lavoura`, `uso_terra_pastagem`, `uso_terra_matas`, `uso_terra_outros`, `irrigacao`, `pessoal_total`, `pessoal_familiar`, `pessoal_empregados`, `mecanizacao_tratores`, `mecanizacao_implementos`, `bovinos`, `suinos`, `aves`, `ovinos_caprinos`, `equinos_muares`, `bubalinos_coelhos`, `inseminacao_ordenha`, `leite_la`, `producao_ovos_mel`, `producao_casulos_cera`, `lavoura_permanente_area`, `lavoura_permanente_prod`, `lavoura_temporaria_area`, `lavoura_temporaria_prod`, `lavoura_temp_flores`, `horticultura`, `silvicultura_area`, `silvicultura_prod`, `extracao_vegetal`, `forrageiras`, `efetivo_aves_detalhe`, `producao_particular`, ...

Use `temas_censo_agro_municipal_1985()` para a lista completa.

## Schema

| Coluna | Tipo | Nullable | Descricao |
|--------|------|----------|-----------|
| `ano` | int | ❌ | Sempre 1985 |
| `uf` | str | ❌ | Sigla da UF (22 UFs) |
| `uf_cod` | int | ❌ | Codigo IBGE da UF (11-53) |
| `localidade` | str | ❌ | Nome do municipio/mesorregiao/microrregiao |
| `localidade_cod` | int | ✅ | Codigo IBGE (resolvido por OCR, pode ser None) |
| `nivel` | str | ❌ | total, mesorregiao, microrregiao, municipio |
| `tema` | str | ❌ | Tema da tabela |
| `categoria` | str | ❌ | Sempre "geral" |
| `variavel` | str | ❌ | Nome da variavel (semantico ou val_N) |
| `valor` | float64 | ✅ | Valor numerico |
| `unidade` | str | ❌ | Unidade de medida |
| `confianca` | str | ❌ | Qualidade OCR: alta, media ou baixa |
| `fonte` | str | ❌ | Sempre "ibge_censo_agro_municipal_1985" |

## Primary Key

Vazio (`[]`). Dados OCR podem gerar labels homonimos (ex: 3 municipios "Santo Antonio" em MG pertencentes a microrregioes distintas). Unicidade nao e garantida a nivel de nome.

## Formato

Long format: cada linha tem um par variavel/valor.

### Colunas semanticas vs val_N

12 tabelas tem colunas com nomes semanticos (ex: `estab_total`, `area_ha_total`). As demais usam `val_1`, `val_2`, etc.

### Unidades por prefixo

| Prefixo | Unidade |
|---------|---------|
| `estab_` | estabelecimentos |
| `area_ha_` | hectares |
| `inform_` | informantes |
| `num_pessoas_` | pessoas |
| `efetivo_` | cabecas |
| `qtde_` | toneladas |
| `valor_` | mil_cruzeiros |
| `val_` | unidades |

## Niveis Territoriais

| Nivel | Descricao |
|-------|-----------|
| `total` | Total da UF |
| `mesorregiao` | Mesorregiao |
| `microrregiao` | Microrregiao |
| `municipio` | Municipio |

## UFs Disponiveis (22)

AC, AL, AM, AP, BA, ES, GO, MG, MS, MT, PA, PB, PE, PR, RJ, RN (parcial), RO, RR, RS, SC, SE, SP

**Excluidos:** MA, PI, CE, RN — PDFs sem camada OCR (Tesseract insuficiente).

## Garantias

- Ano sempre 1985
- Valores numericos sempre >= 0
- Fonte sempre "ibge_censo_agro_municipal_1985"
- `confianca` indica qualidade OCR: alta, media ou baixa
- `localidade_cod` pode ser None quando OCR nao permite match exato
- PK vazio: OCR pode gerar labels homonimos
- Dados extraidos de 28 PDFs estaduais + 1 nacional (cross-validation 77.9%)
- Frequencia de atualizacao: never (dados historicos)

## Quirks

- **Labels OCR**: ~4.2% dos labels de municipio contem artefatos OCR residuais
- **0.08% irrecuperaveis**: labels com digitos embutidos no nome nao sao resolviveis
- **Colunas val_N**: 41 tabelas usam nomes genericos (consultar _index.csv para significado)
- **Cross-validation**: 77.9% match entre totais estaduais e nacionais (96.8% exato quando ha match)

## Exemplo

```python
from agrobr import ibge

# Propriedade de terras em Sao Paulo
df = await ibge.censo_agro_municipal_1985('propriedade_terras', uf='SP')

# Apenas municipios
df = await ibge.censo_agro_municipal_1985('bovinos', nivel='municipio')

# Listar temas
temas = await ibge.temas_censo_agro_municipal_1985()

# Via dataset semantico
from agrobr import datasets
df = await datasets.censo_agropecuario_municipal_1985('uso_terra_lavoura', uf='MG')

# Com metadados
df, meta = await ibge.censo_agro_municipal_1985('propriedade_terras', return_meta=True)
```

### CLI

```bash
# Dados de propriedade de terras em SP
agrobr ibge censo-municipal-1985 propriedade_terras --uf SP

# Formato CSV
agrobr ibge censo-municipal-1985 bovinos --formato csv

# Listar temas disponiveis
agrobr ibge temas-municipal-1985
```

## Schema JSON

Disponivel em `agrobr/schemas/censo_agropecuario_municipal_1985.json`.

```python
from agrobr.contracts import get_contract
contract = get_contract("censo_agropecuario_municipal_1985")
print(contract.to_json())
```

## Relacao com outros contratos

| Contrato | Escopo | Periodos |
|----------|--------|----------|
| `censo_agropecuario` | 10 temas tematicos (SIDRA) | 1995, 2006, 2017 |
| `censo_agropecuario_legado` | 6 temas legados (FTP) | 1995 |
| `censo_agropecuario_historico` | 9 temas serie historica (SIDRA, ate UF) | 1920-2006 |
| **`censo_agropecuario_municipal_1985`** | **53 temas municipais (OCR de PDFs)** | **1985** |

Sao contratos separados, sem conflito. Este e o unico com dados municipais de 1985.
