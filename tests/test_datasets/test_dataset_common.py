"""Testes parametrizados comuns a todos os datasets."""

import pytest

from agrobr.datasets import registry

ALL_DATASETS = sorted(registry.list_datasets())

DYNAMIC_PRODUCTS_DATASETS = {
    name for name in ALL_DATASETS if registry.get_dataset(name).info.products == []
}


@pytest.mark.parametrize("dataset_name", ALL_DATASETS)
class TestDatasetInfo:
    def test_info_name(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        assert ds.info.name == dataset_name

    def test_info_has_products(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        if dataset_name in DYNAMIC_PRODUCTS_DATASETS:
            assert ds.info.products == []
        else:
            assert len(ds.info.products) > 0
            assert all(isinstance(p, str) for p in ds.info.products)

    def test_info_has_sources(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        assert len(ds.info.sources) > 0
        for source in ds.info.sources:
            assert isinstance(source.name, str)
            assert source.name
            assert callable(source.fetch_fn)

    def test_info_contract_version(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        assert isinstance(ds.info.contract_version, str)
        assert ds.info.contract_version in {"1.0", "1.1"}

    def test_info_update_frequency(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        assert ds.info.update_frequency in {
            "daily",
            "monthly",
            "yearly",
            "quarterly",
            "continuous",
            "weekly",
            "decennial",
            "never",
        }

    def test_info_to_dict(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        info_dict = ds.info.to_dict()
        assert info_dict["name"] == dataset_name
        assert isinstance(info_dict["sources"], list)
        assert len(info_dict["sources"]) > 0
        assert isinstance(info_dict["products"], list)
        if dataset_name not in DYNAMIC_PRODUCTS_DATASETS:
            assert len(info_dict["products"]) > 0
        assert "contract_version" in info_dict


DATASETS_WITH_PRODUCTS = [d for d in ALL_DATASETS if d not in DYNAMIC_PRODUCTS_DATASETS]


@pytest.mark.parametrize("dataset_name", DATASETS_WITH_PRODUCTS)
class TestDatasetValidation:
    def test_validate_produto_valid(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        first_product = ds.info.products[0]
        ds._validate_produto(first_product)
        assert first_product in ds.info.products

    def test_validate_produto_invalid(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        with pytest.raises(ValueError, match="banana_inexistente"):
            ds._validate_produto("banana_inexistente")


@pytest.mark.parametrize("dataset_name", ALL_DATASETS)
class TestDatasetRegistry:
    def test_registered_in_registry(self, dataset_name):
        assert dataset_name in registry.list_datasets()

    def test_accessible_via_get_dataset(self, dataset_name):
        ds = registry.get_dataset(dataset_name)
        assert ds.info.name == dataset_name

    def test_list_products(self, dataset_name):
        products = registry.list_products(dataset_name)
        assert isinstance(products, list)
        if dataset_name not in DYNAMIC_PRODUCTS_DATASETS:
            assert len(products) > 0
