"""
QTableView для предпросмотра первых строк очищенных данных.

УЛУЧШЕНО:
- Поиск и фильтрация
- Копирование в буфер обмена
- Контекстное меню
- Экспорт в Excel
"""

import logging
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex, QSortFilterProxyModel
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableView,
    QLineEdit,
    QPushButton,
    QLabel,
    QMenu,
    QFileDialog,
    QMessageBox,
    QApplication,
)
from PyQt6.QtGui import QAction

from config.settings import settings


logger = logging.getLogger(__name__)


class DataFrameTableModel(QAbstractTableModel):
    """
    Простейшая модель для отображения pandas.DataFrame в QTableView.

    Подходит для чтения; редактирование в MVP не требуется.
    """

    def __init__(self, df: pd.DataFrame | None = None, parent=None) -> None:
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Задать новый DataFrame и уведомить виджет о смене данных."""
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iat[index.row(), index.column()]
            return "" if value is None else str(value)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            try:
                return str(self._df.columns[section])
            except IndexError:
                return ""
        else:
            return str(section + 1)


class PreviewTable(QWidget):
    """
    Улучшенная таблица для предпросмотра с поиском и экспортом.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        # Модель и прокси для фильтрации
        self._model = DataFrameTableModel()
        self._proxy_model = QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setFilterCaseSensitivity(
            Qt.CaseSensitivity.CaseInsensitive)

        # Полный DataFrame (для экспорта)
        self._full_df: pd.DataFrame = pd.DataFrame()

        self._setup_ui()
        logger.info("Улучшенная таблица предпросмотра инициализирована")

    def _setup_ui(self):
        """Создать UI."""
        layout = QVBoxLayout()

        # Панель поиска
        search_layout = QHBoxLayout()

        search_label = QLabel("🔍 Поиск:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите текст для поиска...")
        self.search_input.textChanged.connect(self._on_search_changed)

        self.btn_clear_search = QPushButton("✖")
        self.btn_clear_search.setMaximumWidth(30)
        self.btn_clear_search.clicked.connect(self._on_clear_search)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.btn_clear_search)

        layout.addLayout(search_layout)

        # Таблица
        self.table_view = QTableView()
        self.table_view.setModel(self._proxy_model)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(
            self._show_context_menu)

        layout.addWidget(self.table_view)

        # Информация и кнопки
        info_layout = QHBoxLayout()

        self.info_label = QLabel("Нет данных")
        self.info_label.setStyleSheet("color: #999; font-style: italic;")

        self.btn_export = QPushButton("📊 Экспорт в Excel")
        self.btn_export.clicked.connect(self._on_export_clicked)
        self.btn_export.setEnabled(False)

        self.btn_copy = QPushButton("📋 Копировать (Ctrl+C)")
        self.btn_copy.clicked.connect(self._on_copy_clicked)
        self.btn_copy.setEnabled(False)

        info_layout.addWidget(self.info_label)
        info_layout.addStretch()
        info_layout.addWidget(self.btn_copy)
        info_layout.addWidget(self.btn_export)

        layout.addLayout(info_layout)

        self.setLayout(layout)

    def show_dataframe(self, df: pd.DataFrame, limit: int = 10) -> None:
        """
        Показать первые N строк DataFrame.

        Args:
            df: DataFrame для отображения
            limit: количество строк (по умолчанию 10)
        """
        self._full_df = df.copy()  # Сохраняем полный DataFrame
        preview_df = df.head(limit)

        self._model.set_dataframe(preview_df)
        self.table_view.resizeColumnsToContents()

        # Обновляем информацию
        self.info_label.setText(
            f"📊 Показано: {len(preview_df)} из {len(df)} строк | "
            f"Колонок: {len(df.columns)}"
        )
        self.info_label.setStyleSheet("color: #64B5F6; font-weight: bold;")

        # Активируем кнопки
        self.btn_export.setEnabled(len(df) > 0)
        self.btn_copy.setEnabled(len(df) > 0)

    def _on_search_changed(self, text: str):
        """Обработка изменения текста поиска."""
        # Фильтруем по всем колонкам
        self._proxy_model.setFilterKeyColumn(-1)  # -1 = все колонки
        self._proxy_model.setFilterFixedString(text)

        # Обновляем информацию
        visible_rows = self._proxy_model.rowCount()
        total_rows = self._model.rowCount()

        if text:
            self.info_label.setText(
                f"🔍 Найдено: {visible_rows} из {total_rows} строк"
            )
        else:
            self.info_label.setText(
                f"📊 Показано: {total_rows} из {len(self._full_df)} строк | "
                f"Колонок: {len(self._full_df.columns)}"
            )

    def _on_clear_search(self):
        """Очистить поиск."""
        self.search_input.clear()

    def _show_context_menu(self, position):
        """Показать контекстное меню при правом клике."""
        menu = QMenu(self)

        # Действие: Копировать
        copy_action = QAction("📋 Копировать выделенное", self)
        copy_action.triggered.connect(self._on_copy_clicked)
        menu.addAction(copy_action)

        # Действие: Экспорт
        export_action = QAction("📊 Экспорт в Excel", self)
        export_action.triggered.connect(self._on_export_clicked)
        menu.addAction(export_action)

        menu.exec(self.table_view.viewport().mapToGlobal(position))

    def _on_copy_clicked(self):
        """Скопировать выделенные ячейки в буфер обмена."""
        selection = self.table_view.selectedIndexes()

        if not selection:
            QMessageBox.information(
                self,
                "ℹ️ Информация",
                "Выделите ячейки для копирования.",
            )
            return

        # Сортируем по строкам и колонкам
        selection = sorted(
            selection, key=lambda idx: (idx.row(), idx.column()))

        # Формируем текст для буфера обмена (TSV формат)
        current_row = selection[0].row()
        rows_data = []
        row_data = []

        for idx in selection:
            if idx.row() != current_row:
                rows_data.append("\t".join(row_data))
                row_data = []
                current_row = idx.row()

            row_data.append(idx.data() or "")

        # Добавляем последнюю строку
        if row_data:
            rows_data.append("\t".join(row_data))

        clipboard_text = "\n".join(rows_data)

        # Копируем в буфер обмена
        clipboard = QApplication.clipboard()
        clipboard.setText(clipboard_text)

        logger.info(f"Скопировано {len(selection)} ячеек в буфер обмена")

        # Показываем уведомление
        self.info_label.setText(f"✅ Скопировано {len(selection)} ячеек")
        self.info_label.setStyleSheet("color: #4CAF50; font-weight: bold;")

        # Через 2 секунды возвращаем обычный текст
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(2000, lambda: self.info_label.setStyleSheet(
            "color: #64B5F6; font-weight: bold;"))

    def _on_export_clicked(self):
        """Экспортировать таблицу в Excel."""
        if self._full_df.empty:
            QMessageBox.warning(
                self,
                "⚠️ Нет данных",
                "Таблица пуста, нечего экспортировать.",
            )
            return

        try:
            default_name = f"preview_{pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            default_path = str(settings.paths.output_dir / default_name)

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить предпросмотр в Excel",
                default_path,
                "Excel Files (*.xlsx);;All Files (*)",
            )

            if not file_path:
                return

            output_path = Path(file_path)

            # Экспортируем ПОЛНЫЙ DataFrame (не только preview)
            self._full_df.to_excel(
                output_path, index=False, sheet_name="Предпросмотр")

            QMessageBox.information(
                self,
                "✅ Экспорт завершён",
                f"Таблица экспортирована:\n{output_path}\n\n"
                f"Строк: {len(self._full_df)}\n"
                f"Колонок: {len(self._full_df.columns)}",
            )

            logger.info(
                f"Предпросмотр экспортирован: {output_path}, {len(self._full_df)} строк")

        except Exception as exc:
            logger.exception("Ошибка экспорта предпросмотра")
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                f"Не удалось экспортировать таблицу:\n{exc}",
            )

    def keyPressEvent(self, event):
        """Обработка горячих клавиш."""
        # Ctrl+C — копирование
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._on_copy_clicked()
        else:
            super().keyPressEvent(event)
