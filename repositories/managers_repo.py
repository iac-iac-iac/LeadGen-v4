"""
Репозиторий для работы с менеджерами.

CRUD-операции для таблицы managers.
"""

import logging
from typing import List

from repositories.base import BaseRepository
from core.exceptions import DatabaseError


logger = logging.getLogger(__name__)


class ManagersRepository(BaseRepository):
    """Репозиторий менеджеров."""

    def create_table(self) -> None:
        """Создать таблицу managers, если её нет."""
        query = """
        CREATE TABLE IF NOT EXISTS managers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
        self.execute(query, commit=True)
        logger.info("Таблица managers создана/проверена")

    def get_all_active(self) -> List[str]:
        """Получить список активных менеджеров."""
        query = "SELECT name FROM managers WHERE is_active = 1 ORDER BY name"
        rows = self.fetch_all(query)
        return [row["name"] for row in rows]

    def add_manager(self, name: str) -> None:
        """
        Добавить нового менеджера.

        Args:
            name: имя менеджера (должно быть уникальным).

        Raises:
            DatabaseError: если менеджер с таким именем уже есть.
        """
        query = "INSERT INTO managers (name) VALUES (?)"
        try:
            self.execute(query, (name,), commit=True)
            logger.info(f"Менеджер добавлен: {name}")
        except DatabaseError as exc:
            if "UNIQUE constraint failed" in str(exc):
                raise DatabaseError(
                    f"Менеджер '{name}' уже существует") from exc
            raise

    def deactivate_manager(self, name: str) -> None:
        """Деактивировать менеджера (мягкое удаление)."""
        query = "UPDATE managers SET is_active = 0 WHERE name = ?"
        self.execute(query, (name,), commit=True)
        logger.info(f"Менеджер деактивирован: {name}")

    def sync_managers(self, manager_names: List[str]) -> None:
        """
        Синхронизировать список менеджеров с БД.

        Добавляет новых, деактивирует отсутствующих в списке.
        """
        existing = set(self.get_all_active())
        new_set = set(manager_names)

        # Добавляем новых
        for name in new_set - existing:
            try:
                self.add_manager(name)
            except DatabaseError:
                pass  # уже есть

        # Деактивируем удалённых
        for name in existing - new_set:
            self.deactivate_manager(name)

        logger.info(f"Менеджеры синхронизированы: {len(new_set)} активных")
