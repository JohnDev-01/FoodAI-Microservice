# FoodAI FastAPI

Servicio API construido con FastAPI y Mangum para exponer endpoints de salud y una predicción sencilla de demanda para FoodAI. El proyecto está preparado para ejecutarse localmente con Uvicorn y para empaquetarse como función de AWS Lambda mediante la imagen oficial de Python.

## Requisitos previos

- Python 3.11 o superior (se recomienda 3.11)
- `pip` actualizado (versión 23+)
- (Opcional) `virtualenv` o `venv` para aislar dependencias
- (Opcional) Docker si deseas construir la imagen para Lambda

## Instalación

1. Clona el repositorio y entra en la carpeta del proyecto:
   ```bash
   git clone https://github.com/JohnDev-01/FoodAI-Microservice.git
   cd foodai-fastapi
   ```
2. Crea y activa un entorno virtual (opcional pero recomendado):
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
3. Instala las dependencias:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Variables de entorno

El archivo `.env` (ignorado en git) almacena los valores sensibles necesarios para conectarse a Supabase.

| Variable         | Descripción                                       |
| ---------------- | ------------------------------------------------- |
| `SUPABASE_URL`   | URL del proyecto Supabase                         |
| `SUPABASE_KEY`   | Clave de servicio o API Key de Supabase           |

Puedes duplicar el archivo de ejemplo y personalizarlo:
```bash
cp .env .env.local
```
Completa `SUPABASE_URL` y `SUPABASE_KEY` y, si usas `python-dotenv`, renombra `.env.local` a `.env` o exporta las variables en tu shell.

## Estructura del proyecto

```text
app/
├── api/
│   └── v1/
│       ├── routes_health.py      # Endpoints de health check
│       └── routes_predict.py     # Endpoint de predicción
├── models/
│   └── predict.py                # Modelos Pydantic de entrada/salida
├── services/
│   └── predictor.py              # Lógica de cálculo de demanda
└── main.py                       # App FastAPI y adaptador Mangum
```

## Ejecución local

Inicia el servidor de desarrollo con Uvicorn:
```bash
uvicorn app.main:app --reload
```
La API queda disponible en `http://127.0.0.1:8000`.

## Documentación interactiva

FastAPI expone automáticamente dos interfaces:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints principales

### GET `/api/v1/health`
Devuelve el estado general del servicio.

### GET `/api/v1/ok`
Confirma que la API se encuentra en funcionamiento.

### POST `/api/v1/predict`
Calcula una predicción de demanda basándose en día de la semana, si es feriado y temperatura ambiente.

Ejemplo de solicitud:
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -d '{
        "day_of_week": 4,
        "is_holiday": false,
        "temperature_c": 22.5
      }'
```
Respuesta esperada:
```json
{
  "demand": 92.25
}
```

## Pruebas automatizadas

Ejecuta la suite con `pytest`:
```bash
pytest
```

## Calidad y estilo de código

- Para formatear el código puedes usar herramientas como `ruff`, `black` o `isort`.
- Añade dependencias nuevas en `requirements.txt` y vuelve a ejecutar `pip install -r requirements.txt`.

## Uso con Docker (Lambda Runtime)

La `Dockerfile` utiliza la imagen base `public.ecr.aws/lambda/python:3.11` y expone el handler `app.main.handler` para AWS Lambda.

Construye la imagen:
```bash
docker build -t foodai-fastapi-lambda .
```
Prueba la función de forma local con el runtime Lambda (puerto 9000):
```bash
docker run --rm -p 9000:8080 foodai-fastapi-lambda
```
Y realiza una invocación de ejemplo:
```bash
curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
  -d '{"path": "/api/v1/health", "httpMethod": "GET", "headers": {}, "queryStringParameters": null, "body": null, "isBase64Encoded": false}'
```

## Despliegue sugerido

1. Publica la imagen en Amazon ECR o en un registro privado.
2. Crea una función Lambda basada en contenedores apuntando a esa imagen.
3. Configura las variables de entorno (`SUPABASE_URL`, `SUPABASE_KEY`) desde la consola de AWS.
4. Expón la función mediante API Gateway o Lambda Function URL para que la API sea accesible públicamente.

## Contribución

- Abre un issue describiendo la mejora o corrección.
- Crea un branch, realiza tus cambios y abre un Pull Request con la descripción y pasos de prueba.

---

Para dudas adicionales o soporte, crea un issue en el repositorio.
