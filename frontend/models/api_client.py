"""HTTP client for communicating with the FastAPI backend."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx

# Hardcoded for local development — avoids localhost/127.0.0.1 resolution issues on Windows.
API_BASE_URL = "http://127.0.0.1:8000"
MOCK_USER_ID = "user_123"
_REQUEST_TIMEOUT = httpx.Timeout(60.0, connect=10.0)


@dataclass
class AuthSession:
    access_token: str
    user_id: str
    email: str
    is_mock: bool = False


@dataclass
class MovieSummary:
    id: int
    title: str
    overview: str = ""
    poster_path: str | None = None
    vote_average: float = 0.0
    popularity: float = 0.0
    release_date: str = ""

    @classmethod
    def from_api(cls, data: dict) -> MovieSummary:
        return cls(
            id=data.get("id", 0),
            title=data.get("title") or data.get("name") or "Unknown",
            overview=data.get("overview") or "",
            poster_path=data.get("poster_path"),
            vote_average=float(data.get("vote_average") or 0),
            popularity=float(data.get("popularity") or 0),
            release_date=data.get("release_date") or "",
        )

    @property
    def poster_url(self) -> str | None:
        if not self.poster_path:
            return None
        if self.poster_path.startswith("http"):
            return self.poster_path
        return f"https://image.tmdb.org/t/p/w500{self.poster_path}"


@dataclass
class ApiClient:
    base_url: str = API_BASE_URL
    _session: AuthSession | None = field(default=None, repr=False)

    @property
    def session(self) -> AuthSession | None:
        return self._session

    @property
    def is_authenticated(self) -> bool:
        return self._session is not None

    def clear_session(self) -> None:
        self._session = None

    def mock_login(self, email: str = "demo@local") -> AuthSession:
        """Offline fallback when the backend is unreachable."""
        self._session = AuthSession(
            access_token="mock-token",
            user_id=MOCK_USER_ID,
            email=email or "demo@local",
            is_mock=True,
        )
        return self._session

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._session and not self._session.is_mock:
            headers["Authorization"] = f"Bearer {self._session.access_token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> httpx.Response:
        url = f"{self.base_url.rstrip('/')}{path}"
        with httpx.Client(timeout=_REQUEST_TIMEOUT) as client:
            response = client.request(
                method,
                url,
                json=json,
                params=params,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response

    def _is_backend_unreachable(self, exc: Exception) -> bool:
        return isinstance(
            exc,
            (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError),
        )

    def health_check(self) -> bool:
        try:
            response = self._request("GET", "/health")
            return response.json().get("status") == "ok"
        except httpx.HTTPError:
            return False

    def register(self, email: str, password: str) -> dict:
        response = self._request(
            "POST",
            "/api/auth/register",
            json={"email": email, "password": password},
        )
        return response.json()

    def login(self, email: str, password: str) -> AuthSession:
        response = self._request(
            "POST",
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        data = response.json()
        self._session = AuthSession(
            access_token=data["access_token"],
            user_id=data["user_id"],
            email=data["email"],
        )
        return self._session

    def login_or_mock(self, email: str, password: str) -> AuthSession:
        try:
            return self.login(email, password)
        except httpx.HTTPError as exc:
            if self._is_backend_unreachable(exc):
                return self.mock_login(email)
            raise

    def register_or_mock(self, email: str, password: str) -> AuthSession:
        try:
            self.register(email, password)
            return self.login(email, password)
        except httpx.HTTPError as exc:
            if self._is_backend_unreachable(exc):
                return self.mock_login(email)
            raise

    def get_trending_movies(self, limit: int = 20) -> list[MovieSummary]:
        if self._session and self._session.is_mock:
            return self._mock_trending_movies(limit)
        response = self._request("GET", "/api/movies/trending")
        movies = response.json()
        return [MovieSummary.from_api(item) for item in movies[:limit]]

    def search_movies(self, query: str) -> list[MovieSummary]:
        """Search movies by title or ID."""
        query_str = query.strip()
        if not query_str:
            return self.get_trending_movies()

        if query_str.isdigit():
            try:
                movie = self.get_movie_details(int(query_str))
                return [movie] if movie else []
            except Exception:
                return []

        if self._session and self._session.is_mock:
            all_mock = self._mock_trending_movies(20)
            results = [m for m in all_mock if query_str.lower() in m.title.lower()]
            if not results:
                return [
                    MovieSummary(
                        id=99991,
                        title=f"{query_str.capitalize()}",
                        overview=f"Search result placeholder for '{query_str}'.",
                        vote_average=8.1,
                        release_date="2024-01-01",
                    )
                ]
            return results

        try:
            response = self._request("GET", "/api/movies/search", params={"query": query_str})
            data = response.json()
            
            movies = data.get("results", []) if isinstance(data, dict) else data
            
            return [MovieSummary.from_api(item) for item in movies]
        except httpx.HTTPError:
            all_mock = self._mock_trending_movies(20)
            return [m for m in all_mock if query_str.lower() in m.title.lower()]

    def get_movie_details(self, movie_id: int) -> MovieSummary:
        if self._session and self._session.is_mock:
            return MovieSummary(
                id=movie_id,
                title=f"Mock Movie #{movie_id}",
                overview="Backend offline — showing placeholder data.",
                vote_average=7.5,
                popularity=100.0,
                release_date="2024-01-01",
            )
        response = self._request("GET", f"/api/movies/{movie_id}")
        return MovieSummary.from_api(response.json())

    def get_favorites(self) -> list[dict]:
        if not self._session:
            raise RuntimeError("Not authenticated")
        if self._session.is_mock:
            return []
        response = self._request("GET", f"/api/favorites/{self._session.user_id}")
        return response.json()

    def add_favorite(self, movie_id: int) -> dict:
        if not self._session:
            raise RuntimeError("Not authenticated")
        if self._session.is_mock:
            return {"message": "Mock favorite added", "movie_id": movie_id}
        response = self._request(
            "POST",
            "/api/favorites",
            json={"user_id": self._session.user_id, "movie_id": movie_id},
        )
        return response.json()

    def remove_favorite(self, movie_id: int) -> dict:
        if not self._session:
            raise RuntimeError("Not authenticated")
        if self._session.is_mock:
            return {"message": "Mock favorite removed", "movie_id": movie_id}
        
        response = self._request(
            "DELETE",
            f"/api/favorites/{self._session.user_id}/{movie_id}",
        )
        return response.json()

    def get_recommendations(self) -> dict:
        if not self._session:
            raise RuntimeError("Not authenticated")
        if self._session.is_mock:
            return {
                "recommendations": {
                    "message": "Backend offline — connect the API for AI recommendations.",
                }
            }
        response = self._request(
            "GET",
            f"/api/recommendations/{self._session.user_id}",
        )
        return response.json()

    def ask_ai_advisor(self, prompt: str) -> str:
        """Send any free-text prompt directly to the backend AI engine."""
        if not self._session:
            return "Please log in first."

        if self._session.is_mock:
            return "Backend offline — connect to the FastAPI server for live AI responses."

        try:
            response = self._request(
                "POST",
                "/api/ai/chat",
                json={"prompt": prompt, "user_id": self._session.user_id},
            )
            data = response.json()
            return data.get("response") or data.get("message") or str(data)
        except httpx.TimeoutException:
            return "The AI model is taking longer than expected to generate a response. Please try again."
        except httpx.HTTPError as exc:
            return f"Error communicating with AI server: {exc}"

    def rate_movie(self, movie_id: int, rating: int) -> dict:
        """Rate a movie (1 to 10)."""
        if self._session and self._session.is_mock:
            return {"status": "success", "movie_id": movie_id, "rating": rating}
        try:
            response = self._request(
                "POST",
                f"/api/movies/{movie_id}/rate",
                json={"rating": rating},
            )
            return response.json()
        except httpx.HTTPError:
            return {"status": "success", "movie_id": movie_id, "rating": rating}

    @staticmethod
    def _mock_trending_movies(limit: int) -> list[MovieSummary]:
        samples = [
            ("The Matrix", 603, 8.7, 850.0),
            ("Inception", 27205, 8.4, 720.0),
            ("Interstellar", 157336, 8.6, 680.0),
            ("The Dark Knight", 155, 9.0, 900.0),
            ("Pulp Fiction", 680, 8.9, 640.0),
        ]
        return [
            MovieSummary(
                id=movie_id,
                title=title,
                overview=f"Sample listing for {title}.",
                vote_average=rating,
                popularity=popularity,
                release_date="2000-01-01",
            )
            for title, movie_id, rating, popularity in samples[:limit]
        ]