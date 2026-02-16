"""
Виджет аналитики с графиками и статистикой.

Отображает:
- Общую статистику в карточках
- Графики matplotlib
- Кнопки экспорта отчётов
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QScrollArea,
    QFileDialog,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from services.analytics_service import AnalyticsService
from repositories.processing_history_repo import ProcessingHistoryRepository
from repositories.managers_repo import ManagersRepository
from config.settings import settings


logger = logging.getLogger(__name__)


class StatCard(QWidget):
    """Карточка со статистикой (темная тема)."""

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self._setup_ui(title, value)

    def _setup_ui(self, title: str, value: str):
        """Создать UI карточки."""
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        title_label = QLabel(title)
        title_label.setStyleSheet(
            "font-size: 12px; color: #999; font-weight: normal;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Значение
        value_label = QLabel(value)
        value_label.setStyleSheet(
            "font-size: 24px; color: #64B5F6; font-weight: bold;"
        )
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addStretch()

        self.setLayout(layout)
        self.setStyleSheet(
            """
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #2d2d2d, stop:1 #252525
                );
                border-radius: 8px;
                border: 1px solid #444;
            }
            """
        )
        self.setMinimumHeight(100)
        self.setMinimumWidth(150)


class AnalyticsWidget(QWidget):
    """Виджет аналитики с графиками и статистикой."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # ========== ТЕМНАЯ ТЕМА ДЛЯ MATPLOTLIB ==========
        import matplotlib
        matplotlib.rcParams.update({
            'figure.facecolor': '#1e1e1e',      # Фон графика
            'axes.facecolor': '#2d2d2d',        # Фон области с данными
            'axes.edgecolor': '#555',           # Цвет рамки
            'axes.labelcolor': '#e0e0e0',       # Цвет подписей осей
            'text.color': '#e0e0e0',            # Цвет текста
            'xtick.color': '#e0e0e0',           # Цвет меток X
            'ytick.color': '#e0e0e0',           # Цвет меток Y
            'grid.color': '#444',               # Цвет сетки
            'legend.facecolor': '#2d2d2d',      # Фон легенды
            'legend.edgecolor': '#555',         # Рамка легенды
        })

        # Репозитории
        self.history_repo = ProcessingHistoryRepository()
        self.managers_repo = ManagersRepository()

        # Сервис аналитики
        self.analytics_service = AnalyticsService(
            self.history_repo, self.managers_repo
        )

        # Данные для графиков (заполняются извне)
        self.cleaned_df: Optional[pd.DataFrame] = None
        self.bitrix_df: Optional[pd.DataFrame] = None

        self._setup_ui()
        logger.info("Виджет аналитики инициализирован")

    def _setup_ui(self):
        """Создать UI виджета."""
        main_layout = QVBoxLayout()

        # Заголовок
        header = QLabel("📊 Аналитика и статистика")
        header.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(header)

        # Скролл-область для всего контента
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Блок 1: Карточки со статистикой
        stats_group = self._create_stats_cards()
        scroll_layout.addWidget(stats_group)

        # Блок 2: Графики
        charts_group = self._create_charts_section()
        scroll_layout.addWidget(charts_group)

        # Блок 3: Кнопки экспорта
        export_group = self._create_export_section()
        scroll_layout.addWidget(export_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)
        # ========== ТЕМНАЯ ТЕМА ДЛЯ ВСЕГО ВИДЖЕТА ==========
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QGroupBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #e0e0e0;
                background: transparent;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 8px 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4a4a4a;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666;
            }
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
        """)

        self.setLayout(main_layout)

    def _create_stats_cards(self) -> QGroupBox:
        """Создать блок с карточками статистики."""
        group = QGroupBox("Общая статистика")
        layout = QHBoxLayout()

        # Создаём карточки (пустые, заполним при обновлении)
        self.card_total_leads = StatCard("Всего лидов", "0")
        self.card_unique_phones = StatCard("Уникальных телефонов", "0")
        self.card_duplicates = StatCard("Дубликатов", "0")
        self.card_invalid = StatCard("Битых номеров", "0")
        self.card_files = StatCard("Обработано файлов", "0")

        layout.addWidget(self.card_total_leads)
        layout.addWidget(self.card_unique_phones)
        layout.addWidget(self.card_duplicates)
        layout.addWidget(self.card_invalid)
        layout.addWidget(self.card_files)

        group.setLayout(layout)
        return group

    def _create_charts_section(self) -> QGroupBox:
        """Создать блок с графиками."""
        from PyQt6.QtWidgets import QSizePolicy

        group = QGroupBox("Визуализация данных")
        layout = QVBoxLayout()

        # График 1: Динамика по дням
        layout.addWidget(QLabel("График обработки лидов по дням:"))
        self.chart_daily = FigureCanvas(Figure(figsize=(14, 6)))
        self.chart_daily.setMinimumHeight(400)
        self.chart_daily.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.chart_daily)

        # График 2: Распределение по менеджерам
        layout.addWidget(QLabel("Распределение лидов по менеджерам:"))
        self.chart_managers = FigureCanvas(Figure(figsize=(10, 10)))
        self.chart_managers.setMinimumHeight(600)
        self.chart_managers.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.chart_managers)

        # График 3: Лиды по источникам
        layout.addWidget(QLabel("Лиды по источникам (файлам):"))
        self.chart_sources = FigureCanvas(Figure(figsize=(14, 6)))
        self.chart_sources.setMinimumHeight(400)
        self.chart_sources.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.chart_sources)

        group.setLayout(layout)
        return group

    def _create_export_section(self) -> QGroupBox:
        """Создать блок с кнопками экспорта."""
        group = QGroupBox("Экспорт отчётов")
        layout = QHBoxLayout()

        self.btn_export_excel = QPushButton("📊 Экспорт в Excel")
        self.btn_export_excel.clicked.connect(self._on_export_excel_clicked)

        self.btn_refresh = QPushButton("🔄 Обновить данные")
        self.btn_refresh.clicked.connect(self.refresh_analytics)

        layout.addWidget(self.btn_export_excel)
        layout.addWidget(self.btn_refresh)
        layout.addStretch()

        group.setLayout(layout)
        return group

    def refresh_analytics(self):
        """Обновить всю аналитику."""
        try:
            # Обновляем карточки статистики
            stats = self.analytics_service.get_overall_stats()
            self._update_stats_cards(stats)

            # Обновляем график динамики
            fig_daily = self.analytics_service.create_daily_chart(days=30)
            self.chart_daily.figure = fig_daily
            self.chart_daily.draw()

            # Обновляем график по менеджерам (если есть данные)
            if self.bitrix_df is not None and not self.bitrix_df.empty:
                fig_managers = self.analytics_service.create_manager_pie_chart(
                    self.bitrix_df
                )
                self.chart_managers.figure = fig_managers
                self.chart_managers.draw()

            # Обновляем график по источникам (если есть данные)
            if self.cleaned_df is not None and not self.cleaned_df.empty:
                fig_sources = self.analytics_service.create_sources_bar_chart(
                    self.cleaned_df
                )
                self.chart_sources.figure = fig_sources
                self.chart_sources.draw()

            logger.info("Аналитика обновлена")

        except Exception as exc:
            logger.exception("Ошибка обновления аналитики")
            QMessageBox.warning(
                self,
                "Ошибка",
                f"Не удалось обновить аналитику:\n{exc}",
            )

    def _update_stats_cards(self, stats: dict):
        """Обновить значения в карточках статистики."""
        # Обновляем карточки (находим QLabel с значением и меняем текст)
        self._update_card_value(
            self.card_total_leads, f"{stats['total_valid_leads']:,}"
        )
        self._update_card_value(
            self.card_unique_phones, f"{stats['total_unique_phones']:,}"
        )
        self._update_card_value(
            self.card_duplicates, f"{stats['total_duplicates']:,}"
        )
        self._update_card_value(
            self.card_invalid, f"{stats['total_invalid_phones']:,}"
        )
        self._update_card_value(self.card_files, f"{stats['total_files']:,}")

    def _update_card_value(self, card: StatCard, value: str):
        """Обновить значение в карточке."""
        # StatCard — это виджет из gui.analytics_widget
        # Находим QLabel с большим шрифтом (это значение)
        for child in card.findChildren(QLabel):
            if "24px" in child.styleSheet() or "color: #64B5F6" in child.styleSheet():
                child.setText(value)
                break

    def set_data(self, cleaned_df: pd.DataFrame, bitrix_df: pd.DataFrame):
        """
        Установить данные для графиков.

        Вызывается из главного окна после обработки файлов.
        """
        self.cleaned_df = cleaned_df
        self.bitrix_df = bitrix_df
        self.refresh_analytics()

    def _on_export_excel_clicked(self):
        """Экспортировать отчёт в Excel."""
        try:
            stats = self.analytics_service.get_overall_stats()

            default_name = f"analytics_report_{pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            default_path = str(settings.paths.reports_dir / default_name)

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить отчёт Excel",
                default_path,
                "Excel Files (*.xlsx);;All Files (*)",
            )

            if not file_path:
                return

            output_path = Path(file_path)
            self.analytics_service.export_excel_report(output_path, stats)

            QMessageBox.information(
                self,
                "✅ Экспорт завершён",
                f"Отчёт сохранён:\n{output_path}",
            )

            logger.info(f"Excel-отчёт экспортирован: {output_path}")

        except Exception as exc:
            logger.exception("Ошибка экспорта отчёта")
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                f"Не удалось экспортировать отчёт:\n{exc}",
            )
