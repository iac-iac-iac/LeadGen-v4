"""
Обёртка над QProgressBar.

Нужна, чтобы не размазывать логику обновления прогресса по всему коду.
"""

from PyQt6.QtWidgets import QProgressBar


class ProgressBarWidget(QProgressBar):
    """
    Простой прогресс-бар с удобными методами обновления.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setMinimum(0)
        self.setMaximum(100)
        self.reset_progress()

    def reset_progress(self) -> None:
        """Сбросить прогресс в начальное состояние."""
        self.setValue(0)
        self.setFormat("Ожидание...")

    def set_progress(self, value: int, text: str | None = None) -> None:
        """
        Обновить значение прогресса и, при необходимости, текст.

        value: число от 0 до 100.
        text: отображаемая строка (если None — используем проценты).
        """
        self.setValue(value)
        if text is not None:
            self.setFormat(text)
        else:
            self.setFormat(f"{value}%")
