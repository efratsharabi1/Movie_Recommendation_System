from fastapi import APIRouter, Depends, HTTPException
from backend.services.rag_service import RAGRecommendationService

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])


def get_rag_service() -> RAGRecommendationService:
    return RAGRecommendationService()


@router.get("/{user_id}")
async def get_recommendations(
    user_id: str,
    rag_service: RAGRecommendationService = Depends(get_rag_service)
):
    try:
        recommendations = await rag_service.get_personalized_recommendations(user_id)
        return {"user_id": user_id, "recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))