from fastapi import APIRouter, HTTPException, Query, Depends
from backend.services.query_handlers.movies_query_handler import MoviesQueryHandler

router = APIRouter()

# create dependency injection for the Handler
def get_movies_handler() -> MoviesQueryHandler:
    return MoviesQueryHandler()

@router.get("/search")
async def search_movies_endpoint(
    query: str = Query(..., description="The movie title to search for"),
    handler: MoviesQueryHandler = Depends(get_movies_handler)
):
    try:
        results = await handler.handle_search(query)
        return {"results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Search failed") from exc

@router.get("/trending")
async def get_trending_movies(
    handler: MoviesQueryHandler = Depends(get_movies_handler)
) -> list[dict]:
    try:
         # call goes to the Handler 
        return await handler.get_trending_movies(limit=5)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch trending movies") from exc

@router.get("/{movie_id}")
async def get_movie_details(
    movie_id: int,
    handler: MoviesQueryHandler = Depends(get_movies_handler)
) -> dict:
    try:
         # call goes to the Handler 
        return await handler.get_movie_details(movie_id)
    except ValueError as exc:
        # catch the logical error and return a 404 error
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Failed to fetch movie details")