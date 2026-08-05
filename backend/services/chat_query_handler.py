from backend.gateway.openai_gateway import OpenAIGateway
from backend.gateway.ollama_gateway import OllamaGateway
from backend.services.rag_service import RAGRecommendationService

class ChatQueryHandler:
    def __init__(self):
        self.openai_gateway = OpenAIGateway()
        self.ollama_gateway = OllamaGateway()
        self.rag_service = RAGRecommendationService()

    async def handle_chat(self, prompt: str, user_id: str) -> dict:
        prompt_lower = prompt.lower()
        
        # Check if the user is asking for recommendations
        is_recommendation = any(word in prompt_lower for word in ["recommend", "המלץ", "המלצה", "מועדפים"])
        
        if is_recommendation:
            # --- Route 1: Recommendations based on RAG through Ollama ---
            local_context = await self.rag_service.get_user_movie_context(user_id)
            short_prompt = f"User favorites: {local_context}. Recommend 3 movies based on this. Request: {prompt}"
            
            response_text = await self.ollama_gateway.generate_response(short_prompt, max_tokens=100)
            return {"response": response_text, "source": "ollama (rag)"}
            
        else:
            # --- Route 2: General chat (try OpenAI, fallback to Ollama) ---
            system_instruction = "You are a brief movie advisor. Keep answers under 3 sentences."
            
            # Try 1: OpenAI
            response_text = await self.openai_gateway.generate_response(system_instruction, prompt)
            if response_text:
                return {"response": response_text, "source": "openai"}
                
            # Try 2: Ollama as backup
            full_prompt = f"{system_instruction}\nUser: {prompt}"
            response_text = await self.ollama_gateway.generate_response(full_prompt, max_tokens=150)
            return {"response": response_text, "source": "ollama (fallback)"}