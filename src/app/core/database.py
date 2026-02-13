# Importar librerías
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Importar configuración
from app.core.settings import settings

# Crear motor de base de datos
engine = create_engine(settings.database_url)

# Crear sesión de base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear modelo base
Base = declarative_base()


# Función para obtener sesión de BD
def get_db():
    """Dependencia FastAPI que provee una sesión de BD."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
