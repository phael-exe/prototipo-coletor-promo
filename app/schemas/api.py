# app/schemas/api.py
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Resposta do endpoint de health check"""
    status: str = Field(..., description="Status da API (healthy/unhealthy)")
    timestamp: datetime = Field(..., description="Timestamp da verificação")
    version: str = Field(default="1.0.0", description="Versão da API")
    services: dict = Field(..., description="Status dos serviços dependentes")


class CollectRequest(BaseModel):
    """Requisição para o endpoint de coleta"""
    sources: List[str] = Field(
        ..., 
        description="Lista de termos de busca (ex: ['monitor gamer', 'ps5'])",
        min_length=1,
        examples=[["monitor gamer 144hz", "iphone 16"]]
    )
    limit_per_source: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Máximo de produtos por fonte (1-500)"
    )
    max_pages_per_source: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Máximo de páginas por fonte (1-10)"
    )
    delay_between_requests: float = Field(
        default=1.5,
        ge=0.5,
        le=5.0,
        description="Delay entre requisições em segundos (0.5-5.0)"
    )
    persist_to_bigquery: bool = Field(
        default=True,
        description="Se True, persiste dados no BigQuery após coleta"
    )


class CollectResponse(BaseModel):
    """Resposta do endpoint de coleta"""
    task_id: str = Field(..., description="ID da task em background")
    execution_id: str = Field(..., description="ID único da execução do crawler")
    status: str = Field(..., description="Status da task (started/running)")
    message: str = Field(..., description="Mensagem informativa")
    sources: List[str] = Field(..., description="Fontes que serão coletadas")
    estimated_time_seconds: int = Field(..., description="Tempo estimado em segundos")


class CollectResult(BaseModel):
    """Resultado final da coleta (armazenado em memória/cache)"""
    execution_id: str = Field(..., description="ID da execução")
    status: str = Field(..., description="Status final (completed/failed)")
    sources_processed: int = Field(..., description="Quantidade de fontes processadas")
    total_products_collected: int = Field(..., description="Total de produtos coletados")
    products_inserted: Optional[int] = Field(None, description="Produtos inseridos no BigQuery")
    products_duplicated: Optional[int] = Field(None, description="Produtos duplicados (não inseridos)")
    started_at: datetime = Field(..., description="Timestamp de início")
    completed_at: datetime = Field(..., description="Timestamp de conclusão")
    error_message: Optional[str] = Field(None, description="Mensagem de erro se falhou")


class ErrorResponse(BaseModel):
    """Resposta padrão de erro"""
    error: str = Field(..., description="Tipo do erro")
    message: str = Field(..., description="Mensagem descritiva do erro")
    details: Optional[dict] = Field(None, description="Detalhes adicionais do erro")
    timestamp: datetime = Field(default_factory=datetime.now, description="Timestamp do erro")
