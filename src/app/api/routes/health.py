"""Endpoint /health para comprobar que el servicio está vivo."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Devuelve el estado del servicio."""
    return {"status": "ok"}
