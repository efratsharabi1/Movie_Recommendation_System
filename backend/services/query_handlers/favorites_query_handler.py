import asyncio
from backend.event_store.repository import EventStoreRepository


class FavoritesQueryHandler:
    def __init__(self, event_store: EventStoreRepository | None = None) -> None:
        self._event_store = event_store or EventStoreRepository()

    async def get_favorites(self, user_id: str) -> list[dict]:

        response = await asyncio.to_thread(
            lambda: self._event_store._client.table("user_favorites")
            .select("movie_id, created_at")
            .eq("user_id", user_id)
            .execute()
        )
        
        return [{"movie_id": row["movie_id"], "created_at": row["created_at"]} for row in response.data]