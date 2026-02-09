import logging
import re
from typing import List
from datetime import datetime, timezone
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings
from app.schemas.product import ProductSchema

# Configuração de logs
logger = logging.getLogger(__name__)

class CrawlerService:
    """
    Serviço de coleta de produtos do Mercado Livre via web scraping.
    Usa requests + BeautifulSoup para extrair dados da página de busca.
    """

    def __init__(self):
        # Headers para simular navegador
        self.headers = {
            "User-Agent": settings.USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        self.base_url = "https://lista.mercadolivre.com.br"

    @retry(
        stop=stop_after_attempt(settings.MAX_RETRIES),
        wait=wait_exponential(min=settings.RETRY_MIN_SECONDS, max=settings.RETRY_MAX_SECONDS),
        reraise=True
    )
    def fetch_products(self, query: str, limit: int = 50) -> List[ProductSchema]:
        """
        Coleta produtos do Mercado Livre baseado em uma query de busca.
        
        Args:
            query: Termo de busca (ex: "monitor gamer 144hz")
            limit: Quantidade máxima de produtos a retornar
            
        Returns:
            Lista de ProductSchema com os produtos encontrados
        """
        logger.info(f"[COLETA] Iniciando busca por: '{query}' (limite: {limit})")
        
        # Monta a URL de busca
        search_url = f"{self.base_url}/{query.replace(' ', '-')}"
        
        try:
            logger.info(f"[COLETA] Requisição para: {search_url}")
            response = requests.get(search_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            # Extrai produtos do HTML
            products = self._extract_from_html(response.text, source_query=query)
            
            logger.info(f"[COLETA] {len(products)} produtos extraídos, retornando {min(len(products), limit)}")
            return products[:limit]
            
        except requests.RequestException as e:
            logger.error(f"[COLETA] Erro na requisição: {e}")
            raise

    def _extract_from_html(self, html_content: str, source_query: str) -> List[ProductSchema]:
        """
        Extrai produtos do HTML da página de busca do Mercado Livre.
        
        Args:
            html_content: HTML bruto da página
            source_query: Query de busca que gerou essa página
            
        Returns:
            Lista de ProductSchema extraídos
        """
        products = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Seletores comuns do ML (eles mudam as vezes, por isso mantemos vários padrões)
        items = soup.find_all('li', {'class': 'ui-search-layout__item'})
        
        # Se não encontrou, tenta outros seletores
        if not items:
            items = soup.find_all('div', {'class': 'ui-search-result__wrapper'})
        if not items:
            items = soup.select('.ui-search-layout__item, .andes-card')
        
        logger.info(f"Encontrados {len(items)} itens no HTML")
        
        for item in items:
            try:
                # Extração resiliente de cada campo
                
                # Título - novo seletor: a.poly-component__title ou h3 > a
                title_tag = item.find('a', {'class': 'poly-component__title'})
                if not title_tag:
                    title_tag = item.find('h2', {'class': 'ui-search-item__title'})
                if not title_tag:
                    h3 = item.find('h3')
                    if h3:
                        title_tag = h3.find('a')
                if not title_tag: 
                    continue
                    
                title = title_tag.text.strip()
                url = title_tag.get('href', '')
                
                # Tenta extrair ID da URL (ex: MLB-12345 ou MLB12345 ou p/MLB12345)
                item_id = None
                id_match = re.search(r'MLB-?(\d+)', url)
                if id_match:
                    item_id = f"MLB{id_match.group(1)}"

                # Preço - busca dentro de poly-price__current
                price = 0.0
                price_container = item.find('div', {'class': 'poly-price__current'})
                if price_container:
                    price_tag = price_container.find('span', {'class': 'andes-money-amount__fraction'})
                    if price_tag:
                        price_text = price_tag.text.replace('.', '').replace(',', '.')
                        price = float(price_text) if price_text else 0.0
                
                # Preço original (desconto) - busca s.andes-money-amount ou poly-price__original
                original_price = None
                original_container = item.find('s', {'class': 'andes-money-amount'})
                if not original_container:
                    original_container = item.find('div', {'class': 'poly-price__original'})
                if original_container:
                    op_fraction = original_container.find('span', {'class': 'andes-money-amount__fraction'})
                    if op_fraction:
                        original_price = float(op_fraction.text.replace('.', '').replace(',', '.'))

                # Imagem - busca img.poly-component__picture
                img_tag = item.find('img', {'class': 'poly-component__picture'})
                if not img_tag:
                    img_tag = item.find('img')
                image_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None

                # Cria o objeto usando o Schema
                product = ProductSchema(
                    item_id=item_id,
                    title=title,
                    price=price,
                    original_price=original_price,
                    url=url,
                    image_url=image_url,
                    currency="BRL",
                    seller=None  # Difícil pegar na listagem sem entrar no item
                )
                products.append(product)
                
            except Exception as e:
                logger.debug(f"Erro ao extrair item: {e}")
                continue
                
        return products

    def fetch_from_url(self, url: str, source_name: str = "custom") -> List[ProductSchema]:
        """
        Coleta produtos de uma URL específica do Mercado Livre.
        Útil para coletar de páginas de ofertas, categorias específicas, etc.
        
        Args:
            url: URL completa da página do ML
            source_name: Nome identificador da fonte
            
        Returns:
            Lista de ProductSchema extraídos
        """
        logger.info(f"[COLETA] Coletando de URL direta: {url}")
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            products = self._extract_from_html(response.text, source_query=source_name)
            logger.info(f"[COLETA] {len(products)} produtos extraídos de {source_name}")
            return products
            
        except requests.RequestException as e:
            logger.error(f"[COLETA] Erro ao coletar de {url}: {e}")
            return []