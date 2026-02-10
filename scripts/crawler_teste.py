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

try:
    from app.services.crawler import CrawlerService
except ImportError:
    logger.error("Import error when loading CrawlerService", exc_info=True)
    sys.exit(1)

def main():
    logger.info("Starting crawler test - Complete normalization")

    # 1. Instanciação
    try:
        crawler = CrawlerService()
        logger.info("Crawler service initialized", extra={"execution_id": crawler.execution_id})
    except Exception:
        logger.error("Failed to initialize CrawlerService", exc_info=True)
        return

    # 2. Definição do teste
    termo = "monitor gamer 144hz"
    limite = 5
    logger.info("Starting search",
                extra={"query": termo, "limit": limite})

    # 3. Execução
    try:
        produtos = crawler.fetch_products(query=termo, limit=limite)

        logger.info("Collection completed",
                    extra={
                        "products_collected": len(produtos),
                        "execution_id": crawler.execution_id,
                    })

        if not produtos:
            logger.warning("No products found for the given query")
            return

        # 4. Log detalhes dos produtos
        for i, p in enumerate(produtos, 1):
            logger.debug("Product collected",
                        extra={
                            "product_number": i,
                            "marketplace": p.marketplace,
                            "item_id": p.item_id,
                            "title": p.title[:100],
                            "price": float(p.price),
                            "original_price": float(p.original_price) if p.original_price else None,
                            "discount_percent": float(p.discount_percent) if p.discount_percent else None,
                            "has_discount": p.has_discount,
                            "dedupe_key": p.dedupe_key,
                            "execution_id": p.execution_id,
                        })

        # 5. Resumo estatístico
        em_promocao = sum(1 for p in produtos if p.has_discount)
        media_preco = sum(p.price for p in produtos) / len(produtos) if produtos else 0

        logger.info("Collection summary",
                    extra={
                        "total_collected": len(produtos),
                        "on_promotion": em_promocao,
                        "average_price": float(media_preco),
                        "query": termo,
                    })

    except Exception:
        logger.error("Critical error during search", exc_info=True)

if __name__ == "__main__":
    main()
