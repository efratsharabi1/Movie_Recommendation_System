"""PySide6 main window — View layer in the MVP pattern."""

from __future__ import annotations

import httpx
from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSet,
    QChart,
    QChartView,
    QHorizontalBarSeries,
    QValueAxis,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models.api_client import MovieSummary
from presenters.main_presenter import MainPresenter


class MainWindow(QMainWindow):
    """Shell window with Login view and Main application tabs view."""

    def __init__(self, presenter: MainPresenter | None = None) -> None:
        super().__init__()
        self._presenter = presenter or MainPresenter()
        self._selected_movie_id: int | None = None

        self.setWindowTitle("Movie Recommendation System")
        self.setMinimumSize(960, 640)

        self._build_ui()
        self._wire_presenter()
        self._wire_view_events()

    def _build_ui(self) -> None:
        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        # Page 0: Login View
        self._login_widget = self._build_login_view()
        self._stack.addWidget(self._login_widget)

        # Page 1: Main Application View
        self._main_widget = self._build_main_view()
        self._stack.addWidget(self._main_widget)

        # Start on Login View
        self._stack.setCurrentWidget(self._login_widget)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status.showMessage("Ready")

    def _build_login_view(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        box = QGroupBox("Sign In / Register")
        box.setFixedWidth(380)
        box_layout = QVBoxLayout(box)
        box_layout.setSpacing(12)

        self._email_input = QLineEdit()
        self._email_input.setPlaceholderText("Email (e.g. user@example.com)")

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Password")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)

        btn_layout = QHBoxLayout()
        self._login_btn = QPushButton("Log In")
        self._register_btn = QPushButton("Register")
        btn_layout.addWidget(self._login_btn)
        btn_layout.addWidget(self._register_btn)

        box_layout.addWidget(QLabel("Email:"))
        box_layout.addWidget(self._email_input)
        box_layout.addWidget(QLabel("Password:"))
        box_layout.addWidget(self._password_input)
        box_layout.addLayout(btn_layout)

        layout.addWidget(box)
        return widget

    def _build_main_view(self) -> QWidget:
        widget = QWidget()
        root_layout = QVBoxLayout(widget)

        header = QHBoxLayout()
        self._user_label = QLabel("Not signed in")
        self._logout_btn = QPushButton("Log Out")
        header.addWidget(self._user_label)
        header.addStretch()
        header.addWidget(self._logout_btn)
        root_layout.addLayout(header)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._build_browse_tab(), "Movies")
        self._tabs.addTab(self._build_favorites_tab(), "Favorites")
        self._tabs.addTab(self._build_charts_tab(), "Analytics")
        self._tabs.addTab(self._build_advisor_tab(), "AI Advisor")
        root_layout.addWidget(self._tabs)

        return widget

    def _build_browse_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search by title or enter a movie ID…")
        self._search_btn = QPushButton("Search")
        self._refresh_movies_btn = QPushButton("Load Trending")
        search_row.addWidget(self._search_input)
        search_row.addWidget(self._search_btn)
        search_row.addWidget(self._refresh_movies_btn)
        layout.addLayout(search_row)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._movie_list = QListWidget()
        self._movie_list.setMinimumWidth(280)
        splitter.addWidget(self._movie_list)

        detail_panel = QFrame()
        detail_panel.setFrameShape(QFrame.Shape.StyledPanel)
        detail_layout = QVBoxLayout(detail_panel)

        self._detail_title = QLabel("Select a movie")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        self._detail_title.setFont(title_font)
        self._detail_title.setWordWrap(True)

        self._detail_meta = QLabel("")
        self._detail_overview = QTextEdit()
        self._detail_overview.setReadOnly(True)

        # רכיב התמונה (Poster Label)
        self._detail_poster = QLabel("No Image")
        self._detail_poster.setFixedSize(160, 240)
        self._detail_poster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._detail_poster.setStyleSheet(
            "border: 1px solid #ccc; background-color: #f8f9fa; border-radius: 4px;"
        )

        # סידור התמונה לצד הפרטים הטקסטואליים
        info_layout = QHBoxLayout()
        info_layout.addWidget(self._detail_poster)

        text_details_layout = QVBoxLayout()
        text_details_layout.addWidget(self._detail_title)
        text_details_layout.addWidget(self._detail_meta)
        text_details_layout.addWidget(self._detail_overview)
        info_layout.addLayout(text_details_layout)

        detail_layout.addLayout(info_layout)

        self._add_favorite_btn = QPushButton("Add to Favorites")
        self._add_favorite_btn.setEnabled(False)

        # אזור הזנת דירוג
        rating_box = QGroupBox("User Input: Rate Movie")
        rating_layout = QHBoxLayout(rating_box)

        self._rating_label = QLabel("Rating (1-10):")
        self._rating_spinbox = QSpinBox()
        self._rating_spinbox.setRange(1, 10)
        self._rating_spinbox.setValue(8)
        self._rating_spinbox.setEnabled(False)

        self._rate_movie_btn = QPushButton("Rate Movie")
        self._rate_movie_btn.setEnabled(False)

        rating_layout.addWidget(self._rating_label)
        rating_layout.addWidget(self._rating_spinbox)
        rating_layout.addWidget(self._rate_movie_btn)

        detail_layout.addWidget(self._add_favorite_btn)
        detail_layout.addWidget(rating_box)
        detail_layout.addStretch()

        splitter.addWidget(detail_panel)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        return tab

    def _build_favorites_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        toolbar = QHBoxLayout()
        self._refresh_favorites_btn = QPushButton("Refresh Favorites")
        toolbar.addWidget(self._refresh_favorites_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._favorites_list = QListWidget()
        layout.addWidget(self._favorites_list)
        return tab

    def _build_charts_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        toolbar = QHBoxLayout()
        self._refresh_chart_btn = QPushButton("Refresh Chart")
        toolbar.addWidget(self._refresh_chart_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        self._chart_view = QChartView()
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        layout.addWidget(self._chart_view)

        self._render_empty_chart()
        return tab

    def _build_advisor_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self._chat_history = QTextEdit()
        self._chat_history.setReadOnly(True)
        self._chat_history.setPlaceholderText("Chat with the AI movie advisor…")
        layout.addWidget(self._chat_history)

        input_row = QHBoxLayout()
        self._chat_input = QLineEdit()
        self._chat_input.setPlaceholderText('Ask anything or try "recommend movies"…')
        self._chat_send_btn = QPushButton("Send")
        input_row.addWidget(self._chat_input)
        input_row.addWidget(self._chat_send_btn)
        layout.addLayout(input_row)

        hint = QLabel(
            "Tip: ask for recommendations to get personalized suggestions based on your favorites."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        return tab

    def _wire_presenter(self) -> None:
        p = self._presenter
        p.auth_changed.connect(self._on_auth_changed)
        p.movies_loaded.connect(self._on_movies_loaded)
        p.movie_detail_loaded.connect(self._on_movie_detail_loaded)
        p.favorites_loaded.connect(self._on_favorites_loaded)
        p.chart_data_loaded.connect(self._on_chart_data_loaded)
        p.chat_reply_received.connect(self._on_chat_reply)
        p.status_message.connect(self._status.showMessage)
        p.error_occurred.connect(self._show_error)
        p.loading_changed.connect(self._on_loading_changed)

    def _wire_view_events(self) -> None:
        # Auth events
        self._login_btn.clicked.connect(self._handle_login)
        self._register_btn.clicked.connect(self._handle_register)
        self._password_input.returnPressed.connect(self._handle_login)
        self._logout_btn.clicked.connect(self._presenter.logout)

        # Main app events
        self._search_btn.clicked.connect(
            lambda: self._presenter.search_movies(self._search_input.text())
        )
        self._search_input.returnPressed.connect(
            lambda: self._presenter.search_movies(self._search_input.text())
        )
        self._refresh_movies_btn.clicked.connect(self._presenter.load_trending_movies)
        self._movie_list.currentItemChanged.connect(self._on_movie_item_changed)
        self._add_favorite_btn.clicked.connect(self._handle_add_favorite)
        self._rate_movie_btn.clicked.connect(self._handle_rate_movie)

        self._refresh_favorites_btn.clicked.connect(self._presenter.load_favorites)
        self._refresh_chart_btn.clicked.connect(self._presenter.load_chart_data)

        self._chat_send_btn.clicked.connect(self._handle_chat_send)
        self._chat_input.returnPressed.connect(self._handle_chat_send)

        self._tabs.currentChanged.connect(self._on_tab_changed)

    # --- Presenter callbacks ---

    def _on_auth_changed(self, authenticated: bool, email: str) -> None:
        if authenticated:
            session = self._presenter.api_client.session
            user_id = session.user_id if session else "user_123"
            self._user_label.setText(f"User: {email} ({user_id})")
            self._stack.setCurrentWidget(self._main_widget)
            self._presenter.on_authenticated()
        else:
            self._user_label.setText("Not signed in")
            self._password_input.clear()
            self._stack.setCurrentWidget(self._login_widget)

    def _on_movies_loaded(self, movies: list) -> None:
        self._movie_list.clear()
        for movie in movies:
            if isinstance(movie, MovieSummary):
                item = QListWidgetItem(f"{movie.title}  ({movie.vote_average:.1f}★)")
                item.setData(Qt.ItemDataRole.UserRole, movie.id)
                self._movie_list.addItem(item)

    def _on_movie_detail_loaded(self, movie: MovieSummary) -> None:
        self._selected_movie_id = movie.id
        self._detail_title.setText(movie.title)
        year = movie.release_date[:4] if movie.release_date else "N/A"
        self._detail_meta.setText(
            f"Rating: {movie.vote_average:.1f}/10  |  Year: {year}  |  ID: {movie.id}"
        )
        self._detail_overview.setPlainText(movie.overview or "No overview available.")

        # טעינת פוסטר התמונה
        self._load_poster(movie.poster_url)

        # הפעלת הרכיבים כשסרט נבחר
        self._add_favorite_btn.setEnabled(True)
        self._rate_movie_btn.setEnabled(True)
        self._rating_spinbox.setEnabled(True)

    def _load_poster(self, poster_url: str | None) -> None:
        """פונקציית עזר להורדה והצגה של תמונת הפוסטר."""
        if not poster_url:
            self._detail_poster.setText("No Image")
            self._detail_poster.setPixmap(QPixmap())
            return

        try:
            response = httpx.get(poster_url, timeout=5.0)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                scaled_pixmap = pixmap.scaled(
                    160,
                    240,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._detail_poster.setPixmap(scaled_pixmap)
            else:
                self._detail_poster.setText("No Image")
                self._detail_poster.setPixmap(QPixmap())
        except Exception:
            self._detail_poster.setText("No Image")
            self._detail_poster.setPixmap(QPixmap())

    def _on_favorites_loaded(self, movies: list) -> None:
        self._favorites_list.clear()
        for movie in movies:
            if isinstance(movie, MovieSummary):
                item = QListWidgetItem(movie.title)
                item.setData(Qt.ItemDataRole.UserRole, movie.id)
                self._favorites_list.addItem(item)

    def _on_chart_data_loaded(self, movies: list) -> None:
        if not movies:
            self._render_empty_chart()
            return

        titles: list[str] = []
        scores: list[float] = []

        for movie in movies:
            if isinstance(movie, MovieSummary):
                label = movie.title if len(movie.title) <= 24 else f"{movie.title[:21]}…"
                titles.append(label)
                scores.append(movie.popularity or movie.vote_average)

        bar_set = QBarSet("Popularity")
        bar_set.append(scores)

        series = QHorizontalBarSeries()
        series.append(bar_set)
        series.setBarWidth(0.6)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("Top Trending Movies")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)

        axis_y = QBarCategoryAxis()
        axis_y.append(titles)
        chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        axis_x = QValueAxis()
        axis_x.setTitleText("Popularity")
        chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)

        self._chart_view.setChart(chart)

    def _on_chat_reply(self, text: str, sources: object) -> None:
        self._append_chat("assistant", text)
        if sources and isinstance(sources, list):
            for movie in sources:
                if isinstance(movie, dict) and movie.get("title"):
                    overview = movie.get("overview", "")
                    snippet = f"{overview[:120]}…" if len(overview) > 120 else overview
                    self._append_chat("source", f"• {movie['title']}: {snippet}")

    def _on_loading_changed(self, loading: bool) -> None:
        if loading:
            self._status.showMessage("Loading…")
        elif self._status.currentMessage() == "Loading…":
            self._status.showMessage("Ready")

    def _on_tab_changed(self, index: int) -> None:
        tab_text = self._tabs.tabText(index)
        if tab_text == "Analytics":
            self._presenter.load_chart_data()
        elif tab_text == "Favorites":
            self._presenter.load_favorites()

    def _on_movie_item_changed(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            return
        movie_id = current.data(Qt.ItemDataRole.UserRole)
        if movie_id is not None:
            self._presenter.load_movie_detail(int(movie_id))

    # --- User actions ---

    def _handle_login(self) -> None:
        email = self._email_input.text().strip()
        password = self._password_input.text().strip()
        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both email and password.")
            return
        self._presenter.login(email, password)

    def _handle_register(self) -> None:
        email = self._email_input.text().strip()
        password = self._password_input.text().strip()
        if not email or not password:
            QMessageBox.warning(self, "Input Error", "Please enter both email and password.")
            return
        self._presenter.register(email, password)

    def _handle_add_favorite(self) -> None:
        if self._selected_movie_id is not None:
            self._presenter.add_favorite(self._selected_movie_id)

    def _handle_rate_movie(self) -> None:
        """מטפל בלחיצה על כפתור הדירוג."""
        if self._selected_movie_id is not None:
            rating = self._rating_spinbox.value()
            self._presenter.rate_movie(self._selected_movie_id, rating)

    def _handle_chat_send(self) -> None:
        message = self._chat_input.text().strip()
        if not message:
            return
        self._append_chat("user", message)
        self._chat_input.clear()
        self._presenter.send_chat_message(message)

    def _append_chat(self, role: str, text: str) -> None:
        prefix = {"user": "You", "assistant": "Advisor", "source": "Source"}.get(role, role)
        self._chat_history.append(f"<b>{prefix}:</b> {text}")

    def _show_error(self, message: str) -> None:
        self._status.showMessage(message)
        QMessageBox.warning(self, "Error", message)

    def _render_empty_chart(self) -> None:
        chart = QChart()
        chart.setTitle("Top Trending Movies")
        self._chart_view.setChart(chart)