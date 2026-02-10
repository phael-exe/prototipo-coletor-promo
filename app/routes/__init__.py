# app/routes/__init__.py
"""Módulo de rotas da API.
Centraliza o registro de todos os routers.
"""
from fastapi import FastAPI

from .collect import router as collect_router
from .health import router as health_router
from .root import router as root_router


def register_routers(app: FastAPI):
    """Registra todos os routers na aplicação FastAPI"""
    app.include_router(root_router, tags=["Root"])
    app.include_router(health_router, tags=["Health Check"])
    app.include_router(collect_router, tags=["Collect"])
