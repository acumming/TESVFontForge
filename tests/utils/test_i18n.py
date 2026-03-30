"""Tests for the i18n (internationalisation) utility module."""

import os
import threading

import pytest

from utils.i18n import (
    detect_system_locale,
    get_language,
    list_available_languages,
    set_language,
    tr,
)


# ---------------------------------------------------------------------------
# set_language / get_language
# ---------------------------------------------------------------------------

def test_set_language_explicit_japanese():
    """set_language with an explicit code activates that language."""
    result = set_language("ja-jp")
    assert result == "ja-jp"
    assert get_language() == "ja-jp"


def test_set_language_explicit_english():
    """set_language with an explicit code activates that language."""
    result = set_language("en-us")
    assert result == "en-us"
    assert get_language() == "en-us"


def test_set_language_normalises_case():
    """Language codes are normalised to lower-case."""
    result = set_language("JA-JP")
    assert result == "ja-jp"


def test_set_language_unknown_falls_back_to_default():
    """An unknown language code falls back to the application default."""
    from const import DEFAULT_LANG_CODE
    result = set_language("xx-yy")
    assert result == DEFAULT_LANG_CODE


def test_set_language_none_does_not_raise():
    """Calling set_language(None) should not raise and must return a string."""
    result = set_language(None)
    assert isinstance(result, str)
    assert len(result) > 0


def test_set_language_returns_active_code():
    """set_language returns the code that is actually active."""
    code = set_language("en-us")
    assert get_language() == code


# ---------------------------------------------------------------------------
# tr – basic key lookup
# ---------------------------------------------------------------------------

def test_tr_known_key_japanese():
    """tr returns the Japanese string for a known key."""
    set_language("ja-jp")
    assert tr("common.select") == "選択"


def test_tr_known_key_english():
    """tr returns the English string for a known key."""
    set_language("en-us")
    assert tr("common.select") == "Select"


def test_tr_nested_key():
    """tr resolves deeply nested dot-notation keys."""
    set_language("en-us")
    assert tr("single_font.metrics_labels.ascent") == "Ascent"


def test_tr_missing_key_returns_key_itself():
    """tr returns the raw key when the key is not in the catalogue."""
    set_language("en-us")
    missing = "no.such.key.at.all"
    assert tr(missing) == missing


def test_tr_missing_key_with_default():
    """tr returns the explicit default when the key is absent."""
    set_language("en-us")
    assert tr("no.such.key", default="fallback text") == "fallback text"


def test_tr_interpolation():
    """Placeholder interpolation via str.format works correctly."""
    set_language("en-us")
    result = tr("common.errors.not_found", label="Font", path="/tmp/x.ttf")
    assert "Font" in result
    assert "/tmp/x.ttf" in result


def test_tr_interpolation_japanese():
    """Placeholder interpolation works in Japanese strings too."""
    set_language("ja-jp")
    result = tr("common.errors.not_found", label="フォント", path="/tmp/x.ttf")
    assert "フォント" in result
    assert "/tmp/x.ttf" in result


def test_tr_bad_interpolation_returns_unformatted():
    """tr returns the unformatted string when interpolation fails."""
    set_language("en-us")
    # Provide a wrong kwarg name; should not raise
    result = tr("common.errors.not_found", wrong_key="oops")
    assert isinstance(result, str)


def test_tr_auto_initialises_language():
    """tr auto-initialises the language when the catalogue is empty."""
    import utils.i18n as i18n_mod
    # Temporarily clear the internal state to simulate a cold start.
    original_code = i18n_mod._current_lang_code
    original_data = i18n_mod._current_lang_data
    try:
        i18n_mod._current_lang_data = {}
        result = tr("common.select")
        # Should return a string (either a translation or the key fallback).
        assert isinstance(result, str)
    finally:
        i18n_mod._current_lang_code = original_code
        i18n_mod._current_lang_data = original_data


# ---------------------------------------------------------------------------
# detect_system_locale
# ---------------------------------------------------------------------------

def test_detect_system_locale_returns_string():
    """detect_system_locale always returns a non-empty string."""
    result = detect_system_locale()
    assert isinstance(result, str)
    assert len(result) > 0


def test_detect_system_locale_from_env(monkeypatch):
    """LANG environment variable is respected by detect_system_locale."""
    monkeypatch.setenv("LANG", "en_US.UTF-8")
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.delenv("LANGUAGE", raising=False)
    result = detect_system_locale()
    assert result == "en-us"


def test_detect_system_locale_japanese_env(monkeypatch):
    """Japanese LANG is normalised correctly."""
    monkeypatch.setenv("LANG", "ja_JP.UTF-8")
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.delenv("LANGUAGE", raising=False)
    result = detect_system_locale()
    assert result == "ja-jp"


def test_detect_system_locale_c_locale_falls_back(monkeypatch):
    """C / POSIX locales are treated as 'no preference' and fall back."""
    from const import DEFAULT_LANG_CODE
    monkeypatch.setenv("LANG", "C.UTF-8")
    monkeypatch.delenv("LC_ALL", raising=False)
    monkeypatch.delenv("LC_MESSAGES", raising=False)
    monkeypatch.delenv("LANGUAGE", raising=False)
    result = detect_system_locale()
    # With all env vars unset and a C locale, should fall back to default.
    assert result == DEFAULT_LANG_CODE


# ---------------------------------------------------------------------------
# list_available_languages
# ---------------------------------------------------------------------------

def test_list_available_languages_returns_list():
    """list_available_languages returns a list."""
    langs = list_available_languages()
    assert isinstance(langs, list)


def test_list_available_languages_contains_shipped_locales():
    """The bundled ja-jp and en-us catalogues are reported as available."""
    langs = list_available_languages()
    assert "ja-jp" in langs
    assert "en-us" in langs


def test_list_available_languages_is_sorted():
    """The returned list is in sorted order."""
    langs = list_available_languages()
    assert langs == sorted(langs)


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------

def test_set_language_thread_safe():
    """Concurrent calls to set_language must not raise exceptions."""
    errors: list[Exception] = []
    errors_lock = threading.Lock()

    def worker(lang: str) -> None:
        try:
            for _ in range(50):
                set_language(lang)
                _ = tr("common.select")
        except Exception as exc:
            with errors_lock:
                errors.append(exc)

    threads = [
        threading.Thread(target=worker, args=("ja-jp",)),
        threading.Thread(target=worker, args=("en-us",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Thread-safety errors: {errors}"
