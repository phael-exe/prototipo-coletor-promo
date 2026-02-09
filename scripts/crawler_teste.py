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

try:
    from app.services.crawler import CrawlerService
except ImportError as e:
    print("Erro de importação! Certifique-se de estar rodando o script da raiz do projeto.")
    print(f"Detalhe: {e}")
    sys.exit(1)

def main():
    print("\n" + "="*60)
    print("🕷️  TESTE DO CRAWLER - MERCADO LIVRE")
    print("="*60 + "\n")

    # 1. Instanciação
    try:
        crawler = CrawlerService()
        print("✅ Serviço Crawler instanciado com sucesso.\n")
    except Exception as e:
        print(f"❌ Erro ao iniciar o serviço: {e}")
        return

    # 2. Definição do teste
    termo = "monitor gamer 144hz"
    limite = 5
    print(f"🔍 Buscando por: '{termo}' (Limite: {limite})\n")

    # 3. Execução
    try:
        produtos = crawler.fetch_products(query=termo, limit=limite)
        
        print(f"\n📊 RESULTADO: {len(produtos)} produtos coletados.\n")

        if not produtos:
            print("⚠️  Nenhum produto encontrado. Verifique os logs acima.")
            return

        # 4. Exibe os produtos
        for i, p in enumerate(produtos, 1):
            print(f"--- Produto #{i} ---")
            print(f"🛒 Título:  {p.title[:60]}..." if len(p.title) > 60 else f"🛒 Título:  {p.title}")
            print(f"💰 Preço:   R$ {p.price:.2f}")
            if p.original_price:
                desconto = ((p.original_price - p.price) / p.original_price) * 100
                print(f"🏷️  Original: R$ {p.original_price:.2f} (-{desconto:.0f}%)")
            print(f"🆔 Item ID: {p.item_id}")
            print(f"🔗 Link:    {p.url[:70]}...")
            print("-" * 40)

    except Exception as e:
        print(f"❌ ERRO CRÍTICO DURANTE A BUSCA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()