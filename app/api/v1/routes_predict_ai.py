from fastapi import APIRouter, Query
import pandas as pd
from app.services.supabase_service import SupabaseService
from app.services.ai_service import InteligenciaReservas

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"])
supabase = SupabaseService()

# ==========================
# 🔹 ENTRENAR MODELO
# ==========================
@router.post("/entrenar")
def entrenar_modelo():
    """
    Entrena el modelo de inteligencia artificial con las reservaciones actuales.
    """
    print("Iniciando entrenamiento del modelo de IA...")
    try:
        df_reservas = supabase.get_reservations_df()
        df_restaurantes = supabase.client.table("restaurants").select("id, name").execute().data

        df_restaurantes = None if not df_restaurantes else \
            supabase.client.table("restaurants").select("id, name").execute().data

        ai = InteligenciaReservas(pd.DataFrame(df_reservas), pd.DataFrame(df_restaurantes))
        return ai.entrenar_modelo()
    except Exception as e:
        return {"error": f"Ocurrió un error al entrenar el modelo: {str(e)}"}


# ==========================
# 🔹 PREDECIR ESTADO
# ==========================
@router.get("/predecir")
def predecir_estado(
    restaurant_id: str,
    invitados: int,
    hora: int = Query(..., ge=0, le=23, description="Hora de la reservación (0-23)"),
    dia_semana: int = Query(..., ge=0, le=6, description="Día de la semana (0=Lunes, 6=Domingo)")
):
    """
    Predice si una reservación será confirmada, cancelada o completada.
    """
    try:
        df_reservas = supabase.get_reservations_df()
        ai = InteligenciaReservas(pd.DataFrame(df_reservas))
        return ai.predecir_estado(restaurant_id, invitados, hora, dia_semana)
    except Exception as e:
        return {"error": f"Ocurrió un error al predecir: {str(e)}"}


# ==========================
# 🔹 RECOMENDAR RESTAURANTE Y HORARIO
# ==========================
@router.get("/recomendar")
def recomendar(top_n: int = 3):
    """
    Genera recomendaciones de restaurantes y horarios más populares
    según las reservaciones confirmadas o completadas.
    """
    try:
        df_reservas = supabase.get_reservations_df()
        df_restaurantes = supabase.client.table("restaurants").select("id, name").execute().data

        df_reservas = pd.DataFrame(df_reservas)
        df_restaurantes = pd.DataFrame(df_restaurantes) if df_restaurantes else None

        ai = InteligenciaReservas(df_reservas, df_restaurantes)
        return ai.recomendar(top_n)
    except Exception as e:
        return {"error": f"Ocurrió un error al generar recomendaciones: {str(e)}"}
