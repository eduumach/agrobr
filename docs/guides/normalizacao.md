# Normalização

O módulo `agrobr.normalize` padroniza dados agrícolas brasileiros para garantir cruzamento entre fontes diferentes. São 38 funções organizadas em 7 sub-módulos.

## Municípios IBGE

5571 municípios com código IBGE de 7 dígitos. Busca accent/case insensitive.

```python
from agrobr.normalize import municipio_para_ibge, ibge_para_municipio, buscar_municipios

# Nome para código IBGE
municipio_para_ibge("Rondonópolis")        # 5107602
municipio_para_ibge("RONDONOPOLIS")        # 5107602 (sem acento, uppercase)
municipio_para_ibge("rondonopolis", "MT")  # 5107602 (desambiguar por UF)

# Código IBGE para info
ibge_para_municipio(5107602)
# {'codigo_ibge': 5107602, 'nome': 'Rondonópolis', 'uf': 'MT'}

# Busca parcial
buscar_municipios("sorriso", uf="MT")
# [{'codigo_ibge': 5107925, 'nome': 'Sorriso', 'uf': 'MT'}]

# Homônimos — sem UF retorna o primeiro, com UF desambigua
municipio_para_ibge("Brasília")            # 5300108 (DF)
municipio_para_ibge("Brasília", "MG")      # 3108909 (Brasília de Minas)
```

