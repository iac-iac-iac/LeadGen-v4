"""
Виджет настроек приложения.

Позволяет изменять:
- Пути к директориям
- Настройки Битрикс24
- Параметры обработки
- Уровень логирования
"""

import logging
from pathlib import Path
import pandas as pd

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QGroupBox,
    QFileDialog,
    QMessageBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt

from config.settings import settings


logger = logging.getLogger(__name__)


class SettingsWidget(QWidget):
    """Виджет настроек приложения."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Храним изменения до сохранения
        self.temp_settings = {}

        self._setup_ui()
        self._load_current_settings()
        logger.info("Виджет настроек инициализирован")

    def _setup_ui(self):
        """Создать UI."""
        main_layout = QVBoxLayout()

        # Заголовок
        header = QLabel("⚙️ Настройки приложения")
        header.setStyleSheet(
            "font-size: 18px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(header)

        # Скролл-область
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Блок 1: Пути
        paths_group = self._create_paths_section()
        scroll_layout.addWidget(paths_group)

        # Блок 2: Битрикс24
        bitrix_group = self._create_bitrix_section()
        scroll_layout.addWidget(bitrix_group)

        # Блок 3: Параметры обработки
        processing_group = self._create_processing_section()
        scroll_layout.addWidget(processing_group)

        # Блок 4: Логирование
        logging_group = self._create_logging_section()
        scroll_layout.addWidget(logging_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        # Кнопки внизу
        buttons_layout = QHBoxLayout()

        self.btn_save = QPushButton("💾 Сохранить настройки")
        self.btn_save.clicked.connect(self._on_save_clicked)
        self.btn_save.setStyleSheet(
            "background-color: #4CAF50; color: white; font-weight: bold; padding: 10px;"
        )

        self.btn_reset = QPushButton("🔄 Сбросить по умолчанию")
        self.btn_reset.clicked.connect(self._on_reset_clicked)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.btn_reset)
        buttons_layout.addWidget(self.btn_save)

        main_layout.addLayout(buttons_layout)

        # Темная тема
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
            }
            QLineEdit {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 1px solid #64B5F6;
            }
            QComboBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #ffffff;
                selection-background-color: #4a4a4a;
            }
            QSpinBox {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #555;
                border-radius: 5px;
                padding: 5px;
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
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
        """)

        self.setLayout(main_layout)

    def _create_paths_section(self) -> QGroupBox:
        """Блок настройки путей."""
        group = QGroupBox("📁 Пути к директориям")
        layout = QFormLayout()

        # Input директория
        self.input_dir_edit = QLineEdit()
        btn_input_browse = QPushButton("📂")
        btn_input_browse.setMaximumWidth(40)
        btn_input_browse.clicked.connect(
            lambda: self._browse_directory(self.input_dir_edit))

        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_dir_edit)
        input_layout.addWidget(btn_input_browse)
        layout.addRow("Входные файлы:", input_layout)

        # Output директория
        self.output_dir_edit = QLineEdit()
        btn_output_browse = QPushButton("📂")
        btn_output_browse.setMaximumWidth(40)
        btn_output_browse.clicked.connect(
            lambda: self._browse_directory(self.output_dir_edit))

        output_layout = QHBoxLayout()
        output_layout.addWidget(self.output_dir_edit)
        output_layout.addWidget(btn_output_browse)
        layout.addRow("Выходные файлы:", output_layout)

        # Reports директория
        self.reports_dir_edit = QLineEdit()
        btn_reports_browse = QPushButton("📂")
        btn_reports_browse.setMaximumWidth(40)
        btn_reports_browse.clicked.connect(
            lambda: self._browse_directory(self.reports_dir_edit))

        reports_layout = QHBoxLayout()
        reports_layout.addWidget(self.reports_dir_edit)
        reports_layout.addWidget(btn_reports_browse)
        layout.addRow("Отчёты:", reports_layout)

        group.setLayout(layout)
        return group

    def _create_bitrix_section(self) -> QGroupBox:
        """Блок настроек Битрикс24."""
        group = QGroupBox("🔗 Настройки Битрикс24")
        layout = QFormLayout()

        # Стадия
        self.bitrix_stage_edit = QLineEdit()
        layout.addRow("Стадия лида:", self.bitrix_stage_edit)

        # Источник
        self.bitrix_source_edit = QLineEdit()
        layout.addRow("Источник:", self.bitrix_source_edit)

        # Тип услуги
        self.bitrix_service_edit = QLineEdit()
        layout.addRow("Тип услуги:", self.bitrix_service_edit)

        group.setLayout(layout)
        return group

    def _create_processing_section(self) -> QGroupBox:
        """Блок параметров обработки."""
        group = QGroupBox("⚙️ Параметры обработки")
        layout = QFormLayout()

        # Макс. размер файла
        self.max_file_size_spin = QSpinBox()
        self.max_file_size_spin.setRange(1, 1000)
        self.max_file_size_spin.setSuffix(" MB")
        layout.addRow("Макс. размер файла:", self.max_file_size_spin)

        # Строк для предпросмотра
        self.preview_rows_spin = QSpinBox()
        self.preview_rows_spin.setRange(5, 100)
        self.preview_rows_spin.setSuffix(" строк")
        layout.addRow("Предпросмотр:", self.preview_rows_spin)

        group.setLayout(layout)
        return group

    def _create_logging_section(self) -> QGroupBox:
        """Блок настроек логирования."""
        group = QGroupBox("📝 Логирование")
        layout = QFormLayout()

        # Уровень логирования
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout.addRow("Уровень логирования:", self.log_level_combo)

        group.setLayout(layout)
        return group

    def _browse_directory(self, line_edit: QLineEdit):
        """Выбрать директорию через диалог."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Выберите директорию",
            line_edit.text() or "",
        )

        if directory:
            line_edit.setText(directory)

    def _load_current_settings(self):
        """Загрузить текущие настройки в поля."""
        # Пути
        self.input_dir_edit.setText(str(settings.paths.input_dir))
        self.output_dir_edit.setText(str(settings.paths.output_dir))
        self.reports_dir_edit.setText(str(settings.paths.reports_dir))

        # Битрикс
        self.bitrix_stage_edit.setText(settings.bitrix_stage)
        self.bitrix_source_edit.setText(settings.bitrix_source)
        self.bitrix_service_edit.setText(settings.bitrix_service_type)

        # Обработка
        self.max_file_size_spin.setValue(settings.max_file_size_mb)
        self.preview_rows_spin.setValue(settings.preview_rows)

        # Логирование
        self.log_level_combo.setCurrentText(settings.log_level)

    def _on_save_clicked(self):
        """Сохранить настройки в .env файл."""
        try:
            # Валидация путей
            input_dir = self.input_dir_edit.text().strip()
            output_dir = self.output_dir_edit.text().strip()
            reports_dir = self.reports_dir_edit.text().strip()

            if not input_dir or not output_dir or not reports_dir:
                QMessageBox.warning(
                    self,
                    "⚠️ Ошибка валидации",
                    "Все пути должны быть заполнены!",
                )
                return

            # Валидация полей Битрикс
            bitrix_stage = self.bitrix_stage_edit.text().strip()
            bitrix_source = self.bitrix_source_edit.text().strip()
            bitrix_service = self.bitrix_service_edit.text().strip()

            if not bitrix_stage or not bitrix_source or not bitrix_service:
                QMessageBox.warning(
                    self,
                    "⚠️ Ошибка валидации",
                    "Все поля Битрикс24 должны быть заполнены!",
                )
                return

            # Создаём содержимое .env
            env_content = f"""# Настройки Lead Generation System
