from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Event(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    aggregate_id: str
    event_type: str
    payload: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserRegistered(Event):
    event_type: Literal["UserRegistered"] = "UserRegistered"


class UserLoggedIn(Event):
    event_type: Literal["UserLoggedIn"] = "UserLoggedIn"


class MovieFavorited(Event):
    event_type: Literal["MovieFavorited"] = "MovieFavorited"


class MovieUnfavorited(Event):
    event_type: Literal["MovieUnfavorited"] = "MovieUnfavorited"
