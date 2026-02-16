"""
Константы: названия колонок, форматы и т.п.

Единое место для магических строк.
"""

from typing import List

# Колонки Webbee AI (входной формат)
WEBBEE_COLUMNS = {
    "NAME": "Название",
    "CATEGORY": "Category 0",
    "PHONE_1": "phone_1",
    "PHONE_2": "phone_2",
    "ADDRESS": "Адрес",
    "URL": "companyUrl",
    "TELEGRAM": "telegram",
    "VK": "vkontakte",
}

# Колонки Битрикс24 (выходной формат)
BITRIX_COLUMNS: List[str] = [
    "Название лида",
    "Рабочий телефон",
    "Мобильный телефон",
    "Адрес",
    "Корпоративный сайт",
    "Контакт Telegram",
    "Контакт ВКонтакте",
    "Название компании",
    "Комментарий",
    "Стадия",
    "Источник",
    "Тип услуги",
    "Источник телефона",
    "Ответственный",
]

# Форматы телефонов
PHONE_LENGTH = 11
VALID_PHONE_PREFIXES = ("7", "8")

# Разделители файлов
TSV_SEPARATOR = "\t"
CSV_SEPARATOR = ","
