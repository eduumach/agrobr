from __future__ import annotations

import re
import zipfile
from datetime import date, datetime
from io import BytesIO
from typing import IO

import pandas as pd
import structlog
from bs4 import BeautifulSoup
from lxml import etree

from agrobr.exceptions import ParseError

from .models import (
    B3_CONTRATOS_AGRO_INV,
    COLUNAS_OI_SAIDA,
    COLUNAS_SAIDA,
    TICKERS_AGRO,
    TICKERS_AGRO_OI,
    UNIDADES,
    parse_numero_br,
    parse_vencimento,
)

logger = structlog.get_logger()

PARSER_VERSION = 1
PARSER_VERSION_ZIP = 1
PARSER_VERSION_OI = 1

_NS = "urn:bvmf.217.01.xsd"

_TAG_TICKER = f"{{{_NS}}}SctyId/{{{_NS}}}TckrSymb"
_TAG_FIN_ATTRS = f"{{{_NS}}}FinInstrmAttrbts"
_TAG_TRADE_DT = f"{{{_NS}}}TradDt/{{{_NS}}}Dt"
_TAG_PRVS_ADJSTD = f"{{{_NS}}}PrvsAdjstdQt"
_TAG_ADJSTD = f"{{{_NS}}}AdjstdQt"
_TAG_VARTN = f"{{{_NS}}}VartnPts"
_TAG_ADJSTD_VAL = f"{{{_NS}}}AdjstdValCtrct"

_RE_TICKER_FUTURO = re.compile(r"^([A-Z]{2,4})([FGHJKMNQUVXZ]\d{2})$")
_RE_TICKER_OPCAO = re.compile(r"^[A-Z]{2,4}[FGHJKMNQUVXZ]\d{2}[CP]\d+$")

_NUMERIC_COLS = ["ajuste_anterior", "ajuste_atual", "variacao", "ajuste_por_contrato"]

_RE_ATUALIZADO = re.compile(r"ATUALIZADO EM:\s*(\d{2}/\d{2}/\d{4})")


def _extrair_data_referencia(html: str) -> date | None:
    m = _RE_ATUALIZADO.search(html)
    if not m:
        return None
    return datetime.strptime(m.group(1), "%d/%m/%Y").date()


def _extrair_ticker(texto: str) -> tuple[str, str]:
    parts = texto.split("-", 1)
    ticker = parts[0].strip()
    descricao = parts[1].strip() if len(parts) > 1 else ""
    return ticker, descricao


def parse_ajustes_html(html: str) -> pd.DataFrame:
    data_ref = _extrair_data_referencia(html)
    if data_ref is None:
        logger.info("b3_sem_pregao", reason="ATUALIZADO EM ausente")
        return pd.DataFrame(columns=COLUNAS_SAIDA)

    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="tblDadosAjustes")
    if table is None:
        raise ParseError(
            source="b3",
            parser_version=PARSER_VERSION,
            reason="Tabela tblDadosAjustes nao encontrada",
        )

    rows = table.find_all("tr")  # type: ignore[union-attr]
    if len(rows) < 2:
        raise ParseError(
            source="b3",
            parser_version=PARSER_VERSION,
            reason=f"Tabela com apenas {len(rows)} rows",
        )

    records: list[dict[str, object]] = []
    current_ticker = ""
    current_desc = ""
    in_agro = False

    for row in rows[1:]:
        cells = row.find_all("td")
        if len(cells) < 6:
            continue

        col1 = cells[0].get_text(strip=True)
        if col1:
            current_ticker, current_desc = _extrair_ticker(col1)
            in_agro = current_ticker in TICKERS_AGRO

        if not in_agro:
            continue

        vct_raw = cells[1].get_text(strip=True)
        if not vct_raw:
            continue

        try:
            vct_ano, vct_mes = parse_vencimento(vct_raw)
        except (KeyError, ValueError, IndexError):
            continue

        records.append(
            {
                "data": data_ref,
                "ticker": current_ticker,
                "descricao": current_desc,
                "vencimento_codigo": vct_raw.strip(),
                "vencimento_mes": vct_mes,
                "vencimento_ano": vct_ano,
                "ajuste_anterior": parse_numero_br(cells[2].get_text(strip=True)),
                "ajuste_atual": parse_numero_br(cells[3].get_text(strip=True)),
                "variacao": parse_numero_br(cells[4].get_text(strip=True)),
                "ajuste_por_contrato": parse_numero_br(cells[5].get_text(strip=True)),
                "unidade": UNIDADES.get(current_ticker, ""),
            }
        )

    df = pd.DataFrame(records, columns=COLUNAS_SAIDA)
    _coerce_ajustes_dtypes(df)

    logger.info("b3_parse_ok", records=len(df), data_ref=str(data_ref))
    return df


