from __future__ import annotations

import warnings

import pytest

from agrobr.utils.warnings import warn_once, warn_once_reset


@pytest.fixture(autouse=True)
def _clean_state():
    warn_once_reset()
    yield
    warn_once_reset()


def test_warn_once_emits_warning():
    with pytest.warns(UserWarning, match="test message"):
        warn_once("test_key", "test message")


def test_warn_once_no_double_warning():
    warn_once("test_key", "first call")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        warn_once("test_key", "second call should not warn")


def test_warn_once_reset_all():
    warn_once("k1", "msg1")
    warn_once("k2", "msg2")

    warn_once_reset()

    with pytest.warns(UserWarning, match="msg1"):
        warn_once("k1", "msg1")


def test_warn_once_reset_specific_key():
    warn_once("k1", "msg1")
    warn_once("k2", "msg2")

    warn_once_reset("k1")

    with pytest.warns(UserWarning, match="msg1"):
        warn_once("k1", "msg1")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        warn_once("k2", "should not warn")


def _caller_helper() -> list[warnings.WarningMessage]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        warn_once("stack_test", "stacklevel check")
    return caught


def test_warn_once_stacklevel():
    caught = _caller_helper()
    assert len(caught) == 1
    assert caught[0].filename == __file__
