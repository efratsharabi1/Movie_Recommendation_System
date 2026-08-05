"""Desktop application entry point."""

import sys

from PySide6.QtWidgets import QApplication
from models.api_client import ApiClient

from presenters.main_presenter import MainPresenter
from views.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Movie Recommendation System")
    app.setOrganizationName("MovieRec")

    api_client = ApiClient()
    presenter = MainPresenter(api_client)
    window = MainWindow(presenter)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
