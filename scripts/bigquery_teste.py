import logging
import os
import sys

# Adiciona o diretório raiz ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# Configura logging estruturado em JSON
from app.core.logging import configure_logging, get_logger

configure_logging(level="INFO")
logger = get_logger(__name__)

# Configura a variável de ambiente para as credenciais
# Procura por qualquer arquivo .json em secrets/ se GOOGLE_APPLICATION_CREDENTIALS não estiver setada
if not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    secrets_dir = os.path.join(root_dir, "secrets")
    if os.path.exists(secrets_dir):
        json_files = [f for f in os.listdir(secrets_dir) if f.endswith('.json')]
        if json_files:
            # Usa o primeiro arquivo JSON encontrado
            credentials_file = os.path.join(secrets_dir, json_files[0])
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_file
            logger.info("GCP credentials found", extra={"credentials_file": json_files[0]})
        else:
            logger.warning("No JSON files found in secrets/")
    else:
        logger.warning("secrets/ directory not found")

from app.services.bigquery import BigQueryService
from app.services.crawler import CrawlerService

# Configuração das fontes de busca
SOURCES = [
    "monitor gamer 144hz",
    "iphone 16",  # Usando 16 pois 17 pode não existir ainda
    "ps5",
]

# Configuração de coleta
LIMIT_PER_SOURCE = 100      # Máximo de produtos por fonte
MAX_PAGES_PER_SOURCE = 3    # Máximo de páginas por fonte
DELAY_BETWEEN_REQUESTS = 1.5  # Delay entre requisições (rate limit)


def main():
    logger.info("Starting multi-source collection with BigQuery persistence",
                extra={"sources": SOURCES, "limit_per_source": LIMIT_PER_SOURCE})

    # 1. Instancia os serviços
    try:
        crawler = CrawlerService()
        logger.info("Crawler service initialized", extra={"execution_id": crawler.execution_id})
        
        bq = BigQueryService()
        logger.info("BigQuery service connected", extra={"table_id": bq.table_id})
    except Exception as e:
        logger.error("Failed to initialize services", exc_info=True)
        return

    # 2. Log configuração
    logger.info("Collection configuration",
                extra={
                    "sources": SOURCES,
                    "limit_per_source": LIMIT_PER_SOURCE,
                    "max_pages_per_source": MAX_PAGES_PER_SOURCE,
                    "delay_between_requests": DELAY_BETWEEN_REQUESTS
                })

    # 3. Coleta de múltiplas fontes com paginação
    logger.info("Starting collection process")
    
    try:
        results = crawler.fetch_from_sources(
            sources=SOURCES,
            limit_per_source=LIMIT_PER_SOURCE,
            max_pages_per_source=MAX_PAGES_PER_SOURCE,
            delay_between_requests=DELAY_BETWEEN_REQUESTS
        )
    except Exception as e:
        logger.error("Collection failed", exc_info=True)
        return

    # 4. Resumo da coleta por fonte
    logger.info("Collection summary by source")
    
    all_products = []
    for source, products in results.items():
        all_products.extend(products)
        em_promo = sum(1 for p in products if p.has_discount)
        avg_price = sum(p.price for p in products) / len(products) if products else 0
        logger.info("Source collection complete",
                    extra={
                        "source": source,
                        "products_collected": len(products),
                        "on_promotion": em_promo,
                        "average_price": avg_price
                    })
    
    logger.info("Total collection completed",
                extra={
                    "total_products": len(all_products),
                    "pages_fetched": crawler.stats['pages_fetched'],
                    "sources_processed": crawler.stats['sources_processed']
                })

    # 5. Insere no BigQuery
    logger.info("Starting BigQuery insertion")
    
    try:
        result = bq.insert_products(all_products)
        logger.info("BigQuery insertion completed",
                    extra={
                        "inserted": result['inserted'],
                        "duplicates": result['duplicates'],
                        "errors": result['errors']
                    })
    except Exception as e:
        logger.error("BigQuery insertion failed", exc_info=True)
        return

    # 6. Estatísticas finais do BigQuery
    logger.info("Fetching BigQuery statistics")
    
    try:
        stats = bq.get_stats()
        if stats:
            logger.info("BigQuery statistics",
                        extra={
                            "total_products": stats.get('total_products', 0),
                            "unique_items": stats.get('unique_items', 0),
                            "total_executions": stats.get('total_executions', 0),
                            "products_on_sale": stats.get('products_on_sale', 0),
                            "average_price": stats.get('avg_price', 0)
                        })
    except Exception as e:
        logger.warning("Failed to fetch BigQuery statistics", exc_info=True)

    logger.info("Collection workflow completed successfully")


if __name__ == "__main__":
    main()

