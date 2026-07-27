import asyncio

from supabase import Client

from backend.event_store.supabase_connection import get_supabase_client
from backend.models.events import Event


class EventStoreRepository:
    def __init__(self, client: Client | None = None) -> None:
        self._client = client or get_supabase_client()

    async def append_event(self, event: Event) -> Event:
        record = {
            "id": str(event.id),
            "aggregate_id": event.aggregate_id,
            "event_type": event.event_type,
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat(),
        }

        await asyncio.to_thread(
            lambda: self._client.table("events").insert(record).execute()
        )
        return event

    async def get_events_for_aggregate(self, aggregate_id: str) -> list[Event]:
        response = await asyncio.to_thread(
            lambda: self._client.table("events")
            .select("*")
            .eq("aggregate_id", aggregate_id)
            .order("timestamp")
            .execute()
        )
        return [Event.model_validate(row) for row in response.data]

    async def find_registered_user_by_email(self, email: str) -> Event | None:
        response = await asyncio.to_thread(
            lambda: self._client.table("events")
            .select("*")
            .eq("event_type", "UserRegistered")
            .filter("payload->>email", "eq", email)
            .limit(1)
            .execute()
        )
        if not response.data:
            return None
        return Event.model_validate(response.data[0])
    async def add_user_favorite(self, user_id: str, movie_id: int) -> None:
        await asyncio.to_thread(
            lambda: self._client.table("user_favorites")
            .upsert({"user_id": user_id, "movie_id": movie_id})
            .execute()
        )

    async def remove_user_favorite(self, user_id: str, movie_id: int) -> None:
        await asyncio.to_thread(
            lambda: self._client.table("user_favorites")
            .delete()
            .eq("user_id", user_id)
            .eq("movie_id", movie_id)
            .execute()
        )
