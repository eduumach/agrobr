from agrobr.zarc.models import COLUNAS_SAIDA, CULTURAS_ZARC, extract_safras, match_safra_resource


def test_culturas_zarc_all_mapped():
    for raw, canon in CULTURAS_ZARC.items():
        assert isinstance(raw, str) and raw
        assert isinstance(canon, str) and canon


def test_colunas_saida_count():
    assert len(COLUNAS_SAIDA) == 46


def test_colunas_saida_dec_range():
    dec_cols = [c for c in COLUNAS_SAIDA if c.startswith("dec")]
    assert len(dec_cols) == 36
    assert dec_cols[0] == "dec1"
    assert dec_cols[-1] == "dec36"


def test_match_safra_resource():
    resources = [
        {"name": "Tabua de Risco - Safra 2025/2026", "url": "https://x/2025.csv", "format": "CSV"},
        {"name": "Tabua de Risco - Safra 2024/2025", "url": "https://x/2024.csv", "format": "CSV"},
        {"name": "Dicionario", "url": "https://x/dict.pdf", "format": "PDF"},
    ]
    assert match_safra_resource(resources, "2025/2026") == "https://x/2025.csv"
    assert match_safra_resource(resources, "2024/2025") == "https://x/2024.csv"
    assert match_safra_resource(resources, "2023/2024") is None


def test_match_safra_perene():
    resources = [
        {"name": "Tabua de Risco - Safra perene", "url": "https://x/perene.csv", "format": "CSV"},
        {"name": "Tabua de Risco - Safra 2025/2026", "url": "https://x/2025.csv", "format": "CSV"},
    ]
    assert match_safra_resource(resources, "perene") == "https://x/perene.csv"


def test_extract_safras_sorted_perene_last():
    resources = [
        {"name": "Safra perene", "url": "https://x/p.csv", "format": "CSV"},
        {"name": "Safra 2025/2026", "url": "https://x/25.csv", "format": "CSV"},
        {"name": "Safra 2016/2017", "url": "https://x/16.csv", "format": "CSV"},
        {"name": "Safra 2020/2021", "url": "https://x/20.csv", "format": "CSV"},
        {"name": "Dicionario", "url": "https://x/d.pdf", "format": "PDF"},
    ]
    result = extract_safras(resources)
    assert result == ["2016/2017", "2020/2021", "2025/2026", "perene"]
