"""
Unit-тесты для DataService.

Проверяем загрузку, очистку, дедупликацию.
"""

import pytest
from pathlib import Path

from services.data_service import DataService
from core.exceptions import FileProcessingError


class TestDataService:
    """Тесты сервиса обработки данных."""

    def test_load_single_file(
        self, data_service: DataService, sample_tsv_file: Path
    ) -> None:
        """Тест: загрузка одного файла."""
        df, stats = data_service.load_and_clean_files([sample_tsv_file])

        assert not df.empty
        assert stats.final_rows > 0
        assert stats.total_rows == 3
        assert "Источник телефона" in df.columns

    def test_filter_empty_phones(
        self, data_service: DataService, sample_csv_with_bad_phones: Path
    ) -> None:
        """Тест: фильтрация строк без телефонов."""
        df, stats = data_service.load_and_clean_files(
            [sample_csv_with_bad_phones])

        # Компания Bad (телефон "123") должна быть отфильтрована
        assert stats.removed_empty_phones >= 1
        assert stats.final_rows == 1

    def test_deduplicate_phones(
        self, data_service: DataService, temp_dir: Path
    ) -> None:
        """Тест: дедупликация по телефонам."""
        import pandas as pd

        # Создаём файл с дублями
        data = {
            "Название": ["Компания A", "Компания B", "Компания C"],
            "Category 0": ["X", "Y", "Z"],
            "phone_1": ["79991234567", "79991234567", "79991234568"],
            "phone_2": [None, None, None],
            "Адрес": ["", "", ""],
            "companyUrl": ["", "", ""],
            "telegram": ["", "", ""],
            "vkontakte": ["", "", ""],
        }
        df = pd.DataFrame(data)
        file_path = temp_dir / "input" / "duplicates.csv"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(file_path, index=False)

        result_df, stats = data_service.load_and_clean_files([file_path])

        # Должны остаться 2 строки (79991234567 встречается дважды)
        assert stats.final_rows == 2
        assert stats.removed_duplicates == 1

    def test_empty_file_list_raises_error(self, data_service: DataService) -> None:
        """Тест: пустой список файлов вызывает ошибку."""
        with pytest.raises(FileProcessingError) as exc_info:
            data_service.load_and_clean_files([])

        assert "Список файлов пуст" in str(exc_info.value)

    def test_nonexistent_file_raises_error(
        self, data_service: DataService, temp_dir: Path
    ) -> None:
        """Тест: несуществующий файл вызывает ошибку."""
        fake_path = temp_dir / "nonexistent.csv"

        with pytest.raises(FileProcessingError):
            data_service.load_and_clean_files([fake_path])
