import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.cluster import KMeans

# Rutas de guardado
MODELOS_DIR = "app/services/models"
MODELO_PATH = os.path.join(MODELOS_DIR, "modelo_reservas.pkl")
ENCODER_ESTADO_PATH = os.path.join(MODELOS_DIR, "encoder_estado.pkl")
ENCODER_RESTAURANTE_PATH = os.path.join(MODELOS_DIR, "encoder_restaurante.pkl")


class InteligenciaReservas:
    """
    Servicio de IA para analizar y predecir reservaciones de restaurantes.
    Incluye:
      - Predicción de estado (confirmada, cancelada, completada)
      - Recomendaciones de restaurante y horario
    """

    def __init__(self, df_reservas: pd.DataFrame, df_restaurantes: pd.DataFrame = None):
        self.df_reservas = df_reservas
        self.df_restaurantes = df_restaurantes

    # ==========================
    # 🔹 PREPARACIÓN DE DATOS
    # ==========================
    def preparar_datos(self):
        """Limpia los datos y genera las columnas necesarias para el análisis."""
        df = self.df_reservas.copy()

        columnas_requeridas = {"status", "guests_count", "reservation_time", "reservation_date", "restaurant_id"}
        faltantes = columnas_requeridas - set(df.columns)
        if faltantes:
            raise ValueError(f"Faltan columnas necesarias: {faltantes}")

        df = df.dropna(subset=list(columnas_requeridas))
        if df.empty:
            raise ValueError("No hay datos válidos para entrenar o analizar.")

        # Extraer hora y día de la semana
        df["hora"] = pd.to_datetime(df["reservation_time"], errors="coerce").dt.hour.fillna(0).astype(int)
        df["dia_semana"] = pd.to_datetime(df["reservation_date"], errors="coerce").dt.dayofweek.fillna(0).astype(int)
        df["guests_count"] = df["guests_count"].astype(int)

        return df

    # ==========================
    # 🤖 ENTRENAMIENTO
    # ==========================
    def entrenar_modelo(self):
        """Entrena el modelo IA para predecir el estado de las reservaciones."""
        try:
            df = self.preparar_datos()

            # Crear codificadores
            encoder_estado = LabelEncoder()
            encoder_restaurante = LabelEncoder()

            df["estado_cod"] = encoder_estado.fit_transform(df["status"])
            df["restaurante_cod"] = encoder_restaurante.fit_transform(df["restaurant_id"])

            X = df[["restaurante_cod", "hora", "dia_semana", "guests_count"]]
            y = df["estado_cod"]

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            modelo = RandomForestClassifier(n_estimators=150, random_state=42)
            modelo.fit(X_train, y_train)

            y_pred = modelo.predict(X_test)
            precision = accuracy_score(y_test, y_pred)

            os.makedirs(MODELOS_DIR, exist_ok=True)
            joblib.dump(modelo, MODELO_PATH)
            joblib.dump(encoder_estado, ENCODER_ESTADO_PATH)
            joblib.dump(encoder_restaurante, ENCODER_RESTAURANTE_PATH)

            return {
                "mensaje": "Modelo entrenado correctamente",
                "precision": round(precision * 100, 2),
                "fecha": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": f"Ocurrió un error al entrenar el modelo: {str(e)}"}

    # ==========================
    # 🔮 PREDICCIÓN
    # ==========================
    def predecir_estado(self, restaurant_id: str, invitados: int, hora: int, dia_semana: int):
        """Predice si una reserva será confirmada, cancelada o completada."""
        try:
            if not os.path.exists(MODELO_PATH):
                return {"error": "El modelo aún no ha sido entrenado."}

            modelo = joblib.load(MODELO_PATH)
            encoder_estado = joblib.load(ENCODER_ESTADO_PATH)
            encoder_restaurante = joblib.load(ENCODER_RESTAURANTE_PATH)

            try:
                rest_cod = encoder_restaurante.transform([restaurant_id])[0]
            except ValueError:
                rest_cod = 0  # Si no existe, asignar valor por defecto

            entrada = pd.DataFrame([{
                "restaurante_cod": rest_cod,
                "hora": hora,
                "dia_semana": dia_semana,
                "guests_count": invitados
            }])

            pred = modelo.predict(entrada)
            proba = modelo.predict_proba(entrada)

            try:
                estado_predicho = encoder_estado.inverse_transform(pred)[0]
            except Exception:
                estado_predicho = "desconocido"

            return {
                "estado_estimado": estado_predicho,
                "confianza": round(float(np.max(proba)) * 100, 2),
                "hora": hora,
                "dia_semana": dia_semana
            }

        except Exception as e:
            return {"error": f"Ocurrió un error al predecir: {str(e)}"}

    # ==========================
    # 🌟 RECOMENDACIÓN
    # ==========================
    def recomendar(self, top_n: int = 3):
        """
        Recomienda los restaurantes y horarios más exitosos según el historial.
        Retorna los lugares con más reservas confirmadas o completadas.
        """
        try:
            df = self.preparar_datos()

            df_exitos = df[df["status"].isin(["confirmed", "completed"])]
            if df_exitos.empty:
                return {"mensaje": "No hay suficientes datos de éxito para generar recomendaciones."}

            # Agrupar por restaurante y hora
            resumen = (
                df_exitos.groupby(["restaurant_id", "hora"])
                .size()
                .reset_index(name="reservas")
                .sort_values(by="reservas", ascending=False)
            )

            # Agrupar por patrón de horas (usando KMeans)
            kmeans = KMeans(n_clusters=min(3, len(resumen)), random_state=42, n_init=10)
            kmeans.fit(resumen[["hora", "reservas"]])
            resumen["grupo"] = kmeans.labels_

            grupo_top = (
                resumen.groupby("grupo")
                .agg({"hora": "mean", "reservas": "sum"})
                .sort_values("reservas", ascending=False)
                .reset_index()
            )

            mejor_grupo = grupo_top.iloc[0]
            mejores = (
                resumen[resumen["grupo"] == mejor_grupo["grupo"]]
                .sort_values("reservas", ascending=False)
                .head(top_n)
            )

            # Obtener nombres de restaurantes si el df_restaurantes fue pasado
            recomendaciones = []
            for _, fila in mejores.iterrows():
                nombre = fila["restaurant_id"]
                if self.df_restaurantes is not None:
                    nombre_rest = self.df_restaurantes.loc[
                        self.df_restaurantes["id"] == fila["restaurant_id"], "name"
                    ].values
                    if len(nombre_rest) > 0:
                        nombre = nombre_rest[0]

                recomendaciones.append({
                    "restaurante": nombre,
                    "hora_recomendada": int(fila["hora"]),
                    "reservas_exitosas": int(fila["reservas"])
                })

            return {
                "mensaje": "Recomendaciones generadas correctamente",
                "mejor_hora_general": int(mejor_grupo["hora"]),
                "sugerencias": recomendaciones
            }

        except Exception as e:
            return {"error": f"No se pudieron generar recomendaciones: {str(e)}"}
