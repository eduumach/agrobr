from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from agrobr.acervo_fundiario import client
from agrobr.exceptions import SourceUnavailableError


class TestBuildUrl:
    def test_basic_url(self):
        url = client._build_url("certificada_sigef_particular", "GO", max_features=100)
        assert "tema=certificada_sigef_particular_go" in url
        assert "typeName=certificada_sigef_particular_go" in url
        assert "maxFeatures=100" in url
        assert "service=WFS" in url
        assert "version=1.0.0" in url

    def test_uf_lowercased(self):
        url = client._build_url("assentamentos", "SP", max_features=10)
        assert "tema=assentamentos_sp" in url

    def test_with_bbox(self):
        url = client._build_url("assentamentos", "go", max_features=10, bbox=(-50, -16, -49, -15))
        assert "BBOX=-50,-16,-49,-15" in url

    def test_without_bbox(self):
        url = client._build_url("assentamentos", "go", max_features=10)
        assert "BBOX" not in url

    def test_with_property_names(self):
        url = client._build_url(
            "certificada_sigef_particular",
            "go",
            max_features=10,
            property_names=["parcela_codigo", "status"],
        )
        assert "propertyName=parcela_codigo,status" in url

    def test_without_property_names(self):
        url = client._build_url("certificada_sigef_particular", "go", max_features=10)
        assert "propertyName" not in url


class TestCheckExceptionReport:
    def test_service_exception_detected(self):
        content = b'<?xml version="1.0"?><ServiceExceptionReport>error</ServiceExceptionReport>'
        with pytest.raises(SourceUnavailableError):
            client._check_exception_report(content, "DF", "http://test")

    def test_exception_report_detected(self):
        content = b'<?xml version="1.0"?><ogc:ExceptionReport>error</ogc:ExceptionReport>'
        with pytest.raises(SourceUnavailableError):
            client._check_exception_report(content, "DF", "http://test")

    def test_ms_wfs_error_detected(self):
        content = b"msWFSGetFeature(): error in layer"
        with pytest.raises(SourceUnavailableError):
            client._check_exception_report(content, "DF", "http://test")

    def test_valid_gml_passes(self):
        content = b'<?xml version="1.0"?><wfs:FeatureCollection>data</wfs:FeatureCollection>'
        client._check_exception_report(content, "GO", "http://test")


@pytest.mark.asyncio
class TestFetchSigef:
    @patch("agrobr.acervo_fundiario.client.fetch_wfs", new_callable=AsyncMock)
    async def test_fetch_returns_content_and_url(self, mock_fetch):
        mock_fetch.return_value = b"<wfs:FeatureCollection></wfs:FeatureCollection>"
        content, url = await client.fetch_sigef("GO", "particular")
        assert content == mock_fetch.return_value
        assert "certificada_sigef_particular_go" in url

    @patch("agrobr.acervo_fundiario.client.fetch_wfs", new_callable=AsyncMock)
    async def test_tabular_uses_property_names(self, mock_fetch):
        mock_fetch.return_value = b"<wfs:FeatureCollection></wfs:FeatureCollection>"
        _, url = await client.fetch_sigef("GO", "particular", geo=False)
        assert "propertyName=" in url

    @patch("agrobr.acervo_fundiario.client.fetch_wfs", new_callable=AsyncMock)
    async def test_geo_omits_property_names(self, mock_fetch):
        mock_fetch.return_value = b"<wfs:FeatureCollection></wfs:FeatureCollection>"
        _, url = await client.fetch_sigef("GO", "particular", geo=True)
        assert "propertyName" not in url

    @patch("agrobr.acervo_fundiario.client.fetch_wfs", new_callable=AsyncMock)
    async def test_publico_layer(self, mock_fetch):
        mock_fetch.return_value = b"<wfs:FeatureCollection></wfs:FeatureCollection>"
        _, url = await client.fetch_sigef("SP", "publico")
        assert "certificada_sigef_publico_sp" in url


@pytest.mark.asyncio
class TestFetchSnci:
    @patch("agrobr.acervo_fundiario.client.fetch_wfs", new_callable=AsyncMock)
    async def test_privado_layer(self, mock_fetch):
        mock_fetch.return_value = b"<wfs:FeatureCollection></wfs:FeatureCollection>"
        _, url = await client.fetch_snci("GO", "privado")
        assert "imoveiscertificados_privado_go" in url

    @patch("agrobr.acervo_fundiario.client.fetch_wfs", new_callable=AsyncMock)
    async def test_publico_layer(self, mock_fetch):
        mock_fetch.return_value = b"<wfs:FeatureCollection></wfs:FeatureCollection>"
        _, url = await client.fetch_snci("GO", "publico")
        assert "imoveiscertificados_publico_go" in url


@pytest.mark.asyncio
class TestFetchAssentamentos:
    @patch("agrobr.acervo_fundiario.client.fetch_wfs", new_callable=AsyncMock)
    async def test_fetch_returns_url_with_layer(self, mock_fetch):
        mock_fetch.return_value = b"<wfs:FeatureCollection></wfs:FeatureCollection>"
        _, url = await client.fetch_assentamentos("GO")
        assert "assentamentos_go" in url

    @patch("agrobr.acervo_fundiario.client.fetch_wfs", new_callable=AsyncMock)
    async def test_with_bbox(self, mock_fetch):
        mock_fetch.return_value = b"<wfs:FeatureCollection></wfs:FeatureCollection>"
        _, url = await client.fetch_assentamentos("GO", bbox=(-50, -16, -49, -15))
        assert "BBOX=" in url
