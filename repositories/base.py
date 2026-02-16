"""
Базовый репозиторий с общими операциями.

Использует SQLite напрямую, но архитектура позволяет заменить на SQLAlchemy.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Any, List, Optional, Type, TypeVar

from config.settings import settings
from core.exceptions import DatabaseError


logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository:
    """Базовый класс для всех репозиториев."""

    def __init__(self, db_path: Path | None = None) -> None:
        """
        Args:
            db_path: путь к БД. Если None — берём из settings.
        """
        self.db_path = db_path or settings.paths.db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self) -> None:
        """Создать файл БД и директорию, если их нет."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.db_path.exists():
            logger.info(f"Создание новой БД: {self.db_path}")

    def _get_connection(self) -> sqlite3.Connection:
        """Получить соединение с БД."""
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # для доступа по именам колонок
            return conn
        except sqlite3.Error as exc:
            logger.exception("Ошибка подключения к БД")
            raise DatabaseError(
                "Не удалось подключиться к базе данных",
                {"db_path": str(self.db_path), "error": str(exc)},
            ) from exc

    def execute(
        self,
        query: str,
        params: tuple | dict | None = None,
        commit: bool = False,
    ) -> sqlite3.Cursor:
        """
        Выполнить SQL-запрос.

        Args:
            query: SQL-запрос.
            params: параметры (tuple для ?, dict для :name).
            commit: сделать ли commit после выполнения.

        Returns:
            Cursor с результатом.

        Raises:
            DatabaseError: при ошибке выполнения.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            if commit:
                conn.commit()
            return cursor
        except sqlite3.Error as exc:
            logger.exception(f"Ошибка выполнения запроса: {query}")
            raise DatabaseError(
                "Ошибка выполнения SQL-запроса",
                {"query": query, "params": params, "error": str(exc)},
            ) from exc
        finally:
            conn.close()

    def fetch_one(self, query: str, params: tuple | dict | None = None) -> Optional[sqlite3.Row]:
        """Выполнить SELECT и вернуть одну строку."""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetch_all(self, query: str, params: tuple | dict | None = None) -> List[sqlite3.Row]:
        """Выполнить SELECT и вернуть все строки."""
        cursor = self.execute(query, params)
        return cursor.fetchall()
