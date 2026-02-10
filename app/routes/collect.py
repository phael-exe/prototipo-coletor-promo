# app/routes/collect.py
"""Endpoints de coleta de produtos.
"""
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.core.logging import get_logger
from app.schemas.api import CollectRequest, CollectResponse, CollectResult
from app.services.bigquery import BigQueryService
from app.services.crawler import CrawlerService

logger = get_logger(__name__)

router = APIRouter()

# Cache em memória para resultados de tarefas (em produção, usar Redis ou similar)
task_results: dict[str, CollectResult] = {}


def run_collection_task(
    task_id: str,
    execution_id: str,
    request: CollectRequest,
):
    """Executa a tarefa de coleta em background.
    Armazena o resultado no cache task_results.
    """
    started_at = datetime.now(timezone.utc)

    try:
        logger.info("Starting collection task",
                   extra={
                       "task_id": task_id,
                       "execution_id": execution_id,
                       "sources": request.sources,
                       "limit_per_source": request.limit_per_source,
                       "max_pages_per_source": request.max_pages_per_source,
                   })

        # 1. Instancia o crawler
        crawler = CrawlerService()
        # Sobrescreve execution_id para manter consistência
        crawler.execution_id = execution_id

        # 2. Coleta produtos
        results = crawler.fetch_from_sources(
            sources=request.sources,
            limit_per_source=request.limit_per_source,
            max_pages_per_source=request.max_pages_per_source,
            delay_between_requests=request.delay_between_requests,
        )

        # 3. Agrega todos os produtos
        all_products = []
        for products in results.values():
            all_products.extend(products)

        logger.info("Products collected",
                   extra={
                       "task_id": task_id,
                       "execution_id": execution_id,
                       "total_products": len(all_products),
                       "sources_count": len(results),
                   })

        # 4. Persiste no BigQuery se solicitado
        products_inserted = None
        products_duplicated = None

        if request.persist_to_bigquery and all_products:
            try:
                bq = BigQueryService()
                insert_result = bq.insert_products(all_products)
                products_inserted = insert_result["inserted"]
                products_duplicated = insert_result["duplicates"]
                logger.info("BigQuery insertion completed",
                           extra={
                               "task_id": task_id,
                               "execution_id": execution_id,
                               "inserted": products_inserted,
                               "duplicates": products_duplicated,
                           })
            except Exception as e:
                logger.error("BigQuery insertion failed",
                            extra={
                                "task_id": task_id,
                                "execution_id": execution_id,
                                "error": str(e),
                            },
                            exc_info=True)
                raise

        # 5. Armazena resultado
        completed_at = datetime.now(timezone.utc)
        task_results[task_id] = CollectResult(
            execution_id=execution_id,
            status="completed",
            sources_processed=len(results),
            total_products_collected=len(all_products),
            products_inserted=products_inserted,
            products_duplicated=products_duplicated,
            started_at=started_at,
            completed_at=completed_at,
            error_message=None,
        )

        logger.info("Collection task completed",
                   extra={
                       "task_id": task_id,
                       "execution_id": execution_id,
                       "duration_seconds": (completed_at - started_at).total_seconds(),
                   })

    except Exception as e:
        logger.error("Collection task failed",
                    extra={
                        "task_id": task_id,
                        "execution_id": execution_id,
                        "error": str(e),
                    },
                    exc_info=True)

        # Armazena erro
        task_results[task_id] = CollectResult(
            execution_id=execution_id,
            status="failed",
            sources_processed=0,
            total_products_collected=0,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
            error_message=str(e),
        )



@router.post(
    "/collect",
    response_model=CollectResponse,
    summary="Iniciar Coleta",
    description="Inicia uma coleta assíncrona de produtos do Mercado Livre",
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Coleta iniciada com sucesso"},
        400: {"description": "Parâmetros inválidos"},
        500: {"description": "Erro interno do servidor"},
    },
)
async def collect_products(
    request: CollectRequest,
    background_tasks: BackgroundTasks,
):
    """Inicia uma coleta assíncrona de produtos.
    
    A coleta roda em background e não bloqueia a resposta HTTP.
    Use o `task_id` retornado para consultar o resultado via GET /collect/{task_id}.
    
    **Parâmetros:**
    - `sources`: Lista de termos de busca
    - `limit_per_source`: Máximo de produtos por fonte (1-500)
    - `max_pages_per_source`: Máximo de páginas por fonte (1-10)
    - `delay_between_requests`: Delay entre requisições (0.5-5.0s)
    - `persist_to_bigquery`: Se deve salvar no BigQuery após coleta
    
    **Exemplo:**
    ```json
    {
        "sources": ["monitor gamer 144hz", "ps5"],
        "limit_per_source": 50,
        "max_pages_per_source": 2,
        "persist_to_bigquery": true
    }
    ```
    """
    try:
        # Gera IDs únicos
        task_id = str(uuid.uuid4())
        execution_id = str(uuid.uuid4())[:8]

        # Calcula tempo estimado (aproximado)
        total_pages = len(request.sources) * request.max_pages_per_source
        estimated_time = int(total_pages * (request.delay_between_requests + 2))  # +2s para processamento

        # Inicia task em background
        background_tasks.add_task(
            run_collection_task,
            task_id=task_id,
            execution_id=execution_id,
            request=request,
        )

        logger.info("Collection task scheduled",
                   extra={
                       "task_id": task_id,
                       "execution_id": execution_id,
                       "sources_count": len(request.sources),
                       "estimated_time_seconds": estimated_time,
                   })

        return CollectResponse(
            task_id=task_id,
            execution_id=execution_id,
            status="started",
            message="Coleta iniciada com sucesso. Use o task_id para consultar o resultado.",
            sources=request.sources,
            estimated_time_seconds=estimated_time,
        )

    except Exception as e:
        logger.error("Failed to schedule collection task",
                    extra={"error": str(e)},
                    exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar coleta: {e!s}",
        )


@router.get(
    "/collect/{task_id}",
    response_model=CollectResult,
    summary="Consultar Resultado da Coleta",
    description="Retorna o resultado de uma coleta usando o task_id",
    responses={
        200: {"description": "Resultado encontrado"},
        404: {"description": "Task não encontrada"},
    },
)
async def get_collect_result(task_id: str):
    """Consulta o resultado de uma coleta em andamento ou concluída.
    
    **Status possíveis:**
    - `completed`: Coleta concluída com sucesso
    - `failed`: Coleta falhou com erro
    
    Se a task ainda não terminou, retorna 404.
    """
    if task_id not in task_results:
        logger.warning("Collection task result not found",
                      extra={"task_id": task_id})
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} não encontrada. Ela pode ainda estar em execução ou o ID é inválido.",
        )

    logger.debug("Collection task result retrieved",
                extra={"task_id": task_id})
    return task_results[task_id]

