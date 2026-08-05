from backend.gateway.tmdb_client import TMDBClient

class SearchMoviesQueryHandler:
    def __init__(self):
        self.tmdb_client = TMDBClient()

    def handle_search(self, query: str) -> list[dict]:
        if not query or query.strip() == "":
            return []
            
        # Call to Gateway to get the results
        results = self.tmdb_client.search_movies(query)
        
        # Add filtering or data processing if needed
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