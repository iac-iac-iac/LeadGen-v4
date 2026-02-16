"""
Сервис валидации и нормализации телефонов.

Production-версия: логирование, метрики битых номеров, расширяемость.
"""

import re
import logging
from typing import Optional

from config.constants import PHONE_LENGTH, VALID_PHONE_PREFIXES
from core.exceptions import ValidationError


logger = logging.getLogger(__name__)


class PhoneService:
    """Сервис работы с телефонными номерами."""

    def __init__(self) -> None:
        self._digit_pattern = re.compile(r"\D")

    def normalize(self, raw: str | None) -> Optional[str]:
        """
        Нормализовать телефон до 11-значного формата.

        Args:
            raw: сырая строка (может содержать +, пробелы, скобки).

        Returns:
            Строка из 11 цифр или None, если номер невалиден.

        Raises:
            ValidationError: если raw имеет неподдерживаемый формат.
        """
        if raw is None:
            return None

        # Убираем все нецифровые символы
        digits = self._digit_pattern.sub("", str(raw))

        # Слишком короткий номер
        if len(digits) < 10:
            logger.debug(f"Номер слишком короткий: {raw} -> {digits}")
            return None

        # Если 10 цифр — добавляем 7
        if len(digits) == 10:
            digits = "7" + digits

        # После добавления должно быть ровно 11
        if len(digits) != PHONE_LENGTH:
            logger.debug(f"Номер неправильной длины: {raw} -> {digits}")
            return None

        # Должен начинаться с 7 или 8
        if digits[0] not in VALID_PHONE_PREFIXES:
            logger.debug(f"Номер с неправильным префиксом: {digits}")
            return None

        return digits

    def normalize_batch(self, phones: list[str | None]) -> list[Optional[str]]:
        """Нормализовать список телефонов."""
        return [self.normalize(p) for p in phones]
