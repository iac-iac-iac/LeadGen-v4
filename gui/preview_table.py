"""
QTableView для предпросмотра первых строк очищенных данных.
"""

import pandas as pd
from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt6.QtWidgets import QTableView


class DataFrameTableModel(QAbstractTableModel):
    """
    Простейшая модель для отображения pandas.DataFrame в QTableView.

    Подходит для чтения; редактирование в MVP не требуется.
    """

    def __init__(self, df: pd.DataFrame | None = None, parent=None) -> None:
        super().__init__(parent)
        self._df = df if df is not None else pd.DataFrame()

    def set_dataframe(self, df: pd.DataFrame) -> None:
        """Задать новый DataFrame и уведомить виджет о смене данных."""
        self.beginResetModel()
        self._df = df
        self.endResetModel()

    # type: ignore[override]
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df)

    # type: ignore[override]
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._df.columns)

    # type: ignore[override]
    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role == Qt.ItemDataRole.DisplayRole:
            value = self._df.iat[index.row(), index.column()]
            return "" if value is None else str(value)
        return None

    def headerData(self, section: int, orientation: Qt.Orientation,
                   role: int = Qt.ItemDataRole.DisplayRole):  # type: ignore[override]
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            try:
                return str(self._df.columns[section])
            except IndexError:
                return ""
        else:
            return str(section + 1)


class PreviewTable(QTableView):
    """
    Таблица для предпросмотра.

    Внутри использует DataFrameTableModel.
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._model = DataFrameTableModel()
        self.setModel(self._model)

        # Немного настроек для читабельности
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)

    def show_dataframe(self, df: pd.DataFrame) -> None:
        """
        Показать первые N строк DataFrame.

        Пока ограничимся 10 строками, как в контексте.
        """
        self._model.set_dataframe(df.head(10))
        self.resizeColumnsToContents()
