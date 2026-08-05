import httpx
from fastapi import HTTPException

class OllamaGateway:
    def __init__(self):
        self.url = "http://ollama:11434/api/generate"

    async def generate_response(self, full_prompt: str, max_tokens: int = 150) -> str:
        payload = {
            "model": "llama3",
            "prompt": full_prompt,
            "stream": False,
            "options": {"num_predict": max_tokens}
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(self.url, json=payload)
                res.raise_for_status()
                return res.json().get("response", "")
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Ollama connection failed: {str(exc)}")