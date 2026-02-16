"""
Очистка URL от UTM-меток и параметров.

Простой вариант: отбрасываем всё после '?'.
"""

from urllib.parse import urlsplit, urlunsplit


def clean_url(url: str) -> str:
    """
    Удалить UTM-метки и параметры запроса из URL.

    Если строка не похожа на URL, возвращаем её как есть.
    """
    if not url:
        return ""

    try:
        parts = urlsplit(url)
        # Оставляем только базовый URL без query и fragment
        cleaned = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
        return cleaned
    except Exception:
        # В случае странных строк не падаем, а возвращаем исходное значение
        return url
