from __future__ import annotations

import io
import zipfile

import httpx
import structlog

from agrobr.constants import MIN_ZIP_SIZE, HTTPSettings
from agrobr.http.retry import retry_on_status
from agrobr.http.user_agents import UserAgentRotator

logger = structlog.get_logger()

FTP_BASE = "https://ftp.ibge.gov.br/Censo_Agropecuario/Censo_Agropecuario_1995_96"

LEGACY_TEMAS: dict[str, str] = {
    "tecnologia": "Tab_3Mn",
    "pessoal_ocupado": "Tab_6Mn",
    "maquinas": "Tab_7Mn",
    "producao_animal": "Tab_9Mn",
    "valor_producao": "Tab_10Mn",
    "financeiro": "Tab_11Mn",
}

UF_DIRS: dict[str, str] = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapa",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceara",
    "DF": "Distrito_Federal",
    "ES": "Espirito_Santo",
    "GO": "Goias",
    "MA": "Maranhao",
    "MT": "Mato_Grosso",
    "MS": "Mato_Grosso_do_Sul",
    "MG": "Minas_Gerais",
    "PA": "Para",
    "PB": "Paraiba",
    "PR": "Parana",
    "PE": "Pernambuco",
    "PI": "Piaui",
    "RJ": "Rio_de_Janeiro",
    "RN": "Rio_Grande_do_Norte",
    "RS": "Rio_Grande_do_Sul",
    "RO": "Rondonia",
    "RR": "Roraima",
    "SC": "Santa_Catarina",
    "SP": "Sao_Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins",
}

_settings = HTTPSettings()

TIMEOUT = httpx.Timeout(
    connect=_settings.timeout_connect,
    read=180.0,
    write=_settings.timeout_write,
    pool=_settings.timeout_pool,
)


async def download_legacy_zip(filename: str, uf_dir: str = "Brasil") -> bytes:
    url = f"{FTP_BASE}/{uf_dir}/{filename}.zip"
    logger.info("ibge_legacy_download", url=url)

    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        headers=UserAgentRotator.get_headers(source="ibge"),
        follow_redirects=True,
    ) as http:
        response = await retry_on_status(
            lambda: http.get(url),
            source="ibge_censo_legado",
        )
        response.raise_for_status()

        content = response.content
        if len(content) < MIN_ZIP_SIZE:
            from agrobr.exceptions import SourceUnavailableError

            raise SourceUnavailableError(
                source="ibge_censo_agro_legado",
                url=url,
                last_error=f"ZIP too small ({len(content)} bytes)",
            )

        logger.info(
            "ibge_legacy_download_ok",
            url=url,
            size_bytes=len(content),
        )
        return content


def extract_xls_from_zip(zip_bytes: bytes, pattern: str | None = None) -> list[tuple[str, bytes]]:
    results: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        for name in zf.namelist():
            if not name.lower().endswith(".xls"):
                continue
            if pattern and pattern.lower() not in name.lower():
                continue
            results.append((name, zf.read(name)))
    return results
