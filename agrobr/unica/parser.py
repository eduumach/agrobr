from __future__ import annotations

import io
import re
from typing import Any, NamedTuple

import openpyxl
import pandas as pd
import structlog

from agrobr.exceptions import ParseError
from agrobr.normalize.regions import normalizar_uf, remover_acentos

from . import models

logger = structlog.get_logger()

SAFRA_CAPA_RE = re.compile(r"S\s*AFRA\s+(\d{4}/\d{4})", re.IGNORECASE)
POSICAO_RE = re.compile(r"Posi[çc][ãa]o\s+at[ée]\s+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
TABELA_TITULO_RE = re.compile(r"Tabela\s+(\d+)\.")
QUINZENA_LINE_RE = re.compile(r"^(\d{2}/\d{2})(?:\s+(.*))?$")
PRIMEIRO_NUMERO_RE = re.compile(r"-?\d[\d.,]*%?")
UNIDADE_XLSX_RE = re.compile(r"Unidade:\s*(.+)", re.IGNORECASE)


class ParsedQuinzenal(NamedTuple):
    resumo: pd.DataFrame
    series: pd.DataFrame
    safra: str
    posicao: pd.Timestamp


def _check_pdfplumber() -> Any:
    try:
        import pdfplumber

        return pdfplumber
    except ImportError:
        raise ImportError(
            "pdfplumber é necessário para parsear o relatório quinzenal da UNICA. "
            "Instale com: pip install agrobr[pdf]"
        ) from None


def _parse_error(reason: str, snippet: str = "") -> ParseError:
    return ParseError(
        source="unica",
        parser_version=models.PARSER_VERSION,
        reason=reason,
        html_snippet=snippet,
    )


def _normalizar_label(label: str) -> str:
    norm = remover_acentos(label.strip().lower())
    norm = re.sub(r"[^a-z0-9/()% -]", "", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return re.sub(r"\s+\d+$", "", norm)


NUMERO_BR_RE = re.compile(r"-?[\d.]+(?:,\d+)?")


def _token_to_float(token: str) -> float | None:
    """Converte token numérico BR estrito ('.' milhar, ',' decimal).

    O PDF da UNICA usa '34.631' para 34631 e '8.253.154' para 8253154 —
    semântica incompatível com parse_numeric_br (ponto único = decimal EN).
    safe_float cobriria os casos válidos, mas é leniente com tokens
    malformados; o fullmatch estrito aqui rejeita lixo de coluna deslocada
    no PDF em vez de convertê-lo silenciosamente.
    """
    raw = token.rstrip("%").strip()
    if not NUMERO_BR_RE.fullmatch(raw):
        return None
    return float(raw.replace(".", "").replace(",", "."))


def _split_label_e_tokens(line: str) -> tuple[str, list[float | None]]:
    match = PRIMEIRO_NUMERO_RE.search(line)
    if not match:
        return line.strip(), []
    label = line[: match.start()].strip()
    tokens = line[match.start() :].split()
    return label, [_token_to_float(t) for t in tokens]


def _quinzena_to_date(quinzena: str, safra: str) -> pd.Timestamp:
    dia, mes = (int(p) for p in quinzena.split("/"))
    ano_inicio = int(safra[:4])
    ano = ano_inicio if mes >= 5 or (mes == 4 and dia >= 16) else ano_inicio + 1
    return pd.Timestamp(year=ano, month=mes, day=dia)


def parse_quinzenal_pdf(pdf_bytes: bytes) -> ParsedQuinzenal:
    pdfplumber = _check_pdfplumber()

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        textos = [page.extract_text() or "" for page in pdf.pages]

    if not textos:
        raise _parse_error("PDF sem páginas legíveis")

    safra, posicao = _parse_capa(textos[0])
    paginas_tabelas = _localizar_tabelas(textos)

    resumo = _parse_resumo(paginas_tabelas, safra)
    series = _parse_series(paginas_tabelas, safra)

    _validate_resumo(resumo)
    _validate_series(series)

    return ParsedQuinzenal(resumo=resumo, series=series, safra=safra, posicao=posicao)


def _parse_capa(texto: str) -> tuple[str, pd.Timestamp]:
    safra_match = SAFRA_CAPA_RE.search(texto)
    posicao_match = POSICAO_RE.search(texto)
    if not safra_match or not posicao_match:
        raise _parse_error("Capa sem safra ou posição reconhecível", texto[:300])
    posicao = pd.to_datetime(posicao_match.group(1), format="%d/%m/%Y")
    return safra_match.group(1), posicao


def _localizar_tabelas(textos: list[str]) -> dict[int, str]:
    paginas: dict[int, str] = {}
    for texto in textos:
        for match in TABELA_TITULO_RE.finditer(texto):
            paginas.setdefault(int(match.group(1)), texto)
    faltantes = [n for n in (1, 2, 3, 4, 5, 6, 7) if n not in paginas]
    if faltantes:
        raise _parse_error(f"Tabelas ausentes no PDF: {faltantes}")
    return paginas


def _parse_resumo(paginas: dict[int, str], safra: str) -> pd.DataFrame:
    registros: list[dict[str, Any]] = []
    texto = paginas[1]
    periodo: str | None = None

    for line in texto.split("\n"):
        titulo = TABELA_TITULO_RE.match(line.strip())
        if titulo:
            num = int(titulo.group(1))
            periodo = {1: "acumulado", 2: "quinzena"}.get(num)
            continue
        if periodo is None:
            continue

        label, tokens = _split_label_e_tokens(line)
        label_norm = _normalizar_label(label)
        if not label_norm or not tokens:
            continue

        valores: list[tuple[float | None, float | None, float | None]]
        if len(tokens) == 6 and label_norm in models.MIX_LABELS:
            produto = models.MIX_LABELS[label_norm]
            unidade = "pct"
            valores = [
                (tokens[0], tokens[1], None),
                (tokens[2], tokens[3], None),
                (tokens[4], tokens[5], None),
            ]
        elif len(tokens) == 9 and label_norm in models.RESUMO_LABELS:
            produto, unidade = models.RESUMO_LABELS[label_norm]
            valores = [
                (tokens[0], tokens[1], tokens[2]),
                (tokens[3], tokens[4], tokens[5]),
                (tokens[6], tokens[7], tokens[8]),
            ]
        else:
            continue

        for regiao, (anterior, atual, variacao) in zip(
            ["centro_sul", "sao_paulo", "demais_estados"], valores, strict=True
        ):
            if atual is None or anterior is None:
                raise _parse_error(
                    f"Resumo: '{label_norm}' ({regiao}) com valor não numérico",
                    line,
                )
            registros.append(
                {
                    "produto": produto,
                    "regiao": regiao,
                    "safra": safra,
                    "periodo": periodo,
                    "valor": atual,
                    "valor_safra_anterior": anterior,
                    "variacao_pct": variacao,
                    "unidade": unidade,
                }
            )

    if not registros:
        raise _parse_error("Nenhuma linha reconhecida nas Tabelas 1-2")

    return pd.DataFrame(registros, columns=models.COLUNAS_RESUMO)


def _parse_series(paginas: dict[int, str], safra: str) -> pd.DataFrame:
    registros: list[dict[str, Any]] = []

    for produto, (numero_tabela, unidade) in models.PRODUTOS_QUINZENAL.items():
        texto = paginas[numero_tabela]
        secao = texto.split(f"Tabela {numero_tabela}.", 1)[1]
        proxima = re.search(r"Tabela \d+\.", secao)
        if proxima:
            secao = secao[: proxima.start()]

        for line in secao.split("\n"):
            match = QUINZENA_LINE_RE.match(line.strip())
            if not match:
                continue
            quinzena = match.group(1)
            resto = match.group(2) or ""
            tokens = [_token_to_float(t) for t in resto.split()]
            if not tokens:
                continue
            if len(tokens) != 9:
                raise _parse_error(
                    f"Tabela {numero_tabela}: quinzena {quinzena} com {len(tokens)} "
                    f"valores (esperado 9)",
                    line,
                )
            if any(t is None for t in tokens):
                raise _parse_error(
                    f"Tabela {numero_tabela}: quinzena {quinzena} com token não numérico",
                    line,
                )

            for regiao, offset in zip(models.REGIOES_QUINZENAL, [0, 3, 6], strict=True):
                registros.append(
                    {
                        "data": _quinzena_to_date(quinzena, safra),
                        "quinzena": quinzena,
                        "safra": safra,
                        "produto": produto,
                        "regiao": regiao,
                        "valor": tokens[offset + 1],
                        "valor_safra_anterior": tokens[offset],
                        "variacao_pct": tokens[offset + 2],
                        "unidade": unidade,
                    }
                )

    if not registros:
        raise _parse_error("Nenhuma quinzena com dados nas Tabelas 3-7")

    df = pd.DataFrame(registros, columns=models.COLUNAS_SERIES)
    return df.sort_values(["produto", "data", "regiao"]).reset_index(drop=True)


def _validate_resumo(df: pd.DataFrame) -> None:
    produtos = set(df["produto"])
    obrigatorios = {"cana", "acucar", "etanol_total", "mix_acucar", "mix_etanol"}
    faltantes = obrigatorios - produtos
    if faltantes:
        raise _parse_error(f"Produtos ausentes no resumo: {sorted(faltantes)}")

    mix = df[df["produto"].isin(["mix_acucar", "mix_etanol"])]["valor"].dropna()
    if not mix.between(0, 100).all():
        raise _parse_error("Mix fora do intervalo 0-100%")

    atr_kg = df[df["produto"] == "atr_por_tonelada"]["valor"].dropna()
    if not atr_kg.between(60, 160).all():
        raise _parse_error("ATR/tonelada fora do intervalo plausível 60-160 kg/t")


def _validate_series(df: pd.DataFrame) -> None:
    valores = df[["valor", "valor_safra_anterior"]]
    if (valores.fillna(0) < 0).any().any():
        raise _parse_error("Valores negativos nas séries quinzenais")

    for produto, maximo in models.SANIDADE_MAX_SERIES.items():
        serie = df[df["produto"] == produto]["valor"].dropna()
        if not serie.empty and serie.max() > maximo:
            raise _parse_error(
                f"Valor de {produto} acima do plausível: {serie.max():.0f} > {maximo:.0f}"
            )


def parse_historico_xlsx(content: bytes, produto: str) -> pd.DataFrame:
    workbook = openpyxl.load_workbook(io.BytesIO(content), data_only=True, read_only=True)
    rows = [list(row) for row in workbook.active.iter_rows(values_only=True)]
    workbook.close()

    unidade = _extrair_unidade_xlsx(rows)
    header_idx, safras = _extrair_header_xlsx(rows)

    registros: list[dict[str, Any]] = []
    for row in rows[header_idx + 1 :]:
        nome = str(row[0]).strip() if row[0] is not None else ""
        if not nome:
            continue
        if nome.lower().startswith(("source", "fonte")):
            break

        localidade = _normalizar_localidade(nome)
        if localidade is None:
            raise _parse_error(f"Localidade não reconhecida no XLSX: '{nome}'")

        for idx, safra in safras:
            valor = row[idx]
            registros.append(
                {
                    "safra": safra,
                    "localidade": localidade,
                    "produto": produto,
                    "valor": float(valor) if isinstance(valor, (int, float)) else None,
                    "unidade": unidade,
                }
            )

    if not registros:
        raise _parse_error("Nenhuma linha de dados no XLSX histórico")

    df = pd.DataFrame(registros, columns=models.COLUNAS_HISTORICO)
    _validate_historico(df, produto)
    return df.sort_values(["safra", "localidade"]).reset_index(drop=True)


def _extrair_unidade_xlsx(rows: list[list[Any]]) -> str:
    for row in rows[:10]:
        for cell in row:
            if cell is None:
                continue
            match = UNIDADE_XLSX_RE.search(str(cell))
            if match:
                bruto = _normalizar_label(match.group(1))
                unidade = models.UNIDADES_HISTORICO.get(bruto)
                if unidade is None:
                    raise _parse_error(f"Unidade desconhecida no XLSX: '{match.group(1)}'")
                return unidade
    raise _parse_error("Linha 'Unidade:' não encontrada no XLSX")


def _extrair_header_xlsx(rows: list[list[Any]]) -> tuple[int, list[tuple[int, str]]]:
    for i, row in enumerate(rows):
        primeiro = str(row[0]).strip() if row[0] is not None else ""
        if primeiro.lower().startswith("estado"):
            safras = [
                (j, str(cell).strip())
                for j, cell in enumerate(row)
                if cell is not None and models.SAFRA_RE.match(str(cell).strip())
            ]
            if not safras:
                raise _parse_error("Header do XLSX sem colunas de safra")
            return i, safras
    raise _parse_error("Header 'Estado/Safra' não encontrado no XLSX")


def _normalizar_localidade(nome: str) -> str | None:
    chave = _normalizar_label(nome)
    if chave in models.AGREGADOS_HISTORICO:
        return models.AGREGADOS_HISTORICO[chave]
    return normalizar_uf(nome)


def _validate_historico(df: pd.DataFrame, produto: str) -> None:
    valores = df["valor"].dropna()
    if (valores < 0).any():
        raise _parse_error("Valores negativos no histórico")

    maximo = models.SANIDADE_MAX_HISTORICO.get(produto)
    if maximo and not valores.empty and valores.max() > maximo:
        raise _parse_error(
            f"Valor de {produto} acima do plausível: {valores.max():.0f} > {maximo:.0f}"
        )
