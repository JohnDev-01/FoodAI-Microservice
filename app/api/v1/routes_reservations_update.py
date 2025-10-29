# app/api/v1/routes_reservations_update.py
from fastapi import APIRouter, HTTPException, Body
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, Field, validator
from app.services.supabase_service import SupabaseService
from app.services.email_sender import send_email_via_api
from app.models.email import EmailRequest

router = APIRouter(prefix="/reservations", tags=["Reservations Management"])
supabase_service = SupabaseService()

# Modelo para actualizar fecha y hora
class RescheduleReservation(BaseModel):
    reservation_date: str = Field(..., description="Nueva fecha (YYYY-MM-DD)")
    reservation_time: str = Field(..., description="Nueva hora (HH:MM)")
    reason: Optional[str] = Field(None, description="Motivo del cambio")
    
    @validator('reservation_date')
    def validate_date(cls, v):
        """Validar que la fecha no sea pasada"""
        try:
            new_date = datetime.strptime(v, "%Y-%m-%d").date()
            if new_date < datetime.now().date():
                raise ValueError("No se pueden hacer reservaciones en fechas pasadas")
            if new_date > (datetime.now().date() + timedelta(days=90)):
                raise ValueError("No se pueden hacer reservaciones con más de 90 días de anticipación")
            return v
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD")
            raise e
    
    @validator('reservation_time')
    def validate_time(cls, v):
        """Validar formato y horario del restaurante"""
        try:
            time_obj = datetime.strptime(v, "%H:%M").time()
            hour = time_obj.hour
            
            # Validar horario del restaurante (12pm - 10pm)
            if hour < 12 or hour >= 22:
                raise ValueError("El horario de reservación debe ser entre 12:00 PM y 10:00 PM")
            
            # Solo permitir reservas en intervalos de 30 minutos
            if time_obj.minute not in [0, 30]:
                raise ValueError("Las reservaciones solo están disponibles en intervalos de 30 minutos (:00 o :30)")
            
            return f"{v}:00"  # Agregar segundos para compatibilidad con DB
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError("Formato de hora inválido. Use HH:MM (24 horas)")
            raise e

