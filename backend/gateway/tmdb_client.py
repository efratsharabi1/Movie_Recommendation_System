import httpx
from backend.config import settings

BASE_URL = "https://api.themoviedb.org/3"

class TMDBClient:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or settings.tmdb_api_key


    async def _get(self, path: str, params: dict | None = None) -> dict | list:
        params = params or {}
        params["api_key"] = self.api_key

        # AsyncClient
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=10.0) as client:
            response = await client.get(path, params=params)
            response.raise_for_status()
            return response.json()

    async def get_trending_movies(self, limit: int = 5) -> list[dict]:
        data = await self._get("/trending/movie/day")
        return data.get("results", [])[:limit]

    async def get_movie_details(self, movie_id: int) -> dict:
        return await self._get(f"/movie/{movie_id}")

    async def search_movies(self, query: str) -> list[dict]:
        params = {
            "query": query,
            "language": "en-US",
            "page": 1,
            "include_adult": "false"
        }
        data = await self._get("/search/movie", params=params)
        return data.get("results", [])