"""
Репозиторий истории обработки файлов.

Логирует каждый запуск обработки для аналитики.
"""

import logging
from datetime import datetime
from typing import Optional

from repositories.base import BaseRepository
from schemas.lead import ProcessingStats


logger = logging.getLogger(__name__)


class ProcessingHistoryRepository(BaseRepository):
    """Репозиторий истории обработки."""

    def create_table(self) -> None:
        """Создать таблицу processing_history."""
        query = """
        CREATE TABLE IF NOT EXISTS processing_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            file_count INTEGER NOT NULL,
            total_rows INTEGER NOT NULL,
            removed_duplicates INTEGER NOT NULL,
            removed_empty_phones INTEGER NOT NULL,
            final_rows INTEGER NOT NULL,
            unique_phones INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'success'
        );
        """
        self.execute(query, commit=True)
        logger.info("Таблица processing_history создана/проверена")

    def start_processing(self, file_count: int) -> int:
        """
        Начать новую запись обработки.

        Args:
            file_count: количество файлов в обработке.

        Returns:
            ID созданной записи.
        """
        query = """
        INSERT INTO processing_history (started_at, file_count, total_rows,
                                       removed_duplicates, removed_empty_phones,
                                       final_rows, unique_phones)
        VALUES (?, ?, 0, 0, 0, 0, 0)
        """
        cursor = self.execute(
            query,
            (datetime.now().isoformat(), file_count),
            commit=True,
        )
        record_id = cursor.lastrowid
        logger.info(f"Начата обработка, record_id={record_id}")
        return record_id

    def finish_processing(
        self,
        record_id: int,
        stats: ProcessingStats,
        status: str = "success",
    ) -> None:
        """
        Завершить запись обработки.

        Args:
            record_id: ID записи из start_processing.
            stats: статистика обработки.
            status: статус ('success' или 'failed').
        """
        query = """
        UPDATE processing_history
        SET finished_at = ?,
            total_rows = ?,
            removed_duplicates = ?,
            removed_empty_phones = ?,
            final_rows = ?,
            unique_phones = ?,
            status = ?
        WHERE id = ?
        """
        self.execute(
            query,
            (
                datetime.now().isoformat(),
                stats.total_rows,
                stats.removed_duplicates,
                stats.removed_empty_phones,
                stats.final_rows,
                stats.unique_phones,
                status,
                record_id,
            ),
            commit=True,
        )
        logger.info(
            f"Обработка завершена, record_id={record_id}, status={status}")
