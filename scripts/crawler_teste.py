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
    print("🕷️  TESTE DO CRAWLER - NORMALIZAÇÃO COMPLETA")
    print("="*60 + "\n")

    # 1. Instanciação
    try:
        crawler = CrawlerService()
        print(f"✅ Serviço Crawler instanciado")
        print(f"   execution_id: {crawler.execution_id}\n")
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
        
        print(f"\n📊 RESULTADO: {len(produtos)} produtos coletados e normalizados.\n")

        if not produtos:
            print("⚠️  Nenhum produto encontrado. Verifique os logs acima.")
            return

        # 4. Exibe os produtos com todos os campos normalizados
        for i, p in enumerate(produtos, 1):
            print(f"{'='*50}")
            print(f"📦 PRODUTO #{i}")
            print(f"{'='*50}")
            print(f"🏪 Marketplace:     {p.marketplace}")
            print(f"🆔 Item ID:         {p.item_id}")
            print(f"🛒 Título:          {p.title[:50]}..." if len(p.title) > 50 else f"🛒 Título:          {p.title}")
            print(f"💰 Preço:           R$ {p.price:.2f}")
            if p.original_price:
                print(f"🏷️  Preço Original: R$ {p.original_price:.2f}")
                print(f"📉 Desconto:        {p.discount_percent:.1f}%")
            print(f"🔗 URL:             {p.url[:60]}...")
            print(f"📸 Imagem:          {p.image_url[:50] if p.image_url else 'N/A'}...")
            print(f"📁 Source:          {p.source}")
            print(f"🔑 Dedupe Key:      {p.dedupe_key}")
            print(f"🕐 Collected At:    {p.collected_at}")
            print(f"🎯 Execution ID:    {p.execution_id}")
            print(f"✨ Em promoção:     {'Sim' if p.has_discount else 'Não'}")
            print()

        # 5. Resumo estatístico
        print("="*50)
        print("📈 RESUMO DA COLETA")
        print("="*50)
        print(f"Total coletados:    {len(produtos)}")
        em_promocao = sum(1 for p in produtos if p.has_discount)
        print(f"Em promoção:        {em_promocao}")
        if produtos:
            media_preco = sum(p.price for p in produtos) / len(produtos)
            print(f"Preço médio:        R$ {media_preco:.2f}")

    except Exception as e:
        print(f"❌ ERRO CRÍTICO DURANTE A BUSCA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()