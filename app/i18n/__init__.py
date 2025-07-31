import importlib.resources
from typing import Any, Dict

import tomllib

_cache: Dict[str, Dict[str, Any]] = {}


def load_lang(lang: str) -> Dict[str, Any]:
    """Загружает языковой файл из кэша или с диска"""
    if lang in _cache:
        return _cache[lang]

    try:
        data = (
            importlib.resources.files(__package__).joinpath(f"{lang}.toml").read_bytes()
        )
        _cache[lang] = tomllib.loads(data.decode())
        return _cache[lang]
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        # Fallback к русскому языку
        if lang != "ru":
            return load_lang("ru")
        return {}


def t(key: str, lang: str = "ru") -> str:
    """
    Получает локализованную строку по ключу

    Args:
        key: Ключ в формате "section.key" (например "common.start_welcome")
        lang: Код языка ("ru", "en")

    Returns:
        Локализованная строка или ключ, если строка не найдена
    """
    parts = key.split(".")
    node = load_lang(lang)

    for part in parts:
        if isinstance(node, dict):
            node = node.get(part, {})
        else:
            return key

    return node if isinstance(node, str) else key


def clear_cache():
    """Очищает кэш локализации (для разработки)"""
    _cache.clear()
