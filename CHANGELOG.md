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

## [0.3.0] - 2026-02-09

### Adicionado
- Coleta multi-fonte: suporte a múltiplas queries simultâneas
- Paginação dinâmica automática com `fetch_products_paginated()`
- Método `fetch_from_sources()` para orquestrar coletas
- Estatísticas de coleta por fonte (produtos, promoções, preço médio)
- Script `bigquery_teste.py` com teste completo multi-fonte

### Alterado
- Padrão de URL para paginação usando `_Desde_XX_NoIndex_True`
- Limite configurável por fonte e máximo de páginas

---

## [0.2.0] - 2026-02-09

### Adicionado
- Serviço `BigQueryService` para persistência no Google BigQuery
- Schema da tabela `promotions` com todos os campos do desafio
- **Deduplicação** via verificação pré-inserção com `dedupe_key`
- Composição: `dedupe_key = marketplace + item_id + price`
- Inserção via LOAD JOB (compatível com free tier GCP)
- Métodos `get_stats()` e `get_recent_products()` para consultas
- Configurações GCP no `config.py` (PROJECT_ID, DATASET_ID)

### Técnico
- Usa arquivo NDJSON temporário para LOAD JOB
- Query de verificação de duplicatas com IN clause

---

## [0.1.0] - 2026-02-09

### Adicionado
- Serviço de web scraping `CrawlerService` com BeautifulSoup
- Normalização de dados com Pydantic (`ProductSchema`)
- Retry com backoff exponencial usando tenacity
- Extração de campos: preço, desconto, vendedor, imagem, URL
- Configurações via variáveis de ambiente (.env)
- Scripts de teste para validação

### Campos do Schema
- `marketplace`, `item_id`, `url`, `title`, `price`
- `original_price`, `discount_percent`, `seller`, `image_url`
- `source`, `dedupe_key`, `execution_id`, `collected_at`

---

## Links

[Unreleased]: https://github.com/phaelzin/prototipo-coletor-promo/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/phaelzin/prototipo-coletor-promo/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/phaelzin/prototipo-coletor-promo/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/phaelzin/prototipo-coletor-promo/releases/tag/v0.1.0
