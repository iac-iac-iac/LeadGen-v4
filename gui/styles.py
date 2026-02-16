"""
Минимальные стили для приложения.

Здесь можно хранить QSS-строки или функции настройки палитры.
"""

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor


def apply_basic_theme(app: QApplication) -> None:
    """
    Применить простую светлую тему.

    В MVP делаем только небольшие изменения, чтобы не усложнять код.
    """
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#f5f5f5"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#202020"))
    app.setPalette(palette)
