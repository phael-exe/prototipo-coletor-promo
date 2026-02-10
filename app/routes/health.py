# app/routes/health.py
"""
Endpoint de health check.
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, status

from app.schemas.api import HealthResponse
from app.services.bigquery import BigQueryService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verifica o status da API e serviços dependentes",
    status_code=status.HTTP_200_OK,
)
async def health_check():
    """
    Endpoint de health check para monitoramento.
    Verifica conectividade com BigQuery e status geral da aplicação.
    """
    services_status = {
        "crawler": "healthy",
        "bigquery": "unknown"
    }
    overall_status = "healthy"
    
    # Testa conexão com BigQuery
    try:
        bq = BigQueryService()
        # Tenta uma operação simples para verificar conectividade
        bq.client.get_dataset(bq.dataset_id)
        services_status["bigquery"] = "healthy"
        logger.info("✅ BigQuery health check: OK")
    except Exception as e:
        services_status["bigquery"] = f"unhealthy: {str(e)}"
        overall_status = "degraded"
        logger.error(f"❌ BigQuery health check failed: {e}")
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc),
        version="1.0.0",
        services=services_status
    )