# Сгенерировано автоматически: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

# ========== ПУТИ К ДИРЕКТОРИЯМ ==========
PATHS__INPUT_DIR={input_dir}
PATHS__OUTPUT_DIR={output_dir}
PATHS__REPORTS_DIR={reports_dir}
PATHS__DB_PATH=data/database.db

# ========== НАСТРОЙКИ БИТРИКС24 ==========
BITRIX_STAGE={bitrix_stage}
BITRIX_SOURCE={bitrix_source}
BITRIX_SERVICE_TYPE={bitrix_service}

# ========== ПАРАМЕТРЫ ОБРАБОТКИ ==========
MAX_FILE_SIZE_MB={self.max_file_size_spin.value()}
PREVIEW_ROWS={self.preview_rows_spin.value()}

# ========== ЛОГИРОВАНИЕ ==========
LOG_LEVEL={self.log_level_combo.currentText()}
"""

            # Сохраняем в .env
            env_path = Path(".env")
            env_path.write_text(env_content, encoding="utf-8")

            QMessageBox.information(
                self,
                "✅ Настройки сохранены",
                f"Настройки успешно сохранены в файл:\n{env_path.absolute()}\n\n"
                "⚠️ ВАЖНО: Перезапустите приложение,\n"
                "чтобы изменения вступили в силу!",
            )

            logger.info(f"Настройки сохранены в {env_path}")

        except Exception as exc:
            logger.exception("Ошибка сохранения настроек")
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                f"Не удалось сохранить настройки:\n{exc}",
            )

    def _on_reset_clicked(self):
        """Сбросить настройки по умолчанию."""
        reply = QMessageBox.question(
            self,
            "⚠️ Подтверждение",
            "Вы уверены, что хотите сбросить все настройки\n"
            "до значений по умолчанию?\n\n"
            "Текущие настройки будут потеряны!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Загружаем дефолтные значения
            self.input_dir_edit.setText("data/input")
            self.output_dir_edit.setText("data/output")
            self.reports_dir_edit.setText("data/reports")

            self.bitrix_stage_edit.setText("Новая заявка")
            self.bitrix_source_edit.setText("Холодный звонок")
            self.bitrix_service_edit.setText("ГЦК")

            self.max_file_size_spin.setValue(100)
            self.preview_rows_spin.setValue(10)

            self.log_level_combo.setCurrentText("INFO")

            logger.info("Настройки сброшены до значений по умолчанию")

            QMessageBox.information(
                self,
                "✅ Сброшено",
                "Настройки сброшены до значений по умолчанию.\n\n"
                "Нажмите 'Сохранить', чтобы применить изменения.",
            )
