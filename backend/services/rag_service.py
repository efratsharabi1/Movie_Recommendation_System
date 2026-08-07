import asyncio
from backend.event_store.repository import EventStoreRepository
from backend.gateway.tmdb_client import TMDBClient
from backend.gateway.ollama_gateway import OllamaGateway

class RAGRecommendationService:
  
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
        # 1. Retrieving favorites
        response = await asyncio.to_thread(
            lambda: self._event_store._client.table("user_favorites")
            .select("movie_id")
            .eq("user_id", user_id)
            .execute()
        )
        
        favorites = response.data
        if not favorites:
            return {"message": "there is no favorites yet. add some movies to get recommendations!"}

       
        movie_ids_str = [str(fav["movie_id"]) for fav in favorites]

        # 2. Retrieving movies similar to the last 3 favorites
        catalog_movies = []
        recent_favorites = movie_ids_str[-3:] if len(movie_ids_str) > 3 else movie_ids_str
        
        for base_movie_id in recent_favorites:
            similar_to_this = await self._tmdb_client.get_similar_movies(int(base_movie_id), limit=5)
            catalog_movies.extend(similar_to_this)

        unique_movies = {movie["id"]: movie for movie in catalog_movies if "id" in movie}
        catalog_movies = list(unique_movies.values())

        if not catalog_movies:
            catalog_movies = await self._tmdb_client.get_trending_movies(limit=10)

        if not catalog_movies:
            return {"message": "Could not fetch movie catalog for recommendations."}

        # 3. sort for the AI
        catalog_context = ""
        catalog_dict = {}
        for movie in catalog_movies:
            current_id_str = str(movie.get("id"))
            title = movie.get("title")
            
          
            if current_id_str in movie_ids_str or not title:
                continue
                
            catalog_context += f"- {title}\n"
            catalog_dict[title.strip().lower()] = movie

        # 4. promt
        prompt = (
            f"Here is a curated catalog of recommended movies for a user:\n{catalog_context}\n"
            "Choose exactly 2 movie titles from the catalog above.\n"
            "Return ONLY the exact movie titles separated by commas, with no extra text."
        )

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