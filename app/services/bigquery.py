# app/services/bigquery.py
import json
import logging
import tempfile
from datetime import datetime, timezone
from typing import List, Optional

from google.cloud import bigquery
from google.cloud.exceptions import NotFound

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.product import ProductSchema

logger = get_logger(__name__)

# Schema da tabela no BigQuery (baseado no desafio)
TABLE_SCHEMA = [
    bigquery.SchemaField("marketplace", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("item_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("url", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("title", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("price", "NUMERIC", mode="REQUIRED"),
    bigquery.SchemaField("original_price", "NUMERIC", mode="NULLABLE"),
    bigquery.SchemaField("discount_percent", "FLOAT64", mode="NULLABLE"),
    bigquery.SchemaField("seller", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("image_url", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("source", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("dedupe_key", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("execution_id", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("collected_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("inserted_at", "TIMESTAMP", mode="REQUIRED"),
]

TABLE_NAME = "promotions"


class BigQueryService:
    """
    Serviço para persistência de dados no BigQuery.
    Implementa inserção com deduplicação.
    """

    def __init__(self):
        """
        Inicializa o cliente BigQuery.
        Usa credenciais do arquivo JSON via variável de ambiente GOOGLE_APPLICATION_CREDENTIALS
        ou do arquivo configurado em GCP_CREDENTIALS_PATH.
        """
        self.project_id = settings.GCP_PROJECT_ID
        self.dataset_id = settings.GCP_DATASET_ID
        self.table_id = f"{self.project_id}.{self.dataset_id}.{TABLE_NAME}"
        
        # Inicializa cliente (usa GOOGLE_APPLICATION_CREDENTIALS automaticamente)
        self.client = bigquery.Client(project=self.project_id)
        
        logger.info(f"[BIGQUERY] Conectado ao projeto: {self.project_id}")
        logger.info(f"[BIGQUERY] Dataset: {self.dataset_id}")
        logger.info(f"[BIGQUERY] Tabela: {self.table_id}")

    def ensure_table_exists(self) -> None:
        """
        Garante que a tabela existe. Se não existir, cria com o schema definido.
        """
        try:
            self.client.get_table(self.table_id)
            logger.info(f"[BIGQUERY] Tabela {TABLE_NAME} já existe")
        except NotFound:
            logger.info(f"[BIGQUERY] Criando tabela {TABLE_NAME}...")
            table = bigquery.Table(self.table_id, schema=TABLE_SCHEMA)
            table = self.client.create_table(table)
            logger.info(f"[BIGQUERY] Tabela {TABLE_NAME} criada com sucesso!")

    def insert_products(self, products: List[ProductSchema]) -> dict:
        """
        Insere produtos no BigQuery com deduplicação.
        Usa LOAD JOB (funciona no free tier) em vez de streaming insert.
        
        Args:
            products: Lista de produtos normalizados
            
        Returns:
            dict com estatísticas: inserted, duplicates, errors
        """
        if not products:
            logger.warning("[BIGQUERY] Nenhum produto para inserir")
            return {"inserted": 0, "duplicates": 0, "errors": 0}

        # Garante que a tabela existe
        self.ensure_table_exists()
        
        # Busca dedupe_keys existentes
        existing_keys = self._get_existing_dedupe_keys([p.dedupe_key for p in products])
        
        # Filtra produtos novos (não duplicados)
        new_products = [p for p in products if p.dedupe_key not in existing_keys]
        duplicates = len(products) - len(new_products)
        
        if duplicates > 0:
            logger.info(f"[BIGQUERY] {duplicates} produtos duplicados ignorados")
        
        if not new_products:
            logger.info("[BIGQUERY] Todos os produtos já existem na tabela")
            return {"inserted": 0, "duplicates": duplicates, "errors": 0}

        # Prepara rows para inserção via LOAD JOB (funciona no free tier)
        inserted_at = datetime.now(timezone.utc)
        rows_to_insert = []
        
        for p in new_products:
            row = {
                "marketplace": p.marketplace,
                "item_id": p.item_id,
                "url": p.url,
                "title": p.title,
                "price": float(p.price),
                "original_price": float(p.original_price) if p.original_price else None,
                "discount_percent": float(p.discount_percent) if p.discount_percent else None,
                "seller": p.seller,
                "image_url": p.image_url,
                "source": p.source,
                "dedupe_key": p.dedupe_key,
                "execution_id": p.execution_id,
                "collected_at": p.collected_at.isoformat(),
                "inserted_at": inserted_at.isoformat(),
            }
            rows_to_insert.append(row)

        # Usa LOAD JOB com arquivo NDJSON temporário (funciona no free tier!)
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                for row in rows_to_insert:
                    f.write(json.dumps(row) + '\n')
                temp_file = f.name
            
            job_config = bigquery.LoadJobConfig(
                source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                schema=TABLE_SCHEMA,
            )
            
            with open(temp_file, 'rb') as source_file:
                job = self.client.load_table_from_file(
                    source_file,
                    self.table_id,
                    job_config=job_config
                )
            
            job.result()  # Aguarda conclusão
            
            logger.info(f"[BIGQUERY] {len(new_products)} produtos inseridos com sucesso!")
            return {"inserted": len(new_products), "duplicates": duplicates, "errors": 0}
            
        except Exception as e:
            logger.error(f"[BIGQUERY] Erro na inserção: {e}")
            return {"inserted": 0, "duplicates": duplicates, "errors": 1}

        logger.info(f"[BIGQUERY] {len(new_products)} produtos inseridos com sucesso!")
        return {"inserted": len(new_products), "duplicates": duplicates, "errors": 0}

    def _get_existing_dedupe_keys(self, keys: List[str]) -> set:
        """
        Busca quais dedupe_keys já existem na tabela.
        """
        if not keys:
            return set()

        # Formata keys para a query
        keys_str = ", ".join([f"'{k}'" for k in keys])
        
        query = f"""
            SELECT DISTINCT dedupe_key 
            FROM `{self.table_id}`
            WHERE dedupe_key IN ({keys_str})
        """
        
        try:
            result = self.client.query(query).result()
            existing = {row.dedupe_key for row in result}
            logger.debug(f"[BIGQUERY] {len(existing)} dedupe_keys já existentes")
            return existing
        except NotFound:
            # Tabela não existe ainda
            return set()

    def get_recent_products(self, hours: int = 24, limit: int = 100) -> List[dict]:
        """
        Retorna produtos coletados nas últimas X horas.
        Útil para validação e relatórios.
        """
        query = f"""
            SELECT *
            FROM `{self.table_id}`
            WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR)
            ORDER BY collected_at DESC
            LIMIT {limit}
        """
        
        try:
            result = self.client.query(query).result()
            return [dict(row) for row in result]
        except Exception as e:
            logger.error(f"[BIGQUERY] Erro ao buscar produtos recentes: {e}")
            return []

    def get_stats(self) -> dict:
        """
        Retorna estatísticas da tabela.
        """
        query = f"""
            SELECT 
                COUNT(*) as total_products,
                COUNT(DISTINCT item_id) as unique_items,
                COUNT(DISTINCT execution_id) as total_executions,
                MIN(collected_at) as first_collection,
                MAX(collected_at) as last_collection,
                AVG(price) as avg_price,
                COUNT(CASE WHEN discount_percent IS NOT NULL THEN 1 END) as products_on_sale
            FROM `{self.table_id}`
        """
        
        try:
            result = list(self.client.query(query).result())[0]
            return dict(result)
        except Exception as e:
            logger.error(f"[BIGQUERY] Erro ao buscar estatísticas: {e}")
            return {}
