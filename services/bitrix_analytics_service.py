"""
Сервис аналитики по экспортам из Битрикс24.

Анализирует:
- LEAD (лиды) — отказы, причины
- DEAL (сделки) — стадии, успешные продажи
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter

import pandas as pd

logger = logging.getLogger(__name__)


class BitrixAnalyticsService:
    """Сервис анализа экспортов из Битрикс24."""

    def __init__(self):
        self.lead_df: pd.DataFrame = pd.DataFrame()
        self.deal_df: pd.DataFrame = pd.DataFrame()
        self.metrics: Dict = {}

    def load_bitrix_exports(self, lead_csv_path: Path, deal_csv_path: Path) -> Tuple[bool, str]:
        """
        Загрузить экспорты из Битрикс24.

        Args:
            lead_csv_path: путь к LEAD.csv
            deal_csv_path: путь к DEAL.csv

        Returns:
            (success, message)
        """
        # Загрузка LEAD
        try:
            self.lead_df = self._load_csv_with_detection(lead_csv_path)
            logger.info(
                f"LEAD загружен: {len(self.lead_df)} строк, "
                f"{len(self.lead_df.columns)} колонок"
            )
            logger.debug(f"Колонки LEAD: {list(self.lead_df.columns)}")
        except Exception as exc:
            logger.exception(f"Ошибка загрузки LEAD: {exc}")
            return False, f"Не удалось загрузить LEAD.csv: {exc}"

        # Загрузка DEAL
        try:
            self.deal_df = self._load_csv_with_detection(deal_csv_path)
            logger.info(
                f"DEAL загружен: {len(self.deal_df)} строк, "
                f"{len(self.deal_df.columns)} колонок"
            )
            logger.debug(f"Колонки DEAL: {list(self.deal_df.columns)}")
        except Exception as exc:
            logger.exception(f"Ошибка загрузки DEAL: {exc}")
            return False, f"Не удалось загрузить DEAL.csv: {exc}"

        return True, "Файлы загружены успешно"

    def _load_csv_with_detection(self, path: Path) -> pd.DataFrame:
        """
        Универсальная загрузка CSV с автоопределением разделителя.
        """
        # Пробуем разные разделители и кодировки
        separators = [";", ",", "\t"]
        encodings = ["utf-8", "utf-8-sig", "cp1251", "latin-1"]

        for sep in separators:
            for encoding in encodings:
                try:
                    df = pd.read_csv(
                        path,
                        sep=sep,
                        encoding=encoding,
                        low_memory=False,
                        dtype=str,
                    )
                    # Проверяем, что колонок больше 1 (успешный парсинг)
                    if len(df.columns) > 1:
                        return df
                except Exception:
                    continue

        # Если ничего не подошло — пробуем с автоопределением
        return pd.read_csv(path, encoding="utf-8", low_memory=False, dtype=str)

    def filter_my_leads(self) -> Tuple[int, int]:
        """
        Фильтровать только "наши" лиды (с меткой "Источник телефона").

        Returns:
            (количество_до_фильтрации, количество_после)
        """
        # Ищем колонку "Источник телефона"
        source_col_lead = self._find_column(
            self.lead_df,
            ["Источник телефона", "Phone Source", "Lead Source File"]
        )
        source_col_deal = self._find_column(
            self.deal_df,
            ["Источник телефона", "Phone Source", "Deal Source File"]
        )

        initial_lead = len(self.lead_df)
        initial_deal = len(self.deal_df)

        # Фильтрация LEAD
        if source_col_lead:
            logger.info(f"Найдена колонка LEAD: '{source_col_lead}'")
            # Показываем примеры значений
            sample = self.lead_df[source_col_lead].dropna().unique()[:3]
            logger.debug(f"Примеры значений: {list(sample)}")

            # Фильтруем: оставляем только где есть ".csv"
            self.lead_df = self.lead_df[
                self.lead_df[source_col_lead].astype(str).str.contains(
                    ".csv", case=False, na=False
                )
            ]
            logger.info(f"LEAD: {initial_lead} → {len(self.lead_df)} (после фильтрации)")
        else:
            logger.warning("Колонка 'Источник телефона' не найдена в LEAD — анализируем все")

        # Фильтрация DEAL
        if source_col_deal:
            logger.info(f"Найдена колонка DEAL: '{source_col_deal}'")
            sample = self.deal_df[source_col_deal].dropna().unique()[:3]
            logger.debug(f"Примеры значений: {list(sample)}")

            self.deal_df = self.deal_df[
                self.deal_df[source_col_deal].astype(str).str.contains(
                    ".csv", case=False, na=False
                )
            ]
            logger.info(f"DEAL: {initial_deal} → {len(self.deal_df)} (после фильтрации)")
        else:
            logger.warning("Колонка 'Источник телефона' не найдена в DEAL — анализируем все")

        return initial_lead + initial_deal, len(self.lead_df) + len(self.deal_df)

    def _find_column(self, df: pd.DataFrame, candidates: List[str]) -> str | None:
        """
        Найти колонку по списку возможных названий (case-insensitive).
        """
        for col in df.columns:
            for candidate in candidates:
                if candidate.lower() in col.lower():
                    return col
        return None

    def calculate_metrics(self) -> Dict:
        """
        Рассчитать все метрики.

        Returns:
            Словарь с метриками.
        """
        # 1. Общая статистика
        total_leads = len(self.lead_df) + len(self.deal_df)
        self.metrics["total_leads"] = total_leads
        self.metrics["total_lead_records"] = len(self.lead_df)
        self.metrics["total_deal_records"] = len(self.deal_df)

        logger.info(f"Подсчёт метрик: всего записей = {total_leads}")

        # 2. Причины отказа (из LEAD)
        rejection_col = self._find_column(
            self.lead_df,
            ["причина отказа", "отказ", "reason", "rejection"]
        )

        if rejection_col and not self.lead_df.empty:
            rejection_reasons = self.lead_df[rejection_col].dropna()
            rejection_reasons = rejection_reasons[rejection_reasons.astype(str).str.strip() != ""]

            reason_counts = Counter(rejection_reasons)
            self.metrics["rejection_reasons"] = dict(reason_counts)
            self.metrics["total_rejections"] = len(rejection_reasons)

            logger.info(f"Причины отказа: {len(rejection_reasons)} записей")
        else:
            self.metrics["rejection_reasons"] = {}
            self.metrics["total_rejections"] = 0
            logger.warning("Колонка 'Причина отказа' не найдена в LEAD")

        # 3. Стадии сделок (из DEAL)
        stage_col = self._find_column(
            self.deal_df,
            ["стадия", "stage", "status"]
        )

        if stage_col and not self.deal_df.empty:
            stage_counts = self.deal_df[stage_col].value_counts().to_dict()
            self.metrics["deal_stages"] = stage_counts

            logger.info(f"Стадии сделок: {list(stage_counts.keys())[:3]}...")
        else:
            self.metrics["deal_stages"] = {}
            logger.warning("Колонка 'Стадия' не найдена в DEAL")

        # 4. Успешные продажи
        successful_deals = 0
        if stage_col and not self.deal_df.empty:
            success_keywords = [
                "успешно", "реализовано", "выигран",
                "won", "success", "closed", "завершен"
            ]

            for keyword in success_keywords:
                mask = self.deal_df[stage_col].astype(str).str.contains(
                    keyword, case=False, na=False
                )
                count = mask.sum()
                if count > 0:
                    successful_deals += count
                    logger.debug(f"Найдено '{keyword}': {count} сделок")

        self.metrics["successful_deals"] = successful_deals
        logger.info(f"Успешных продаж: {successful_deals}")

        # 5. Конверсия
        if total_leads > 0:
            conversion = ((len(self.deal_df) + successful_deals) / total_leads) * 100
            self.metrics["conversion"] = round(conversion, 2)
        else:
            self.metrics["conversion"] = 0.0

        logger.info(f"Конверсия: {self.metrics['conversion']}%")

        # 6. Топ-менеджеры (из DEAL)
        manager_col = self._find_column(
            self.deal_df,
            ["ответственный", "responsible", "manager", "assigned"]
        )

        if manager_col and not self.deal_df.empty:
            manager_counts = self.deal_df[manager_col].value_counts().head(5).to_dict()
            self.metrics["top_managers"] = manager_counts

            logger.info(f"Топ-менеджеры: {list(manager_counts.keys())[:3]}")
        else:
            self.metrics["top_managers"] = {}
            logger.warning("Колонка 'Ответственный' не найдена в DEAL")

        return self.metrics

    def get_report_summary(self) -> str:
        """
        Сгенерировать текстовую сводку отчёта.

        Returns:
            Многострочная строка с отчётом.
        """
        summary = f"""
