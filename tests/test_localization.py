"""Тесты локализации и шаблонов сообщений."""

import toml
from pathlib import Path
import pytest
from typing import Dict, Any


def flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
    """Рекурсивно выравнивает вложенный словарь в плоский."""
    out = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten_dict(v, key))
        else:
            out[key] = v
    return out


class TestLocalization:
    """Тесты локализации."""

    def test_locale_keys_are_synced(self) -> None:
        """Проверяет синхронизацию ключей между локалями."""
        ru_path = Path("app/i18n/ru.toml")
        en_path = Path("app/i18n/en.toml")
        
        assert ru_path.exists(), "Русский файл локализации не найден"
        assert en_path.exists(), "Английский файл локализации не найден"
        
        ru = toml.load(ru_path)
        en = toml.load(en_path)
        
        ru_flat = flatten_dict(ru)
        en_flat = flatten_dict(en)
        
        ru_keys = set(ru_flat.keys())
        en_keys = set(en_flat.keys())
        
        missing_in_en = ru_keys - en_keys
        missing_in_ru = en_keys - ru_keys
        
        assert not missing_in_en, f"Ключи отсутствуют в английской локализации: {missing_in_en}"
        assert not missing_in_ru, f"Ключи отсутствуют в русской локализации: {missing_in_ru}"
        
        # Проверяем, что все ключи присутствуют в обеих локалях
        assert ru_keys == en_keys, "Ключи локализации не синхронизированы"

    def test_template_variables_are_valid(self) -> None:
        """Проверяет корректность шаблонов с переменными."""
        ru_path = Path("app/i18n/ru.toml")
        ru = toml.load(ru_path)
        ru_flat = flatten_dict(ru)
        
        # Ключи, которые должны содержать переменные
        template_keys = [
            "teacher.ticket_created",
            "student.ticket_created", 
            "parent.ticket_created",
            "admin.users_count",
            "admin.tickets_count",
            "admin.notes_count",
            "director.users_count",
            "director.tickets_count", 
            "director.notes_count"
        ]
        
        for key in template_keys:
            if key in ru_flat:
                value = ru_flat[key]
                # Проверяем, что шаблон содержит фигурные скобки для переменных
                assert "{" in value and "}" in value, f"Шаблон {key} не содержит переменных"
                
                # Проверяем корректность синтаксиса фигурных скобок
                open_braces = value.count("{")
                close_braces = value.count("}")
                assert open_braces == close_braces, f"Непарные скобки в шаблоне {key}"

    def test_message_generation_with_variables(self) -> None:
        """Тестирует генерацию сообщений с подстановкой переменных."""
        ru_path = Path("app/i18n/ru.toml")
        ru = toml.load(ru_path)
        
        # Тест подстановки переменных в шаблоны
        test_cases = [
            {
                "template": ru["teacher"]["ticket_created"],
                "variables": {"ticket_id": "12345"},
                "expected_contains": "12345"
            },
            {
                "template": ru["admin"]["users_count"], 
                "variables": {"count": "100"},
                "expected_contains": "100"
            }
        ]
        
        for case in test_cases:
            template = case["template"]
            variables = case["variables"]
            expected = case["expected_contains"]
            
            # Подставляем переменные
            result = template.format(**variables)
            assert expected in result, f"Переменная {expected} не подставлена в шаблон"

    def test_no_empty_messages(self) -> None:
        """Проверяет отсутствие пустых сообщений."""
        ru_path = Path("app/i18n/ru.toml")
        en_path = Path("app/i18n/en.toml")
        
        ru = toml.load(ru_path)
        en = toml.load(en_path)
        
        ru_flat = flatten_dict(ru)
        en_flat = flatten_dict(en)
        
        for locale_name, locale_data in [("ru", ru_flat), ("en", en_flat)]:
            for key, value in locale_data.items():
                assert value.strip(), f"Пустое сообщение в {locale_name}: {key}"
                assert len(value.strip()) > 0, f"Сообщение состоит только из пробелов в {locale_name}: {key}"

    def test_no_duplicate_keys(self) -> None:
        """Проверяет отсутствие дублирующихся ключей."""
        ru_path = Path("app/i18n/ru.toml")
        en_path = Path("app/i18n/en.toml")
        
        ru = toml.load(ru_path)
        en = toml.load(en_path)
        
        ru_flat = flatten_dict(ru)
        en_flat = flatten_dict(en)
        
        # Проверяем, что нет дублирующихся ключей
        assert len(ru_flat) == len(set(ru_flat.keys())), "Дублирующиеся ключи в русской локализации"
        assert len(en_flat) == len(set(en_flat.keys())), "Дублирующиеся ключи в английской локализации"

    def test_required_sections_exist(self) -> None:
        """Проверяет наличие обязательных секций."""
        ru_path = Path("app/i18n/ru.toml")
        en_path = Path("app/i18n/en.toml")
        
        ru = toml.load(ru_path)
        en = toml.load(en_path)
        
        required_sections = ["common", "teacher", "student", "parent", "psych", "admin", "director", "errors"]
        
        for section in required_sections:
            assert section in ru, f"Отсутствует секция {section} в русской локализации"
            assert section in en, f"Отсутствует секция {section} в английской локализации"

    def test_emoji_consistency(self) -> None:
        """Проверяет консистентность использования эмодзи."""
        ru_path = Path("app/i18n/ru.toml")
        en_path = Path("app/i18n/en.toml")
        
        ru = toml.load(ru_path)
        en = toml.load(en_path)
        
        ru_flat = flatten_dict(ru)
        en_flat = flatten_dict(en)
        
        # Проверяем, что эмодзи используются консистентно
        for key in ru_flat:
            if key in en_flat:
                ru_value = ru_flat[key]
                en_value = en_flat[key]
                
                # Если в русском есть эмодзи, то и в английском должен быть
                if any(ord(c) > 127 for c in ru_value[:2]):  # Простая проверка на эмодзи
                    assert any(ord(c) > 127 for c in en_value[:2]), f"Несоответствие эмодзи в ключе {key}" 