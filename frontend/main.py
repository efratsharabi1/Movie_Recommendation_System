"""Desktop application entry point."""

import sys

from PySide6.QtWidgets import QApplication

from frontend.models.api_client import ApiClient
from frontend.presenters.main_presenter import MainPresenter
from frontend.views.main_window import MainWindow


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
