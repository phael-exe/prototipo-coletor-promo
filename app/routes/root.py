# app/routes/root.py
"""
Endpoint raiz da API.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/",
    summary="Root endpoint",
    description="Retorna informações básicas da API"
)
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "name": "Coletor de Promoções ML API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }
