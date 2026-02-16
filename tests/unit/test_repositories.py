"""
Unit-тесты для репозиториев.

Проверяем CRUD-операции с БД.
"""

import pytest

from repositories.managers_repo import ManagersRepository
from repositories.processing_history_repo import ProcessingHistoryRepository
from schemas.lead import ProcessingStats
from core.exceptions import DatabaseError


class TestManagersRepository:
    """Тесты репозитория менеджеров."""

    def test_add_manager(self, managers_repo: ManagersRepository) -> None:
        """Тест: добавление менеджера."""
        managers_repo.add_manager("Иванов Иван")
        managers = managers_repo.get_all_active()

        assert "Иванов Иван" in managers

    def test_add_duplicate_manager_raises_error(
        self, managers_repo: ManagersRepository
    ) -> None:
        """Тест: добавление дубликата вызывает ошибку."""
        managers_repo.add_manager("Петров Пётр")

        with pytest.raises(DatabaseError):
            managers_repo.add_manager("Петров Пётр")

    def test_deactivate_manager(self, managers_repo: ManagersRepository) -> None:
        """Тест: деактивация менеджера."""
        managers_repo.add_manager("Сидоров Сидор")
        managers_repo.deactivate_manager("Сидоров Сидор")

        managers = managers_repo.get_all_active()
        assert "Сидоров Сидор" not in managers

    def test_sync_managers(self, managers_repo: ManagersRepository) -> None:
        """Тест: синхронизация списка менеджеров."""
        managers_repo.add_manager("Старый Менеджер")

        new_list = ["Новый Менеджер 1", "Новый Менеджер 2"]
        managers_repo.sync_managers(new_list)

        managers = managers_repo.get_all_active()
        assert "Новый Менеджер 1" in managers
        assert "Новый Менеджер 2" in managers
        assert "Старый Менеджер" not in managers


class TestProcessingHistoryRepository:
    """Тесты репозитория истории обработки."""

    def test_start_processing(
        self, history_repo: ProcessingHistoryRepository
    ) -> None:
        """Тест: начало обработки."""
        record_id = history_repo.start_processing(file_count=3)

        assert isinstance(record_id, int)
        assert record_id > 0

    def test_finish_processing(
        self, history_repo: ProcessingHistoryRepository
    ) -> None:
        """Тест: завершение обработки."""
        record_id = history_repo.start_processing(file_count=2)

        stats = ProcessingStats(
            total_rows=100,
            removed_empty_phones=10,
            removed_duplicates=5,
            final_rows=85,
            unique_phones=85,
        )

        history_repo.finish_processing(record_id, stats, "success")

        # Проверяем, что запись обновлена
        row = history_repo.fetch_one(
            "SELECT * FROM processing_history WHERE id = ?", (record_id,)
        )
        assert row is not None
        assert row["status"] == "success"
        assert row["final_rows"] == 85
