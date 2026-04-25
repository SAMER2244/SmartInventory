"""
SmartInventory i18n — Translation Helper
=================================
Provides:
    - t(key)       → returns the translated string for the active language
    - get_lang()   → returns the current language code ('tr', 'en', 'ar')
    - LANG_OPTIONS → display-name-to-code mapping for the language picker
"""

import streamlit as st

from core.translations import TRANSLATIONS

# Display labels → internal language codes
LANG_OPTIONS: dict[str, str] = {
    "Türkçe": "tr",
    "English": "en",
    "العربية": "ar",
}

# Reverse mapping for selectbox default index
_CODE_TO_LABEL: dict[str, str] = {v: k for k, v in LANG_OPTIONS.items()}


def get_lang() -> str:
    """Return the active language code from session state (default: Turkish)."""
    return st.session_state.get("lang", "tr")


def t(key: str, **kwargs) -> str:
    """
    Translate *key* into the active language.

    Supports ``str.format()`` interpolation::

        t('success_restock', updated=5, new=2)
        # → "Success! 5 updated, 2 new parts added."

    Falls back to English, then to the raw key name if nothing matches.
    """
    lang = get_lang()
    entry = TRANSLATIONS.get(key, {})
    text = entry.get(lang) or entry.get("en") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass  # Return un-interpolated text rather than crashing
    return text
