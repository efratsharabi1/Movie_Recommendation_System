import httpx 
from backend.gateway.tmdb_client import TMDBClient

class MoviesQueryHandler:
    def __init__(self):
        self.tmdb_client = TMDBClient()

    async def handle_search(self, query: str) -> list[dict]:
     
        if not query or query.strip() == "":
            return []
            
        results = await self.tmdb_client.search_movies(query)
        
        formatted_results = []
        for movie in results:
            formatted_results.append({
                "id": movie.get("id"),
                "title": movie.get("title"),
                "overview": movie.get("overview"),
                "release_date": movie.get("release_date"),
                "vote_average": movie.get("vote_average"),
                "poster_path": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get("poster_path") else None
            })
            
        return formatted_results

    async def get_trending_movies(self, limit: int = 5) -> list[dict]:
        return await self.tmdb_client.get_trending_movies(limit=limit)

    # handle the errors by converting the technical error to a logical error
    async def get_movie_details(self, movie_id: int) -> dict:
        try:
            return await self.tmdb_client.get_movie_details(movie_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                raise ValueError("Movie not found") from exc
            raise ValueError("Failed to fetch movie details from TMDB") from exc
        except httpx.HTTPError as exc:
            raise ValueError("Network error while connecting to TMDB") from exc