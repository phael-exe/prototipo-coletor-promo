# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado
- API FastAPI com endpoint `/health`
- Dockerfile e docker-compose
- Deploy no Cloud Run (GCP)
- Logs estruturados (JSON)

---

## [1.0.0] - 2026-02-09

### 🎉 Primeira Release

MVP completo do coletor de promoções do Mercado Livre com todas as funcionalidades core.

### Adicionado

#### Coleta Multi-Fonte
- Suporte a múltiplas queries simultâneas
- Paginação dinâmica automática com `fetch_products_paginated()`
- Método `fetch_from_sources()` para orquestrar coletas
- Estatísticas de coleta por fonte (produtos, promoções, preço médio)

#### Persistência BigQuery
- Serviço `BigQueryService` para persistência no Google BigQuery
- Schema da tabela `promotions` com todos os campos do desafio
- Inserção via LOAD JOB (compatível com free tier GCP)
- Métodos `get_stats()` e `get_recent_products()` para consultas

#### Deduplicação
- Verificação pré-inserção com `dedupe_key`
- Composição: `dedupe_key = marketplace + item_id + price`
- Query de verificação de duplicatas otimizada

#### Web Scraping
- Serviço `CrawlerService` com BeautifulSoup
- Retry com backoff exponencial usando tenacity
- Extração de campos: preço, desconto, vendedor, imagem, URL

#### Normalização
- Schema Pydantic `ProductSchema` com validação
- Campos: `marketplace`, `item_id`, `url`, `title`, `price`, `original_price`, `discount_percent`, `seller`, `image_url`, `source`, `dedupe_key`, `execution_id`, `collected_at`

#### CI/CD
- Workflow CI: lint e validação de imports
- Workflow Release: criação automática via tags
- CHANGELOG seguindo Keep a Changelog

---

## Links

[Unreleased]: https://github.com/phaelzin/prototipo-coletor-promo/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/phaelzin/prototipo-coletor-promo/releases/tag/v1.0.0
