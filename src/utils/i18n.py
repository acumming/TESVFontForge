"""
Internationalisation (i18n) utilities.

Language catalogues are stored as YAML files under ``data/lang/``, named
after their BCP-47 language tag (e.g. ``ja-jp.yml``, ``en-us.yml``).
Strings are addressed with dot-notation keys and support ``{named}``
placeholder interpolation via :func:`str.format`.

Typical usage
-------------
Call :func:`set_language` once at application startup (``main.py``) to
load the appropriate catalogue.  Pass an explicit language code or omit
the argument to let the module detect the OS locale automatically::

    from utils.i18n import set_language
    set_language()          # auto-detect system locale
    set_language("en-us")   # explicit override

Then translate keys anywhere in the codebase::

    from utils.i18n import tr
    label = tr("common.select")
    msg   = tr("single_font.messages.task_done", task_name="MyFont")

Available helpers
-----------------
- :func:`detect_system_locale` – detect the OS preferred language code
- :func:`list_available_languages` – list language codes with catalogue files
- :func:`set_language` – load a catalogue and make it active
- :func:`get_language` – return the currently active language code
- :func:`tr` – look up and interpolate a translation key
"""
from __future__ import annotations

import locale
import os
import threading
from pathlib import Path
from typing import Any

import yaml

from const import DEFAULT_LANG_CODE, DEFAULT_LANG_FILE, ENCODE, LANG_DIR

# Module-level state protected by a lock for thread-safe updates.
_lock = threading.Lock()
_current_lang_code: str = DEFAULT_LANG_CODE
_current_lang_data: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _read_lang_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding=ENCODE) as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            return {}
        return data
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_system_locale() -> str:
    """Detect the operating system's preferred language and return it as a
    normalised BCP-47 tag (lower-case, hyphen-separated, e.g. ``"ja-jp"``).

    Detection is attempted in the following order:

    1. ``LC_ALL``, ``LC_MESSAGES``, ``LANG``, ``LANGUAGE`` environment
       variables (Unix convention; also respected on Windows when set).
    2. :func:`locale.getlocale` with ``LC_MESSAGES`` category (Python 3
       standard; avoids the deprecated :func:`locale.getdefaultlocale`).
    3. ``GetUserDefaultLocaleName`` via *ctypes* on Windows platforms.
    4. Falls back to :data:`~const.DEFAULT_LANG_CODE` when no locale can be
       determined.

    :return: Detected language code, e.g. ``"ja-jp"`` or ``"en-us"``.
    :rtype: str
    """
    # 1. Environment variables (standard on Unix; may be set on Windows too)
    for var in ("LC_ALL", "LC_MESSAGES", "LANG", "LANGUAGE"):
        val = os.environ.get(var, "").split(":")[0].strip()
        if val and val not in ("C", "POSIX", "C.UTF-8", "C.utf8"):
            lang_part = val.split(".")[0].split("@")[0]  # strip encoding / modifier
            if "_" in lang_part or "-" in lang_part:
                return lang_part.lower().replace("_", "-")

    # 2. locale module (Python 3.x; avoids deprecated getdefaultlocale)
    try:
        code = locale.getlocale(locale.LC_MESSAGES)[0]
        if code and code not in ("C", "POSIX"):
            return code.lower().replace("_", "-").split(".")[0]
    except Exception:
        pass

    # 3. Windows: GetUserDefaultLocaleName (e.g. "ja-JP" -> "ja-jp")
    try:
        import ctypes  # Windows-only; guarded by the try/except
        buf = ctypes.create_unicode_buffer(85)
        ctypes.windll.kernel32.GetUserDefaultLocaleName(buf, 85)  # type: ignore[attr-defined]
        tag = buf.value.strip()
        if tag:
            return tag.lower()
    except Exception:
        pass

    return DEFAULT_LANG_CODE


def list_available_languages() -> list[str]:
    """Return a sorted list of language codes for which a translation
    catalogue (``*.yml``) exists under ``data/lang/``.

    :return: Sorted list of language codes, e.g. ``["en-us", "ja-jp"]``.
    :rtype: list[str]
    """
    return sorted(p.stem for p in LANG_DIR.glob("*.yml"))


def set_language(lang_code: str | None = None) -> str:
    """Load the translation catalogue for *lang_code* and make it active.

    When *lang_code* is ``None`` (the default), the system locale is
    detected automatically via :func:`detect_system_locale`.  If no
    catalogue file exists for the requested code, the function falls back
    to :data:`~const.DEFAULT_LANG_CODE`.

    This function is thread-safe: concurrent calls update the shared state
    atomically.

    :param lang_code: BCP-47 tag such as ``"ja-jp"`` or ``"en-us"``.
        Pass ``None`` to auto-detect from the operating system locale.
    :type lang_code: str | None
    :return: The language code that was actually activated.
    :rtype: str
    """
    global _current_lang_code, _current_lang_data

    if lang_code is None:
        requested = detect_system_locale()
    else:
        requested = lang_code.strip().lower()

    target_file = LANG_DIR / f"{requested}.yml"
    data = _read_lang_file(target_file)

    if not data and requested != DEFAULT_LANG_CODE:
        # Requested language unavailable; fall back to the application default.
        requested = DEFAULT_LANG_CODE
        data = _read_lang_file(DEFAULT_LANG_FILE)

    with _lock:
        _current_lang_code = requested
        _current_lang_data = data

    return _current_lang_code


def get_language() -> str:
    """Return the currently active language code.

    :return: Active language code, e.g. ``"ja-jp"``.
    :rtype: str
    """
    return _current_lang_code


def tr(key: str, default: str | None = None, **kwargs: Any) -> str:
    """Look up *key* in the active translation catalogue and return the
    translated string.

    Keys use dot notation to address nested YAML nodes, for example
    ``"common.select"`` or ``"single_font.tooltips.base_font"``.
    Placeholders in translation values use Python :meth:`str.format` syntax:
    ``"{name}"`` is replaced by the correspondingly named keyword argument.

    When the key is not found, *default* is returned if supplied; otherwise
    the raw key string is returned.  This ensures the UI remains functional
    even when a translation is missing, and makes untranslated keys easy to
    spot during development.

    :param key: Dot-separated translation key, e.g. ``"common.select"``.
    :type key: str
    :param default: Fallback string returned when *key* is absent from the
        catalogue.  Pass ``None`` (the default) to fall back to the key
        itself.
    :type default: str | None
    :param kwargs: Named values substituted into ``{placeholder}`` slots in
        the translated string.
    :return: Translated (and interpolated) string.
    :rtype: str
    """
    if not _current_lang_data:
        set_language()

    node: Any = _current_lang_data
    for part in key.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            node = None
            break

    # Fall back to explicit default, or to the key itself when no default given.
    text = default if default is not None else key
    if isinstance(node, str):
        text = node

    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
