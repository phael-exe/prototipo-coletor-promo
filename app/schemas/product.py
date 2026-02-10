# app/schemas/product.py
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, computed_field


class ProductSchema(BaseModel):
    """
    Schema normalizado de produto/promoção do Mercado Livre.
    Segue o modelo definido no desafio técnico.
    """
    
    # Campos obrigatórios do desafio
    marketplace: str = Field(default="mercado_livre", description="Identificador do marketplace")
    item_id: str = Field(..., description="ID único do item (ex: MLB12345678)")
    url: str = Field(..., description="Link direto para o produto")
    title: str = Field(..., description="Título completo do produto")
    price: float = Field(..., description="Preço atual do produto")
    original_price: Optional[float] = Field(None, description="Preço original antes do desconto")
    discount_percent: Optional[float] = Field(None, description="Percentual de desconto calculado")
    seller: Optional[str] = Field(None, description="Nome do vendedor ou loja oficial")
    image_url: Optional[str] = Field(None, description="URL da imagem principal")
    source: str = Field(..., description="Query/página que gerou o item (ex: 'monitor gamer 144hz')")
    
    # Campos de rastreabilidade
    dedupe_key: str = Field(..., description="Chave única para deduplicação (marketplace + item_id + price)")
    execution_id: str = Field(..., description="ID único da execução/coleta")
    collected_at: datetime = Field(..., description="Timestamp da coleta")
    
    # Campos extras úteis
    currency: str = Field(default="BRL", description="Moeda do preço")
    
    @computed_field
    @property
    def has_discount(self) -> bool:
        """Indica se o produto está em promoção."""
        return self.original_price is not None and self.original_price > self.price