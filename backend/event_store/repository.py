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

