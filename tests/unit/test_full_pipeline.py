"""
Интеграционные тесты: полный pipeline обработки файлов.

Проверяем работу всей цепочки: файл → очистка → маппинг → экспорт.
"""

import pandas as pd
from pathlib import Path

from services.phone_service import PhoneService
from services.data_service import DataService
from services.bitrix_service import BitrixService


class TestFullPipeline:
    """Интеграционные тесты полного пайплайна."""

    def test_end_to_end_processing(self, temp_dir: Path) -> None:
        """Тест: полный цикл от загрузки до экспорта."""
        # 1. Создаём тестовый файл
        data = {
            "Название": ["Компания A", "Компания B", "Компания C"],
            "Category 0": ["Категория X", "Категория Y", "Категория X"],
            "phone_1": ["79991234567", "79991234568", "79991234567"],  # дубль
            "phone_2": [None, "79991234569", None],
            "Адрес": ["Москва", "СПб", "Казань"],
            "companyUrl": [
                "https://a.com?utm=test",
                "https://b.com",
                "https://c.com",
            ],
            "telegram": ["@userA", "", ""],
            "vkontakte": ["", "https://vk.com/idB", ""],
        }
        df = pd.DataFrame(data)

        input_dir = temp_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)
        file_path = input_dir / "test_data.tsv"
        df.to_csv(file_path, sep="\t", index=False)

        # 2. Инициализируем сервисы
        phone_service = PhoneService()
        data_service = DataService(phone_service)
        bitrix_service = BitrixService(["Менеджер 1", "Менеджер 2"])

        # 3. Обрабатываем файл
        cleaned_df, stats = data_service.load_and_clean_files([file_path])

        # Проверяем статистику
        assert stats.total_rows == 3
        assert stats.removed_duplicates == 1  # один дубль по phone_1
        assert stats.final_rows == 2

        # 4. Маппим в Битрикс
        bitrix_df = bitrix_service.map_to_bitrix(cleaned_df)

        assert len(bitrix_df) == 2
        assert "Название лида" in bitrix_df.columns
        assert "Ответственный" in bitrix_df.columns

        # Проверяем round-robin
        managers = bitrix_df["Ответственный"].unique()
        assert len(managers) <= 2

        # 5. Экспортируем
        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "export.csv"

        bitrix_df.to_csv(output_path, index=False, encoding="utf-8")

        # Проверяем, что файл создан
        assert output_path.exists()

        # Читаем и проверяем структуру
        exported = pd.read_csv(output_path)
        assert len(exported) == 2
        assert "Название лида" in exported.columns

    def test_multiple_files_processing(self, temp_dir: Path) -> None:
        """Тест: обработка нескольких файлов одновременно."""
        phone_service = PhoneService()
        data_service = DataService(phone_service)

        input_dir = temp_dir / "input"
        input_dir.mkdir(parents=True, exist_ok=True)

        # Создаём 2 файла
        for i in range(1, 3):
            data = {
                "Название": [f"Компания {i}-1", f"Компания {i}-2"],
                "Category 0": ["X", "Y"],
                "phone_1": [f"7999123456{i}", f"7999123457{i}"],
                "phone_2": [None, None],
                "Адрес": ["", ""],
                "companyUrl": ["", ""],
                "telegram": ["", ""],
                "vkontakte": ["", ""],
            }
            df = pd.DataFrame(data)
            file_path = input_dir / f"file{i}.csv"
            df.to_csv(file_path, index=False)

        files = list(input_dir.glob("*.csv"))
        cleaned_df, stats = data_service.load_and_clean_files(files)

        # Должны быть все 4 строки (2 файла по 2 строки)
        assert stats.final_rows == 4
        assert "Источник телефона" in cleaned_df.columns

        # Проверяем, что источник указан
        sources = cleaned_df["Источник телефона"].unique()
        assert len(sources) == 2