Dados da [API IBGE Localidades](https://servicodados.ibge.gov.br/api/docs/localidades) — livre para uso.

## Culturas

144 variantes mapeando para 35 culturas canônicas. Aceita português, inglês, com/sem acento.

```python
from agrobr.normalize import normalizar_cultura, listar_culturas, is_cultura_valida

# Padronização
normalizar_cultura("SOJA")             # "soja"
normalizar_cultura("Soja em Grão")     # "soja"
normalizar_cultura("soybean")          # "soja"
normalizar_cultura("milho 2ª safra")   # "milho_2"
normalizar_cultura("café arábica")     # "cafe_arabica"
normalizar_cultura("boi gordo")        # "boi"
normalizar_cultura("cotton")           # "algodao"

# Listar canônicas
listar_culturas()
# ['acucar', 'acucar_cristal', 'acucar_refinado', 'algodao', 'algodao_pluma',
#  'amendoim', 'arroz', 'aveia', 'batata', 'boi', 'cafe', 'cafe_arabica',
#  'cafe_robusta', 'cana', 'cebola', 'centeio', 'cevada', 'etanol_anidro',
#  'etanol_hidratado', 'farelo_soja', 'feijao', 'feijao_1', 'feijao_2',
#  'feijao_3', 'frango_congelado', 'frango_resfriado', 'laranja',
#  'laranja_in_natura', 'laranja_industria', 'leite', 'mandioca', 'milho',
#  'milho_1', 'milho_2', 'milho_3', 'oleo_soja', 'soja', 'sorgo', 'suino',
#  'tomate', 'trigo']

# Validação
is_cultura_valida("soja em grão")  # True
is_cultura_valida("batata doce")   # False
```

## UFs e Regiões

27 UFs com código IBGE, nome completo e região. Aceita sigla, nome completo, com/sem acento.

```python
from agrobr.normalize import (
    normalizar_uf, validar_uf, uf_para_nome, uf_para_regiao,
    uf_para_ibge, ibge_para_uf, listar_ufs, listar_regioes,
)

normalizar_uf("São Paulo")     # "SP"
normalizar_uf("sp")            # "SP"
normalizar_uf("SAO PAULO")     # "SP"
normalizar_uf("mato grosso")   # "MT"

uf_para_nome("MT")             # "Mato Grosso"
uf_para_regiao("MT")           # "Centro-Oeste"
uf_para_ibge("MT")             # 51
ibge_para_uf(51)               # "MT"

validar_uf("SP")               # True
validar_uf("XX")               # False

listar_ufs()                   # ['AC', 'AL', 'AM', ..., 'TO']
listar_regioes()               # ['Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
```

## Biomas

6 biomas brasileiros. Aceita com/sem acento, case insensitive. Usada automaticamente em `desmatamento`, `queimadas` e `mapbiomas`.

```python
from agrobr.normalize import normalizar_bioma, BIOMAS_VALIDOS

normalizar_bioma("amazonia")        # "Amazônia"
normalizar_bioma("cerrado")         # "Cerrado"
normalizar_bioma("mata atlantica")  # "Mata Atlântica"
normalizar_bioma("  Caatinga  ")    # "Caatinga"
normalizar_bioma("desconhecido")    # "desconhecido" (passthrough)

BIOMAS_VALIDOS
# {'Amazônia', 'Caatinga', 'Cerrado', 'Mata Atlântica', 'Pampa', 'Pantanal'}
```

## Safras

Datas de safra agrícola no formato brasileiro `YYYY/YY`. A safra agrícola vai de julho a junho.

```python
from agrobr.normalize import (
    safra_atual, normalizar_safra, validar_safra,
    safra_para_anos, anos_para_safra, safra_anterior, safra_posterior,
    periodo_safra, lista_safras,
)

safra_atual()                    # "2025/26" (se estiver entre jul/2025 e jun/2026)
normalizar_safra("24/25")        # "2024/25"
normalizar_safra("2024/2025")    # "2024/25"
validar_safra("2024/25")         # True

safra_para_anos("2024/25")       # (2024, 2025)
anos_para_safra(2024, 2025)      # "2024/25"
safra_anterior("2024/25")        # "2023/24"
safra_posterior("2024/25")       # "2025/26"

periodo_safra("2024/25")         # (date(2024, 7, 1), date(2025, 6, 30))
lista_safras("2020/21", "2024/25")
# ['2020/21', '2021/22', '2022/23', '2023/24', '2024/25']
```

## Unidades

Conversão entre unidades agrícolas brasileiras: sacas, toneladas, bushels, arrobas, hectares.

```python
from agrobr.normalize import (
    converter, sacas_para_toneladas, toneladas_para_sacas,
    preco_saca_para_tonelada, preco_tonelada_para_saca,
)

# Conversão genérica
converter(1, "ton", "sc60kg")           # 16.6667 (sacas de 60kg)
converter(100, "sc60kg", "ton")         # 6.0
converter(1, "ton", "bu", produto="soja")  # 36.7437 (bushels)
converter(1, "arroba", "kg")            # 15.0

# Atalhos para preços
preco_saca_para_tonelada(145.50)        # 2425.0 (R$/ton a partir de R$/sc60kg)
preco_tonelada_para_saca(2425.0)        # 145.5  (R$/sc60kg a partir de R$/ton)

# Peso para volume
sacas_para_toneladas(1000)              # 60.0
toneladas_para_sacas(60)                # 1000.0
```

## Encoding

Detecção e decodificação de encoding para HTML/CSV de fontes brasileiras (ISO-8859-1, Windows-1252, UTF-8).

```python
from agrobr.normalize import detect_encoding, decode_content, detect_encoding_chain

# Detectar encoding de bytes (chardet)
encoding, confidence = detect_encoding(raw_bytes)   # ("iso-8859-1", 0.95)

# Decodificar com fallback chain completa
text, enc = decode_content(raw_bytes)               # (str, "utf-8")

# Chain rápida sem chardet (UTF-8 → UTF-8-sig → Windows-1252 → ISO-8859-1)
enc = detect_encoding_chain(raw_bytes)              # "windows-1252"
```

`detect_encoding_chain` usa probe de 4KB na ordem UTF-8, UTF-8-sig, Windows-1252, ISO-8859-1 — com chardet como fallback final. Usada internamente pelos parsers `alt/` para CSVs de governo.

## Numérico BR

Parsing de valores numéricos no formato brasileiro (ponto como milhar, vírgula como decimal).

```python
from agrobr.normalize import parse_numeric_br

parse_numeric_br("1.234,56")     # 1234.56
parse_numeric_br("1234,56")      # 1234.56
parse_numeric_br("500.000,50")   # 500000.5
parse_numeric_br(42)             # 42.0 (passthrough int/float)
parse_numeric_br("-")            # None (marcador de dado ausente)
parse_numeric_br(None)           # None
parse_numeric_br("abc")          # None (inválido retorna None)
```

## Referência Rápida

| Sub-módulo | Funções | Dados |
|---|---|---|
| `municipalities` | `municipio_para_ibge`, `ibge_para_municipio`, `buscar_municipios`, `total_municipios` | 5571 municípios |
| `crops` | `normalizar_cultura`, `listar_culturas`, `is_cultura_valida` | 144 variantes, 35 canônicas |
| `regions` | `normalizar_uf`, `validar_uf`, `uf_para_nome`, `uf_para_regiao`, `uf_para_ibge`, `ibge_para_uf`, `listar_ufs`, `listar_regioes`, `normalizar_municipio`, `normalizar_praca`, `normalizar_bioma` | 27 UFs, 6 biomas |
| `dates` | `safra_atual`, `normalizar_safra`, `validar_safra`, `safra_para_anos`, `anos_para_safra`, `safra_anterior`, `safra_posterior`, `periodo_safra`, `lista_safras` | Safras Jul-Jun |
| `units` | `converter`, `sacas_para_toneladas`, `toneladas_para_sacas`, `preco_saca_para_tonelada`, `preco_tonelada_para_saca` | sc, ton, bu, @, ha |
| `encoding` | `detect_encoding`, `decode_content`, `detect_encoding_chain` | ISO-8859-1, CP1252, UTF-8 |
| `numeric` | `parse_numeric_br` | Formato BR (1.234,56) |
