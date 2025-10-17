# 🧠 FoodAI FastAPI

Servicio API construido con **FastAPI** y **Mangum**, diseñado para exponer endpoints de salud, predicción de demanda y análisis inteligente de reservaciones de restaurantes.  
Está preparado para ejecutarse localmente con **Uvicorn** o desplegarse como **función Lambda en AWS** mediante contenedores.

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

## 📁 Estructura del proyecto

```text
app/
├── api/
│   └── v1/
│       ├── routes_health.py          # Endpoints de salud
│       ├── routes_predict.py         # Predicción de demanda
│       ├── routes_predict_ai.py      # IA: predicción y recomendación
│       └── routes_analytics.py       # Análisis y reportes
├── services/
│   ├── predictor.py                  # Lógica de predicción clásica
│   ├── ai_service.py                 # Lógica de IA con Supabase
│   └── supabase_service.py           # Conexión y consultas a Supabase
├── models/
│   └── predict.py                    # Modelos Pydantic
└── main.py                           # Inicialización FastAPI + Mangum
```

---

## ▶️ Ejecución local

```bash
uvicorn app.main:app --reload
```
API disponible en: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 📖 Documentación interactiva

FastAPI expone dos interfaces:
- Swagger UI → [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc → [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## ⚡ Endpoints Principales

### 🔹 GET `/api/v1/health`
Verifica el estado general del servicio.

### 🔹 GET `/api/v1/ok`
Confirma que el servidor FastAPI está operativo.

### 🔹 POST `/api/v1/predict`
Predice demanda de clientes según día, temperatura y feriado.

**Ejemplo:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/predict"   -H "Content-Type: application/json"   -d '{"day_of_week": 4, "is_holiday": false, "temperature_c": 22.5}'
```

**Respuesta:**
```json
{"demand": 92.25}
```

---

## 🤖 Endpoints de Inteligencia Artificial

### 🔹 POST `/api/v1/ia/entrenar`
Entrena el modelo de IA con las reservaciones actuales.

### 🔹 GET `/api/v1/ia/predecir`
Predice el estado de una reservación.

### 🔹 GET `/api/v1/ia/recomendar`
Recomienda los restaurantes y horarios más exitosos.

---

## 📊 Endpoint de Análisis

### 🔹 GET `/api/v1/analisis/restaurante-mas-reservado`
Devuelve el restaurante con más reservaciones, su nombre, tipo de cocina y ciudad.

**Ejemplo:**
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/analisis/restaurante-mas-reservado"
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
