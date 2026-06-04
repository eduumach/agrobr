"""Tests for agrobr.health.registry module."""

from __future__ import annotations

from agrobr.constants import Fonte
from agrobr.health.registry import (
    HEALTH_REGISTRY,
    SOURCE_DATASET_MAP,
    SourceHealthConfig,
    get_affected_datasets,
)


class TestHealthRegistry:
    def test_all_fontes_in_registry(self):
        for fonte in Fonte:
            assert fonte in HEALTH_REGISTRY, f"{fonte} missing from HEALTH_REGISTRY"

    def test_registry_has_22_entries(self):
        assert len(HEALTH_REGISTRY) == len(Fonte)

    def test_all_urls_are_nonempty_strings(self):
        for fonte, config in HEALTH_REGISTRY.items():
            assert isinstance(config.url, str), f"{fonte} url is not a string"
            assert len(config.url) > 0, f"{fonte} has empty url"

    def test_config_is_frozen_dataclass(self):
        config = HEALTH_REGISTRY[Fonte.CEPEA]
        assert isinstance(config, SourceHealthConfig)

    def test_cepea_has_deep_check(self):
        assert HEALTH_REGISTRY[Fonte.CEPEA].has_deep_check is True

    def test_cepea_is_critical_tier(self):
        assert HEALTH_REGISTRY[Fonte.CEPEA].tier == "critical"

    def test_usda_requires_api_key(self):
        config = HEALTH_REGISTRY[Fonte.USDA]
        assert config.requires_api_key is True
        assert config.api_key_env_var == "AGROBR_USDA_API_KEY"

    def test_inmet_requires_api_key(self):
        config = HEALTH_REGISTRY[Fonte.INMET]
        assert config.requires_api_key is True
        assert config.api_key_env_var == "AGROBR_INMET_TOKEN"

    def test_comtrade_requires_api_key(self):
        config = HEALTH_REGISTRY[Fonte.COMTRADE]
        assert config.requires_api_key is True

    def test_ibge_uses_api_url(self):
        config = HEALTH_REGISTRY[Fonte.IBGE]
        assert "apisidra" in config.url

    def test_default_method_is_get(self):
        for config in HEALTH_REGISTRY.values():
            assert config.method in ("GET", "HEAD")

    def test_default_tier_is_standard(self):
        for fonte, config in HEALTH_REGISTRY.items():
            if fonte != Fonte.CEPEA:
                assert config.tier in ("standard", "best_effort"), f"{fonte} unexpected tier"


class TestSourceDatasetMap:
    def test_cepea_datasets(self):
        assert "preco_diario" in SOURCE_DATASET_MAP["cepea"]

    def test_conab_datasets(self):
        datasets = SOURCE_DATASET_MAP["conab"]
        assert "estimativa_safra" in datasets
        assert "producao_anual" in datasets

    def test_ibge_datasets(self):
        datasets = SOURCE_DATASET_MAP["ibge"]
        assert "estimativa_safra" in datasets
        assert "abate_trimestral" in datasets

    def test_unknown_source_returns_empty(self):
        assert get_affected_datasets(Fonte.DEFENSIVOS) == []

    def test_get_affected_datasets_cepea(self):
        result = get_affected_datasets(Fonte.CEPEA)
        assert result == ["preco_diario"]

    def test_get_affected_datasets_ibge(self):
        result = get_affected_datasets(Fonte.IBGE)
        assert len(result) == 12

    def test_get_affected_datasets_nasa_power(self):
        result = get_affected_datasets(Fonte.NASA_POWER)
        assert result == ["clima"]
