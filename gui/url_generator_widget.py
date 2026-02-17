import logging
from pathlib import Path
from typing import List, Optional

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLineEdit,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QMessageBox,
    QFileDialog,
    QGroupBox,
    QTextEdit,
    QAbstractItemView,
    QHeaderView,
)

from services.yandex_maps_url_generator import YandexMapsURLGenerator
from config.settings import settings

logger = logging.getLogger(__name__)


class URLGeneratorWidget(QWidget):
    """
    Виджет для генерации ссылок Яндекс.Карт.

    Функционал:
    - Выбор сегмента бизнеса
    - Выбор городов (множественный выбор)
    - Опция использования районов для мегаполисов
    - Генерация и предпросмотр ссылок
    - Экспорт в CSV для Webbee AI
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.generator = YandexMapsURLGenerator()
        self.generated_urls: List[dict] = []

        self._setup_ui()
        self._connect_signals()

        logger.info("URLGeneratorWidget инициализирован")

    def refresh_cities(self) -> None:
        """Обновить список городов (вызывается при изменении настроек)."""
        # Сохраняем текущий выбор
        selected_cities = [item.text()
                           for item in self.cities_list.selectedItems()]

        # Очищаем и заново загружаем
        self.cities_list.clear()

        # Перезагружаем генератор (чтобы подхватить изменения из файла)
        self.generator = YandexMapsURLGenerator()

        # Заполняем список
        for city in self.generator.get_popular_cities():
            self.cities_list.addItem(city)

        # Восстанавливаем выбор
        for i in range(self.cities_list.count()):
            item = self.cities_list.item(i)
            if item.text() in selected_cities:
                item.setSelected(True)

        logger.info("Список городов обновлён")

    def _setup_ui(self) -> None:
        """Построить UI виджета."""
        main_layout = QVBoxLayout(self)

        # ============================================================
        # БЛОК 1: Сегмент бизнеса
        # ============================================================
        group_segment = QGroupBox("🎯 1. Сегмент бизнеса")
        layout_segment = QVBoxLayout()

        self.segment_input = QLineEdit()
        self.segment_input.setPlaceholderText(
            "Например: Мебель на заказ, Ремонт квартир, Доставка еды..."
        )
        layout_segment.addWidget(QLabel("Введите сегмент для поиска:"))
        layout_segment.addWidget(self.segment_input)

        # Примеры популярных сегментов
        examples_label = QLabel(
            "💡 <i>Популярные примеры: Мебель на заказ, Натяжные потолки, "
            "Кафе, Автосервис, Фитнес-клуб, Стоматология</i>"
        )
        examples_label.setWordWrap(True)
        examples_label.setStyleSheet("color: #666; font-size: 11px;")
        layout_segment.addWidget(examples_label)

        group_segment.setLayout(layout_segment)

        # ============================================================
        # БЛОК 2: Выбор городов
        # ============================================================
        group_cities = QGroupBox("🌆 2. Выбор городов")
        layout_cities = QVBoxLayout()

        # Кнопки быстрого выбора
        buttons_layout = QHBoxLayout()
        self.btn_select_all = QPushButton("✅ Выбрать все")
        self.btn_deselect_all = QPushButton("❌ Снять все")
        self.btn_select_megapolis = QPushButton("🏙️ Только мегаполисы")

        buttons_layout.addWidget(self.btn_select_all)
        buttons_layout.addWidget(self.btn_deselect_all)
        buttons_layout.addWidget(self.btn_select_megapolis)
        buttons_layout.addStretch()

        layout_cities.addLayout(buttons_layout)

        # Список городов
        self.cities_list = QListWidget()
        self.cities_list.setSelectionMode(
            QAbstractItemView.SelectionMode.MultiSelection
        )

        # Заполняем города
        for city in self.generator.get_popular_cities():
            self.cities_list.addItem(city)

        layout_cities.addWidget(
            QLabel("Выберите города (Ctrl/Shift для множественного выбора):"))
        layout_cities.addWidget(self.cities_list)

        group_cities.setLayout(layout_cities)

        # ============================================================
        # БЛОК 3: Настройки районов
        # ============================================================
        group_districts = QGroupBox("📍 3. Настройки районирования")
        layout_districts = QVBoxLayout()

        self.use_districts_cb = QCheckBox(
            "Использовать районы для мегаполисов "
            "(Москва, СПб, Екатеринбург, Новосибирск)"
        )
        self.use_districts_cb.setChecked(True)

        districts_info = QLabel(
            "💡 <i>При включении этой опции для мегаполисов будут сгенерированы "
            "отдельные ссылки для каждого района (например, ЦАО, САО для Москвы). "
            "Это позволит получить более полные данные от Webbee AI.</i>"
        )
        districts_info.setWordWrap(True)
        districts_info.setStyleSheet("color: #666; font-size: 11px;")

        layout_districts.addWidget(self.use_districts_cb)
        layout_districts.addWidget(districts_info)

        group_districts.setLayout(layout_districts)

        # ============================================================
        # БЛОК 4: Генерация
        # ============================================================
        group_generate = QGroupBox("⚙️ 4. Генерация ссылок")
        layout_generate = QVBoxLayout()

        self.btn_generate = QPushButton("🚀 Сгенерировать ссылки")
        self.btn_generate.setMinimumHeight(50)
        self.btn_generate.setStyleSheet(
            """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
            """
        )

        self.status_label = QLabel("✅ Готово к генерации")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout_generate.addWidget(self.btn_generate)
        layout_generate.addWidget(self.status_label)

        group_generate.setLayout(layout_generate)

        # ============================================================
        # БЛОК 5: Результаты
        # ============================================================
        group_results = QGroupBox("📋 5. Сгенерированные ссылки")
        layout_results = QVBoxLayout()

        # Таблица результатов
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels([
            "Город", "Район", "Сегмент", "URL"
        ])

        # Настройка таблицы
        header = self.results_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.results_table.setAlternatingRowColors(True)
        self.results_table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )

        layout_results.addWidget(self.results_table)

        # Статистика
        self.stats_label = QLabel("Статистика: ожидание генерации...")
        self.stats_label.setStyleSheet("font-weight: bold; color: #333;")
        layout_results.addWidget(self.stats_label)

        group_results.setLayout(layout_results)

        # ============================================================
        # БЛОК 6: Экспорт
        # ============================================================
        group_export = QGroupBox("💾 6. Экспорт результатов")
        layout_export = QHBoxLayout()

        self.btn_export_csv = QPushButton("📄 Экспортировать в CSV")
        self.btn_export_csv.setEnabled(False)

        self.btn_copy_urls = QPushButton("📋 Копировать все URL")
        self.btn_copy_urls.setEnabled(False)

        layout_export.addWidget(self.btn_export_csv)
        layout_export.addWidget(self.btn_copy_urls)
        layout_export.addStretch()

        group_export.setLayout(layout_export)

        # ============================================================
        # Добавляем все блоки в главный layout
        # ============================================================
        main_layout.addWidget(group_segment)
        main_layout.addWidget(group_cities)
        main_layout.addWidget(group_districts)
        main_layout.addWidget(group_generate)
        main_layout.addWidget(group_results, stretch=1)
        main_layout.addWidget(group_export)

    def _connect_signals(self) -> None:
        """Подключить сигналы."""
        self.btn_generate.clicked.connect(self._on_generate_clicked)
        self.btn_export_csv.clicked.connect(self._on_export_csv_clicked)
        self.btn_copy_urls.clicked.connect(self._on_copy_urls_clicked)

        self.btn_select_all.clicked.connect(self._select_all_cities)
        self.btn_deselect_all.clicked.connect(self._deselect_all_cities)
        self.btn_select_megapolis.clicked.connect(self._select_megapolis_only)

        # Обновление состояния кнопки при изменении полей
        self.segment_input.textChanged.connect(self._update_generate_button)
        self.cities_list.itemSelectionChanged.connect(
            self._update_generate_button)

    def _update_generate_button(self) -> None:
        """Обновить состояние кнопки генерации."""
        has_segment = bool(self.segment_input.text().strip())
        has_cities = len(self.cities_list.selectedItems()) > 0

        self.btn_generate.setEnabled(has_segment and has_cities)

    def _select_all_cities(self) -> None:
        """Выбрать все города."""
        for i in range(self.cities_list.count()):
            self.cities_list.item(i).setSelected(True)

    def _deselect_all_cities(self) -> None:
        """Снять выбор со всех городов."""
        self.cities_list.clearSelection()

    def _select_megapolis_only(self) -> None:
        """Выбрать только мегаполисы с районами."""
        self.cities_list.clearSelection()
        megapolis_cities = ["Москва", "Санкт-Петербург",
                            "Екатеринбург", "Новосибирск"]

        for i in range(self.cities_list.count()):
            item = self.cities_list.item(i)
            if item.text() in megapolis_cities:
                item.setSelected(True)

    def _on_generate_clicked(self) -> None:
        """Сгенерировать ссылки."""
        segment = self.segment_input.text().strip()
        if not segment:
            QMessageBox.warning(
                self,
                "❌ Ошибка",
                "Введите сегмент бизнеса для поиска."
            )
            return

        selected_cities = [
            item.text() for item in self.cities_list.selectedItems()
        ]
        if not selected_cities:
            QMessageBox.warning(
                self,
                "❌ Ошибка",
                "Выберите хотя бы один город."
            )
            return

        try:
            self.status_label.setText("⏳ Генерация ссылок...")
            self.btn_generate.setEnabled(False)

            use_districts = self.use_districts_cb.isChecked()

            # Генерируем ссылки
            self.generated_urls = self.generator.generate_urls_batch(
                cities=selected_cities,
                segment=segment,
                use_districts=use_districts
            )

            # Заполняем таблицу
            self._populate_results_table()

            # Обновляем статистику
            total_urls = len(self.generated_urls)
            cities_count = len(selected_cities)
            with_districts = sum(
                1 for url in self.generated_urls if url.get('district'))

            self.stats_label.setText(
                f"📊 Статистика: Всего {total_urls} ссылок | "
                f"Городов: {cities_count} | "
                f"С районами: {with_districts}"
            )

            self.status_label.setText(f"✅ Сгенерировано {total_urls} ссылок")

            # Включаем кнопки экспорта
            self.btn_export_csv.setEnabled(True)
            self.btn_copy_urls.setEnabled(True)

            logger.info(
                f"Сгенерировано {total_urls} ссылок для сегмента '{segment}' "
                f"в {cities_count} городах"
            )

            QMessageBox.information(
                self,
                "✅ Успех",
                f"Успешно сгенерировано {total_urls} ссылок!\n\n"
                f"Готово к экспорту в CSV для Webbee AI."
            )

        except Exception as exc:
            logger.exception("Ошибка при генерации ссылок")
            QMessageBox.critical(
                self,
                "❌ Критическая ошибка",
                f"Не удалось сгенерировать ссылки:\n{exc}"
            )
            self.status_label.setText("❌ Ошибка генерации")

        finally:
            self.btn_generate.setEnabled(True)

    def _populate_results_table(self) -> None:
        """Заполнить таблицу результатами."""
        self.results_table.setRowCount(len(self.generated_urls))

        for i, result in enumerate(self.generated_urls):
            # Город
            city_item = QTableWidgetItem(result['city'])
            self.results_table.setItem(i, 0, city_item)

            # Район
            district = result.get('district', '') or ''
            district_item = QTableWidgetItem(district)
            district_item.setForeground(Qt.GlobalColor.darkGray)
            self.results_table.setItem(i, 1, district_item)

            # Сегмент
            segment_item = QTableWidgetItem(result['segment'])
            self.results_table.setItem(i, 2, segment_item)

            # URL
            url_item = QTableWidgetItem(result['url'])
            url_item.setToolTip(result['url'])  # Подсказка при наведении
            self.results_table.setItem(i, 3, url_item)

    def _on_export_csv_clicked(self) -> None:
        """Экспортировать результаты в CSV."""
        if not self.generated_urls:
            QMessageBox.warning(
                self,
                "❌ Ошибка",
                "Нет данных для экспорта. Сначала сгенерируйте ссылки."
            )
            return

        # Предлагаем имя файла
        from datetime import datetime
        segment_name = self.segment_input.text().strip()[
            :30]  # Ограничиваем длину
        default_name = f"yandex_maps_{segment_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        default_path = str(settings.paths.output_dir / default_name)

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV со ссылками",
            default_path,
            "CSV Files (*.csv);;All Files (*)",
        )

        if not file_path:
            return

        try:
            # Создаём DataFrame
            df = pd.DataFrame(self.generated_urls)

            # Экспортируем в CSV
            df.to_csv(
                file_path,
                index=False,
                encoding='utf-8-sig',  # BOM для корректного отображения в Excel
                sep=';',  # Точка с запятой для совместимости
            )

            QMessageBox.information(
                self,
                "✅ Экспорт завершён",
                f"✅ Файл успешно сохранён:\n{file_path}\n\n"
                f"📊 Экспортировано: {len(self.generated_urls)} ссылок\n"
                f"💡 Готово для загрузки в Webbee AI!"
            )

            logger.info(
                f"Экспортировано {len(self.generated_urls)} ссылок в {file_path}")

        except Exception as exc:
            logger.exception("Ошибка при экспорте CSV")
            QMessageBox.critical(
                self,
                "❌ Критическая ошибка",
                f"Не удалось экспортировать файл:\n{exc}"
            )

    def _on_copy_urls_clicked(self) -> None:
        """Скопировать все URL в буфер обмена."""
        if not self.generated_urls:
            QMessageBox.warning(
                self,
                "❌ Ошибка",
                "Нет ссылок для копирования."
            )
            return

        try:
            from PyQt6.QtWidgets import QApplication

            # Собираем все URL в текст (каждый с новой строки)
            urls_text = "\n".join(result['url']
                                  for result in self.generated_urls)

            # Копируем в буфер обмена
            clipboard = QApplication.clipboard()
            clipboard.setText(urls_text)

            QMessageBox.information(
                self,
                "✅ Скопировано",
                f"✅ {len(self.generated_urls)} ссылок скопированы в буфер обмена!\n\n"
                f"Вы можете вставить их в любой документ (Ctrl+V)."
            )

            logger.info(
                f"Скопировано {len(self.generated_urls)} ссылок в буфер обмена")

        except Exception as exc:
            logger.exception("Ошибка при копировании в буфер обмена")
            QMessageBox.critical(
                self,
                "❌ Ошибка",
                f"Не удалось скопировать:\n{exc}"
            )

    def refresh_cities(self) -> None:
        """
        Обновить список городов (вызывается при изменении настроек).
        """
        try:
            # Сохраняем текущий выбор
            selected_cities = [item.text()
                               for item in self.cities_list.selectedItems()]

            # Очищаем список
            self.cities_list.clear()

            # Перезагружаем генератор (подхватываем изменения из файла)
            self.generator = YandexMapsURLGenerator()

            # Заполняем список заново
            for city in self.generator.get_popular_cities():
                self.cities_list.addItem(city)

            # Восстанавливаем выбор
            for i in range(self.cities_list.count()):
                item = self.cities_list.item(i)
                if item.text() in selected_cities:
                    item.setSelected(True)

            logger.info("Список городов обновлён после изменения настроек")

            # Показываем уведомление
            QMessageBox.information(
                self,
                "✅ Города обновлены",
                f"Список городов успешно обновлён!\n\n"
                f"Теперь доступно: {self.cities_list.count()} городов"
            )

        except Exception as exc:
            logger.exception("Ошибка при обновлении списка городов")
            QMessageBox.warning(
                self,
                "⚠️ Предупреждение",
                f"Не удалось полностью обновить список городов:\n{exc}"
            )
