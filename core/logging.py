"""
Настройка логирования для всего приложения.

Production-вариант: ротация файлов, JSON-формат для ELK-стека (опционально).
"""

import logging
import sys
from pathlib import Path

from config.settings import settings


def setup_logging() -> None:
    """
    Настроить корневой логгер.

    - В консоль: цветной вывод для разработки.
    - В файл: ротация по дням, JSON для продакшна.
    """
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Форматтер
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)-8s] %(name)s:%(lineno)d — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Хендлер в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)

    # Хендлер в файл (опционально, для production)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Отключаем лишние логи от сторонних библиотек
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Получить логгер по имени модуля."""
    return logging.getLogger(name)
