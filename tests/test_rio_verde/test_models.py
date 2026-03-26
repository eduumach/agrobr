from agrobr.rio_verde.models import COLUNAS_SAIDA, MIN_PDF_SIZE, SAFRAS_URLS


def test_safras_has_entries():
    assert len(SAFRAS_URLS) >= 2


def test_all_urls_are_https():
    for url in SAFRAS_URLS.values():
        assert url.startswith("https://")


def test_colunas_has_10_fields():
    assert len(COLUNAS_SAIDA) == 10


def test_min_pdf_size():
    assert MIN_PDF_SIZE == 50_000
