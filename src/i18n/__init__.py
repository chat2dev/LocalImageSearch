"""Internationalization (i18n) module for multi-language support."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

# Default language
DEFAULT_LANGUAGE = "en"

# Cache for loaded translations
_translations: Dict[str, Dict[str, str]] = {}
_current_language: str = DEFAULT_LANGUAGE


def load_language(language: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    """
    Load translation file for the specified language.

    Args:
        language: Language code (e.g., 'en', 'zh')

    Returns:
        Dictionary of translations
    """
    if language in _translations:
        return _translations[language]

    lang_file = Path(__file__).parent / f"{language}.json"

    if not lang_file.exists():
        # Fall back to English if language file doesn't exist
        if language != DEFAULT_LANGUAGE:
            return load_language(DEFAULT_LANGUAGE)
        return {}

    with open(lang_file, 'r', encoding='utf-8') as f:
        translations = json.load(f)
        _translations[language] = translations
        return translations


def set_language(language: str):
    """
    Set the current language for the application.

    Args:
        language: Language code (e.g., 'en', 'zh')
    """
    global _current_language
    _current_language = language
    # Preload the language
    load_language(language)


def get_text(key: str, language: Optional[str] = None, **kwargs) -> str:
    """
    Get translated text for a given key.

    Args:
        key: Translation key
        language: Optional language override
        **kwargs: Format arguments for the text

    Returns:
        Translated text, or the key itself if not found
    """
    lang = language or _current_language
    translations = load_language(lang)

    text = translations.get(key, key)

    # Apply formatting if kwargs provided
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass

    return text


# Shorthand alias
t = get_text


__all__ = ["load_language", "set_language", "get_text", "t", "DEFAULT_LANGUAGE"]
