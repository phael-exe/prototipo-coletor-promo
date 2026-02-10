# app/main.py
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.routes import register_routers
from app.schemas.api import ErrorResponse

# Configura logging estruturado em JSON
configure_logging(level="INFO")
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    logger.info("🚀 Iniciando API Coletor de Promoções")
    logger.info(f"📋 Projeto: {settings.PROJECT_NAME}")
    logger.info(f"🗄️  BigQuery: {settings.GCP_PROJECT_ID}.{settings.GCP_DATASET_ID}")
    yield
    logger.info("🛑 Encerrando API Coletor de Promoções")


# Inicializa FastAPI
app = FastAPI(
    title="Coletor de Promoções ML API",
    description="API REST para coleta de promoções do Mercado Livre com persistência no BigQuery",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Registra todos os routers
register_routers(app)


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handler customizado para exceções HTTP"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            timestamp=datetime.now(timezone.utc),
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handler customizado para exceções genéricas"""
    logger.error(f"❌ Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="InternalServerError",
            message="Erro interno do servidor. Verifique os logs para mais detalhes.",
            details={"error_type": exc.__class__.__name__},
            timestamp=datetime.now(timezone.utc),
        ).model_dump(mode="json"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
