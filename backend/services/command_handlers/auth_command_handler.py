from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import jwt
from passlib.context import CryptContext

from backend.config import settings
from backend.event_store.repository import EventStoreRepository
from backend.models.events import UserLoggedIn, UserRegistered

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthCommandHandler:
    def __init__(self, event_store: EventStoreRepository | None = None) -> None:
        self._event_store = event_store or EventStoreRepository()

    async def register(self, email: str, password: str) -> dict:
        existing_user = await self._event_store.find_registered_user_by_email(email)
        if existing_user is not None:
            raise ValueError("Email already registered")

        user_id = str(uuid4())
        print(f"--- DEBUG: Password received is: '{password}' | Length: {len(password)} ---")
        password_hash = pwd_context.hash(password)

        event = UserRegistered(
            aggregate_id=user_id,
            payload={
                "user_id": user_id,
                "email": email,
                "password_hash": password_hash,
            },
        )
        await self._event_store.append_event(event)

        return {"user_id": user_id, "email": email}

    async def login(self, email: str, password: str) -> dict:
        user_event = await self._event_store.find_registered_user_by_email(email)
        if user_event is None:
            raise ValueError("Invalid email or password")

        password_hash = user_event.payload.get("password_hash")
        if not password_hash or not pwd_context.verify(password, password_hash):
            raise ValueError("Invalid email or password")

        user_id = user_event.payload["user_id"]
        login_event = UserLoggedIn(
            aggregate_id=user_id,
            payload={"email": email},
        )
        await self._event_store.append_event(login_event)

        token = self._create_access_token(user_id, email)
        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user_id,
            "email": email,
        }

    def _create_access_token(self, user_id: str, email: str) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt_expire_minutes
        )
        payload = {"sub": user_id, "email": email, "exp": expire}
        return jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )
