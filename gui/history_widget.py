"""
Виджет истории обработок.

Отображает таблицу всех прошлых обработок файлов с возможностью:
- Просмотра деталей
- Удаления записей
- Экспорта в Excel
"""

import logging
from typing import List, Optional
from pathlib import Path

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
    QHeaderView,
    QGroupBox,
    QFileDialog,
)
from PyQt6.QtCore import Qt

from repositories.processing_history_repo import ProcessingHistoryRepository
from config.settings import settings


logger = logging.getLogger(__name__)


class HistoryWidget(QWidget):
    """Виджет истории обработок."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Репозиторий
        self.history_repo = ProcessingHistoryRepository()

        self._setup_ui()
        self._load_history()
        logger.info("Виджет истории инициализирован")

    def _setup_ui(self):
        """Создать UI."""
        main_layout = QVBoxLayout()

        # Заголовок
        header = QLabel("📜 История обработок")
        header.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(header)

        # Информация
        self.info_label = QLabel("Загрузка истории...")
        self.info_label.setStyleSheet("color: #999; font-style: italic;")
        main_layout.addWidget(self.info_label)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID",
            "Дата начала",
            "Дата окончания",
            "Файлов",
            "Всего строк",
            "Валидных",
            "Дубликатов",
            "Статус",
        ])

        # Настройки таблицы
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(True)

        # Автоширина колонок
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(7):
            header.setSectionResizeMode(
                i, QHeaderView.ResizeMode.ResizeToContents)

        # Двойной клик для просмотра деталей
        self.table.itemDoubleClicked.connect(self._on_row_double_clicked)

        main_layout.addWidget(self.table)

        # Кнопки управления
        buttons_layout = QHBoxLayout()

        self.btn_refresh = QPushButton("🔄 Обновить")
        self.btn_refresh.clicked.connect(self._load_history)

        self.btn_delete = QPushButton("🗑️ Удалить запись")
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        self.btn_delete.setEnabled(False)

        self.btn_clear = QPushButton("🧹 Очистить историю")
        self.btn_clear.clicked.connect(self._on_clear_clicked)

        self.btn_export = QPushButton("📊 Экспорт в Excel")
        self.btn_export.clicked.connect(self._on_export_clicked)

        buttons_layout.addWidget(self.btn_refresh)
        buttons_layout.addWidget(self.btn_delete)
        buttons_layout.addWidget(self.btn_clear)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_export)

        main_layout.addLayout(buttons_layout)

        # Обновление состояния кнопок при выборе строки
        self.table.itemSelectionChanged.connect(self._update_buttons_state)

        # Темная тема
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #252525;
                color: #e0e0e0;
                gridline-color: #444;
                border: 1px solid #444;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QTableWidget::item:selected {
                background-color: #4a4a4a;
            }
            QHeaderView::section {
                background-color: #3a3a3a;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #555;
                font-weight: bold;
            }
            QLabel {
                color: #e0e0e0;
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
            }
            QPushButton:pressed {
                background-color: #2a2a2a;
            }
            QPushButton:disabled {
                background-color: #2a2a2a;
                color: #666;
            }
        """)

        self.setLayout(main_layout)

    def _load_history(self):
        """Загрузить историю из БД."""
        try:
            # Запрос всей истории
            query = """
            SELECT 
                id,
                started_at,
                finished_at,
                file_count,
                total_rows,
                final_rows,
                removed_duplicates,
                status
            FROM processing_history
            ORDER BY started_at DESC
            """

            rows = self.history_repo.fetch_all(query)

            # Очищаем таблицу
            self.table.setRowCount(0)

            if not rows:
                self.info_label.setText("📭 История пуста")
                self.info_label.setStyleSheet("color: #999;")
                return

            # Заполняем таблицу
            self.table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                # ID
                self.table.setItem(
                    row_idx, 0, QTableWidgetItem(str(row["id"])))

                # Дата начала
                started = row["started_at"][:19] if row["started_at"] else "-"
                self.table.setItem(row_idx, 1, QTableWidgetItem(started))

                # Дата окончания
                finished = row["finished_at"][:19] if row["finished_at"] else "-"
                self.table.setItem(row_idx, 2, QTableWidgetItem(finished))

                # Файлов
                self.table.setItem(
                    row_idx, 3, QTableWidgetItem(str(row["file_count"])))

                # Всего строк
                self.table.setItem(
                    row_idx, 4, QTableWidgetItem(str(row["total_rows"])))

                # Валидных
                self.table.setItem(
                    row_idx, 5, QTableWidgetItem(str(row["final_rows"])))

                # Дубликатов
                self.table.setItem(row_idx, 6, QTableWidgetItem(
                    str(row["removed_duplicates"])))

                # Статус
                status_item = QTableWidgetItem(row["status"])
                if row["status"] == "success":
                    status_item.setForeground(Qt.GlobalColor.green)
                else:
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(row_idx, 7, status_item)

                # Выравнивание чисел по центру
                for col in [0, 3, 4, 5, 6]:
                    item = self.table.item(row_idx, col)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.info_label.setText(f"📊 Всего записей: {len(rows)}")
            self.info_label.setStyleSheet("color: #64B5F6; font-weight: bold;")

            logger.info(f"История загружена: {len(rows)} записей")

        except Exception as exc:
            logger.exception("Ошибка загрузки истории")
            self.info_label.setText(f"❌ Ошибка загрузки: {exc}")
            self.info_label.setStyleSheet("color: red;")

    def _update_buttons_state(self):
        """Обновить состояние кнопок."""
        has_selection = len(self.table.selectedItems()) > 0
        self.btn_delete.setEnabled(has_selection)

    def _on_row_double_clicked(self, item: QTableWidgetItem):
        """Показать детали обработки при двойном клике."""
        row = item.row()

        # Получаем ID записи
        record_id = int(self.table.item(row, 0).text())

        # Формируем детальное сообщение
        details = f"""
╔════════════════════════════════════╗
║  ДЕТАЛИ ОБРАБОТКИ #{record_id}
╚════════════════════════════════════╝

📅 Начало:          {self.table.item(row, 1).text()}
📅 Окончание:       {self.table.item(row, 2).text()}

📁 Файлов:          {self.table.item(row, 3).text()}
📊 Всего строк:     {self.table.item(row, 4).text()}
✅ Валидных:        {self.table.item(row, 5).text()}
🔄 Дубликатов:      {self.table.item(row, 6).text()}

🏷️ Статус:          {self.table.item(row, 7).text().upper()}
"""

        QMessageBox.information(
            self,
            f"📋 Обработка #{record_id}",
            details,
        )

    def _on_delete_clicked(self):
        """Удалить выбранную запись."""
        selected = self.table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        record_id = int(self.table.item(row, 0).text())

        reply = QMessageBox.question(
            self,
            "⚠️ Подтверждение",
            f"Вы уверены, что хотите удалить запись #{record_id}?\n\n"
            "Это действие нельзя отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM processing_history WHERE id = ?"
                self.history_repo.execute_write(query, (record_id,))

                logger.info(f"Удалена запись #{record_id}")
                self._load_history()

                QMessageBox.information(
                    self,
                    "✅ Удалено",
                    f"Запись #{record_id} успешно удалена.",
                )

            except Exception as exc:
                logger.exception("Ошибка удаления записи")
                QMessageBox.critical(
                    self,
                    "❌ Ошибка",
                    f"Не удалось удалить запись:\n{exc}",
                )

    def _on_clear_clicked(self):
        """Очистить всю историю."""
        reply = QMessageBox.question(
            self,
            "⚠️ ВНИМАНИЕ!",
            "Вы уверены, что хотите ПОЛНОСТЬЮ ОЧИСТИТЬ историю?\n\n"
            "ВСЕ записи будут удалены безвозвратно!\n\n"
            "Это действие НЕЛЬЗЯ отменить!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                query = "DELETE FROM processing_history"
                self.history_repo.execute_write(query)

                logger.warning("История полностью очищена")
                self._load_history()

                QMessageBox.information(
                    self,
                    "✅ Очищено",
                    "История успешно очищена.",
                )

            except Exception as exc:
                logger.exception("Ошибка очистки истории")
                QMessageBox.critical(
                    self,
                    "❌ Ошибка",
                    f"Не удалось очистить историю:\n{exc}",
                )

    def _on_export_clicked(self):
        """Экспортировать историю в Excel."""
        try:
            # Получаем все данные
            query = """
            SELECT *
            FROM processing_history
            ORDER BY started_at DESC
            """

            rows = self.history_repo.fetch_all(query)

            if not rows:
                QMessageBox.warning(
                    self,
                    "⚠️ Нет данных",
                    "История пуста, нечего экспортировать.",
                )
                return

            # Конвертируем в DataFrame
            data = [dict(row) for row in rows]
            df = pd.DataFrame(data)

            # Выбираем путь сохранения
            default_name = f"history_{pd.Timestamp.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx"
            default_path = str(settings.paths.reports_dir / default_name)

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Сохранить историю в Excel",
                default_path,
                "Excel Files (*.xlsx);;All Files (*)",
            )

            if not file_path:
                return

            output_path = Path(file_path)

            # Экспортируем в Excel
            df.to_excel(output_path, index=False, sheet_name="История")

            QMessageBox.information(
                self,
                "✅ Экспорт завершён",
                f"История экспортирована:\n{output_path}\n\n"
                f"Записей: {len(df)}",
            )

            logger.info(
                f"История экспортирована: {output_path}, {len(df)} записей")

        except Exception as exc:
            logger.exception("Ошибка экспорта истории")
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                f"Не удалось экспортировать историю:\n{exc}",
            )

    def refresh(self):
        """Обновить историю (вызывается извне)."""
        self._load_history()

    def refresh(self):
        """Обновить историю (вызывается извне)."""
        self._load_history()
