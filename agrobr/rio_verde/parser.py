from __future__ import annotations

import io
import re
from typing import Any

import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.normalize.numeric import safe_float

from .models import COLUNAS_SAIDA

logger = structlog.get_logger()

PARSER_VERSION = 1

_SUMMARY_RE = re.compile(
    r"^(.+?)\s+"
    r"(\S+)\s+"
    r"(?:\d+\.?\d*)\s+"
    r"(?:\d+\.?\d*)\s+"
    r"(\d+)\s+"
    r"([\d,.-]+|[-])\s+"
    r"([\d,.-]+|[-])\s+"
    r"([\d,.-]+|[-])\s+"
    r"([\d,.-]+|[-])\s+"
    r"([\d,.-]+)"
)

_SKIP_PREFIXES = ("Empresa", "G.M.", "Estimado", "(dias)")


def _check_pdfplumber() -> Any:
    try:
        import pdfplumber

        return pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber is required for rio_verde. Install it with: pip install agrobr[pdf]"
        ) from None


def _parse_summary_line(line: str, safra: str) -> dict[str, Any] | None:
    m = _SUMMARY_RE.match(line.strip())
    if not m:
        return None

    empresa_cultivar = m.group(1).strip()
    parts = empresa_cultivar.rsplit(None, 1)
    if len(parts) < 2:
        return None

    empresa = parts[0].strip()
    cultivar = parts[1].strip()

    return {
        "safra": safra,
        "empresa": empresa,
        "cultivar": cultivar,
        "grupo_maturacao": m.group(2),
        "ciclo_dias": safe_float(m.group(3)),
        "produtividade_1_epoca_sc_ha": safe_float(m.group(4)),
        "produtividade_2_epoca_sc_ha": safe_float(m.group(5)),
        "produtividade_3_epoca_sc_ha": safe_float(m.group(6)),
        "produtividade_4_epoca_sc_ha": safe_float(m.group(7)),
        "produtividade_media_sc_ha": safe_float(m.group(8)),
    }


def _extract_records(pages: list[str], safra: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    in_summary = False
    done = False

    for text in pages:
        if done:
            break
        for line in text.split("\n"):
            lower = line.lower()
            if not in_summary:
                if (
                    "competi" in lower
                    and "soja" in lower
                    and not lower.lstrip().startswith("resultado")
                ):
                    in_summary = True
                    continue
            else:
                if lower.lstrip().startswith("resultado"):
                    in_summary = False
                    done = True
                    break
                if line.strip():
                    if line.strip().startswith(_SKIP_PREFIXES):
                        continue
                    record = _parse_summary_line(line, safra)
                    if record is not None:
                        records.append(record)

    if not records:
        logger.warning("rio_verde_empty_extraction", safra=safra, pages=len(pages))

    return records


def _records_to_df(records: list[dict[str, Any]], safra: str) -> pd.DataFrame:
    if not records:
        raise ParseError(
            source="rio_verde",
            parser_version=PARSER_VERSION,
            reason=f"Nenhum registro extraído (safra {safra})",
        )

    df = pd.DataFrame(records, columns=COLUNAS_SAIDA)
    logger.info("rio_verde_parse_ok", safra=safra, records=len(df))
    return df


def parse_ensaio_soja(data: bytes, safra: str) -> pd.DataFrame:
    pdfplumber = _check_pdfplumber()

    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as exc:
        raise ParseError(
            source="rio_verde",
            parser_version=PARSER_VERSION,
            reason=f"Falha ao abrir PDF: {exc}",
        ) from exc

    try:
        pages = [page.extract_text() or "" for page in pdf.pages]
    finally:
        pdf.close()

    return _records_to_df(_extract_records(pages, safra), safra)


def parse_ensaio_soja_from_text(pages: list[str], safra: str) -> pd.DataFrame:
    return _records_to_df(_extract_records(pages, safra), safra)
