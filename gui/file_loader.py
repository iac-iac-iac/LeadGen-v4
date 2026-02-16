"""
Логика выбора файлов через QFileDialog и Drag & Drop.

ОБНОВЛЕНО:
- Добавлен Drag & Drop
- Визуальная подсветка при наведении
- Валидация файлов
- Удаление файлов из списка
"""

from pathlib import Path
from typing import List

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QLabel,
    QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
import logging


logger = logging.getLogger(__name__)


class FileLoaderWidget(QWidget):
    """
    Виджет для выбора и отображения списка входных файлов.

    Поддерживает:
    - Выбор через кнопку
    - Drag & Drop
    - Удаление файлов
    """

    # Сигнал испускается при изменении списка файлов
    files_changed = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.selected_files: List[Path] = []

        # Включаем Drag & Drop
        self.setAcceptDrops(True)

        self.button_select = QPushButton("📁 Выбрать файлы")
        self.button_remove = QPushButton("🗑️ Удалить выбранные")
        self.button_clear = QPushButton("🧹 Очистить всё")

        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(
            QListWidget.SelectionMode.ExtendedSelection
        )

        self.label_count = QLabel("Загружено: 0 файлов")

        # Drag & Drop зона
        self.drop_zone_label = QLabel(
            "🎯 Перетащите файлы сюда\n"
            "или нажмите кнопку ниже"
        )
        self.drop_zone_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drop_zone_label.setMinimumHeight(100)
        self.drop_zone_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #555;
                border-radius: 10px;
                background-color: #2d2d2d;
                color: #999;
                font-size: 14px;
                padding: 20px;
            }
        """)

        layout = QVBoxLayout()
        layout.addWidget(self.drop_zone_label)

        # Горизонтальный layout для кнопок
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.button_select)
        buttons_layout.addWidget(self.button_remove)
        buttons_layout.addWidget(self.button_clear)
        layout.addLayout(buttons_layout)

        layout.addWidget(self.list_widget)
        layout.addWidget(self.label_count)
        self.setLayout(layout)

        # Подключаем сигналы
        self.button_select.clicked.connect(self._on_select_files_clicked)
        self.button_remove.clicked.connect(self._on_remove_selected_clicked)
        self.button_clear.clicked.connect(self._on_clear_all_clicked)
        self.list_widget.itemSelectionChanged.connect(
            self._update_buttons_state)

        # Изначально кнопки удаления неактивны
        self._update_buttons_state()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Обработка наведения файла."""
        if event.mimeData().hasUrls():
            # Проверяем, что хотя бы один файл — CSV/TSV
            valid = False
            for url in event.mimeData().urls():
                path = Path(url.toLocalFile())
                if path.suffix.lower() in [".csv", ".tsv"]:
                    valid = True
                    break

            if valid:
                event.acceptProposedAction()
                # Подсветка при наведении
                self.drop_zone_label.setStyleSheet("""
                    QLabel {
                        border: 2px dashed #4CAF50;
                        border-radius: 10px;
                        background-color: #2d4a2d;
                        color: #4CAF50;
                        font-size: 14px;
                        padding: 20px;
                        font-weight: bold;
                    }
                """)
            else:
                event.ignore()
        else:
            event.ignore()

    def dragLeaveEvent(self, event) -> None:
        """Обработка ухода курсора."""
        self._reset_drop_zone_style()

    def dropEvent(self, event: QDropEvent) -> None:
        """Обработка сброса файлов."""
        urls = event.mimeData().urls()
        new_files = []

        for url in urls:
            path = Path(url.toLocalFile())

            # Валидация расширения
            if path.suffix.lower() in [".csv", ".tsv"]:
                if path not in self.selected_files:
                    new_files.append(path)
                    logger.info(
                        f"Добавлен файл через Drag & Drop: {path.name}")
            else:
                logger.warning(
                    f"Пропущен файл (неверное расширение): {path.name}")

        if new_files:
            self.selected_files.extend(new_files)
            self._refresh_list()

            # Анимация успеха
            self.drop_zone_label.setStyleSheet("""
                QLabel {
                    border: 2px solid #4CAF50;
                    border-radius: 10px;
                    background-color: #1e3a1e;
                    color: #4CAF50;
                    font-size: 14px;
                    padding: 20px;
                    font-weight: bold;
                }
            """)
            self.drop_zone_label.setText(
                f"✅ Добавлено файлов: {len(new_files)}\n"
                f"Перетащите ещё или нажмите кнопку"
            )

            # Через 2 секунды возвращаем обычный вид
            QTimer.singleShot(2000, self._reset_drop_zone_style)
        else:
            # Возвращаем стиль сразу
            self._reset_drop_zone_style()

        event.acceptProposedAction()

    def _reset_drop_zone_style(self):
        """Вернуть обычный стиль drop-зоны."""
        self.drop_zone_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #555;
                border-radius: 10px;
                background-color: #2d2d2d;
                color: #999;
                font-size: 14px;
                padding: 20px;
            }
        """)
        self.drop_zone_label.setText(
            "🎯 Перетащите файлы сюда\n"
            "или нажмите кнопку ниже"
        )

    def _on_select_files_clicked(self) -> None:
        """Обработчик клика по кнопке выбора файлов."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы Webbee AI",
            "",
            "Data Files (*.tsv *.csv);;All Files (*)",
        )
        if not file_paths:
            return

        # Добавляем новые файлы (избегаем дубликатов)
        new_files = []
        for p in file_paths:
            path = Path(p)
            if path not in self.selected_files:
                new_files.append(path)

        if new_files:
            self.selected_files.extend(new_files)
            self._refresh_list()
            logger.info(f"Добавлено файлов через диалог: {len(new_files)}")

    def _on_remove_selected_clicked(self) -> None:
        """Удалить выбранные файлы из списка."""
        selected_items = self.list_widget.selectedItems()

        if not selected_items:
            return

        # Получаем пути выбранных файлов
        paths_to_remove = []
        for item in selected_items:
            path = Path(item.text())
            paths_to_remove.append(path)

        # Удаляем из списка
        for path in paths_to_remove:
            if path in self.selected_files:
                self.selected_files.remove(path)
                logger.info(f"Удалён файл: {path.name}")

        self._refresh_list()

    def _on_clear_all_clicked(self) -> None:
        """Очистить весь список файлов."""
        if not self.selected_files:
            return

        count = len(self.selected_files)
        self.selected_files.clear()
        self._refresh_list()

        logger.info(f"Очищен список файлов: удалено {count} файлов")

    def _update_buttons_state(self) -> None:
        """Обновить состояние кнопок удаления."""
        has_files = len(self.selected_files) > 0
        has_selection = len(self.list_widget.selectedItems()) > 0

        self.button_remove.setEnabled(has_selection)
        self.button_clear.setEnabled(has_files)

    def _refresh_list(self) -> None:
        """Перерисовать список файлов и счётчик."""
        self.list_widget.clear()
        for path in self.selected_files:
            self.list_widget.addItem(str(path))

        self.label_count.setText(
            f"Загружено: {len(self.selected_files)} файлов")

        # Обновляем состояние кнопок
        self._update_buttons_state()

        # Испускаем сигнал об изменении
        self.files_changed.emit()

    def clear_files(self) -> None:
        """Очистить список файлов (вызывается извне)."""
        self.selected_files.clear()
        self._refresh_list()
