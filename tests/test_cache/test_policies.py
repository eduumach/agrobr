from __future__ import annotations

from datetime import datetime

from agrobr.cache.policies import (
    POLICIES,
    CachePolicy,
    calculate_expiry,
    format_ttl,
    get_next_update_info,
    get_policy,
)
from agrobr.constants import Fonte
from agrobr.utils.time import utcnow


class TestFormatTTL:
    def test_seconds(self):
        assert format_ttl(30) == "30 segundos"

    def test_one_minute(self):
        assert format_ttl(60) == "1 minuto"

    def test_multiple_minutes(self):
        assert format_ttl(120) == "2 minutos"

    def test_one_hour(self):
        assert format_ttl(3600) == "1 hora"

    def test_multiple_hours(self):
        assert format_ttl(7200) == "2 horas"

    def test_one_day(self):
        assert format_ttl(86400) == "1 dia"

    def test_multiple_days(self):
        assert format_ttl(172800) == "2 dias"

    def test_30_days(self):
        assert format_ttl(30 * 86400) == "30 dias"


class TestGetNextUpdateInfo:
    def test_smart_expiry_source(self):
        info = get_next_update_info("cepea_diario")
        assert info["type"] == "smart"
        assert "expires_at" in info
        assert "18h" in info["description"]

    def test_ttl_source(self):
        info = get_next_update_info(Fonte.CONAB)
        assert info["type"] == "ttl"
        assert "ttl" in info
        assert "description" in info

    def test_noticias_agricolas_smart(self):
        info = get_next_update_info(Fonte.NOTICIAS_AGRICOLAS)
        assert info["type"] == "smart"


class TestGetPolicy:
    def test_string_key_direct(self):
        policy = get_policy("cepea_diario")
        assert policy.smart_expiry is True

    def test_fonte_enum(self):
        policy = get_policy(Fonte.CEPEA)
        assert isinstance(policy, CachePolicy)

    def test_string_fonte_value(self):
        policy = get_policy("cepea")
        assert isinstance(policy, CachePolicy)

    def test_unknown_string_fallback(self):
        policy = get_policy("unknown_source_xyz")
        assert policy == POLICIES["cepea_diario"]

    def test_with_endpoint(self):
        policy = get_policy(Fonte.CONAB, endpoint="safras")
        assert isinstance(policy, CachePolicy)


class TestCalculateExpiry:
    def test_smart_expiry(self):
        expiry = calculate_expiry("cepea_diario")
        assert isinstance(expiry, datetime)
        assert expiry > utcnow()

    def test_ttl_expiry(self):
        before = utcnow()
        expiry = calculate_expiry(Fonte.CONAB)
        assert expiry > before
