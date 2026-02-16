"""
Кастомные исключения для бизнес-логики.

Позволяют различать типы ошибок и обрабатывать их осмысленно.
"""


class LeadGenError(Exception):
    """Базовое исключение для всех ошибок приложения."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ValidationError(LeadGenError):
    """Ошибка валидации данных."""


class FileProcessingError(LeadGenError):
    """Ошибка при обработке файла."""


class DatabaseError(LeadGenError):
    """Ошибка работы с БД."""


class ConfigurationError(LeadGenError):
    """Ошибка конфигурации."""


class ExportError(LeadGenError):
    """Ошибка экспорта данных."""
