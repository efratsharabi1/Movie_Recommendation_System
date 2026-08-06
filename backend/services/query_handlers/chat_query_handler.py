from backend.gateway.ollama_gateway import OllamaGateway
from backend.services.rag_service import RAGRecommendationService

class ChatQueryHandler:
    def __init__(self):
        self.ollama_gateway = OllamaGateway()
        self.rag_service = RAGRecommendationService()

    async def handle_chat(self, prompt: str, user_id: str) -> dict:
        prompt_lower = prompt.lower()
        
        # identify if the user is asking for personalized recommendations
        is_recommendation = any(word in prompt_lower for word in ["recommend", "המלץ", "המלצה", "מועדפים"])
        
        if is_recommendation:
            # RAG route: personalized recommendations and catalog
            recommendations = await self.rag_service.get_personalized_recommendations(user_id)
            return {"response": recommendations, "source": "ollama (rag)"}
            
        else:
            # general chat route (fulfills requirement 3.4: consultation on concepts)
            system_instruction = (
                "You are an expert movie advisor and a cinematic AI assistant. "
                "Answer the user's questions about movie concepts, genres, directors, "
                "or film history clearly, professionally, and concisely."
            )
            full_prompt = f"{system_instruction}\nUser: {prompt}"
            
            response_text = await self.ollama_gateway.generate_response(full_prompt, max_tokens=200)
            return {"response": response_text, "source": "ollama (consultation)"}