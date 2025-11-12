from fastapi import APIRouter, HTTPException

from app.services.restaurant_insights_service import RestaurantAIInsightsService
from app.services.supabase_service import SupabaseService


router = APIRouter(prefix="/restaurants", tags=["Restaurant Insights"])

supabase_service = SupabaseService()
insights_service = RestaurantAIInsightsService(supabase_service)


@router.get("/{restaurant_id}/ai-insights")
async def get_restaurant_ai_insights(restaurant_id: str):
    """Retorna todos los indicadores predictivos para un restaurante."""
    try:
        return insights_service.generate_insights(restaurant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - FastAPI manejará los errores
        raise HTTPException(status_code=500, detail=f"Error generando insights: {exc}") from exc
