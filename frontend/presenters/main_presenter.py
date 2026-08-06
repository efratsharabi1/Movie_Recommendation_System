"""Main presenter — orchestrates view actions and backend API calls (MVP)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
from PySide6.QtCore import QObject, QThread, Signal

from models.api_client import ApiClient, AuthSession, MovieSummary


def _format_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        try:
            detail = exc.response.json().get("detail", exc.response.text)
            if isinstance(detail, list):
                return "; ".join(str(item) for item in detail)
            return str(detail)
        except Exception:
            return exc.response.text or str(exc)
    return str(exc)


class _BackgroundTask(QObject):
    """Runs a callable on a dedicated QThread and reports back via signals."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(self, fn: Callable[[], Any]) -> None:
        super().__init__()
        self._fn = fn

    def execute(self) -> None:
        try:
            res = self._fn()
            self.finished.emit(res)
        except Exception as exc:  # noqa: BLE001 — surface API errors to the view
            self.error.emit(_format_error(exc))


class MainPresenter(QObject):
    """Presenter layer: receives view events, calls the model (ApiClient), emits view updates."""

    auth_changed = Signal(bool, str)
    movies_loaded = Signal(list)
    movie_detail_loaded = Signal(object)
    favorites_loaded = Signal(list)
    chart_data_loaded = Signal(list)
    chat_reply_received = Signal(str, object)
    status_message = Signal(str)
    error_occurred = Signal(str)
    loading_changed = Signal(bool)

    def __init__(self, api_client: ApiClient | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._api = api_client or ApiClient()
        self._cached_movies: list[MovieSummary] = []
        self._pending_tasks = 0
        # שמירת גם ה-Thread וגם ה-Task בזיכרון למניעת Garbage Collection
        self._workers: list[tuple[QThread, _BackgroundTask]] = []

    @property
    def api_client(self) -> ApiClient:
        return self._api

    def _set_loading(self, active: bool) -> None:
        if active:
            self._pending_tasks += 1
        else:
            self._pending_tasks = max(0, self._pending_tasks - 1)
        self.loading_changed.emit(self._pending_tasks > 0)

    def _run_async(
        self,
        fn: Callable[[], Any],
        on_success: Callable[[Any], None],
        *,
        start_loading: bool = True,
        on_error: Callable[[str], None] | None = None,
    ) -> None:
        """Always runs network tasks asynchronously on a background QThread."""
        if start_loading:
            self._set_loading(True)

        thread = QThread()
        task = _BackgroundTask(fn)
        task.moveToThread(thread)

        worker_pair = (thread, task)
        self._workers.append(worker_pair)

        def _finish_loading() -> None:
            if start_loading:
                self._set_loading(False)

        def _on_success(result: object) -> None:
            _finish_loading()
            on_success(result)

        def _on_error(message: str) -> None:
            _finish_loading()
            if on_error:
                on_error(message)
            else:
                self.error_occurred.emit(message)

        def _cleanup() -> None:
            if worker_pair in self._workers:
                self._workers.remove(worker_pair)

        thread.started.connect(task.execute)
        task.finished.connect(_on_success)
        task.error.connect(_on_error)
        task.finished.connect(thread.quit)
        task.error.connect(thread.quit)
        thread.finished.connect(task.deleteLater)
        thread.finished.connect(_cleanup)

        thread.start()

    # --- Auth ---

    def login(self, email: str, password: str) -> None:
        def _task() -> AuthSession:
            return self._api.login_or_mock(email.strip(), password)

        self._run_async(_task, self._on_login_success)

    def register(self, email: str, password: str) -> None:
        def _task() -> AuthSession:
            return self._api.register_or_mock(email.strip(), password)

        self._run_async(_task, self._on_login_success)

    def logout(self) -> None:
        self._api.clear_session()
        self._cached_movies.clear()
        self.auth_changed.emit(False, "")
        self.status_message.emit("Logged out.")

    def _on_login_success(self, session: AuthSession) -> None:
        self.auth_changed.emit(True, session.email)
        if session.is_mock:
            self.status_message.emit(
                f"Welcome, {session.email}! (offline mock user: {session.user_id})"
            )
        else:
            self.status_message.emit(f"Welcome, {session.email}!")

    def on_authenticated(self) -> None:
        """Load initial data after successful login."""
        self.load_trending_movies(start_loading=False)
        self.load_favorites(start_loading=False)
        self.load_chart_data(start_loading=False)

    # --- Movies / Search ---

    def load_trending_movies(self, *, start_loading: bool = True) -> None:
        def _task() -> list[MovieSummary]:
            movies = self._api.get_trending_movies(limit=20)
            self._cached_movies = movies
            return movies

        self._run_async(
            _task,
            self.movies_loaded.emit,
            start_loading=start_loading,
            on_error=lambda msg: self.status_message.emit(f"Movies unavailable: {msg}"),
        )

    def search_movies(self, query: str) -> None:
        query = query.strip()
        if not query:
            self.load_trending_movies()
            return

        if query.isdigit():
            self.load_movie_detail(int(query))
            return

        # Asynchronous task that calls the server we set up (/api/movies/search)
        def _task() -> list[MovieSummary]:
            return self._api.search_movies(query)

        self._run_async(
            _task,
            self.movies_loaded.emit,
            on_error=lambda msg: self.status_message.emit(f"Search failed: {msg}"),
        )

    def load_movie_detail(self, movie_id: int) -> None:
        def _task() -> MovieSummary:
            return self._api.get_movie_details(movie_id)

        self._run_async(
            _task,
            self.movie_detail_loaded.emit,
            on_error=lambda msg: self.error_occurred.emit(f"Could not load movie: {msg}"),
        )

    # --- Favorites ---

    def load_favorites(self, *, start_loading: bool = True) -> None:
        def _task() -> list[MovieSummary]:
            raw = self._api.get_favorites()
            detailed: list[MovieSummary] = []
            for item in raw:
                movie_id = item.get("movie_id")
                if movie_id is not None:
                    detailed.append(self._api.get_movie_details(int(movie_id)))
            return detailed

        self._run_async(
            _task,
            self.favorites_loaded.emit,
            start_loading=start_loading,
            on_error=lambda msg: self.status_message.emit(f"Favorites unavailable: {msg}"),
        )

    def add_favorite(self, movie_id: int) -> None:
        def _task() -> dict:
            return self._api.add_favorite(movie_id)

        def _on_added(_result: dict) -> None:
            self.status_message.emit("Added to favorites.")
            self.load_favorites(start_loading=False)

        self._run_async(_task, _on_added)

    def remove_favorite(self, movie_id: int) -> None:
        def _task() -> dict:
            return self._api.remove_favorite(movie_id)

        def _on_removed(_result: dict) -> None:
            self.status_message.emit("Removed from favorites.")
            self.load_favorites(start_loading=False)

        self._run_async(_task, _on_removed)

    def rate_movie(self, movie_id: int, rating: int) -> None:
        def _task() -> dict:
            return self._api.rate_movie(movie_id, rating)

        def _on_rated(_result: dict) -> None:
            self.status_message.emit(f"Successfully rated movie with {rating}/10 ⭐!")

        self._run_async(_task, _on_rated)

    # --- Charts ---

    def load_chart_data(self, *, start_loading: bool = True) -> None:
        def _task() -> list[MovieSummary]:
            return self._api.get_trending_movies(limit=5)

        self._run_async(
            _task,
            self.chart_data_loaded.emit,
            start_loading=start_loading,
            on_error=lambda msg: self.status_message.emit(f"Chart unavailable: {msg}"),
        )

    # --- AI Advisor ---
    def send_chat_message(self, message: str) -> None:
        message = message.strip()
        if not message:
            return

        lowered = message.lower()
        if lowered in {"recommend", "recommendations", "suggest", "help"} or "recommend" in lowered:
            self._fetch_recommendations()
            return

        def _task() -> str:
            return self._api.ask_ai_advisor(message)

        def _on_result(reply: str) -> None:
            self.chat_reply_received.emit(reply, None)

        self._run_async(_task, _on_result)

    def _fetch_recommendations(self) -> None:
        def _task() -> dict:
            return self._api.get_recommendations()

        def _on_result(data: dict) -> None:
            recommendations = data.get("recommendations", data)
            if isinstance(recommendations, dict):
                if "message" in recommendations:
                    self.chat_reply_received.emit(recommendations["message"], None)
                    return
                movies = recommendations.get("recommended_movies", [])
            else:
                movies = recommendations

            if not movies:
                self.chat_reply_received.emit(
                    "No recommendations yet — add some favorites first!", None
                )
                return

            titles = ", ".join(
                m.get("title", "Unknown") for m in movies if isinstance(m, dict)
            )
            self.chat_reply_received.emit(
                f"Based on your favorites, I recommend: {titles}", movies
            )

        self._run_async(_task, _on_result)