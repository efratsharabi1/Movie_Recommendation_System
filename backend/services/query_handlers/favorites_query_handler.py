from backend.event_store.repository import EventStoreRepository


class FavoritesQueryHandler:
    def __init__(self, event_store: EventStoreRepository | None = None) -> None:
        self._event_store = event_store or EventStoreRepository()

    async def get_favorites(self, user_id: str) -> list[dict]:
        events = await self._event_store.get_events_for_aggregate(user_id)
        favorites: dict[int, dict] = {}

        for event in events:
            movie_id = event.payload.get("movie_id")
            if movie_id is None:
                continue

            if event.event_type == "MovieFavorited":
                favorites[movie_id] = event.payload
            elif event.event_type == "MovieUnfavorited":
                favorites.pop(movie_id, None)

        return list(favorites.values())
