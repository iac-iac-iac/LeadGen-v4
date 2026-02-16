"""
Настройки приложения через Pydantic Settings.

Читает из .env и переменных окружения, с fallback на дефолты.
"""

from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Paths(BaseSettings):
    """Пути к директориям данных."""

    input_dir: Path = Field(default=Path("data/input"))
    output_dir: Path = Field(default=Path("data/output"))
    reports_dir: Path = Field(default=Path("data/reports"))
    db_path: Path = Field(default=Path("data/database.db"))

    @field_validator("input_dir", "output_dir", "reports_dir")
    @classmethod
    def create_if_not_exists(cls, v: Path) -> Path:
        """Создать директорию, если её нет."""
        v.mkdir(parents=True, exist_ok=True)
        return v


class Settings(BaseSettings):
    """Главный конфиг приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
    )

    # Менеджеры — загружаем из БД, но дефолтный список есть
    default_managers: List[str] = Field(
        default_factory=lambda: ["Менеджер 1", "Менеджер 2"])

    # Пути
    paths: Paths = Field(default_factory=Paths)

    # Настройки обработки
    max_file_size_mb: int = Field(default=100, ge=1, le=1000)
    preview_rows: int = Field(default=10, ge=5, le=100)
    log_level: str = Field(default="INFO")

    # Битрикс
    bitrix_stage: str = Field(default="Новая заявка")
    bitrix_source: str = Field(default="Холодный звонок")
    bitrix_service_type: str = Field(default="ГЦК")


# Singleton
settings = Settings()
