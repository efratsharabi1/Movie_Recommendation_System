import httpx
from backend.config import settings

class OpenAIGateway:
    def __init__(self):
        self.url = "https://api.openai.com/v1/chat/completions"
        self.api_key = getattr(settings, "openai_api_key", None)

    async def generate_response(self, system_prompt: str, user_prompt: str) -> str | None:
        if not self.api_key:
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-4o-mini", 
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 150
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(self.url, headers=headers, json=payload)
                res.raise_for_status()
                return res.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"OpenAI Gateway Error: {e}")
            return None