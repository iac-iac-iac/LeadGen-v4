"""
Unit-тесты для BitrixService.

Проверяем маппинг в формат Битрикс24, round-robin менеджеров.
"""

import pandas as pd
import pytest

from services.bitrix_service import BitrixService
from config.constants import BITRIX_COLUMNS


class TestBitrixService:
    """Тесты сервиса маппинга в Битрикс."""

    def test_map_to_bitrix_basic(self, bitrix_service: BitrixService) -> None:
        """Тест: базовый маппинг."""
        data = {
            "Название": ["Компания X"],
            "Category 0": ["Категория A"],
            "phone_1": ["79991234567"],
            "phone_2": [None],
            "Адрес": ["Москва"],
            "companyUrl": ["https://example.com?utm_source=test"],
            "telegram": ["@user"],
            "vkontakte": ["https://vk.com/id123"],
            "Источник телефона": ["test.tsv"],
        }
        df = pd.DataFrame(data)

        result = bitrix_service.map_to_bitrix(df)

        assert len(result) == 1
        assert "Название лида" in result.columns
        assert result.iloc[0]["Название лида"] == "Категория A - Компания X"
        assert result.iloc[0]["Рабочий телефон"] == "79991234567"
        assert result.iloc[0]["Корпоративный сайт"] == "https://example.com"

    def test_round_robin_managers(self) -> None:
        """Тест: распределение лидов по менеджерам (round-robin)."""
        managers = ["Менеджер 1", "Менеджер 2", "Менеджер 3"]
        service = BitrixService(managers)

        data = {
            "Название": ["Компания A", "Компания B", "Компания C", "Компания D"],
            "Category 0": ["", "", "", ""],
            "phone_1": ["79991234567", "79991234568", "79991234569", "79991234570"],
            "phone_2": [None, None, None, None],
            "Адрес": ["", "", "", ""],
            "companyUrl": ["", "", "", ""],
            "telegram": ["", "", "", ""],
            "vkontakte": ["", "", "", ""],
            "Источник телефона": ["test", "test", "test", "test"],
        }
        df = pd.DataFrame(data)

        result = service.map_to_bitrix(df)

        # Проверяем цикличность распределения
        assert result.iloc[0]["Ответственный"] == "Менеджер 1"
        assert result.iloc[1]["Ответственный"] == "Менеджер 2"
        assert result.iloc[2]["Ответственный"] == "Менеджер 3"
        assert result.iloc[3]["Ответственный"] == "Менеджер 1"

    def test_empty_dataframe(self, bitrix_service: BitrixService) -> None:
        """Тест: пустой DataFrame."""
        df = pd.DataFrame()
        result = bitrix_service.map_to_bitrix(df)

        assert result.empty
        assert list(result.columns) == BITRIX_COLUMNS

    def test_url_cleaning(self, bitrix_service: BitrixService) -> None:
        """Тест: очистка URL от UTM-меток."""
        data = {
            "Название": ["Компания"],
            "Category 0": [""],
            "phone_1": ["79991234567"],
            "phone_2": [None],
            "Адрес": [""],
            "companyUrl": ["https://example.com?utm_source=google&utm_medium=cpc"],
            "telegram": [""],
            "vkontakte": [""],
            "Источник телефона": ["test"],
        }
        df = pd.DataFrame(data)

        result = bitrix_service.map_to_bitrix(df)
        assert result.iloc[0]["Корпоративный сайт"] == "https://example.com"

    def test_telegram_cleanup(self, bitrix_service: BitrixService) -> None:
        """Тест: очистка Telegram username."""
        data = {
            "Название": ["Компания"],
            "Category 0": [""],
            "phone_1": ["79991234567"],
            "phone_2": [None],
            "Адрес": [""],
            "companyUrl": [""],
            "telegram": ["https://t.me/testuser"],
            "vkontakte": [""],
            "Источник телефона": ["test"],
        }
        df = pd.DataFrame(data)

        result = bitrix_service.map_to_bitrix(df)
        assert result.iloc[0]["Контакт Telegram"] == "testuser"
