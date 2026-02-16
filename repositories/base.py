"""
Базовый репозиторий с общими операциями.

ИСПРАВЛЕНО: используем context manager для корректного управления соединениями.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Any, List, Optional, Type, TypeVar
from contextlib import contextmanager

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

    @contextmanager
    def _get_connection(self):
        """
        Context manager для получения соединения с БД.
        
        Гарантирует, что соединение будет закрыто после использования.
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as exc:
            logger.exception("Ошибка подключения к БД")
            if conn:
                conn.rollback()
            raise DatabaseError(
                "Не удалось подключиться к базе данных",
                {"db_path": str(self.db_path), "error": str(exc)},
            ) from exc
        finally:
            if conn:
                conn.close()

    def execute(
        self,
        query: str,
        params: tuple | dict | None = None,
        commit: bool = False,
    ) -> List[sqlite3.Row]:
        """
        Выполнить SQL-запрос и вернуть результаты.

        Args:
            query: SQL-запрос.
            params: параметры (tuple для ?, dict для :name).
            commit: сделать ли commit после выполнения.

        Returns:
            List результатов (пустой для INSERT/UPDATE/DELETE).

        Raises:
            DatabaseError: при ошибке выполнения.
        """
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                
                if commit:
                    conn.commit()
                
                # Возвращаем результаты сразу, пока соединение открыто
                return cursor.fetchall()
                
            except sqlite3.Error as exc:
                logger.exception(f"Ошибка выполнения запроса: {query}")
                raise DatabaseError(
                    "Ошибка выполнения SQL-запроса",
                    {"query": query, "params": params, "error": str(exc)},
                ) from exc

    def fetch_one(self, query: str, params: tuple | dict | None = None) -> Optional[sqlite3.Row]:
        """Выполнить SELECT и вернуть одну строку."""
        results = self.execute(query, params)
        return results[0] if results else None

    def fetch_all(self, query: str, params: tuple | dict | None = None) -> List[sqlite3.Row]:
        """Выполнить SELECT и вернуть все строки."""
        return self.execute(query, params)

    def execute_write(
        self,
        query: str,
        params: tuple | dict | None = None,
    ) -> int:
        """
        Выполнить INSERT/UPDATE/DELETE и вернуть lastrowid.

        Returns:
            lastrowid для INSERT, 0 для UPDATE/DELETE.
        """
        with self._get_connection() as conn:
            try:
                cursor = conn.cursor()
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.lastrowid
                
            except sqlite3.Error as exc:
                logger.exception(f"Ошибка выполнения записи: {query}")
                raise DatabaseError(
                    "Ошибка выполнения SQL-записи",
                    {"query": query, "params": params, "error": str(exc)},
                ) from exc
