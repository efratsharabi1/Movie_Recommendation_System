import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.command_handlers.favorites_command_handler import (
    FavoritesCommandHandler,
)
from backend.services.query_handlers.favorites_query_handler import (
    FavoritesQueryHandler,
)

router = APIRouter()
command_handler = FavoritesCommandHandler()
query_handler = FavoritesQueryHandler()


class AddFavoriteRequest(BaseModel):
    user_id: str
    movie_id: int


@router.post("")
async def add_favorite(request: AddFavoriteRequest) -> dict:
    try:
        event = await command_handler.add_favorite(request.user_id, request.movie_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Failed to validate movie") from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to add favorite") from exc

    return {
        "message": "Movie added to favorites",
        "event_id": str(event.id),
        "favorite": event.payload,
    }


@router.get("/{user_id}")
async def get_favorites(user_id: str) -> list[dict]:
    return await query_handler.get_favorites(user_id)