@router.put("/{reservation_id}/reschedule")
async def reschedule_reservation(
    reservation_id: str,
    reschedule_data: RescheduleReservation = Body(...)
):
    """
    Modificar fecha y hora de una reservación existente con validaciones y notificaciones.
    
    Validaciones incluidas:
    - No permite fechas pasadas
    - No permite cambios con menos de 24 horas de anticipación
    - Verifica horario del restaurante (12pm-10pm)
    - Verifica disponibilidad del restaurante
    - Envía notificaciones por email
    """
    try:
        # 1. Obtener la reservación actual
        current_reservation = supabase_service.client.table("reservations")\
            .select("*, restaurants(name, email)")\
            .eq("id", reservation_id)\
            .single()\
            .execute()
        
        if not current_reservation.data:
            raise HTTPException(status_code=404, detail="Reservación no encontrada")
        
        reservation_data = current_reservation.data
        
        # 2. Validar que la reservación esté activa
        if reservation_data["status"] in ["cancelled", "completed"]:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede modificar una reservación {reservation_data['status']}"
            )
        
        # 3. Validar tiempo mínimo de anticipación (24 horas)
        original_datetime = datetime.strptime(
            f"{reservation_data['reservation_date']} {reservation_data['reservation_time']}", 
            "%Y-%m-%d %H:%M:%S"
        )
        
        if original_datetime - datetime.now() < timedelta(hours=24):
            raise HTTPException(
                status_code=400,
                detail="No se pueden modificar reservaciones con menos de 24 horas de anticipación"
            )
        
        # 4. Verificar disponibilidad (simplificado - en producción verificarías contra otras reservas)
        new_datetime = datetime.strptime(
            f"{reschedule_data.reservation_date} {reschedule_data.reservation_time}", 
            "%Y-%m-%d %H:%M:%S"
        )
        
        # Verificar que no sea el mismo horario
        if new_datetime == original_datetime:
            raise HTTPException(
                status_code=400,
                detail="La nueva fecha y hora son iguales a las actuales"
            )
        
        # 5. Buscar conflictos con otras reservaciones
        conflicts = supabase_service.client.table("reservations")\
            .select("id")\
            .eq("restaurant_id", reservation_data["restaurant_id"])\
            .eq("reservation_date", reschedule_data.reservation_date)\
            .eq("reservation_time", reschedule_data.reservation_time)\
            .eq("status", "confirmed")\
            .neq("id", reservation_id)\
            .execute()
        
        if conflicts.data and len(conflicts.data) > 0:
            # En un sistema real, aquí verificarías capacidad del restaurante
            # Por ahora, solo advertimos si hay muchas reservas
            if len(conflicts.data) >= 5:
                raise HTTPException(
                    status_code=409,
                    detail="Este horario tiene alta demanda. Por favor seleccione otro horario"
                )
        
        # 6. Actualizar la reservación
        update_data = {
            "reservation_date": reschedule_data.reservation_date,
            "reservation_time": reschedule_data.reservation_time,
            "updated_at": datetime.now().isoformat(),
            "modification_reason": reschedule_data.reason,
            "last_modified_date": reservation_data["reservation_date"],
            "last_modified_time": reservation_data["reservation_time"]
        }
        
        updated_reservation = supabase_service.client.table("reservations")\
            .update(update_data)\
            .eq("id", reservation_id)\
            .execute()
        
        if not updated_reservation.data:
            raise HTTPException(status_code=500, detail="Error al actualizar la reservación")
        
        # 7. Preparar datos para emails
        restaurant_name = reservation_data.get("restaurants", {}).get("name", "Restaurante")
        customer_email = reservation_data.get("customer_email", "")
        customer_name = reservation_data.get("customer_name", "Cliente")
        
        # 8. Enviar email al cliente
        if customer_email:
            email_subject = f"Cambio de fecha/hora - Reservación en {restaurant_name}"
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2 style="color: #2c3e50;">Tu reservación ha sido modificada</h2>
                
                <p>Hola {customer_name},</p>
                
                <p>Te confirmamos que tu reservación ha sido actualizada exitosamente.</p>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="color: #28a745;">Nueva fecha y hora:</h3>
                    <ul>
                        <li><strong>Fecha:</strong> {reschedule_data.reservation_date}</li>
                        <li><strong>Hora:</strong> {reschedule_data.reservation_time[:5]}</li>
                        <li><strong>Restaurante:</strong> {restaurant_name}</li>
                        <li><strong>Personas:</strong> {reservation_data.get('guests_count', 'N/A')}</li>
                    </ul>
                </div>
                
                <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h4 style="color: #856404;">Fecha y hora anterior:</h4>
                    <ul>
                        <li><strong>Fecha:</strong> {reservation_data['reservation_date']}</li>
                        <li><strong>Hora:</strong> {reservation_data['reservation_time'][:5]}</li>
                    </ul>
                </div>
                
                {f'<p><strong>Motivo del cambio:</strong> {reschedule_data.reason}</p>' if reschedule_data.reason else ''}
                
                <p style="color: #6c757d; font-size: 14px; margin-top: 30px;">
                    Si necesitas hacer cambios adicionales, hazlo con al menos 24 horas de anticipación.
                    Para cancelar tu reservación, contacta al restaurante directamente.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
                
                <p style="color: #999; font-size: 12px;">
                    Este es un correo automático de FoodAI. Por favor no respondas a este mensaje.
                </p>
            </body>
            </html>
            """
            
            try:
                email_request = EmailRequest(
                    to=customer_email,
                    subject=email_subject,
                    html=email_body
                )
                await send_email_via_api(email_request)
            except Exception as e:
                print(f"Error enviando email al cliente: {e}")
        
        # 9. Enviar notificación al restaurante
        restaurant_email = reservation_data.get("restaurants", {}).get("email")
        if restaurant_email:
            restaurant_subject = f"Modificación de reservación - {customer_name}"
            restaurant_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Notificación de cambio en reservación</h2>
                
                <p>Una reservación ha sido modificada en su restaurante.</p>
                
                <h3>Detalles del cambio:</h3>
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Cliente:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{customer_name}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Nueva fecha:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{reschedule_data.reservation_date}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Nueva hora:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{reschedule_data.reservation_time[:5]}</td>
                    </tr>
                    <tr>
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Personas:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{reservation_data.get('guests_count', 'N/A')}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Fecha anterior:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{reservation_data['reservation_date']}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="border: 1px solid #ddd; padding: 8px;"><strong>Hora anterior:</strong></td>
                        <td style="border: 1px solid #ddd; padding: 8px;">{reservation_data['reservation_time'][:5]}</td>
                    </tr>
                </table>
                
                {f'<p><strong>Motivo:</strong> {reschedule_data.reason}</p>' if reschedule_data.reason else ''}
                
                <p style="color: #666; font-size: 14px;">
                    ID de reservación: {reservation_id}
                </p>
            </body>
            </html>
            """
            
            try:
                email_request = EmailRequest(
                    to=restaurant_email,
                    subject=restaurant_subject,
                    html=restaurant_body
                )
                await send_email_via_api(email_request)
            except Exception as e:
                print(f"Error enviando email al restaurante: {e}")
        
        # 10. Retornar respuesta exitosa
        return {
            "success": True,
            "message": "Reservación actualizada exitosamente",
            "reservation_id": reservation_id,
            "old_datetime": {
                "date": reservation_data['reservation_date'],
                "time": reservation_data['reservation_time'][:5]
            },
            "new_datetime": {
                "date": reschedule_data.reservation_date,
                "time": reschedule_data.reservation_time[:5]
            },
            "emails_sent": {
                "customer": bool(customer_email),
                "restaurant": bool(restaurant_email)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@router.get("/{reservation_id}/availability")
async def check_availability(
    reservation_id: str,
    date: str,
    time: str
):
    """
    Verificar disponibilidad antes de modificar una reservación.
    Útil para el frontend para validar antes de enviar el cambio.
    """
    try:
        # Obtener datos de la reservación
        reservation = supabase_service.client.table("reservations")\
            .select("restaurant_id")\
            .eq("id", reservation_id)\
            .single()\
            .execute()
        
        if not reservation.data:
            raise HTTPException(status_code=404, detail="Reservación no encontrada")
        
        # Verificar conflictos
        conflicts = supabase_service.client.table("reservations")\
            .select("id")\
            .eq("restaurant_id", reservation.data["restaurant_id"])\
            .eq("reservation_date", date)\
            .eq("reservation_time", f"{time}:00")\
            .in_("status", ["confirmed", "pending"])\
            .neq("id", reservation_id)\
            .execute()
        
        available = len(conflicts.data) < 5  # Máximo 5 reservas por slot
        
        return {
            "available": available,
            "date": date,
            "time": time,
            "existing_reservations": len(conflicts.data),
            "message": "Horario disponible" if available else "Este horario tiene alta demanda"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verificando disponibilidad: {str(e)}")