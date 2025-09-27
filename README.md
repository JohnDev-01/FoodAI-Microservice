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

- Actualiza `.firebaserc` con el `projectId` de Firebase que ya tienes enlazado a GitHub.
- Define las variables `SUPABASE_URL` y `SUPABASE_KEY` en la sección de *Environment variables* de Firebase App Hosting para que Cloud Run las tenga disponibles.
- El archivo `firebase.json` apunta a la `Dockerfile` incluida en este repositorio. Firebase App Hosting construirá la imagen automáticamente en cada confirmación.
- La `Dockerfile` expone el servicio con Uvicorn en el puerto determinado por Cloud Run (`$PORT`). Si haces cambios en dependencias o comandos de arranque, actualiza este archivo.
- Cuando Firebase termine el build podrás ver la versión desplegada desde App Hosting o promovida a producción según tu flujo de trabajo.
