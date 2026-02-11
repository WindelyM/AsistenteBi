# AsistenteBi — Asistente de BI con Exploración de Datos Interactiva GenBI

Microservicio FastAPI que traduce preguntas en lenguaje natural a consultas SQL
usando Google Gemini (LangChain).

## Requisitos previos

- Python ≥ 3.11
- PostgreSQL corriendo y con la base de datos `asistentebi` creada
- Clave de API de Google Gemini

## Arranque local

```bash
# 1. Clonar y entrar
git clone <repo-url> && cd AsistenteBi

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# 3. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus valores reales

# 4. Arrancar el servidor
uvicorn src.app.main:app --reload

# 5. Comprobar que funciona
curl http://localhost:8000/health
```

## Arranque con Docker

```bash
# 1. Configurar variables
cp .env.example .env
# Edita .env

# 2. Construir y arrancar
docker compose up --build

# 3. Comprobar
curl http://localhost:8000/health
```

## Tests

```bash
python -m pytest tests/ -v
```

## Estructura del proyecto

```
pyproject.toml          # dependencias y config
Dockerfile              # imagen del microservicio
docker-compose.yml      # arranque con Docker
.env.example            # variables de entorno (ejemplo)
src/
  app/
    main.py             # punto de entrada FastAPI
    core/
      settings.py       # configuración desde entorno
    api/
      routes/
        health.py       # GET /health
tests/
  test_health.py        # test de integración
```
