"""
Главное окно приложения (production-версия) - ПОЛНАЯ ВЕРСИЯ.
"""

import logging
from pathlib import Path
from typing import List, Optional
from services.yandex_maps_url_generator import YandexMapsURLGenerator

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QDialog,
    QMainWindow,
    QVBoxLayout,
    QListWidget,
    QLineEdit,
    QCheckBox,
    QTableWidget,
    QHBoxLayout,
    QTableWidgetItem,
    QPushButton,
    QTextEdit,
    QLabel,
    QMessageBox,
    QFileDialog,
    QGroupBox,
)

from config.settings import settings
from core.exceptions import LeadGenError, FileProcessingError, ValidationError
from repositories.managers_repo import ManagersRepository
from repositories.processing_history_repo import ProcessingHistoryRepository
from services.phone_service import PhoneService
from services.data_service import DataService
from services.bitrix_service import BitrixService
from gui.file_loader import FileLoaderWidget
from gui.preview_table import PreviewTable
from gui.progress_bar import ProgressBarWidget


logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Главное окно PyQt6-приложения.

    Разделение ответственности:
    - GUI: отображение, события, валидация ввода.
    - Services: вся бизнес-логика.
    - Repositories: сохранение данных в БД.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Lead Generation System v1.0 (Production)")
        self.resize(1200, 800)

        # Репозитории
        self.managers_repo = ManagersRepository()
        self.history_repo = ProcessingHistoryRepository()

        # Сервисы
        self.phone_service = PhoneService()
        self.data_service = DataService(self.phone_service)
        self.bitrix_service: Optional[BitrixService] = None

        # Компоненты GUI
        self.file_loader = FileLoaderWidget()
        self.managers_edit = QTextEdit()
        self.button_save_managers = QPushButton("💾 Сохранить менеджеров")
        self.button_process = QPushButton("🔄 Очистить и объединить")
        self.button_export = QPushButton("📤 Экспортировать для Битрикс")

        self.progress_bar = ProgressBarWidget()
        self.status_label = QLabel("✅ Готово к работе")
        self.preview_table = PreviewTable()

        # Результаты обработки
        self.cleaned_df: Optional[pd.DataFrame] = None
        self.bitrix_df: Optional[pd.DataFrame] = None
        self.current_processing_id: Optional[int] = None

        self._setup_ui()
        self._connect_signals()
        self._load_managers_from_db()

        logger.info("Главное окно инициализировано")

    def _setup_ui(self) -> None:
        """Построить компоновку главного окна с вкладками."""
        from PyQt6.QtWidgets import QTabWidget
        from gui.analytics_widget import AnalyticsWidget
        from gui.url_generator_widget import URLGeneratorWidget

        central = QWidget()
        main_layout = QVBoxLayout()

        # Создаём вкладки
        tabs = QTabWidget()

        # ============================================================
        # ВКЛАДКА 1: ОБРАБОТКА ДАННЫХ (основной функционал)
        # ============================================================
        tab_processing = QWidget()
        processing_layout = QVBoxLayout()

        # Блок 1: Загрузка файлов
        group_files = QGroupBox("📁 1. Загрузка файлов")
        layout_files = QVBoxLayout()
        layout_files.addWidget(self.file_loader)
        group_files.setLayout(layout_files)

        # Блок 2: Менеджеры
        group_managers = QGroupBox("👥 2. Настройки менеджеров")
        layout_managers = QVBoxLayout()
        self.managers_edit.setPlaceholderText(
            "Один менеджер на строку\nНапример:\nИванов Иван\nПетров Пётр"
        )
        self.managers_edit.setMaximumHeight(120)
        layout_managers.addWidget(self.managers_edit)
        layout_managers.addWidget(self.button_save_managers)
        group_managers.setLayout(layout_managers)

        # Блок 3: Обработка
        group_process = QGroupBox("⚙️ 3. Очистка и объединение")
        layout_process = QVBoxLayout()
        self.button_process.setEnabled(False)
        layout_process.addWidget(self.button_process)
        layout_process.addWidget(self.progress_bar)
        layout_process.addWidget(self.status_label)
        group_process.setLayout(layout_process)

        # Блок 4: Предпросмотр
        group_preview = QGroupBox("👁️ 4. Предпросмотр результатов")
        layout_preview = QVBoxLayout()
        layout_preview.addWidget(self.preview_table)
        group_preview.setLayout(layout_preview)

        # Блок 5: Экспорт
        group_export = QGroupBox("💾 5. Экспорт")
        layout_export = QHBoxLayout()
        layout_export.addStretch(1)
        self.button_export.setEnabled(False)
        layout_export.addWidget(self.button_export)
        group_export.setLayout(layout_export)

        # Добавляем все блоки в layout вкладки обработки
        processing_layout.addWidget(group_files)
        processing_layout.addWidget(group_managers)
        processing_layout.addWidget(group_process)
        processing_layout.addWidget(group_preview)
        processing_layout.addWidget(group_export)

        tab_processing.setLayout(processing_layout)

        # ============================================================
        # ВКЛАДКА 2: АНАЛИТИКА
        # ============================================================
        self.analytics_widget = AnalyticsWidget()

        # Добавляем вкладки
        tabs.addTab(tab_processing, "📝 Обработка данных")
        tabs.addTab(self.analytics_widget, "📊 Статистика обработки")

        # Вкладка: Битрикс-аналитика
        from gui.bitrix_analytics_widget import BitrixAnalyticsWidget
        self.bitrix_analytics_widget = BitrixAnalyticsWidget()
        tabs.addTab(self.bitrix_analytics_widget, "📈 Битрикс Аналитика")

        # Вкладка: История (НОВАЯ!)
        from gui.history_widget import HistoryWidget
        self.history_widget = HistoryWidget()
        tabs.addTab(self.history_widget, "📜 История")

        # ============================================================
        # ВКЛАДКА: ГЕНЕРАТОР ССЫЛОК ЯНДЕКС.КАРТ (НОВАЯ!)
        # ============================================================
        self.url_generator_widget = URLGeneratorWidget()
        tabs.addTab(self.url_generator_widget, "🗺️ Генератор ссылок")

        # Вкладка: Настройки
        from gui.settings_widget import SettingsWidget
        self.settings_widget = SettingsWidget()
        tabs.addTab(self.settings_widget, "⚙️ Настройки")

        # ============================================================
        # СВЯЗЬ ВИДЖЕТОВ: обновление городов при изменении настроек
        # ============================================================
        # Когда города изменяются в настройках, обновляем генератор
        self.settings_widget.cities_manager.cities_updated.connect(
            self.url_generator_widget.refresh_cities
        )

        # Добавляем вкладки в главный layout
        main_layout.addWidget(tabs)

        central.setLayout(main_layout)
        self.setCentralWidget(central)

    def _connect_signals(self) -> None:
        """Подключить сигналы."""
        self.button_save_managers.clicked.connect(
            self._on_save_managers_clicked)
        self.button_process.clicked.connect(self._on_process_clicked)
        self.button_export.clicked.connect(self._on_export_clicked)

        self.file_loader.button_select.clicked.connect(
            self._update_buttons_state)
        self.managers_edit.textChanged.connect(self._update_buttons_state)

    def _load_managers_from_db(self) -> None:
        """Загрузить менеджеров из БД."""
        try:
            managers = self.managers_repo.get_all_active()
            if managers:
                self.managers_edit.setText("\n".join(managers))
                logger.info(f"Загружено {len(managers)} менеджеров из БД")
            else:
                # Если в БД пусто, берём из settings
                self.managers_edit.setText(
                    "\n".join(settings.default_managers))
        except Exception as exc:
            logger.exception("Ошибка загрузки менеджеров из БД")
            QMessageBox.warning(
                self,
                "Предупреждение",
                f"Не удалось загрузить менеджеров из БД:\n{exc}",
            )

    def _get_managers_from_edit(self) -> List[str]:
        """Считать менеджеров из текстового поля."""
        lines = [line.strip()
                 for line in self.managers_edit.toPlainText().splitlines()]
        return [line for line in lines if line]

    def _on_save_managers_clicked(self) -> None:
        """Сохранить менеджеров в БД."""
        managers = self._get_managers_from_edit()
        if not managers:
            QMessageBox.warning(
                self,
                "❌ Ошибка",
                "Нужно указать хотя бы одного менеджера.",
            )
            return

        try:
            self.managers_repo.sync_managers(managers)
            QMessageBox.information(
                self,
                "✅ Сохранено",
                f"Список из {len(managers)} менеджеров сохранён.",
            )
            logger.info(f"Менеджеры сохранены: {managers}")
            self._update_buttons_state()
        except Exception as exc:
            logger.exception("Ошибка сохранения менеджеров")
            QMessageBox.critical(
                self,
                "❌ Критическая ошибка",
                f"Не удалось сохранить менеджеров:\n{exc}",
            )

    def _update_buttons_state(self) -> None:
        """Обновить состояние кнопок."""
        has_files = len(self.file_loader.selected_files) > 0
        has_managers = len(self._get_managers_from_edit()) > 0
        has_results = self.bitrix_df is not None and not self.bitrix_df.empty

        self.button_process.setEnabled(has_files and has_managers)
        self.button_export.setEnabled(has_results)

    def _on_process_clicked(self) -> None:
        """Обработать файлы."""
        file_paths = self.file_loader.selected_files
        if not file_paths:
            QMessageBox.warning(self, "❌ Ошибка", "Не выбраны файлы.")
            return

        managers = self._get_managers_from_edit()
        if not managers:
            QMessageBox.warning(
                self, "❌ Ошибка", "Нет менеджеров для распределения.")
            return

        # Начинаем запись в БД
        try:
            self.current_processing_id = self.history_repo.start_processing(
                len(file_paths))
        except Exception as exc:
            logger.exception("Ошибка записи в историю обработки")
            QMessageBox.warning(self, "⚠️ Предупреждение",
                                "Не удалось записать историю в БД.")

        try:
            self.progress_bar.set_progress(10, "📂 Чтение и очистка файлов...")
            self.status_label.setText("⏳ Идёт обработка...")

            # Шаг 1: Загрузка и очистка
            cleaned_df, stats = self.data_service.load_and_clean_files(
                file_paths)
            self.cleaned_df = cleaned_df

            self.progress_bar.set_progress(50, "🔄 Маппинг в формат Битрикс...")

            # Шаг 2: Маппинг в Битрикс
            self.bitrix_service = BitrixService(managers)
            self.bitrix_df = self.bitrix_service.map_to_bitrix(cleaned_df)

            self.progress_bar.set_progress(
                80, "👁️ Обновление предпросмотра...")

            # Шаг 3: Предпросмотр
            preview_cols = [
                "Название лида",
                "Рабочий телефон",
                "Адрес",
                "Ответственный",
            ]
            preview_df = self.bitrix_df[preview_cols].copy()
            self.preview_table.show_dataframe(
                preview_df, limit=settings.preview_rows)  # ← используем настройку

            self.progress_bar.set_progress(100, "✅ Готово")
            self.status_label.setText(
                f"✅ Обработано: {stats.final_rows} строк | "
                f"Уникальных номеров: {stats.unique_phones} | "
                f"Удалено дубликатов: {stats.removed_duplicates}"
            )

            # Сохраняем статистику в БД
            if self.current_processing_id:
                self.history_repo.finish_processing(
                    self.current_processing_id, stats, "success"
                )

            logger.info(f"Обработка завершена успешно: {stats.model_dump()}")
            self._update_buttons_state()

            # Передаём данные в виджет аналитики
            try:
                self.analytics_widget.set_data(self.cleaned_df, self.bitrix_df)
                logger.debug("Данные переданы в виджет аналитики")
            except Exception as exc:
                logger.warning(f"Не удалось обновить аналитику: {exc}")

            # Обновляем историю обработок
            try:
                self.history_widget.refresh()
                logger.debug("История обработок обновлена")
            except Exception as exc:
                logger.warning(f"Не удалось обновить историю: {exc}")

        except FileProcessingError as exc:
            logger.error(f"Ошибка обработки файлов: {exc.message}")
            QMessageBox.critical(
                self,
                "❌ Ошибка обработки файлов",
                f"{exc.message}\n\nДетали: {exc.details}",
            )
            self._handle_processing_error()

        except ValidationError as exc:
            logger.error(f"Ошибка валидации: {exc.message}")
            QMessageBox.critical(
                self,
                "❌ Ошибка валидации данных",
                f"{exc.message}\n\nПроверьте корректность входных файлов.",
            )
            self._handle_processing_error()

        except LeadGenError as exc:
            logger.error(f"Ошибка бизнес-логики: {exc.message}")
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                f"{exc.message}",
            )
            self._handle_processing_error()

        except Exception as exc:
            logger.exception("Неожиданная ошибка при обработке")
            QMessageBox.critical(
                self,
                "❌ Критическая ошибка",
                f"Неожиданная ошибка:\n{exc}",
            )
            self._handle_processing_error()

    def _handle_processing_error(self) -> None:
        """Обработать ошибку во время processing."""
        self.progress_bar.reset_progress()
        self.status_label.setText("❌ Ошибка при обработке")
        if self.current_processing_id:
            # Пытаемся записать failed статус
            try:
                from schemas.lead import ProcessingStats
                empty_stats = ProcessingStats(
                    total_rows=0,
                    removed_empty_phones=0,
                    removed_duplicates=0,
                    final_rows=0,
                    unique_phones=0,
                )
                self.history_repo.finish_processing(
                    self.current_processing_id, empty_stats, "failed"
                )
            except Exception:
                pass

    def _on_export_clicked(self) -> None:
        """
        Экспортировать в CSV для Битрикс24.

        ФОРМАТ БИТРИКС:
        - Разделитель: точка с запятой (;)
        - Кодировка: UTF-8 с BOM (utf-8-sig)
        - Кавычки: все значения в кавычках
        """
        if self.bitrix_df is None or self.bitrix_df.empty:
            QMessageBox.warning(self, "❌ Ошибка", "Нет данных для экспорта.")
            return

        # Предлагаем имя файла по умолчанию
        from datetime import datetime
        default_name = f"bitrix_export_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        default_path = str(settings.paths.output_dir / default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV для Битрикс24",
            default_path,
            "CSV Files (*.csv);;All Files (*)",
        )
        if not file_path:
            return

        try:
            output_path = Path(file_path)

            # КРИТИЧНО для Битрикс24: точка с запятой, UTF-8 с BOM, кавычки
            self.bitrix_df.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig",  # BOM для корректного отображения в Excel/Битрикс
                sep=";",               # ← КЛЮЧЕВОЕ: точка с запятой!
                quoting=1,             # csv.QUOTE_ALL — все значения в кавычках
            )

            # Показываем детальную информацию об экспорте
            success_msg = (
                f"✅ Файл успешно сохранён:\n{output_path}\n\n"
                f"📊 Параметры экспорта:\n"
                f"   • Разделитель: точка с запятой (;)\n"
                f"   • Кодировка: UTF-8 с BOM\n"
                f"   • Строк экспортировано: {len(self.bitrix_df)}\n"
                f"   • Колонок: {len(self.bitrix_df.columns)}\n\n"
                f"💡 Готово к импорту в Битрикс24!"
            )

            QMessageBox.information(
                self,
                "✅ Экспорт завершён",
                success_msg,
            )

            logger.info(
                f"Экспорт выполнен: {output_path}, {len(self.bitrix_df)} строк, "
                f"разделитель=';', кодировка=utf-8-sig"
            )

        except Exception as exc:
            logger.exception("Ошибка при экспорте")
            QMessageBox.critical(
                self,
                "❌ Критическая ошибка",
                f"Не удалось экспортировать файл:\n{exc}",
            )

    def closeEvent(self, event) -> None:
        """Обработать закрытие окна (сохранение состояния и т.п.)."""
        logger.info("Закрытие главного окна")
        event.accept()