def parse_ajustes_zip(zip_bytes: bytes) -> pd.DataFrame:
    try:
        with zipfile.ZipFile(BytesIO(zip_bytes)) as outer_zip:
            inner_names = [n for n in outer_zip.namelist() if n.endswith(".zip")]
            if not inner_names:
                raise ParseError(
                    source="b3",
                    parser_version=PARSER_VERSION_ZIP,
                    reason="ZIP interno nao encontrado no arquivo externo",
                )

            try:
                with zipfile.ZipFile(BytesIO(outer_zip.read(inner_names[0]))) as inner_zip:
                    xml_names = sorted(n for n in inner_zip.namelist() if n.endswith(".xml"))
                    if not xml_names:
                        raise ParseError(
                            source="b3",
                            parser_version=PARSER_VERSION_ZIP,
                            reason="Nenhum XML encontrado no ZIP interno",
                        )

                    with inner_zip.open(xml_names[-1]) as xml_stream:
                        records = _parse_bvmf_xml(xml_stream)
            except zipfile.BadZipFile as exc:
                raise ParseError(
                    source="b3",
                    parser_version=PARSER_VERSION_ZIP,
                    reason=f"ZIP interno corrompido: {exc}",
                ) from exc
    except zipfile.BadZipFile as exc:
        raise ParseError(
            source="b3",
            parser_version=PARSER_VERSION_ZIP,
            reason=f"ZIP externo corrompido: {exc}",
        ) from exc

    df = pd.DataFrame(records, columns=COLUNAS_SAIDA)
    _coerce_ajustes_dtypes(df)

    logger.info("b3_zip_parse_ok", records=len(df))
    return df


def _coerce_ajustes_dtypes(df: pd.DataFrame) -> None:
    if df.empty:
        return
    df["data"] = pd.to_datetime(df["data"])
    for col in _NUMERIC_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")


