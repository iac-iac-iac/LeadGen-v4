"""
Сервис обработки данных: загрузка, очистка, дедупликация.

Использует PhoneService, возвращает typed-модели (CleanedLead).
"""

import logging
from pathlib import Path
from typing import List, Tuple

import pandas as pd

from config.constants import WEBBEE_COLUMNS, TSV_SEPARATOR, CSV_SEPARATOR
from core.exceptions import FileProcessingError
from schemas.lead import CleanedLead, ProcessingStats
from services.phone_service import PhoneService


logger = logging.getLogger(__name__)


class DataService:
    """Сервис обработки файлов и данных."""

    def __init__(self, phone_service: PhoneService) -> None:
        self.phone_service = phone_service

    def load_and_clean_files(
        self, file_paths: List[Path]
    ) -> Tuple[pd.DataFrame, ProcessingStats]:
        """
        Загрузить и обработать список файлов.

        Args:
            file_paths: список путей к TSV/CSV.

        Returns:
            (DataFrame, ProcessingStats) — очищенные данные и статистика.

        Raises:
            FileProcessingError: если не удалось прочитать файл.
        """
        if not file_paths:
            raise FileProcessingError("Список файлов пуст", {"files": []})

        frames = []
        total_rows = 0
        removed_empty_phones = 0
        removed_duplicates = 0
        seen_phones: set[str] = set()

        for path in file_paths:
            try:
                df = self._read_file(path)
                total_rows += len(df)

                # Добавляем источник
                df["Источник телефона"] = path.name

                # Нормализуем телефоны
                df = self._normalize_phones(df)

                # Фильтруем строки без телефонов
                df, removed = self._filter_empty_phones(df)
                removed_empty_phones += removed

                # Дедупликация
                df, dupes = self._deduplicate(df, seen_phones)
                removed_duplicates += dupes

                frames.append(df)
                logger.info(
                    f"Файл {path.name} обработан: {len(df)} строк после очистки")

            except Exception as exc:
                logger.exception(f"Ошибка обработки файла {path}")
                raise FileProcessingError(
                    f"Не удалось обработать файл {path.name}",
                    {"path": str(path), "error": str(exc)},
                ) from exc

        merged = pd.concat(
            frames, ignore_index=True) if frames else pd.DataFrame()

        stats = ProcessingStats(
            total_rows=total_rows,
            removed_empty_phones=removed_empty_phones,
            removed_duplicates=removed_duplicates,
            final_rows=len(merged),
            unique_phones=len(seen_phones),
        )

        logger.info(f"Обработка завершена: {stats.model_dump()}")
        return merged, stats

    def _read_file(self, path: Path) -> pd.DataFrame:
        """Прочитать TSV/CSV файл."""
        sep = TSV_SEPARATOR if path.suffix.lower() == ".tsv" else CSV_SEPARATOR
        return pd.read_csv(path, sep=sep, dtype=str)

    def _normalize_phones(self, df: pd.DataFrame) -> pd.DataFrame:
        """Нормализовать колонки с телефонами."""
        for col in ("phone_1", "phone_2"):
            if col not in df.columns:
                df[col] = None
            df[col] = df[col].apply(self.phone_service.normalize)
        return df

    def _filter_empty_phones(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
        """Удалить строки, где оба телефона пустые."""
        mask_has_phone = df["phone_1"].notna() | df["phone_2"].notna()
        removed = (~mask_has_phone).sum()
        return df[mask_has_phone], int(removed)

    def _deduplicate(
        self, df: pd.DataFrame, seen_phones: set[str]
    ) -> Tuple[pd.DataFrame, int]:
        """Удалить дубликаты по телефонам."""
        keep_rows = []
        removed = 0

        for idx, row in df.iterrows():
            phones = {row["phone_1"], row["phone_2"]} - {None}
            if not phones:
                removed += 1
                continue

            if phones & seen_phones:
                removed += 1
                continue

            seen_phones.update(phones)
            keep_rows.append(idx)

        return df.loc[keep_rows], removed
