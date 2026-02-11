"""Punto de entrada: crea la app FastAPI y registra rutas."""

import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.core.database import engine
from src.app import models
from src.app.api.routes import health, root, ask

# Cargar variables de entorno
load_dotenv()

# Configurar Google API Key
api_key_env = os.getenv("GOOGLE_API_KEY")
if api_key_env is None:
    print("ADVERTENCIA: No se encontró la clave GOOGLE_API_KEY en el .env")
    os.environ["GOOGLE_API_KEY"] = ""
else:
    os.environ["GOOGLE_API_KEY"] = api_key_env
    print("Clave de Google Gemini cargada correctamente.")

# Crear la app FastAPI
app = FastAPI(
    title="AsistenteBi",
    description="Microservicio de BI con Exploración de Datos Interactiva GenBI",
    version="0.1.0",
)

# Sincronizar tablas
models.Base.metadata.create_all(bind=engine)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(health.router)
app.include_router(root.router)
app.include_router(ask.router)
