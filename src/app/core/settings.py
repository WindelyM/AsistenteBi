from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración centralizada de la aplicación."""
    app_name: str = "AsistenteBi"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False
    
    database_url: str = "postgresql+psycopg2://postgres:postgres@127.0.0.1:5432/asistentebi"
    google_api_key: str = ""

    model_config = SettingsConfigDict(env_prefix="APP_", env_file=".env", extra="ignore", case_sensitive=False)


settings = Settings()
