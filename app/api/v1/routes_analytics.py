# app/api/v1/routes_analytics.py
from fastapi import APIRouter
from app.services.supabase_service import SupabaseService

router = APIRouter(prefix="/analisis", tags=["Analisis"])
supabase_service = SupabaseService()

@router.get("/restaurante-mas-reservado")
def most_booked_restaurant():
    """Devuelve el restaurante con más reservaciones"""
    return supabase_service.get_most_booked_restaurant()

@router.get("/resumen")
def summary():
    """Estadísticas generales de las reservaciones"""
    return supabase_service.get_summary()
