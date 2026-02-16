"""
Логика выбора файлов через QFileDialog и хранение списка выбранных файлов.
"""

from pathlib import Path
from typing import List

from PyQt6.QtWidgets import QWidget, QFileDialog, QListWidget, QVBoxLayout, QPushButton, QLabel


class FileLoaderWidget(QWidget):
    """
    Виджет для выбора и отображения списка входных файлов.

    Состоит из:
    - кнопки "Выбрать файлы"
    - списка выбранных файлов
    - подписи с количеством файлов
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.selected_files: List[Path] = []

        self.button_select = QPushButton("Выбрать файлы")
        self.list_widget = QListWidget()
        self.label_count = QLabel("Загружено: 0 файлов")

        layout = QVBoxLayout()
        layout.addWidget(self.button_select)
        layout.addWidget(self.list_widget)
        layout.addWidget(self.label_count)
        self.setLayout(layout)

        self.button_select.clicked.connect(self._on_select_files_clicked)

    def _on_select_files_clicked(self) -> None:
        """
        Обработчик клика по кнопке выбора файлов.

        Использует QFileDialog.getOpenFileNames и обновляет список.
        """
        # Фильтр: TSV и CSV — основной формат для Webbee AI
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите файлы Webbee AI",
            "",
            "Data Files (*.tsv *.csv);;All Files (*)",
        )
        if not file_paths:
            return

        # Конвертируем строки в Path
        self.selected_files = [Path(p) for p in file_paths]
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Перерисовать список файлов и счётчик."""
        self.list_widget.clear()
        for path in self.selected_files:
            self.list_widget.addItem(str(path))
        self.label_count.setText(
            f"Загружено: {len(self.selected_files)} файлов")
