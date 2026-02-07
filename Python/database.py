# Cargar variables de entorno
from dotenv import load_dotenv
import os

# importamos my SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar .env (el archivo donde tenemos la url de la base de datos 
# protegida porque está en gitignore)
load_dotenv()

# Tomar URL de conexión de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL")

# Crear el motor de SQLAlchemy, que se conecta a PostgreSQL
engine = create_engine(DATABASE_URL)


# Crear sesión local (para hacer preguntas)
# Crear una "fábrica" de sesiones
# autocommit=False -> no se hace commit (se envían) automáticamente
# autoflush=False -> no se envían cambios automáticamente
# bind=engine -> la sesión usa nuestro motor
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base para declarar tablas con SQLAlchemy ORM
Base = declarative_base()
