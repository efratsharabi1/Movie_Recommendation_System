import asyncio

import httpx

from backend.event_store.repository import EventStoreRepository
from backend.gateway.tmdb_client import TMDBClient
from backend.models.events import MovieFavorited


class FavoritesCommandHandler:
    def __init__(
        self,
        event_store: EventStoreRepository | None = None,
        tmdb_client: TMDBClient | None = None,
    ) -> None:
        self._event_store = event_store or EventStoreRepository()
        self._tmdb_client = tmdb_client or TMDBClient()

    async def add_favorite(self, user_id: str, movie_id: int) -> MovieFavorited:
        try:
            movie = await asyncio.to_thread(
                self._tmdb_client.get_movie_details, movie_id
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ValueError("Movie not found") from exc
            raise ValueError("Failed to validate movie") from exc
        except httpx.HTTPError as exc:
            raise ValueError("Failed to validate movie") from exc

        event = MovieFavorited(
            aggregate_id=user_id,
            payload={
                "movie_id": movie_id,
                "title": movie.get("title"),
                "poster_path": movie.get("poster_path"),
            },
        )
        return await self._event_store.append_event(event)
