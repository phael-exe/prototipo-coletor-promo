# app/schemas/product.py
from pydantic import BaseModel, Field
from typing import Optional

class ProductSchema(BaseModel):
    title: str = Field(..., description="O título completo do produto")
    price: float = Field(..., description="O preço atual do produto (apenas numeros)")
    original_price: Optional[float] = Field(None, description="O preço original antes do desconto, se houver")
    currency: str = Field("BRL", description="A moeda do preço (ex: BRL)")
    url: str = Field(..., description="O link direto para o produto")
    seller: Optional[str] = Field(None, description="Nome do vendedor ou loja oficial")
    image_url: Optional[str] = Field(None, description="URL da imagem principal do produto")
    
    # O item_id as vezes vem na URL (MLB...), vamos tentar extrair
    item_id: Optional[str] = Field(None, description="O ID único do item (geralmente começa com MLB)")