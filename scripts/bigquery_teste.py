import sys
import os
import logging

# Configuração de logs
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Adiciona o diretório raiz ao PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

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
            print(f"✅ Credenciais GCP encontradas: {json_files[0]}")
        else:
            print("❌ Nenhum arquivo .json encontrado em secrets/")
    else:
        print("❌ Diretório secrets/ não encontrado")

from app.services.crawler import CrawlerService
from app.services.bigquery import BigQueryService

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
    print("\n" + "="*70)
    print("🗄️  COLETA MULTI-FONTE COM PAGINAÇÃO + BIGQUERY")
    print("="*70 + "\n")

    # 1. Instancia os serviços
    try:
        crawler = CrawlerService()
        print(f"✅ Crawler instanciado (execution_id: {crawler.execution_id})")
        
        bq = BigQueryService()
        print(f"✅ BigQuery conectado: {bq.table_id}")
    except Exception as e:
        print(f"❌ Erro ao iniciar serviços: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Exibe configuração
    print(f"\n📋 CONFIGURAÇÃO:")
    print(f"   Fontes: {SOURCES}")
    print(f"   Limite por fonte: {LIMIT_PER_SOURCE}")
    print(f"   Máx. páginas por fonte: {MAX_PAGES_PER_SOURCE}")
    print(f"   Delay entre requisições: {DELAY_BETWEEN_REQUESTS}s")
    print()

    # 3. Coleta de múltiplas fontes com paginação
    print("="*70)
    print("🔍 INICIANDO COLETA")
    print("="*70 + "\n")
    
    try:
        results = crawler.fetch_from_sources(
            sources=SOURCES,
            limit_per_source=LIMIT_PER_SOURCE,
            max_pages_per_source=MAX_PAGES_PER_SOURCE,
            delay_between_requests=DELAY_BETWEEN_REQUESTS
        )
    except Exception as e:
        print(f"❌ Erro na coleta: {e}")
        import traceback
        traceback.print_exc()
        return

    # 4. Resumo da coleta por fonte
    print("\n" + "="*70)
    print("📊 RESUMO DA COLETA POR FONTE")
    print("="*70)
    
    all_products = []
    for source, products in results.items():
        all_products.extend(products)
        em_promo = sum(1 for p in products if p.has_discount)
        print(f"\n📦 {source}")
        print(f"   Produtos coletados: {len(products)}")
        print(f"   Em promoção: {em_promo}")
        if products:
            avg_price = sum(p.price for p in products) / len(products)
            print(f"   Preço médio: R$ {avg_price:.2f}")
    
    print(f"\n🎯 TOTAL COLETADO: {len(all_products)} produtos")
    print(f"   Páginas requisitadas: {crawler.stats['pages_fetched']}")

    # 5. Insere no BigQuery
    print("\n" + "="*70)
    print("💾 INSERINDO NO BIGQUERY")
    print("="*70 + "\n")
    
    try:
        result = bq.insert_products(all_products)
        print(f"📊 RESULTADO DA INSERÇÃO:")
        print(f"   ✅ Inseridos:   {result['inserted']}")
        print(f"   ⏭️  Duplicados:  {result['duplicates']}")
        print(f"   ❌ Erros:       {result['errors']}")
    except Exception as e:
        print(f"❌ Erro na inserção: {e}")
        import traceback
        traceback.print_exc()
        return

    # 6. Estatísticas finais do BigQuery
    print("\n" + "="*70)
    print("📈 ESTATÍSTICAS DO BIGQUERY")
    print("="*70)
    
    try:
        stats = bq.get_stats()
        if stats:
            print(f"\n   Total de produtos:    {stats.get('total_products', 0)}")
            print(f"   Itens únicos:         {stats.get('unique_items', 0)}")
            print(f"   Total de execuções:   {stats.get('total_executions', 0)}")
            print(f"   Produtos em promoção: {stats.get('products_on_sale', 0)}")
            print(f"   Preço médio geral:    R$ {stats.get('avg_price', 0):.2f}")
    except Exception as e:
        print(f"⚠️  Erro ao buscar stats: {e}")

    print("\n" + "="*70)
    print("✅ COLETA FINALIZADA!")
    print("="*70)
    print(f"\n🔗 Verifique no console:")
    print(f"   https://console.cloud.google.com/bigquery?project=promozone-ml")

if __name__ == "__main__":
    main()
