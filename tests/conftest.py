"""
Pytest fixtures для всех тестов.

ИСПРАВЛЕНО: полное игнорирование Windows cleanup-ошибок для SQLite.
"""

import tempfile
import gc
import time
import shutil
from pathlib import Path
from typing import Generator

import pandas as pd
import pytest

from config.settings import Settings, Paths
from repositories.managers_repo import ManagersRepository
from repositories.processing_history_repo import ProcessingHistoryRepository
from services.phone_service import PhoneService
from services.data_service import DataService
from services.bitrix_service import BitrixService


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Временная директория для тестов.

    Windows-specific: игнорируем ошибки при удалении SQLite файлов.
    """
    tmpdir = tempfile.mkdtemp()
    try:
        yield Path(tmpdir)
    finally:
        # Windows-specific: принудительно освобождаем ресурсы
        gc.collect()
        time.sleep(0.2)

        # Игнорируем все ошибки при удалении (специфика Windows + SQLite)
        try:
            shutil.rmtree(tmpdir, ignore_errors=True)
        except Exception:
            pass  # полностью игнорируем любые ошибки cleanup


@pytest.fixture
def temp_db(temp_dir: Path) -> Path:
    """Временная база данных."""
    db_path = temp_dir / "test.db"
    return db_path


@pytest.fixture
def test_settings(temp_dir: Path, temp_db: Path) -> Settings:
    """Настройки для тестов."""
    paths = Paths(
        input_dir=temp_dir / "input",
        output_dir=temp_dir / "output",
        reports_dir=temp_dir / "reports",
        db_path=temp_db,
    )
    return Settings(
        default_managers=["Тестовый Менеджер 1", "Тестовый Менеджер 2"],
        paths=paths,
        max_file_size_mb=10,
        preview_rows=5,
        log_level="DEBUG",
    )


@pytest.fixture
def phone_service() -> PhoneService:
    """Сервис валидации телефонов."""
    return PhoneService()


@pytest.fixture
def data_service(phone_service: PhoneService) -> DataService:
    """Сервис обработки данных."""
    return DataService(phone_service)


@pytest.fixture
def bitrix_service() -> BitrixService:
    """Сервис маппинга в Битрикс."""
    return BitrixService(["Менеджер 1", "Менеджер 2"])


@pytest.fixture
def managers_repo(temp_db: Path) -> ManagersRepository:
    """Репозиторий менеджеров с тестовой БД."""
    repo = ManagersRepository(temp_db)
    repo.create_table()
    return repo


@pytest.fixture
def history_repo(temp_db: Path) -> ProcessingHistoryRepository:
    """Репозиторий истории с тестовой БД."""
    repo = ProcessingHistoryRepository(temp_db)
    repo.create_table()
    return repo


@pytest.fixture
def sample_tsv_file(temp_dir: Path) -> Path:
    """Создать тестовый TSV-файл."""
    data = {
        "Название": ["Компания 1", "Компания 2", "Компания 3"],
        "Category 0": ["Категория A", "Категория B", "Категория A"],
        "phone_1": ["89991234567", "+7 999 123-45-68", "9991234569"],
        "phone_2": [None, "89991234570", None],
        "Адрес": ["Москва, ул. Ленина", "СПб, Невский пр.", "Казань"],
        "companyUrl": [
            "https://example.com?utm_source=test",
            "https://test.ru",
            "https://company3.com",
        ],
        "telegram": ["@test_user", None, "https://t.me/user3"],
        "vkontakte": ["https://vk.com/id123", None, "vk.com/company3"],
    }
    df = pd.DataFrame(data)

    file_path = temp_dir / "input" / "test_data.tsv"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, sep="\t", index=False)

    return file_path


@pytest.fixture
def sample_csv_with_bad_phones(temp_dir: Path) -> Path:
    """Создать CSV с битыми телефонами."""
    data = {
        "Название": ["Компания Bad", "Компания Good"],
        "Category 0": ["Категория X", "Категория Y"],
        "phone_1": ["123", "79991234567"],  # первый битый
        "phone_2": [None, None],
        "Адрес": ["", "Адрес"],
        "companyUrl": ["", "https://good.com"],
        "telegram": ["", ""],
        "vkontakte": ["", ""],
    }
    df = pd.DataFrame(data)

    file_path = temp_dir / "input" / "bad_phones.csv"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(file_path, index=False)

    return file_path
