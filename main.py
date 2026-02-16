"""
Точка входа приложения.

Инициализирует:
- Логирование
- Настройки
- БД (создание таблиц)
- Qt-приложение
"""

import sys
import logging

from PyQt6.QtWidgets import QApplication

from core.logging import setup_logging
from config.settings import settings
from repositories.managers_repo import ManagersRepository
from repositories.processing_history_repo import ProcessingHistoryRepository
from gui.main_window import MainWindow


logger = logging.getLogger(__name__)


def initialize_database() -> None:
    """Создать таблицы БД при первом запуске."""
    try:
        managers_repo = ManagersRepository()
        managers_repo.create_table()

        history_repo = ProcessingHistoryRepository()
        history_repo.create_table()

        # Синхронизируем дефолтных менеджеров из settings
        if settings.default_managers:
            managers_repo.sync_managers(settings.default_managers)

        logger.info("База данных инициализирована")
    except Exception as exc:
        logger.exception("Ошибка инициализации БД")
        raise


def main() -> None:
    """Главная точка входа."""
    # 1. Настроить логирование
    setup_logging()
    logger.info("=" * 60)
    logger.info("Запуск Lead Generation System")
    logger.info(f"Версия Python: {sys.version}")
    logger.info(f"Уровень логирования: {settings.log_level}")
    logger.info("=" * 60)

    # 2. Инициализировать БД
    try:
        initialize_database()
    except Exception as exc:
        logger.critical("Не удалось инициализировать БД, выход")
        sys.exit(1)

    # 3. Запустить Qt-приложение
    app = QApplication(sys.argv)
    app.setApplicationName("Lead Generation System")
    app.setOrganizationName("YourCompany")

    window = MainWindow()
    window.show()

    logger.info("Главное окно открыто, приложение готово к работе")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