def _parse_bvmf_xml(xml_stream: IO[bytes]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    tag_pric_rpt = f"{{{_NS}}}PricRpt"

    for _event, elem in etree.iterparse(xml_stream, events=("end",), tag=tag_pric_rpt):
        record = _extract_record(elem)
        if record is not None:
            records.append(record)
        elem.clear()
        parent = elem.getparent()
        if parent is not None:
            while parent.getprevious() is not None:
                del parent[0]

    return records


def _extract_record(elem: etree._Element) -> dict[str, object] | None:
    ticker_symb = elem.findtext(_TAG_TICKER, "").strip()
    m = _RE_TICKER_FUTURO.match(ticker_symb)
    if not m:
        return None

    ticker = m.group(1)
    if ticker not in TICKERS_AGRO:
        return None

    vct_codigo = m.group(2)

    try:
        vct_ano, vct_mes = parse_vencimento(vct_codigo)
    except (KeyError, ValueError, IndexError):
        return None

    attrs = elem.find(_TAG_FIN_ATTRS)
    if attrs is None:
        return None

    trade_dt = elem.findtext(_TAG_TRADE_DT, "")

    return {
        "data": trade_dt,
        "ticker": ticker,
        "descricao": B3_CONTRATOS_AGRO_INV.get(ticker, ""),
        "vencimento_codigo": vct_codigo,
        "vencimento_mes": vct_mes,
        "vencimento_ano": vct_ano,
        "ajuste_anterior": _attr_float(attrs, _TAG_PRVS_ADJSTD),
        "ajuste_atual": _attr_float(attrs, _TAG_ADJSTD),
        "variacao": _attr_float(attrs, _TAG_VARTN),
        "ajuste_por_contrato": _attr_float(attrs, _TAG_ADJSTD_VAL),
        "unidade": UNIDADES.get(ticker, ""),
    }


def _attr_float(parent: etree._Element, tag: str) -> float | None:
    el = parent.find(tag)
    if el is None or not el.text:
        return None
    try:
        return float(el.text)
    except (ValueError, TypeError):
        return None


def _classificar_tipo(ticker_completo: str) -> str:
    if _RE_TICKER_FUTURO.match(ticker_completo):
        return "futuro"
    if _RE_TICKER_OPCAO.match(ticker_completo):
        return "opcao"
    return "opcao" if len(ticker_completo) > 6 else "futuro"


def _parse_vencimento_safe(codigo: str) -> tuple[int | None, int | None]:
    try:
        ano, mes = parse_vencimento(codigo)
        return ano, mes
    except (KeyError, ValueError, IndexError):
        return None, None


def parse_posicoes_abertas(csv_bytes: bytes) -> pd.DataFrame:
    if not csv_bytes or len(csv_bytes.strip()) == 0:
        return pd.DataFrame(columns=COLUNAS_OI_SAIDA)

    try:
        df_raw = pd.read_csv(BytesIO(csv_bytes), sep=";", encoding="utf-8")
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=COLUNAS_OI_SAIDA)

    if "SgmtNm" not in df_raw.columns:
        raise ParseError(
            source="b3",
            parser_version=PARSER_VERSION_OI,
            reason="Coluna SgmtNm ausente no CSV",
        )

    df_agro = df_raw[df_raw["SgmtNm"] == "AGRIBUSINESS"].copy()

    if df_agro.empty:
        return pd.DataFrame(columns=COLUNAS_OI_SAIDA)

    df_agro = df_agro[df_agro["Asst"].isin(TICKERS_AGRO_OI)].copy()

    if df_agro.empty:
        return pd.DataFrame(columns=COLUNAS_OI_SAIDA)

    df_agro["data"] = pd.to_datetime(df_agro["RptDt"])
    df_agro["ticker"] = df_agro["Asst"]
    df_agro["ticker_completo"] = df_agro["TckrSymb"].str.strip()
    df_agro["vencimento_codigo"] = df_agro["XprtnCd"].str.strip()

    vct = df_agro["vencimento_codigo"].apply(_parse_vencimento_safe)
    df_agro["vencimento_ano"] = vct.apply(lambda x: x[0]).astype("Int64")
    df_agro["vencimento_mes"] = vct.apply(lambda x: x[1]).astype("Int64")

    df_agro["tipo"] = df_agro["ticker_completo"].apply(_classificar_tipo)
    df_agro["descricao"] = df_agro["ticker"].map(lambda t: B3_CONTRATOS_AGRO_INV.get(t, ""))
    df_agro["unidade"] = df_agro["ticker"].map(lambda t: UNIDADES.get(t, ""))

    df_agro["posicoes_abertas"] = pd.to_numeric(df_agro["OpnIntrst"], errors="coerce").astype(
        "Int64"
    )
    df_agro["variacao_posicoes"] = pd.to_numeric(df_agro["VartnOpnIntrst"], errors="coerce").astype(
        "Int64"
    )

    df_out = df_agro[COLUNAS_OI_SAIDA].reset_index(drop=True)

    logger.info("b3_oi_parse_ok", records=len(df_out))
    return df_out
