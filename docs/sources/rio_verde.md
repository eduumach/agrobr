# Fundacao Rio Verde — Ensaios de Cultivares de Soja

> **Licenca:** Sem termos publicos.
> Classificacao: `zona_cinza`

Resultados de ensaios de cultivares de soja conduzidos pela Fundacao Rio Verde
em Lucas do Rio Verde, MT.

## Visao Geral

| Campo | Valor |
|-------|-------|
| **Operador** | Fundacao Rio Verde (Lucas do Rio Verde, MT) |
| **Website** | [fundacaorioverde.com.br](https://fundacaorioverde.com.br) |
| **Licenca** | `zona_cinza` — Sem termos publicos |
| **Formato** | PDF text-based |
| **Atualizacao** | Anual (por safra) |
| **Cobertura** | ~97 cultivares x 4 epocas de semeio (safra 2025/26) |

## Dados Disponiveis

### Ensaio de Soja

Resultados de produtividade por cultivar e epoca de semeio.

**Colunas:** `safra`, `empresa`, `cultivar`, `grupo_maturacao`, `ciclo_dias`,
`produtividade_1_epoca_sc_ha`, `produtividade_2_epoca_sc_ha`, `produtividade_3_epoca_sc_ha`,
`produtividade_4_epoca_sc_ha`, `produtividade_media_sc_ha`

## API

```python
import asyncio
from agrobr import rio_verde

async def main():
    # Ensaio da safra 2025/2026
    df = await rio_verde.ensaio_soja("2025/2026")

    # Safra especifica
    df = await rio_verde.ensaio_soja("2024/2025")

    # Listar safras disponiveis
    safras = await rio_verde.safras_disponiveis()

    # Com metadados
    df, meta = await rio_verde.ensaio_soja("2025/2026", return_meta=True)

    # Polars
    df = await rio_verde.ensaio_soja("2025/2026", as_polars=True)

asyncio.run(main())
```

## Notas Tecnicas

- Requer `pip install agrobr[pdf]` (pdfplumber)
- PDF text-based (nao requer OCR)
- Parser extrai tabelas de produtividade por epoca de semeio
- Produtividade em sacas/hectare (sc/ha)
- Safras disponiveis dependem dos PDFs publicados pela fundacao

## Fonte

- URL: `https://fundacaorioverde.com.br`
- Formato: PDF
- Atualizacao: anual (por safra)
- Licenca: `zona_cinza` — Sem termos publicos (verificar com a fundacao)
