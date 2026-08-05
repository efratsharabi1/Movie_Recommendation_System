import httpx
from fastapi import APIRouter, HTTPException, Query
from backend.gateway.tmdb_client import TMDBClient
from backend.services.query_handlers.search_movies_query_handler import SearchMoviesQueryHandler


router = APIRouter()
tmdb_client = TMDBClient()

@router.get("/search")
def search_movies_endpoint(query: str = Query(..., description="The movie title to search for")):
    handler = SearchMoviesQueryHandler()
    results = handler.handle_search(query)
    return {"results": results}

@router.get("/trending")
def get_trending_movies() -> list[dict]:
    try:
        return tmdb_client.get_trending_movies(limit=5)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch trending movies") from exc

@router.get("/{movie_id}")
def get_movie_details(movie_id: int) -> dict:
    try:
        return tmdb_client.get_movie_details(movie_id)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Movie not found") from exc
        raise HTTPException(status_code=502, detail="Failed to fetch movie details") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch movie details") from exc