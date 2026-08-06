import asyncio
from backend.event_store.repository import EventStoreRepository
from backend.gateway.tmdb_client import TMDBClient
from backend.gateway.ollama_gateway import OllamaGateway

class RAGRecommendationService:
    # צעד 1: הזרקת ה-Gateways במקום הגדרת משתני רשת
    def __init__(
        self, 
        event_store: EventStoreRepository | None = None,
        tmdb_client: TMDBClient | None = None,
        ollama_gateway: OllamaGateway | None = None
    ) -> None:
        self._event_store = event_store or EventStoreRepository()
        self._tmdb_client = tmdb_client or TMDBClient()
        self._ollama_gateway = ollama_gateway or OllamaGateway()

    async def get_personalized_recommendations(self, user_id: str) -> dict:
        # 1. שליפת המועדפים של המשתמש מהמסד
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

    
        catalog_movies = await self._tmdb_client.get_trending_movies(limit=5)

        if not catalog_movies:
            return {"message": "Could not fetch movie catalog for recommendations."}

        catalog_context = ""
        catalog_dict = {}
        for movie in catalog_movies:
            title = movie.get("title")
            catalog_context += f"- {title}\n"
            catalog_dict[title.strip().lower()] = movie

        # 3. Augmentation -
        prompt = (
            f"The user's favorite movie IDs are: {movie_ids}.\n"
            f"Here is a short movie catalog to choose from:\n{catalog_context}\n"
            "Choose exactly 2 movie titles from the catalog above that would fit the user best. "
            "Return ONLY the exact movie titles separated by commas, with no extra text or explanations."
        )

        # 4. 
        ai_response = await self._ollama_gateway.generate_response(prompt)

   
        ai_titles = [t.strip() for t in ai_response.split(",") if t.strip()]

        # 5. TMDB
        detailed_recommendations = []
        for title in ai_titles:
            clean_title = title.lower()
            matched_movie = None
            
            for cat_title, movie_obj in catalog_dict.items():
                if clean_title in cat_title or cat_title in clean_title:
                    matched_movie = movie_obj
                    break

            if matched_movie:
                detailed_recommendations.append({
                    "id": matched_movie.get("id"),
                    "title": matched_movie.get("title"),
                    "overview": matched_movie.get("overview"),
                    "poster_path": f"https://image.tmdb.org/t/p/w500{matched_movie.get('poster_path')}" if matched_movie.get('poster_path') else None
                })

        return {
            "user_id": user_id,
            "recommended_movies": detailed_recommendations
        }
    async def get_user_movie_context(self, user_id: str) -> str:
      
        response = await asyncio.to_thread(
            lambda: self._event_store._client.table("user_favorites")
            .select("movie_id")
            .eq("user_id", user_id)
            .execute()
        )
        
        favorites = response.data
        if not favorites:
            return "The user has no favorite movies yet."

   
        movie_titles = []
        for fav in favorites:
            movie_id = fav["movie_id"]
            try:
            
                movie_details = await self._tmdb_client.get_movie_details(movie_id)
                title = movie_details.get("title")
                if title:
                    movie_titles.append(title)
            except Exception as e:
         
                print(f"Warning: Could not fetch details for movie_id {movie_id} - {str(e)}")

        if not movie_titles:
            return "The user has no favorite movies yet."
            
        return ", ".join(movie_titles)