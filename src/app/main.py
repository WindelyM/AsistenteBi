# Importar librerías
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importar rutas
from app.api.routes import health, root, ask
from app.core.database import engine
from app import models
from app.core.settings import settings

# Crear la aplicación FastAPI
def create_app() -> FastAPI:
    # Sincronizar tablas
    models.Base.metadata.create_all(bind=engine)
    
    # Auto-Seed: Si no hay categorías, poblamos la base de datos (ideal para Docker)
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    try:
        db = SessionLocal()
        # Verificar si la base de datos está vacía sin mantener la sesión abierta
        is_empty = False
        try:
            is_empty = db.query(models.Categoria).count() == 0
        finally:
            db.close()
        
        if is_empty:
            print("Base de datos vacía detectada. Iniciando carga de datos de ejemplo (Seed)...")
            from app.seed import populate_db
            populate_db()
            print("Datos de ejemplo cargados correctamente.")
    except Exception as e:
        print(f"Error en auto-seed: {e}")

    # Configurar Google API Key en el entorno para LangChain
    if settings.google_api_key:
        os.environ["GOOGLE_API_KEY"] = settings.google_api_key
        print("Clave de Google Gemini cargada correctamente.")
    else:
        print("ADVERTENCIA: No se encontró la clave GOOGLE_API_KEY")

    # Configurar FastAPI
    app = FastAPI(
        title=settings.app_name,
        description="Microservicio de BI con Exploración de Datos Interactiva GenBI",
        version="0.1.0",
        debug=settings.app_debug,
    )

    # CORS (permisos para que el front pueda comunicarse con el back)
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

    return app

# Crear la aplicación
app = create_app()
