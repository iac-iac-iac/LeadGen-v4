"""
Unit-тесты для PhoneService.

Проверяем нормализацию телефонов: валидные, невалидные, граничные случаи.
"""

import pytest
from services.phone_service import PhoneService


class TestPhoneService:
    """Тесты сервиса валидации телефонов."""

    def test_normalize_valid_11_digit(self, phone_service: PhoneService) -> None:
        """Тест: валидный 11-значный номер."""
        result = phone_service.normalize("79991234567")
        assert result == "79991234567"

    def test_normalize_with_plus(self, phone_service: PhoneService) -> None:
        """Тест: номер с +."""
        result = phone_service.normalize("+7 999 123-45-67")
        assert result == "79991234567"

    def test_normalize_10_digits(self, phone_service: PhoneService) -> None:
        """Тест: 10 цифр -> добавляем 7."""
        result = phone_service.normalize("9991234567")
        assert result == "79991234567"

    def test_normalize_starts_with_8(self, phone_service: PhoneService) -> None:
        """Тест: номер с 8 в начале."""
        result = phone_service.normalize("89991234567")
        assert result == "89991234567"

    def test_normalize_too_short(self, phone_service: PhoneService) -> None:
        """Тест: слишком короткий номер."""
        result = phone_service.normalize("123456")
        assert result is None

    def test_normalize_too_long(self, phone_service: PhoneService) -> None:
        """Тест: слишком длинный номер."""
        result = phone_service.normalize("799912345678999")
        assert result is None

    def test_normalize_invalid_prefix(self, phone_service: PhoneService) -> None:
        """Тест: неправильный префикс (не 7 и не 8)."""
        result = phone_service.normalize("59991234567")
        assert result is None

    def test_normalize_none(self, phone_service: PhoneService) -> None:
        """Тест: None на входе."""
        result = phone_service.normalize(None)
        assert result is None

    def test_normalize_empty_string(self, phone_service: PhoneService) -> None:
        """Тест: пустая строка."""
        result = phone_service.normalize("")
        assert result is None

    def test_normalize_with_letters(self, phone_service: PhoneService) -> None:
        """Тест: строка с буквами (убираются)."""
        result = phone_service.normalize("+7 (999) ABC-123-45-67")
        assert result == "79991234567"

    def test_normalize_batch(self, phone_service: PhoneService) -> None:
        """Тест: батч-обработка."""
        phones = ["+79991234567", "123", None, "89991234568"]
        result = phone_service.normalize_batch(phones)
        assert result == ["79991234567", None, None, "89991234568"]

    @pytest.mark.parametrize(
        "input_phone,expected",
        [
            ("8 (999) 123-45-67", "89991234567"),
            ("+7-999-123-45-67", "79991234567"),
            ("7 999 123 45 67", "79991234567"),
            ("9991234567", "79991234567"),
            ("12345", None),
            ("abcdefghijk", None),
        ],
    )
    def test_normalize_parametrized(
        self, phone_service: PhoneService, input_phone: str, expected: str | None
    ) -> None:
        """Параметризованный тест разных форматов."""
        result = phone_service.normalize(input_phone)
        assert result == expected
