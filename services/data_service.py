"""
Модуль обработки сырых TSV/CSV файлов.

PRODUCTION-VERSION: универсальный парсер с автоопределением формата.
"""

import csv
import logging
from pathlib import Path
from typing import List, Tuple, Optional

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
        """
        Универсальный парсер CSV/TSV с автоопределением формата.

        Определяет:
        - Разделитель (запятая, точка с запятой, табуляция)
        - Кодировку (UTF-8, CP1251, Latin-1)
        - Пропускает битые строки
        """
        # Список кодировок для России
        encodings = ["utf-8", "cp1251", "latin-1", "utf-8-sig"]

        for encoding in encodings:
            try:
                # Шаг 1: Определяем разделитель
                delimiter = self._detect_delimiter(path, encoding)

                # Шаг 2: Читаем файл с определённым разделителем
                df = pd.read_csv(
                    path,
                    sep=delimiter,
                    dtype=str,
                    encoding=encoding,
                    on_bad_lines="skip",
                    engine="python",
                    skipinitialspace=True,  # убирает пробелы после разделителя
                )

                logger.info(
                    f"Файл {path.name} прочитан: "
                    f"кодировка={encoding}, разделитель={repr(delimiter)}, "
                    f"строк={len(df)}, колонок={len(df.columns)}"
                )

                return df

            except UnicodeDecodeError:
                continue
            except Exception as exc:
                logger.debug(f"Не удалось прочитать с {encoding}: {exc}")
                continue

        raise FileProcessingError(
            f"Не удалось прочитать файл {path.name} ни с одной кодировкой",
            {"encodings_tried": encodings}
        )

    def _detect_delimiter(self, path: Path, encoding: str) -> str:
        """
        Автоопределение разделителя CSV.

        Читает первые 5 строк и определяет наиболее вероятный разделитель.
        """
        try:
            with open(path, "r", encoding=encoding) as f:
                # Читаем первые 5 строк для анализа
                sample = "".join([f.readline() for _ in range(5)])

            # csv.Sniffer автоматически определяет разделитель
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter

            logger.debug(f"Автоопределён разделитель: {repr(delimiter)}")
            return delimiter

        except Exception:
            # Fallback: пробуем по расширению файла
            if path.suffix.lower() == ".tsv":
                return "\t"
            elif path.suffix.lower() == ".csv":
                # Подсчитываем частоту разделителей в первой строке
                with open(path, "r", encoding=encoding) as f:
                    first_line = f.readline()

                comma_count = first_line.count(",")
                semicolon_count = first_line.count(";")
                tab_count = first_line.count("\t")

                # Выбираем самый частый
                if tab_count > max(comma_count, semicolon_count):
                    return "\t"
                elif semicolon_count > comma_count:
                    return ";"
                else:
                    return ","

            # По умолчанию — запятая
            return ","

    def _normalize_phones(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Нормализовать колонки с телефонами.

        УЛУЧШЕНО: гибкий поиск колонок с телефонами по паттернам.
        """
        # Возможные названия колонок с телефонами (case-insensitive)
        phone_patterns = [
            "phone_1", "phone_2", "phone1", "phone2",
            "телефон", "телефон 1", "телефон 2",
            "phone", "tel", "telephone",
            "мобильный", "рабочий"
        ]

        # Приводим названия колонок к нижнему регистру для поиска
        columns_lower = {col.lower(): col for col in df.columns}

        # Ищем колонки, похожие на телефоны
        phone_columns = []
        for pattern in phone_patterns:
            for col_lower, col_original in columns_lower.items():
                if pattern in col_lower and col_original not in phone_columns:
                    phone_columns.append(col_original)

        # Если не нашли ни одной колонки — используем дефолтные
        if not phone_columns:
            logger.warning(
                f"Не найдены колонки с телефонами. "
                f"Доступные колонки: {list(df.columns)}"
            )
            phone_columns = ["phone_1", "phone_2"]

        # Переименовываем первые 2 найденные колонки в стандартные имена
        if len(phone_columns) >= 1:
            if phone_columns[0] != "phone_1":
                df = df.rename(columns={phone_columns[0]: "phone_1"})
        else:
            df["phone_1"] = None

        if len(phone_columns) >= 2:
            if phone_columns[1] != "phone_2":
                df = df.rename(columns={phone_columns[1]: "phone_2"})
        else:
            df["phone_2"] = None

        # Нормализуем
        for col in ("phone_1", "phone_2"):
            if col not in df.columns:
                df[col] = None
            df[col] = df[col].apply(self.phone_service.normalize)

        logger.debug(
            f"Найдено телефонных колонок: {phone_columns[:2]} -> "
            f"phone_1={df['phone_1'].notna().sum()}, "
            f"phone_2={df['phone_2'].notna().sum()}"
        )

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
