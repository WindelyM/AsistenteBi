# Importar librerías
from pydantic_settings import BaseSettings, SettingsConfigDict
import os


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación."""
    app_name: str = "AsistenteBi"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False

    # Configuración de base de datos
    database_url: str = os.environ.get("DATABASE_URL")
    
    # Configuración de Google Gemini
    google_api_key: str = os.environ.get("GOOGLE_API_KEY")

    # Configuración de Pydantic Settings
    model_config = SettingsConfigDict(env_prefix="", env_file=".env", extra="ignore", case_sensitive=False)

# Crear configuración
settings = Settings()
