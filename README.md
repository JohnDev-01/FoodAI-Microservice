# 📘 Documentación de API — FoodAI FastAPI

> **Base URL de producción:**  
> `https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1`

---

## 🔹 Información general

Esta API está construida con **FastAPI** y conectada a **Supabase** para analizar reservaciones de restaurantes mediante **Inteligencia Artificial (IA)**.  
Permite:
- Entrenar un modelo con datos históricos  
- Predecir si una reserva será confirmada o cancelada  
- Recomendar restaurantes y horarios populares  
- Obtener análisis agregados, como el restaurante más reservado  


---

## ⚙️ Requisitos previos

- Python 3.11 o superior  
- `pip` actualizado (>= 23)  
- (Opcional) Entorno virtual (`venv` o `virtualenv`)  
- (Opcional) Docker, si se desea empaquetar para Lambda

---

## 🚀 Instalación

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/JohnDev-01/FoodAI-Microservice.git
   cd foodai-fastapi
   ```

2. **Crear entorno virtual y activarlo:**
   - macOS / Linux:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```
   - Windows (PowerShell):
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```

3. **Instalar dependencias:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 🔐 Variables de entorno

El archivo `.env` contiene las claves necesarias para conectar con **Supabase**:

| Variable | Descripción |
|-----------|-------------|
| `SUPABASE_URL` | URL del proyecto Supabase |
| `SUPABASE_KEY` | API Key o clave de servicio de Supabase |

Ejemplo:
```bash
cp .env.example .env
```

---

## ⚙️ Endpoints disponibles

| Grupo | Método | Endpoint | Descripción |
|--------|---------|-----------|--------------|
| **IA** | `POST` | `/ia/entrenar` | Entrena el modelo de IA con los datos actuales |
| **IA** | `GET` | `/ia/predecir` | Predice el estado probable de una nueva reservación |
| **IA** | `GET` | `/ia/recomendar` | Sugiere los mejores restaurantes y horarios |
| **Análisis** | `GET` | `/analisis/restaurante-mas-reservado` | Devuelve el restaurante con más reservaciones |
| **Análisis** | `GET` | `/analisis/resumen` | Devuelve estadísticas generales del sistema |
| **Insights** | `GET` | `/restaurants/{restaurant_id}/ai-insights` | Indicadores predictivos completos para un restaurante |

---

## 🧠 Endpoints de Inteligencia Artificial

### 1️⃣ POST `/ia/entrenar`

**Descripción:**  
Entrena el modelo de IA utilizando las reservaciones existentes en la base de datos Supabase.  
Crea y guarda los modelos en el servidor (`RandomForestClassifier` y codificadores `LabelEncoder`).

**URL completa:**
```
https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/ia/entrenar
```

**Método:** `POST`

**Ejemplo de solicitud:**
```bash
curl -X POST "https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/ia/entrenar"
```

**Respuesta exitosa:**
```json
{
  "mensaje": "Modelo entrenado correctamente",
  "precision": 88.5,
  "fecha": "2025-10-18T00:15:04.123Z"
}
```

**Posibles errores:**
```json
{"error": "Ocurrió un error al entrenar el modelo: No hay datos válidos"}
```

---

### 2️⃣ GET `/ia/predecir`

**Descripción:**  
Predice el estado probable de una reservación según los parámetros proporcionados.

**URL completa:**
```
https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/ia/predecir
```

**Método:** `GET`

**Parámetros:**

| Nombre | Tipo | Obligatorio | Descripción |
|--------|------|-------------|--------------|
| `restaurant_id` | string | ✅ | ID del restaurante |
| `invitados` | int | ✅ | Número de personas |
| `hora` | int | ✅ | Hora de la reservación (0–23) |
| `dia_semana` | int | ✅ | Día de la semana (0=Lunes, 6=Domingo) |

**Ejemplo de solicitud:**
```bash
curl -X GET "https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/ia/predecir?restaurant_id=2cbb0ee2-d9c9-4986-a32e-b4326ad2abb5&invitados=4&hora=20&dia_semana=5"
```

**Respuesta exitosa:**
```json
{
  "estado_estimado": "confirmada",
  "confianza": 0.94,
  "hora": 20,
  "dia_semana": 5
}
```

**Errores posibles:**
```json
{"error": "Ocurrió un error al predecir: Modelo no encontrado"}
```

---

### 3️⃣ GET `/ia/recomendar`

**Descripción:**  
Genera recomendaciones de restaurantes y horarios más populares basados en reservaciones confirmadas o completadas.

**URL completa:**
```
https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/ia/recomendar
```

**Método:** `GET`

**Parámetros opcionales:**

| Nombre | Tipo | Descripción |
|--------|------|--------------|
| `top_n` | int | Cantidad de resultados deseados (por defecto = 3) |

**Ejemplo de solicitud:**
```bash
curl -X GET "https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/ia/recomendar?top_n=3"
```

**Respuesta exitosa:**
```json
{
  "mensaje": "Recomendaciones generadas correctamente",
  "mejor_hora_general": 19,
  "sugerencias": [
    {"restaurante": "El Buen Sabor", "hora_recomendada": 20, "reservas_exitosas": 45},
    {"restaurante": "La Parrillada", "hora_recomendada": 19, "reservas_exitosas": 39},
    {"restaurante": "Pasta & Vino", "hora_recomendada": 21, "reservas_exitosas": 25}
  ]
}
```

---

## 📊 Endpoints de Análisis

### 4️⃣ GET `/analisis/restaurante-mas-reservado`

**Descripción:**  
Devuelve el restaurante con más reservaciones registradas en el sistema, junto a sus datos básicos.

**URL completa:**
```
https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/analisis/restaurante-mas-reservado
```

**Ejemplo de solicitud:**
```bash
curl -X GET "https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/analisis/restaurante-mas-reservado"
```

**Respuesta:**
```json
{
  "restaurant_id": "2cbb0ee2-d9c9-4986-a32e-b4326ad2abb5",
  "nombre": "La Casa del Chef",
  "ciudad": "Santo Domingo",
  "tipo_cocina": "Caribeña",
  "valoracion": 4.7,
  "total_reservaciones": 56
}
```

---

### 5️⃣ GET `/analisis/resumen`

**Descripción:**  
Devuelve un resumen general de todas las reservaciones en el sistema, incluyendo totales y estados.

**URL completa:**
```
https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/analisis/resumen
```

**Ejemplo de solicitud:**
```bash
curl -X GET "https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/analisis/resumen"
```

**Respuesta:**
```json
{
  "total_reservaciones": 150,
  "confirmadas": 97,
  "canceladas": 25,
  "pendientes": 18,
  "completadas": 10
}
```

---

## 🧪 Recomendación de uso

1️⃣ Entrenar el modelo con `/ia/entrenar`  
2️⃣ Predecir reservas con `/ia/predecir`  
3️⃣ Obtener recomendaciones con `/ia/recomendar`  
4️⃣ Analizar resultados con `/analisis/*`

---

## 🔮 GET `/restaurants/{restaurant_id}/ai-insights`

**Descripción:**
Entrega en una sola respuesta todos los indicadores predictivos solicitados para un restaurante específico. La API genera insights de demanda, ocupación, cancelaciones, comportamiento de clientes, economía, segmentación, operaciones y estacionalidad usando modelos ligeros (regresiones, suavizados exponenciales y clustering) montados con pandas/scikit-learn.

**URL completa:**
```
https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/restaurants/{restaurant_id}/ai-insights
```

**Ejemplo de solicitud:**
```bash
curl -X GET "https://eqv7ecjeolvi7q5ijpiu7zbaam0npwwf.lambda-url.us-east-1.on.aws/api/v1/restaurants/2cbb0ee2-d9c9-4986-a32e-b4326ad2abb5/ai-insights"
```

**Fragmento de respuesta:**
```json
{
  "restaurant_id": "2cbb0ee2-d9c9-4986-a32e-b4326ad2abb5",
  "generated_at": "2024-06-01T14:25:08.120Z",
  "indicators": {
    "demand_capacity": {
      "next_peak": {
        "datetime": "2024-06-08T20:00:00",
        "insight": "Se espera el próximo pico el sábado 08/06 a las 08:00 PM con 94 % de ocupación."
      },
      "weekday_demand": ["..."],
      "hourly_occupancy": ["..."]
    },
    "cancellations": {
      "cancellation_risk_by_reservation": ["..."],
      "users_prone_to_cancel": ["..."],
      "loyal_customers_forecast": {"expected_next_month": 45}
    }
  }
}
```

Cada bloque de indicadores incluye los ejemplos solicitados en el brief (pico de reservas, ocupación por hora, demanda semanal, probabilidades de cancelación, clientes fieles esperados, ticket promedio, alertas operativas, estacionalidad, etc.).

---

📬 **Soporte:** Para reportar errores o solicitar mejoras, abre un *issue* en el repositorio de GitHub.
