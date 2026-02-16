"""
Pydantic-схемы для лидов и обработки данных.

Валидация на границах системы: при чтении файлов, перед записью в БД.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class RawLead(BaseModel):
    """
    Сырой лид из файла Webbee AI (до обработки).

    Все поля опциональны, т.к. файлы могут быть неполными.
    """

    название: Optional[str] = None
    category_0: Optional[str] = Field(None, alias="Category 0")
    phone_1: Optional[str] = None
    phone_2: Optional[str] = None
    адрес: Optional[str] = None
    company_url: Optional[str] = Field(None, alias="companyUrl")
    telegram: Optional[str] = None
    vkontakte: Optional[str] = None

    model_config = {"populate_by_name": True}


class CleanedLead(BaseModel):
    """
    Очищенный лид (после валидации телефонов).

    Телефоны уже нормализованы, хотя бы один должен быть валидным.
    """

    название: str
    category_0: str = ""
    phone_1: Optional[str] = None
    phone_2: Optional[str] = None
    адрес: str = ""
    company_url: str = ""
    telegram: str = ""
    vkontakte: str = ""
    источник_телефона: str  # имя файла

    @field_validator("phone_1", "phone_2")
    @classmethod
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        """Проверить, что телефон — 11 цифр."""
        if v is None:
            return None
        if not v.isdigit() or len(v) != 11:
            raise ValueError(
                f"Телефон должен быть строкой из 11 цифр, получено: {v}")
        return v

    @field_validator("название")
    @classmethod
    def название_not_empty(cls, v: str) -> str:
        """Название не должно быть пустым."""
        if not v or not v.strip():
            raise ValueError("Название не может быть пустым")
        return v.strip()


class BitrixLead(BaseModel):
    """
    Лид в формате Битрикс24 (готовый к экспорту).

    Все поля — строки, как требует CSV для импорта.
    """

    название_лида: str = Field(..., alias="Название лида")
    рабочий_телефон: str = Field(default="", alias="Рабочий телефон")
    мобильный_телефон: str = Field(default="", alias="Мобильный телефон")
    адрес: str = Field(default="", alias="Адрес")
    корпоративный_сайт: str = Field(default="", alias="Корпоративный сайт")
    контакт_telegram: str = Field(default="", alias="Контакт Telegram")
    контакт_вконтакте: str = Field(default="", alias="Контакт ВКонтакте")
    название_компании: str = Field(default="", alias="Название компании")
    комментарий: str = Field(default="", alias="Комментарий")
    стадия: str = Field(default="Новая заявка", alias="Стадия")
    источник: str = Field(default="Холодный звонок", alias="Источник")
    тип_услуги: str = Field(default="ГЦК", alias="Тип услуги")
    источник_телефона: str = Field(..., alias="Источник телефона")
    ответственный: str = Field(default="", alias="Ответственный")

    model_config = {"populate_by_name": True}


class ProcessingStats(BaseModel):
    """Статистика обработки файлов."""

    total_rows: int = Field(ge=0)
    removed_empty_phones: int = Field(ge=0)
    removed_duplicates: int = Field(ge=0)
    final_rows: int = Field(ge=0)
    unique_phones: int = Field(ge=0)
