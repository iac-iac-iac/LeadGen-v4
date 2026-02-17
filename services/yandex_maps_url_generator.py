import urllib.parse
from typing import List, Dict, Optional
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class YandexMapsURLGenerator:
    """
    Генератор URL для Яндекс.Карт для последующего парсинга через Webbee AI
    """

    BASE_URL = "https://yandex.ru/maps?text="

    # Районы мегаполисов (по умолчанию)
    DEFAULT_DISTRICTS = {
        "Москва": [
            "ЦАО", "САО", "СВАО", "ВАО", "ЮВАО", "ЮАО", "ЮЗАО", "ЗАО",
            "СЗАО", "Зеленоград", "Троицкий АО", "Новомосковский АО"
        ],
        "Санкт-Петербург": [
            "Адмиралтейский", "Василеостровский", "Выборгский", "Калининский",
            "Кировский", "Колпинский", "Красногвардейский", "Красносельский",
            "Кронштадтский", "Курортный", "Московский", "Невский",
            "Петроградский", "Петродворцовый", "Приморский", "Пушкинский",
            "Фрунзенский", "Центральный"
        ],
        "Екатеринбург": [
            "Верх-Исетский", "Железнодорожный", "Кировский", "Ленинский",
            "Октябрьский", "Орджоникидзевский", "Чкаловский"
        ],
        "Новосибирск": [
            "Дзержинский", "Железнодорожный", "Заельцовский", "Калининский",
            "Кировский", "Ленинский", "Октябрьский", "Первомайский",
            "Советский", "Центральный"
        ]
    }

    # Популярные города (по умолчанию)
    DEFAULT_POPULAR_CITIES = [
        "Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург",
        "Казань", "Нижний Новгород", "Челябинск", "Самара", "Омск",
        "Ростов-на-Дону", "Уфа", "Красноярск", "Воронеж", "Пермь",
        "Волгоград", "Краснодар", "Саратов", "Тюмень", "Тольятти"
    ]

    def __init__(self, config_path: Optional[Path] = None):
        """
        Инициализация генератора

        Args:
            config_path: Путь к файлу конфигурации городов
        """
        self.config_path = config_path or Path("data/cities_config.json")
        self.districts = self.DEFAULT_DISTRICTS.copy()
        self.popular_cities = self.DEFAULT_POPULAR_CITIES.copy()

        # Загружаем пользовательскую конфигурацию
        self._load_config()

    def _load_config(self) -> None:
        """Загрузить конфигурацию городов из файла"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)

                self.popular_cities = config.get(
                    'popular_cities', self.DEFAULT_POPULAR_CITIES)
                self.districts = config.get(
                    'districts', self.DEFAULT_DISTRICTS)

                logger.info(
                    f"Загружена конфигурация городов из {self.config_path}")
            except Exception as exc:
                logger.warning(
                    f"Не удалось загрузить конфигурацию городов: {exc}")

    def _save_config(self) -> None:
        """Сохранить конфигурацию городов в файл"""
        try:
            # Создаём директорию если не существует
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            config = {
                'popular_cities': self.popular_cities,
                'districts': self.districts
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            logger.info(f"Конфигурация городов сохранена в {self.config_path}")
        except Exception as exc:
            logger.error(f"Не удалось сохранить конфигурацию городов: {exc}")
            raise

    def get_popular_cities(self) -> List[str]:
        """Получить список популярных городов"""
        return self.popular_cities.copy()

    def add_city(self, city: str) -> None:
        """
        Добавить город в список

        Args:
            city: Название города
        """
        if city and city not in self.popular_cities:
            self.popular_cities.append(city)
            self.popular_cities.sort()  # Сортируем по алфавиту
            self._save_config()
            logger.info(f"Добавлен город: {city}")

    def remove_city(self, city: str) -> None:
        """
        Удалить город из списка

        Args:
            city: Название города
        """
        if city in self.popular_cities:
            self.popular_cities.remove(city)
            # Также удаляем районы если есть
            if city in self.districts:
                del self.districts[city]
            self._save_config()
            logger.info(f"Удалён город: {city}")

    def is_megapolis(self, city: str) -> bool:
        """Проверить, является ли город мегаполисом с районами"""
        return city in self.districts

    def get_districts(self, city: str) -> List[str]:
        """Получить список районов для города"""
        return self.districts.get(city, []).copy()

    def add_district(self, city: str, district: str) -> None:
        """
        Добавить район к городу

        Args:
            city: Название города
            district: Название района
        """
        if city not in self.districts:
            self.districts[city] = []

        if district and district not in self.districts[city]:
            self.districts[city].append(district)
            self.districts[city].sort()
            self._save_config()
            logger.info(f"Добавлен район {district} к городу {city}")

    def remove_district(self, city: str, district: str) -> None:
        """
        Удалить район из города

        Args:
            city: Название города
            district: Название района
        """
        if city in self.districts and district in self.districts[city]:
            self.districts[city].remove(district)
            # Если районов не осталось, удаляем город из мегаполисов
            if not self.districts[city]:
                del self.districts[city]
            self._save_config()
            logger.info(f"Удалён район {district} из города {city}")

    def set_city_districts(self, city: str, districts: List[str]) -> None:
        """
        Установить список районов для города

        Args:
            city: Название города
            districts: Список районов
        """
        if districts:
            self.districts[city] = sorted(districts)
        elif city in self.districts:
            del self.districts[city]

        self._save_config()
        logger.info(f"Обновлены районы для города {city}")

    def reset_to_defaults(self) -> None:
        """Сбросить настройки к значениям по умолчанию"""
        self.popular_cities = self.DEFAULT_POPULAR_CITIES.copy()
        self.districts = self.DEFAULT_DISTRICTS.copy()
        self._save_config()
        logger.info("Настройки городов сброшены к значениям по умолчанию")

    def generate_url(self, segment: str, city: str, district: Optional[str] = None) -> str:
        """
        Генерация одной URL для Яндекс.Карт

        Args:
            segment: Сегмент бизнеса (например, "Мебель на заказ")
            city: Город
            district: Район (опционально)

        Returns:
            Полная URL для Яндекс.Карт
        """
        if district:
            query = f"{segment} {city} {district}"
        else:
            query = f"{segment} {city}"

        # Кодируем запрос для URL
        encoded_query = urllib.parse.quote(query)

        # Формируем полную URL
        url = f"{self.BASE_URL}{encoded_query}"

        return url

    def generate_urls_for_city(
        self,
        city: str,
        segment: str,
        use_districts: bool = True,
        selected_districts: Optional[List[str]] = None
    ) -> List[Dict[str, str]]:
        """
        Генерация всех URL для одного города

        Args:
            city: Город
            segment: Сегмент бизнеса
            use_districts: Использовать ли районы для мегаполисов
            selected_districts: Выбранные районы (None = все районы)

        Returns:
            Список словарей с информацией о каждой ссылке
        """
        results = []

        if use_districts and self.is_megapolis(city):
            # Генерируем URL для каждого района
            districts = selected_districts if selected_districts else self.get_districts(
                city)

            for district in districts:
                url = self.generate_url(segment, city, district)
                results.append({
                    "city": city,
                    "segment": segment,
                    "district": district,
                    "url": url
                })

            logger.info(f"Сгенерировано {len(results)} ссылок для {city}")
        else:
            # Генерируем одну URL для всего города
            url = self.generate_url(segment, city)
            results.append({
                "city": city,
                "segment": segment,
                "district": None,
                "url": url
            })

            logger.info(f"Сгенерирована 1 ссылка для {city}")

        return results

    def generate_urls_batch(
        self,
        cities: List[str],
        segment: str,
        use_districts: bool = True
    ) -> List[Dict[str, str]]:
        """
        Генерация URL для нескольких городов

        Args:
            cities: Список городов
            segment: Сегмент бизнеса
            use_districts: Использовать ли районы для мегаполисов

        Returns:
            Список всех сгенерированных ссылок
        """
        all_results = []

        for city in cities:
            results = self.generate_urls_for_city(city, segment, use_districts)
            all_results.extend(results)

        logger.info(
            f"Всего сгенерировано {len(all_results)} ссылок для {len(cities)} городов")

        return all_results
