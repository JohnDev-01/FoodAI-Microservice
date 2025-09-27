# FoodAI FastAPI

Servicio API construido con FastAPI para exponer endpoints de salud y predicción relacionados con FoodAI.

## Requisitos previos

- Python 3.11 o superior (se recomienda 3.11)
- `pip` actualizado (versión 23+)
- (Opcional) `virtualenv` o `venv` para aislar dependencias

## Instalación

1. Clona el repositorio y entra en la carpeta del proyecto:
   ```bash
   git clone <https://github.com/JohnDev-01/FoodAI-Microservice.git>
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
     .venv\\Scripts\\Activate.ps1
     ```
3. Instala las dependencias:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Configuración

1. Duplica el archivo `.env` y completa los valores según tu entorno:
   ```bash
   cp .env .env.local
   ```
2. Edita `.env.local` e introduce tu `SUPABASE_URL` y `SUPABASE_KEY` válidos.
3. Exporta las variables antes de ejecutar la API (o renombra `.env.local` a `.env` si usas `python-dotenv`).

## Ejecución de la API

Inicia el servidor de desarrollo con Uvicorn:

```bash
uvicorn app.main:app --reload
```

- La API quedará disponible en `http://127.0.0.1:8000`.
- La documentación interactiva de Swagger se encuentra en `http://127.0.0.1:8000/docs` y la documentación ReDoc en `http://127.0.0.1:8000/redoc`.

## Pruebas

Ejecuta la suite de pruebas con `pytest`:

```bash
pytest
```

## Formato y calidad de código

- Para formatear el código puedes usar `ruff` o `black` si los tienes instalados.
- Si necesitas importar nuevos paquetes, agrégalos en `requirements.txt` y reinstala dependencias.

## Despliegue

- Configura las mismas variables de entorno (`SUPABASE_URL` y `SUPABASE_KEY`) en tu proveedor de infraestructura.
- Ejecuta `uvicorn app.main:app` o utiliza un servidor ASGI como `gunicorn` con `uvicorn` workers para producción.

