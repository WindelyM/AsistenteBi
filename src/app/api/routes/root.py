"""Endpoints raíz: / y /favicon.ico."""

from fastapi import APIRouter

router = APIRouter(tags=["root"])


@router.get("/")
def home():
    return {"status": "Microservicio de BI Online (Gemini Ready)", "endpoint": "/ask"}


@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return {"status": "no icon"}
