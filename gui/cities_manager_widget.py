import logging
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLineEdit,
    QPushButton,
    QLabel,
    QMessageBox,
    QGroupBox,
    QTextEdit,
    QAbstractItemView,
    QInputDialog,
)

from services.yandex_maps_url_generator import YandexMapsURLGenerator

logger = logging.getLogger(__name__)


class CitiesManagerWidget(QWidget):
    """
    Виджет для управления городами и районами
    """

    # Сигнал для оповещения об изменениях
    cities_updated = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.generator = YandexMapsURLGenerator()

        self._setup_ui()
        self._connect_signals()
        self._load_cities()

        logger.info("CitiesManagerWidget инициализирован")

    def _setup_ui(self) -> None:
        """Построить UI виджета."""
        main_layout = QVBoxLayout(self)

        # ============================================================
        # БЛОК 1: Управление городами
        # ============================================================
        group_cities = QGroupBox("🌆 Управление городами")
        layout_cities = QVBoxLayout()

        # Список городов
        self.cities_list = QListWidget()
        self.cities_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )
        layout_cities.addWidget(QLabel("Список городов:"))
        layout_cities.addWidget(self.cities_list)

        # Кнопки управления городами
        cities_buttons_layout = QHBoxLayout()

        self.btn_add_city = QPushButton("➕ Добавить город")
        self.btn_remove_city = QPushButton("➖ Удалить город")
        self.btn_edit_districts = QPushButton("📍 Настроить районы")

        cities_buttons_layout.addWidget(self.btn_add_city)
        cities_buttons_layout.addWidget(self.btn_remove_city)
        cities_buttons_layout.addWidget(self.btn_edit_districts)

        layout_cities.addLayout(cities_buttons_layout)

        # Информация о выбранном городе
        self.city_info_label = QLabel(
            "ℹ️ Выберите город для просмотра информации")
        self.city_info_label.setWordWrap(True)
        self.city_info_label.setStyleSheet(
            "color: #666; padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout_cities.addWidget(self.city_info_label)

        group_cities.setLayout(layout_cities)

        # ============================================================
        # БЛОК 2: Управление районами выбранного города
        # ============================================================
        group_districts = QGroupBox("📍 Районы выбранного города")
        layout_districts = QVBoxLayout()

        self.districts_label = QLabel("Выберите город для управления районами")
        layout_districts.addWidget(self.districts_label)

        # Список районов
        self.districts_list = QListWidget()
        self.districts_list.setMaximumHeight(200)
        layout_districts.addWidget(self.districts_list)

        # Кнопки управления районами
        districts_buttons_layout = QHBoxLayout()

        self.btn_add_district = QPushButton("➕ Добавить район")
        self.btn_add_district.setEnabled(False)

        self.btn_remove_district = QPushButton("➖ Удалить район")
        self.btn_remove_district.setEnabled(False)

        districts_buttons_layout.addWidget(self.btn_add_district)
        districts_buttons_layout.addWidget(self.btn_remove_district)
        districts_buttons_layout.addStretch()

        layout_districts.addLayout(districts_buttons_layout)

        group_districts.setLayout(layout_districts)

        # ============================================================
        # БЛОК 3: Действия
        # ============================================================
        group_actions = QGroupBox("⚙️ Действия")
        layout_actions = QHBoxLayout()

        self.btn_reset_defaults = QPushButton("🔄 Сбросить к умолчаниям")
        self.btn_reset_defaults.setStyleSheet(
            "background-color: #ff9800; color: white; padding: 8px;"
        )

        self.btn_save_close = QPushButton("✅ Сохранить и закрыть")
        self.btn_save_close.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;"
        )

        layout_actions.addWidget(self.btn_reset_defaults)
        layout_actions.addStretch()
        layout_actions.addWidget(self.btn_save_close)

        group_actions.setLayout(layout_actions)

        # ============================================================
        # Добавляем все блоки в главный layout
        # ============================================================
        main_layout.addWidget(group_cities)
        main_layout.addWidget(group_districts)
        main_layout.addWidget(group_actions)

    def _connect_signals(self) -> None:
        """Подключить сигналы."""
        self.btn_add_city.clicked.connect(self._on_add_city)
        self.btn_remove_city.clicked.connect(self._on_remove_city)
        self.btn_edit_districts.clicked.connect(self._on_edit_districts)

        self.btn_add_district.clicked.connect(self._on_add_district)
        self.btn_remove_district.clicked.connect(self._on_remove_district)

        self.btn_reset_defaults.clicked.connect(self._on_reset_defaults)
        self.btn_save_close.clicked.connect(self._on_save_close)

        self.cities_list.itemSelectionChanged.connect(self._on_city_selected)

    def _load_cities(self) -> None:
        """Загрузить список городов."""
        self.cities_list.clear()
        cities = self.generator.get_popular_cities()
        self.cities_list.addItems(cities)

        logger.info(f"Загружено {len(cities)} городов")

    def _on_city_selected(self) -> None:
        """Обработать выбор города."""
        selected_items = self.cities_list.selectedItems()
        if not selected_items:
            self.city_info_label.setText(
                "ℹ️ Выберите город для просмотра информации")
            self.districts_label.setText(
                "Выберите город для управления районами")
            self.districts_list.clear()
            self.btn_add_district.setEnabled(False)
            self.btn_remove_district.setEnabled(False)
            return

        city = selected_items[0].text()

        # Обновляем информацию о городе
        is_megapolis = self.generator.is_megapolis(city)
        districts = self.generator.get_districts(city)

        if is_megapolis:
            self.city_info_label.setText(
                f"🏙️ <b>{city}</b> — мегаполис с районами\n"
                f"Количество районов: {len(districts)}"
            )
        else:
            self.city_info_label.setText(
                f"🌆 <b>{city}</b> — обычный город (без районов)"
            )

        # Обновляем список районов
        self.districts_label.setText(f"Районы города {city}:")
        self.districts_list.clear()
        if districts:
            self.districts_list.addItems(districts)

        # Включаем кнопки управления районами
        self.btn_add_district.setEnabled(True)
        self.btn_remove_district.setEnabled(True)

    def _on_add_city(self) -> None:
        """Добавить новый город."""
        city, ok = QInputDialog.getText(
            self,
            "Добавить город",
            "Введите название города:",
            QLineEdit.EchoMode.Normal,
            ""
        )

        if ok and city:
            city = city.strip()

            # Проверяем, не существует ли уже такой город
            if city in self.generator.get_popular_cities():
                QMessageBox.warning(
                    self,
                    "❌ Ошибка",
                    f"Город '{city}' уже есть в списке."
                )
                return

            try:
                self.generator.add_city(city)
                self._load_cities()

                QMessageBox.information(
                    self,
                    "✅ Успех",
                    f"Город '{city}' успешно добавлен!"
                )

                self.cities_updated.emit()
                logger.info(f"Добавлен город: {city}")

            except Exception as exc:
                logger.exception("Ошибка при добавлении города")
                QMessageBox.critical(
                    self,
                    "❌ Ошибка",
                    f"Не удалось добавить город:\n{exc}"
                )

    def _on_remove_city(self) -> None:
        """Удалить выбранный город."""
        selected_items = self.cities_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "❌ Ошибка",
                "Выберите город для удаления."
            )
            return

        city = selected_items[0].text()

        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "❓ Подтверждение",
            f"Вы уверены, что хотите удалить город '{city}'?\n\n"
            f"Это также удалит все его районы (если есть).",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.generator.remove_city(city)
                self._load_cities()

                QMessageBox.information(
                    self,
                    "✅ Успех",
                    f"Город '{city}' успешно удалён!"
                )

                self.cities_updated.emit()
                logger.info(f"Удалён город: {city}")

            except Exception as exc:
                logger.exception("Ошибка при удалении города")
                QMessageBox.critical(
                    self,
                    "❌ Ошибка",
                    f"Не удалось удалить город:\n{exc}"
                )

    def _on_edit_districts(self) -> None:
        """Открыть диалог редактирования районов."""
        selected_items = self.cities_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(
                self,
                "❌ Ошибка",
                "Выберите город для настройки районов."
            )
            return

        city = selected_items[0].text()

        # Открываем диалог редактирования
        dialog = DistrictsEditorDialog(self.generator, city, self)
        if dialog.exec():
            # Обновляем отображение
            self._on_city_selected()
            self.cities_updated.emit()

    def _on_add_district(self) -> None:
        """Добавить район к выбранному городу."""
        selected_items = self.cities_list.selectedItems()
        if not selected_items:
            return

        city = selected_items[0].text()

        district, ok = QInputDialog.getText(
            self,
            "Добавить район",
            f"Введите название района для города {city}:",
            QLineEdit.EchoMode.Normal,
            ""
        )

        if ok and district:
            district = district.strip()

            # Проверяем, не существует ли уже такой район
            if district in self.generator.get_districts(city):
                QMessageBox.warning(
                    self,
                    "❌ Ошибка",
                    f"Район '{district}' уже есть в списке."
                )
                return

            try:
                self.generator.add_district(city, district)
                self._on_city_selected()  # Обновляем отображение

                QMessageBox.information(
                    self,
                    "✅ Успех",
                    f"Район '{district}' добавлен к городу '{city}'!"
                )

                self.cities_updated.emit()
                logger.info(f"Добавлен район {district} к городу {city}")

            except Exception as exc:
                logger.exception("Ошибка при добавлении района")
                QMessageBox.critical(
                    self,
                    "❌ Ошибка",
                    f"Не удалось добавить район:\n{exc}"
                )

    def _on_remove_district(self) -> None:
        """Удалить выбранный район."""
        selected_city_items = self.cities_list.selectedItems()
        selected_district_items = self.districts_list.selectedItems()

        if not selected_city_items or not selected_district_items:
            QMessageBox.warning(
                self,
                "❌ Ошибка",
                "Выберите район для удаления."
            )
            return

        city = selected_city_items[0].text()
        district = selected_district_items[0].text()

        # Подтверждение удаления
        reply = QMessageBox.question(
            self,
            "❓ Подтверждение",
            f"Удалить район '{district}' из города '{city}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.generator.remove_district(city, district)
                self._on_city_selected()  # Обновляем отображение

                QMessageBox.information(
                    self,
                    "✅ Успех",
                    f"Район '{district}' удалён!"
                )

                self.cities_updated.emit()
                logger.info(f"Удалён район {district} из города {city}")

            except Exception as exc:
                logger.exception("Ошибка при удалении района")
                QMessageBox.critical(
                    self,
                    "❌ Ошибка",
                    f"Не удалось удалить район:\n{exc}"
                )

    def _on_reset_defaults(self) -> None:
        """Сбросить настройки к значениям по умолчанию."""
        reply = QMessageBox.question(
            self,
            "❓ Подтверждение",
            "Вы уверены, что хотите сбросить все настройки городов к значениям по умолчанию?\n\n"
            "Все ваши изменения будут потеряны!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.generator.reset_to_defaults()
                self._load_cities()
                self._on_city_selected()

                QMessageBox.information(
                    self,
                    "✅ Успех",
                    "Настройки городов сброшены к значениям по умолчанию!"
                )

                self.cities_updated.emit()
                logger.info("Настройки городов сброшены к умолчаниям")

            except Exception as exc:
                logger.exception("Ошибка при сбросе настроек")
                QMessageBox.critical(
                    self,
                    "❌ Ошибка",
                    f"Не удалось сбросить настройки:\n{exc}"
                )

    def _on_save_close(self) -> None:
        """Сохранить и закрыть."""
        QMessageBox.information(
            self,
            "✅ Сохранено",
            "Все изменения автоматически сохранены!"
        )
        self.close()


class DistrictsEditorDialog(QMessageBox):
    """Диалог для массового редактирования районов."""

    def __init__(self, generator: YandexMapsURLGenerator, city: str, parent=None):
        super().__init__(parent)

        self.generator = generator
        self.city = city

        self.setWindowTitle(f"Редактирование районов: {city}")
        self.setText(f"Редактирование районов для города <b>{city}</b>")
        self.setInformativeText(
            "Введите районы (один на строку).\n"
            "Оставьте пустым, если у города нет районов."
        )

        # Текстовое поле для районов
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QPushButton

        # Преобразуем в кастомный диалог
        self.dialog = QDialog(parent)
        self.dialog.setWindowTitle(f"Редактирование районов: {city}")
        self.dialog.setMinimumSize(500, 400)

        layout = QVBoxLayout()

        layout.addWidget(
            QLabel(f"<b>Редактирование районов для города: {city}</b>"))
        layout.addWidget(QLabel("Введите районы (один на строку):"))

        self.districts_edit = QTextEdit()
        current_districts = self.generator.get_districts(city)
        self.districts_edit.setText("\n".join(current_districts))
        layout.addWidget(self.districts_edit)

        # Кнопки
        buttons_layout = QHBoxLayout()
        btn_save = QPushButton("✅ Сохранить")
        btn_cancel = QPushButton("❌ Отмена")

        btn_save.clicked.connect(self.dialog.accept)
        btn_cancel.clicked.connect(self.dialog.reject)

        buttons_layout.addWidget(btn_save)
        buttons_layout.addWidget(btn_cancel)

        layout.addLayout(buttons_layout)
        self.dialog.setLayout(layout)

    def exec(self):
        """Показать диалог и сохранить результат."""
        result = self.dialog.exec()

        if result:
            # Сохраняем районы
            text = self.districts_edit.toPlainText()
            districts = [d.strip() for d in text.split('\n') if d.strip()]

            try:
                self.generator.set_city_districts(self.city, districts)
                logger.info(
                    f"Обновлены районы для города {self.city}: {len(districts)} районов")
                return True
            except Exception as exc:
                logger.exception("Ошибка при сохранении районов")
                QMessageBox.critical(
                    self.dialog,
                    "❌ Ошибка",
                    f"Не удалось сохранить районы:\n{exc}"
                )
                return False

        return False
