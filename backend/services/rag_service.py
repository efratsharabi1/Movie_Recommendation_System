import asyncio
import httpx
from backend.config import settings
from backend.event_store.repository import EventStoreRepository


class RAGRecommendationService:
    def __init__(self, event_store: EventStoreRepository | None = None) -> None:
        self._event_store = event_store or EventStoreRepository()
        self._tmdb_api_key = settings.tmdb_api_key
        self._tmdb_base_url = "https://api.themoviedb.org/3"
        # address of the Ollama server (in the docker or local)
        self._ollama_url = "http://ollama:11434/api/generate"

    async def get_personalized_recommendations(self, user_id: str) -> dict:
        # 1. get the user's favorites from the read model
        response = await asyncio.to_thread(
            lambda: self._event_store._client.table("user_favorites")
            .select("movie_id")
            .eq("user_id", user_id)
            .execute()
        )
        
        favorites = response.data
        if not favorites:
            return {"message": "there is no favorites yet. add some movies to get recommendations!"}

        movie_ids = [fav["movie_id"] for fav in favorites]

        # 2. build the prompt for the Ollama
        prompt = (
            f"the user marked the following movie ids as favorites: {movie_ids}. "
            "recommend 3 new movies that are suitable for him. "
            "return the response only with the exact movie titles in english, separated by commas, without any extra text."
        )

        # 3. call to the local Ollama server
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            }
            res = await client.post(self._ollama_url, json=payload)
            if res.status_code != 200:
                raise Exception(f"Failed to communicate with Ollama: {res.text}")
            
            ai_response = res.json().get("response", "")

        movie_titles = [title.strip() for title in ai_response.split(",")]

        # 4. call to TMDB to get the real details (image, summary, etc.) for each movie the AI recommended by TMDB
        detailed_recommendations = []
        async with httpx.AsyncClient() as client:
            for title in movie_titles:
                if not title:
                    continue
                url = f"{self._tmdb_base_url}/search/movie"
                params = {"api_key": self._tmdb_api_key, "query": title}
                res = await client.get(url, params=params)
                if res.status_code == 200:
                    results = res.json().get("results", [])
                    if results:
                        movie_data = results[0]
                        detailed_recommendations.append({
                            "id": movie_data.get("id"),
                            "title": movie_data.get("title"),
                            "overview": movie_data.get("overview"),
                            "poster_path": f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get('poster_path') else None
                        })

        return {
            "user_id": user_id,
            "recommended_movies": detailed_recommendations
        }