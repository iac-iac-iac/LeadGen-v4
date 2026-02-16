"""
Сервис маппинга данных в формат Битрикс24.

Production-версия: использует Pydantic-схемы, round-robin по менеджерам.
"""

import logging
from typing import List
from itertools import cycle

import pandas as pd

from config.constants import BITRIX_COLUMNS
from config.settings import settings
from schemas.lead import BitrixLead
from utils.url_cleaner import clean_url


logger = logging.getLogger(__name__)


class BitrixService:
    """Сервис маппинга в формат Битрикс24."""

    def __init__(self, managers: List[str] | None = None) -> None:
        """
        Args:
            managers: список менеджеров для распределения (round-robin).
                     Если None — используются дефолтные из settings.
        """
        self.managers = managers or settings.default_managers
        self._manager_cycle = cycle(self.managers) if self.managers else None

    def map_to_bitrix(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Преобразовать DataFrame к структуре Битрикс24.

        Args:
            df: очищенный DataFrame с нормализованными телефонами.

        Returns:
            DataFrame с колонками BITRIX_COLUMNS, готовый к экспорту.
        """
        if df.empty:
            logger.warning("Пустой DataFrame для маппинга")
            return pd.DataFrame(columns=BITRIX_COLUMNS)

        result = pd.DataFrame("", index=df.index, columns=BITRIX_COLUMNS)

        # Название лида
        result["Название лида"] = (
            df.get("Category 0", "").fillna("").astype(str)
            + " - "
            + df.get("Название", "").fillna("").astype(str)
        )

        # Телефоны
        result["Рабочий телефон"] = df.get(
            "phone_1", "").fillna("").astype(str)
        result["Мобильный телефон"] = df.get(
            "phone_2", "").fillna("").astype(str)

        # Адрес
        result["Адрес"] = df.get("Адрес", "").fillna("").astype(str)

        # URL без UTM
        result["Корпоративный сайт"] = (
            df.get("companyUrl", "").fillna("").astype(str).apply(clean_url)
        )

        # Telegram / VK
        result["Контакт Telegram"] = (
            df.get("telegram", "")
            .fillna("")
            .astype(str)
            .str.replace("https://t.me/", "", case=False)
            .str.replace("@", "", regex=False)
        )

        result["Контакт ВКонтакте"] = (
            df.get("vkontakte", "")
            .fillna("")
            .astype(str)
            .str.replace("https://vk.com/", "", case=False)
        )

        # Название компании
        result["Название компании"] = df.get(
            "Название", "").fillna("").astype(str)

        # Статичные поля
        result["Комментарий"] = ""
        result["Стадия"] = settings.bitrix_stage
        result["Источник"] = settings.bitrix_source
        result["Тип услуги"] = settings.bitrix_service_type

        # Источник телефона
        result["Источник телефона"] = (
            df.get("Источник телефона", "").fillna("").astype(str)
        )

        # Round-robin по менеджерам
        if self._manager_cycle:
            result["Ответственный"] = [
                next(self._manager_cycle) for _ in range(len(result))
            ]
        else:
            result["Ответственный"] = ""

        logger.info(f"Замапплено {len(result)} лидов в формат Битрикс24")
        return result
