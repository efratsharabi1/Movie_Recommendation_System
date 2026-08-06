"""Desktop application entry point."""

import sys

from PySide6.QtWidgets import QApplication
from models.api_client import ApiClient

from presenters.main_presenter import MainPresenter
from views.main_window import MainWindow

DARK_THEME_QSS = """
/* רקע כללי וטקסטים */
QWidget {
    background-color: #0D0D11;
    color: #E2E2E8;
    font-family: "Segoe UI", -apple-system, sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #0D0D11;
}

QStatusBar {
    background: #14141A;
    color: #8E8EA0;
    border-top: 1px solid #22222E;
}

/* שדות קלט (Input, TextEdit, SpinBox) */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox {
    background-color: #171720;
    border: 1px solid #2A2A3A;
    border-radius: 8px;
    padding: 8px 12px;
    color: #FFFFFF;
}

QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
    border: 1px solid #6C5CE7;
    background-color: #1D1D2A;
}

/* כפתורים מעוצבים מעוגלים */
QPushButton {
    background-color: #6C5CE7;
    color: #FFFFFF;
    font-weight: 600;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
}

QPushButton:hover {
    background-color: #7D6EFE;
}

QPushButton:pressed {
    background-color: #5A4AD1;
}

QPushButton:disabled {
    background-color: #22222D;
    color: #555566;
}

/* כרטיסיות (Tabs) */
QTabWidget::pane {
    border: 1px solid #22222E;
    background-color: #14141A;
    border-radius: 12px;
}

QTabBar::tab {
    background: transparent;
    color: #8E8EA0;
    padding: 10px 22px;
    font-weight: 600;
    border-bottom: 2px solid transparent;
}

QTabBar::tab:hover {
    color: #FFFFFF;
}

QTabBar::tab:selected {
    color: #FFFFFF;
    border-bottom: 3px solid #6C5CE7;
    background: #14141A;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}

/* רשימות (List View) */
QListWidget {
    background-color: #14141A;
    border: 1px solid #22222E;
    border-radius: 12px;
    padding: 6px;
}

QListWidget::item {
    background-color: #1A1A24;
    color: #D1D1DF;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 5px;
}

QListWidget::item:hover {
    background-color: #252536;
    color: #FFFFFF;
}

QListWidget::item:selected {
    background-color: #6C5CE7;
    color: #FFFFFF;
    font-weight: bold;
}

/* מסגרות ופאנלים */
QFrame, QGroupBox {
    background-color: #14141A;
    border: 1px solid #22222E;
    border-radius: 12px;
}

QGroupBox {
    font-weight: bold;
    margin-top: 10px;
    padding-top: 14px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #9A9AB0;
}

/* סרגל גלילה */
QScrollBar:vertical {
    background: #0D0D11;
    width: 8px;
}

QScrollBar::handle:vertical {
    background: #2A2A3A;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #6C5CE7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QSplitter::handle {
    background-color: #22222E;
    width: 2px;
}
"""


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Movie Recommendation System")
    app.setOrganizationName("MovieRec")
    app.setStyleSheet(DARK_THEME_QSS)

    api_client = ApiClient()
    presenter = MainPresenter(api_client)
    window = MainWindow(presenter)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())