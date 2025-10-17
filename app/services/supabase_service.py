from supabase import create_client, Client
from app.core.config import settings
import pandas as pd

class SupabaseService:
    def __init__(self):
        self.client: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

    def get_reservations(self):
        response = self.client.table("reservations").select("*").execute()
        return response.data

    def get_most_booked_restaurant(self):
      """
      Retorna el restaurante con más reservaciones, incluyendo su nombre.
      """
      try:
            # Obtener todas las reservaciones
            data = self.get_reservations()
            if not data:
                  return {"mensaje": "No hay reservaciones registradas."}

            # Contar cuántas veces aparece cada restaurante
            from collections import Counter
            restaurant_ids = [r["restaurant_id"] for r in data if r.get("restaurant_id")]
            if not restaurant_ids:
                  return {"mensaje": "No hay datos válidos de restaurantes en las reservaciones."}

            count = Counter(restaurant_ids)
            mas_comun = count.most_common(1)[0]  # (id, total)

            # Obtener los datos del restaurante desde Supabase
            restaurante_data = (
                  self.client.table("restaurants")
                  .select("id, name, city, cuisine_type, rating")
                  .eq("id", mas_comun[0])
                  .execute()
            )

            if restaurante_data.data:
                  restaurante = restaurante_data.data[0]
                  return {
                        "restaurant_id": restaurante["id"],
                        "nombre": restaurante["name"],
                        "ciudad": restaurante.get("city"),
                        "tipo_cocina": restaurante.get("cuisine_type"),
                        "valoracion": restaurante.get("rating"),
                        "total_reservaciones": mas_comun[1],
                  }
            else:
                  # Si no se encuentra el restaurante (caso raro)
                  return {
                        "restaurant_id": mas_comun[0],
                        "nombre": "Desconocido",
                        "total_reservaciones": mas_comun[1],
                  }

      except Exception as e:
            return {"error": f"Ocurrió un error al obtener el restaurante con más reservas: {str(e)}"}

    def get_summary(self):
        data = self.get_reservations()
        if not data:
            return None

        total = len(data)
        confirmed = sum(1 for r in data if r["status"] == "confirmed")
        completed = sum(1 for r in data if r["status"] == "completed")
        cancelled = sum(1 for r in data if r["status"] == "cancelled")

        avg_guests = sum(r["guests_count"] for r in data) / total if total else 0

        return {
            "total_reservations": total,
            "confirmed": confirmed,
            "completed": completed,
            "cancelled": cancelled,
            "average_guests": round(avg_guests, 2),
        }
    def get_reservations_df(self) -> pd.DataFrame:
        """Obtiene las reservaciones desde Supabase como DataFrame."""
        response = self.client.table("reservations").select("*").execute()
        data = response.data
        return pd.DataFrame(data)