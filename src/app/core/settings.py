"""Carga configuración (APP_*) desde variables de entorno."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Configuración centralizada de la aplicación."""

    APP_NAME: str = os.getenv("APP_NAME", "AsistenteBi")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/asistentebi",
    )

    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")


settings = Settings()
