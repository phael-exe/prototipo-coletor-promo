# app/routes/health.py
"""Endpoint de health check.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, status

from app.core.logging import get_logger
from app.schemas.api import HealthResponse
from app.services.bigquery import BigQueryService

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verifica o status da API e serviços dependentes",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """Endpoint de health check para monitoramento.
    Verifica conectividade com BigQuery e status geral da aplicação.
    """
    services_status = {
        "crawler": "healthy",
        "bigquery": "unknown",
    }
    overall_status = "healthy"

    # Testa conexão com BigQuery
    try:
        bq = BigQueryService()
        # Tenta uma operação simples para verificar conectividade
        bq.client.get_dataset(bq.dataset_id)
        services_status["bigquery"] = "healthy"
        logger.info("BigQuery health check passed",
                   extra={"service": "bigquery"})
    except Exception as e:
        services_status["bigquery"] = f"unhealthy: {e!s}"
        overall_status = "degraded"
        logger.error("BigQuery health check failed",
                    extra={"service": "bigquery", "error": str(e)},
                    exc_info=True)

    logger.debug("Health check completed",
                extra={
                    "overall_status": overall_status,
                    "services": services_status,
                })

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        services=services_status,

    )
