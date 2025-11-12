"""Servicio de análisis predictivo por restaurante."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib import response

import numpy as np
import pandas as pd

from app.services.supabase_service import SupabaseService


SPANISH_WEEKDAYS = [
    "Lunes",
    "Martes",
    "Miércoles",
    "Jueves",
    "Viernes",
    "Sábado",
    "Domingo",
]


@dataclass
class RestaurantContext:
    restaurant: Dict[str, Any]
    capacity: int
    avg_ticket: float


class RestaurantAIInsightsService:
    """Centraliza la lógica para construir insights predictivos por restaurante."""

    def __init__(self, supabase_service: SupabaseService) -> None:
        self.supabase = supabase_service

    # ------------------------------------------------------------------
    # Público
    # ------------------------------------------------------------------
    def generate_insights(self, restaurant_id: str) -> Dict[str, Any]:
        df = self._fetch_reservations(restaurant_id)
        if df.empty:
            raise ValueError("No hay reservaciones registradas para este restaurante")

        context = self._build_restaurant_context(df, restaurant_id)
        prepared = self._prepare_dataframe(df, context.avg_ticket)

        return {
            "restaurant_id": restaurant_id,
            "restaurant_name": context.restaurant.get("name"),
            "generated_at": datetime.utcnow().isoformat(),
            "indicators": {
                "demand_capacity": self._demand_and_capacity(prepared, context),
                "cancellations": self._cancellation_insights(prepared),
                "timing_behavior": self._timing_behavior(prepared),
                "economics": self._economic_predictions(prepared, context),
                "segmentation": self._segmentation(prepared),
                "operations": self._operational_alerts(prepared, context),
                "trend_seasonality": self._trend_and_seasonality(prepared),
            },
        }

    # ------------------------------------------------------------------
    # Carga y preparación de datos
    # ------------------------------------------------------------------
    def _fetch_reservations(self, restaurant_id: str) -> pd.DataFrame:
       response = (
            self.supabase.client.table("reservations")
            .select("*")
            .eq("restaurant_id", restaurant_id)
           .execute()
       )
       data = response.data or []
       df = pd.DataFrame(data)

       # 🔧 Versión global: eliminar zona horaria de todas las columnas datetime
       for col in df.select_dtypes(include=["datetimetz"]).columns:
        df[col] = df[col].dt.tz_convert(None)

       return df


    def _build_restaurant_context(self, df: pd.DataFrame, restaurant_id: str) -> RestaurantContext:
        restaurant = (
            self.supabase.client.table("restaurants")
            .select("*")
            .eq("id", restaurant_id)
            .single()
            .execute()
        ).data or {}

        # 🔧 Si algún campo del restaurante llega como tz-aware datetime, limpiarlo
        if isinstance(restaurant, dict):
            for key, value in restaurant.items():
                if isinstance(value, pd.Timestamp) and value.tzinfo is not None:
                    restaurant[key] = value.tz_convert(None)

        avg_ticket = self._infer_average_ticket(df, restaurant)
        capacity = self._infer_capacity(df, restaurant)

        return RestaurantContext(restaurant=restaurant, capacity=capacity, avg_ticket=avg_ticket)



    def _prepare_dataframe(self, df: pd.DataFrame, avg_ticket: float) -> pd.DataFrame:
        work = df.copy()

        work["reservation_date"] = work["reservation_date"].astype(str)
        if "reservation_time" in work.columns:
            work["reservation_time"] = work["reservation_time"].astype(str).str.slice(0, 8)
        else:
            work["reservation_time"] = "20:00:00"

        work["reservation_datetime"] = pd.to_datetime(
            work["reservation_date"].str.strip() + " " + work["reservation_time"].str.strip(),
            errors="coerce",
        )
        work = work.dropna(subset=["reservation_datetime"])

        work["weekday"] = work["reservation_datetime"].dt.weekday
        work["hour"] = work["reservation_datetime"].dt.hour
        work["date_only"] = work["reservation_datetime"].dt.date

        guests = pd.to_numeric(work.get("guests_count"), errors="coerce")
        work["guests_count"] = guests.fillna(2).clip(lower=1).astype(int)

        work["status"] = work.get("status", "pending").fillna("pending").str.lower()
        work["is_cancelled"] = work["status"].isin(["cancelled", "canceled"])
        work["is_confirmed"] = work["status"].isin(["confirmed", "completed"])

        created_col = self._first_available_column(
            work,
            ["created_at", "booking_date", "requested_at", "submitted_at"],
        )
        created_series = pd.to_datetime(work[created_col], errors="coerce") if created_col else None

        fallback_lead = np.where(work["status"] == "pending", 1.5, 2.8)
        if created_series is None:
            created_series = work["reservation_datetime"] - pd.to_timedelta(fallback_lead, unit="D")

        work["lead_time_days"] = (
            (work["reservation_datetime"] - created_series).dt.total_seconds() / 86400
        )
        median_lead = (
            float(np.nanmedian(work["lead_time_days"]))
            if not work["lead_time_days"].isna().all()
            else 2.0
        )
        work["lead_time_days"] = work["lead_time_days"].fillna(median_lead).clip(lower=0)

        id_col = self._first_available_column(
            work,
            ["customer_email", "customer_id", "customer_name", "user_id", "id_cliente"],
        )
        work["customer_label"] = work[id_col].astype(str) if id_col else "Cliente"

        amount_col = self._first_available_column(
            work,
            ["total_amount", "amount", "total", "bill_amount", "ticket_amount"],
        )
        if amount_col:
            amounts = pd.to_numeric(work[amount_col], errors="coerce")
            work["expected_revenue"] = amounts.fillna(work["guests_count"] * avg_ticket)
        else:
            work["expected_revenue"] = work["guests_count"] * avg_ticket

        city_col = self._first_available_column(
            work,
            ["customer_city", "city", "customer_location", "province"],
        )
        work["customer_city"] = work[city_col].fillna("Sin dato") if city_col else "Sin dato"

        return work

    # ------------------------------------------------------------------
    # Demanda y capacidad
    # ------------------------------------------------------------------
    def _demand_and_capacity(self, df: pd.DataFrame, context: RestaurantContext) -> Dict[str, Any]:
        peak_info = self._predict_next_peak(df, context.capacity)
        hourly = self._hourly_occupancy(df, context.capacity)
        weekday = self._weekday_demand(df)

        return {
            "next_peak": peak_info,
            "hourly_occupancy": hourly,
            "weekday_demand": weekday,
        }

    def _predict_next_peak(self, df: pd.DataFrame, capacity: int) -> Dict[str, Any]:
        demand_series = (
            df.set_index("reservation_datetime")["guests_count"]
            .resample("1H")
            .sum()
            .rename("guests")
        )
        if demand_series.empty:
            return {"message": "No hay historial suficiente para estimar el próximo pico"}

        smoothed = demand_series.ewm(span=6, adjust=False).mean()
        best_timestamp = smoothed.idxmax()
        best_value = smoothed.max()

        next_occurrence = self._next_occurrence(best_timestamp.weekday(), best_timestamp.hour)
        occupancy = float(min(1.0, best_value / max(capacity, 1)))

        return {
            "datetime": next_occurrence.isoformat(),
            "weekday": SPANISH_WEEKDAYS[next_occurrence.weekday()],
            "hour": f"{next_occurrence.hour:02d}:00",
            "expected_guests": round(float(best_value), 1),
            "expected_occupancy": round(occupancy * 100, 1),
            "insight": (
                f"Se espera el próximo pico el {SPANISH_WEEKDAYS[next_occurrence.weekday()]} "
                f"{next_occurrence.strftime('%d/%m')} a las {next_occurrence.strftime('%I:%M %p')} "
                f"con una ocupación estimada del {round(occupancy * 100, 1)} %."
            ),
        }

    def _hourly_occupancy(self, df: pd.DataFrame, capacity: int) -> List[Dict[str, Any]]:
        if df.empty:
            return []

        hour_daily = df.groupby(["date_only", "hour"])["guests_count"].sum().reset_index()
        hourly_mean = hour_daily.groupby("hour")["guests_count"].mean()

        results: List[Dict[str, Any]] = []
        for hour in range(0, 24):
            guests = float(hourly_mean.get(hour, 0.0))
            occupancy = min(1.0, guests / max(capacity, 1))
            results.append(
                {
                    "hour": f"{hour:02d}:00",
                    "projected_guests": round(guests, 1),
                    "expected_occupancy": round(occupancy * 100, 1),
                }
            )
        return results

    def _weekday_demand(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        weekday_counts = df.groupby("weekday")["guests_count"].sum().reindex(range(7), fill_value=0)
        average = weekday_counts.mean() or 1
        insights: List[Dict[str, Any]] = []
        for idx, value in weekday_counts.items():
            delta = (value / average) - 1
            insights.append(
                {
                    "weekday": SPANISH_WEEKDAYS[idx],
                    "relative_to_avg": round(delta * 100, 1),
                    "insight": self._weekday_text(delta, idx),
                }
            )
        return insights

    # ------------------------------------------------------------------
    # Cancelaciones y fidelidad
    # ------------------------------------------------------------------
    def _cancellation_insights(self, df: pd.DataFrame) -> Dict[str, Any]:
        baseline = float(df["is_cancelled"].mean() or 0.05)
        customer_ratio = df.groupby("customer_label")["is_cancelled"].mean()

        focus_df = df[df["reservation_datetime"] >= datetime.utcnow()].copy()
        if focus_df.empty:
            focus_df = df.sort_values("reservation_datetime", ascending=False).head(5)

        reservation_risk: List[Dict[str, Any]] = []
        for _, row in focus_df.head(5).iterrows():
            history = float(customer_ratio.get(row["customer_label"], baseline))
            lead_factor = 0.2 if row["lead_time_days"] < 1 else (-0.05 if row["lead_time_days"] > 5 else 0.0)
            size_factor = -0.05 if row["guests_count"] >= 6 else 0.05
            status_factor = 0.1 if row["status"] == "pending" else 0.0

            probability = baseline * 0.4 + history * 0.4 + lead_factor + size_factor + status_factor
            probability = float(np.clip(probability, 0.05, 0.95))

            reservation_risk.append(
                {
                    "reservation_id": row.get("id"),
                    "customer": row.get("customer_label"),
                    "scheduled_for": row["reservation_datetime"].isoformat(),
                    "probability": round(probability, 2),
                }
            )

        high_risk_users_series = customer_ratio[customer_ratio >= baseline + 0.1]
        high_risk_list = [
            {
                "customer": idx,
                "cancel_rate": round(float(value), 2),
            }
            for idx, value in high_risk_users_series.sort_values(ascending=False).head(5).items()
        ]

        loyal_forecast = self._loyal_customers_forecast(df)

        return {
            "cancellation_risk_by_reservation": reservation_risk,
            "users_prone_to_cancel": high_risk_list,
            "loyal_customers_forecast": loyal_forecast,
        }

    def _loyal_customers_forecast(self, df: pd.DataFrame) -> Dict[str, Any]:
        df = df.copy()
        df["month"] = df["reservation_datetime"].dt.to_period("M")
        repeats = df.groupby(["month", "customer_label"]).size().reset_index(name="reservations")
        loyal = repeats[repeats["reservations"] >= 2]
        monthly_loyal = loyal.groupby("month")["customer_label"].nunique().sort_index()

        if monthly_loyal.empty:
            baseline = max(int(df["customer_label"].nunique() * 0.2), 1)
            return {
                "expected_next_month": baseline,
                "trend_vs_last_month": 0,
                "insight": "Aún no hay suficientes datos; se estima una base mínima de clientes fieles.",
            }

        numeric_index = np.arange(len(monthly_loyal))
        y = monthly_loyal.values.astype(float)
        if len(y) >= 2:
            slope, intercept = np.polyfit(numeric_index, y, 1)
            forecast = slope * len(y) + intercept
        else:
            forecast = y[-1]

        forecast = max(forecast, 0)
        trend = 0.0
        if len(y) >= 2 and monthly_loyal.iloc[-2] > 0:
            trend = ((monthly_loyal.iloc[-1] - monthly_loyal.iloc[-2]) / monthly_loyal.iloc[-2]) * 100

        return {
            "expected_next_month": int(round(forecast)),
            "trend_vs_last_month": round(trend, 1),
            "insight": (
                f"Se esperan {int(round(forecast))} clientes recurrentes el próximo mes (variación {round(trend, 1)} %)."
            ),
        }

    # ------------------------------------------------------------------
    # Timing
    # ------------------------------------------------------------------
    def _timing_behavior(self, df: pd.DataFrame) -> Dict[str, Any]:
        avg_lead = float(df["lead_time_days"].mean()) if not df.empty else 0.0

        recent_cut = datetime.utcnow() - timedelta(days=30)
        recent = df[df["reservation_datetime"] >= recent_cut]
        previous = df[(df["reservation_datetime"] < recent_cut) & (df["reservation_datetime"] >= recent_cut - timedelta(days=30))]

        trend = 0.0
        if not recent.empty and not previous.empty and previous["lead_time_days"].mean() > 0:
            trend = ((recent["lead_time_days"].mean() - previous["lead_time_days"].mean()) / previous["lead_time_days"].mean()) * 100

        windows = df.groupby("hour").size().sort_values(ascending=False).head(3)
        windows_list = [
            {
                "hour": f"{int(hour):02d}:00",
                "percentage": round((count / df.shape[0]) * 100, 1),
            }
            for hour, count in windows.items()
        ]

        return {
            "average_lead_time_days": round(avg_lead, 2),
            "lead_time_trend_vs_last_month": round(trend, 1),
            "popular_booking_windows": windows_list,
        }

    # ------------------------------------------------------------------
    # Economía
    # ------------------------------------------------------------------
    def _economic_predictions(self, df: pd.DataFrame, context: RestaurantContext) -> Dict[str, Any]:
        today = datetime.utcnow().date()
        weekday_multipliers = self._weekday_multiplier(df)

        daily_series = df.groupby("date_only")["expected_revenue"].sum().sort_index()
        base_daily = daily_series.tail(7).mean() if not daily_series.empty else df["expected_revenue"].mean()
        base_daily = base_daily or (context.avg_ticket * 10)

        revenue_forecast: List[Dict[str, Any]] = []
        for offset in range(7):
            day = today + timedelta(days=offset)
            multiplier = weekday_multipliers.get(day.weekday(), 1.0)
            revenue_forecast.append(
                {
                    "date": day.isoformat(),
                    "projected_revenue": round(base_daily * multiplier, 2),
                }
            )

        ticket_avg = df["expected_revenue"].sum() / max(df["guests_count"].sum(), 1)
        cancellation_impact = self._estimate_cancellation_impact(df)

        return {
            "expected_revenue_next_days": revenue_forecast,
            "expected_ticket": round(ticket_avg, 2),
            "economic_cancellation_risk": cancellation_impact,
        }

    def _estimate_cancellation_impact(self, df: pd.DataFrame) -> Dict[str, Any]:
        focus = df[df["reservation_datetime"] >= datetime.utcnow()].copy()
        if focus.empty:
            focus = df.head(10)

        baseline = float(df["is_cancelled"].mean() or 0.05)
        focus["risk"] = baseline
        impact = float((focus["risk"] * focus["expected_revenue"]).sum())

        return {
            "projected_loss": round(impact, 2),
            "message": f"Se proyecta una pérdida estimada de RD$ {round(impact, 2):,.0f} por cancelaciones probables.",
        }

    # ------------------------------------------------------------------
    # Segmentación
    # ------------------------------------------------------------------
    def _segmentation(self, df: pd.DataFrame) -> Dict[str, Any]:
        planificadores = df[df["lead_time_days"] >= 3]
        espontaneos = df[df["lead_time_days"] < 1]

        count_col = "id" if "id" in df.columns else "reservation_datetime"
        customer_status = df.groupby("customer_label").agg(
            total=(count_col, "count"),
            cancellations=("is_cancelled", "sum"),
        )
        premium_clients = customer_status[
            (customer_status["total"] >= 3) & (customer_status["cancellations"] == 0)
        ]

        city_growth = self._city_growth(df)

        return {
            "customer_segments": {
                "planificadores": int(planificadores.shape[0]),
                "espontaneos": int(espontaneos.shape[0]),
                "premium": int(premium_clients.shape[0]),
            },
            "city_growth": city_growth,
        }

    def _city_growth(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        if "customer_city" not in df.columns or df["customer_city"].nunique() <= 1:
            return []

        df = df.copy()
        df["month"] = df["reservation_datetime"].dt.to_period("M")
        city_month = df.groupby(["customer_city", "month"]).size().reset_index(name="reservations")

        latest_month = city_month["month"].max()
        prev_month = latest_month - 1 if latest_month else None
        if prev_month is None:
            return []

        latest = city_month[city_month["month"] == latest_month]
        prev = city_month[city_month["month"] == prev_month]

        merged = latest.merge(prev, on="customer_city", how="left", suffixes=("_latest", "_prev"))
        merged["reservations_prev"] = merged["reservations_prev"].fillna(0)

        def _growth(row: pd.Series) -> float:
            prev_value = row["reservations_prev"]
            if prev_value == 0:
                return 100.0
            return ((row["reservations_latest"] - prev_value) / prev_value) * 100

        merged["growth"] = merged.apply(_growth, axis=1)
        merged = merged.sort_values("growth", ascending=False).head(3)

        return [
            {"city": row["customer_city"], "growth_pct": round(row["growth"], 1)}
            for _, row in merged.iterrows()
        ]

    # ------------------------------------------------------------------
    # Operaciones
    # ------------------------------------------------------------------
    def _operational_alerts(self, df: pd.DataFrame, context: RestaurantContext) -> Dict[str, Any]:
        slot_profile = df.groupby(["weekday", "hour"])["guests_count"].mean().reset_index()
        slot_profile["occupancy"] = slot_profile["guests_count"] / max(context.capacity, 1)

        high_pressure = slot_profile[slot_profile["occupancy"] >= 0.85]
        low_pressure = slot_profile[slot_profile["occupancy"] <= 0.4]

        add_capacity = [
            {
                "weekday": SPANISH_WEEKDAYS[int(row["weekday"])],
                "hour": f"{int(row['hour']):02d}:00",
                "suggested_extra_tables": int(max(round(row["occupancy"] * 10 - 8), 1)),
            }
            for _, row in high_pressure.head(3).iterrows()
        ]

        promo_slots = [
            {
                "weekday": SPANISH_WEEKDAYS[int(row["weekday"])],
                "hour": f"{int(row['hour']):02d}:00",
                "expected_occupancy": round(row["occupancy"] * 100, 1),
            }
            for _, row in low_pressure.head(3).iterrows()
        ]

        return {
            "extra_capacity_recommendations": add_capacity,
            "low_demand_alerts": promo_slots,
        }

    # ------------------------------------------------------------------
    # Tendencias
    # ------------------------------------------------------------------
    def _trend_and_seasonality(self, df: pd.DataFrame) -> Dict[str, Any]:
        monthly = df.set_index("reservation_datetime").resample("M").size()
        trend_pct = 0.0
        if len(monthly) >= 2 and monthly.iloc[-2] > 0:
            trend_pct = ((monthly.iloc[-1] - monthly.iloc[-2]) / monthly.iloc[-2]) * 100

        seasonality = "Sin datos suficientes"
        if len(monthly) >= 3:
            best_month = monthly.idxmax()
            seasonality = (
                f"Reservas máximas habituales en {best_month.strftime('%B %Y')} con {int(monthly.max())} reservas."
            )

        max_slot = df.groupby(["weekday", "hour"])["guests_count"].sum()
        max_info = {}
        if not max_slot.empty:
            idx = max_slot.idxmax()
            max_info = {
                "weekday": SPANISH_WEEKDAYS[int(idx[0])],
                "hour": f"{int(idx[1]):02d}:00",
            }

        return {
            "monthly_trend_pct": round(float(trend_pct), 1),
            "seasonality_signal": seasonality,
            "max_expected_slot": max_info,
        }

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _infer_average_ticket(self, df: pd.DataFrame, restaurant: Dict[str, Any]) -> float:
        for key in ["avg_ticket", "average_ticket", "ticket_average", "ticket_promedio"]:
            raw = restaurant.get(key)
            if raw:
                return float(raw)

        for column in ["total_amount", "amount", "total", "bill_amount"]:
            if column in df.columns:
                values = pd.to_numeric(df[column], errors="coerce").dropna()
                if not values.empty:
                    return float(values.mean())

        return 1850.0  # RD$ promedio por reserva si no hay dato histórico

    def _infer_capacity(self, df: pd.DataFrame, restaurant: Dict[str, Any]) -> int:
        for key in ["capacity", "seating_capacity", "max_capacity", "tables"]:
            value = restaurant.get(key)
            if isinstance(value, (int, float)) and value > 0:
                return int(value)

        guests = pd.to_numeric(df.get("guests_count"), errors="coerce").dropna()
        if guests.empty:
            return 40

        return int(max(guests.quantile(0.9) * 4, 30))

    def _weekday_text(self, delta: float, weekday_index: int) -> str:
        if delta >= 0.15:
            return f"{SPANISH_WEEKDAYS[weekday_index]} supera el promedio semanal (+{round(delta * 100, 1)} %)."
        if delta <= -0.15:
            return f"{SPANISH_WEEKDAYS[weekday_index]} cae {round(abs(delta) * 100, 1)} % por debajo del promedio."
        return f"{SPANISH_WEEKDAYS[weekday_index]} se mantiene cercano al promedio semanal."

    def _weekday_multiplier(self, df: pd.DataFrame) -> Dict[int, float]:
        weekday_totals = df.groupby("weekday")["expected_revenue"].sum().reindex(range(7), fill_value=0)
        avg = weekday_totals.mean() or 1
        return {idx: (value / avg) if avg else 1.0 for idx, value in weekday_totals.items()}

    def _first_available_column(self, df: pd.DataFrame, candidates: List[str]) -> Optional[str]:
        for column in candidates:
            if column in df.columns:
                return column
        return None

    def _next_occurrence(self, weekday: int, hour: int) -> datetime:
        now = datetime.utcnow()
        days_ahead = (weekday - now.weekday()) % 7
        candidate = datetime.combine(now.date(), datetime.min.time()) + timedelta(days=days_ahead, hours=hour)
        if candidate <= now:
            candidate += timedelta(days=7)
        return candidate


# Desactivar advertencias de pandas por copias encadenadas (para no saturar logs)
pd.options.mode.chained_assignment = None  # type: ignore[attr-defined]
