# Cargar variables de entorno
from dotenv import load_dotenv
import os

# SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar .env
load_dotenv()

# Tomar URL de conexión de las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el motor de SQLAlchemy, que se conecta a PostgreSQL
engine = create_engine(DATABASE_URL)


# Crear sesión local (para hacer queries)
# Crear una "fábrica" de sesiones
# autocommit=False -> no se hace commit automáticamente
# autoflush=False -> no se envían cambios automáticamente
# bind=engine -> la sesión usa nuestro motor
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para declarar tablas con SQLAlchemy ORM
Base = declarative_base()
