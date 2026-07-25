import httpx

from backend.config import settings

BASE_URL = "https://api.themoviedb.org/3"


class TMDBClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.tmdb_api_key

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        params = params or {}
        params["api_key"] = self.api_key

        with httpx.Client(base_url=BASE_URL, timeout=10.0) as client:
            response = client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    def get_trending_movies(self, limit: int = 5) -> list[dict]:
        data = self._get("/trending/movie/day")
        return data.get("results", [])[:limit]

    def get_movie_details(self, movie_id: int) -> dict:
        return self._get(f"/movie/{movie_id}")