╔═══════════════════════════════════════════════════════════╗
║         ОТЧЁТ ПО ЛИДОГЕНЕРАЦИИ (БИТРИКС24)                ║
╚═══════════════════════════════════════════════════════════╝

1. ОБЩАЯ СТАТИСТИКА
   • Всего записей: {self.metrics.get('total_leads', 0)}
   • Лиды (LEAD): {self.metrics.get('total_lead_records', 0)}
   • Сделки (DEAL): {self.metrics.get('total_deal_records', 0)}
   • Успешные продажи: {self.metrics.get('successful_deals', 0)}
   • Конверсия: {self.metrics.get('conversion', 0)}%

2. ПРИЧИНЫ ОТКАЗА (ТОП-5)
"""

        rejection_reasons = self.metrics.get("rejection_reasons", {})
        if rejection_reasons:
            total_rej = self.metrics.get("total_rejections", 1)
            for idx, (reason, count) in enumerate(
                sorted(rejection_reasons.items(), key=lambda x: x[1], reverse=True)[:5],
                1
            ):
                percentage = (count / total_rej) * 100
                summary += f"   {idx}. {reason}: {count} ({percentage:.1f}%)\n"
        else:
            summary += "   - Нет данных\n"

        summary += "\n3. СТАДИИ СДЕЛОК\n"
        deal_stages = self.metrics.get("deal_stages", {})
        if deal_stages:
            for idx, (stage, count) in enumerate(
                sorted(deal_stages.items(), key=lambda x: x[1], reverse=True),
                1
            ):
                summary += f"   {idx}. {stage}: {count}\n"
        else:
            summary += "   - Нет данных\n"

        summary += "\n4. ТОП-МЕНЕДЖЕРЫ\n"
        top_managers = self.metrics.get("top_managers", {})
        if top_managers:
            for idx, (manager, count) in enumerate(top_managers.items(), 1):
                summary += f"   {idx}. {manager}: {count} сделок\n"
        else:
            summary += "   - Нет данных\n"

        return summary
