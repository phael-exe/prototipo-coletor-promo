# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Planejado
- Deploy no Cloud Run (GCP)
- Autenticação/Rate limiting na API
- Redis para cache de tasks
- Testes automatizados

---

## [1.2.0] - 2026-02-10

### 📊 Logs Estruturados em JSON

Release focada em migrar de logs de texto simples para JSON estruturado, facilitando integração com Cloud Logging.

### Adicionado

#### Sistema de Logging Estruturado
- Novo módulo `app/core/logging.py` com configuração centralizada
- Custom formatter `CustomJsonFormatter` para JSON estruturado
- Função `configure_logging()` para inicializar logger raiz
- Função `get_logger()` para criar loggers estruturados por módulo
- Suporte a `extra` fields para contexto adicional (execution_id, task_id, etc)
- Timestamps em ISO 8601 com timezone UTC
- Normalização de níveis para minúsculas (info, warning, error)

#### Campos JSON Padronizados
- `timestamp` - ISO 8601 com timezone
- `level` - Nível em minúsculas (debug, info, warning, error, critical)
- `name` / `module` - Nome do logger/módulo que gerou o log
- `message` - Mensagem principal
- `execution_id` - ID de execução (quando disponível)
- `task_id` - ID de task (quando disponível)
- Campos customizados via `extra` dict

#### Migrações de Código
- `app/main.py` - Usa `configure_logging()` e `get_logger()`
- `app/routes/collect.py` - Logs estruturados para tasks async
- `app/routes/health.py` - Logs estruturados para health check
- `app/routes/root.py` - Logs estruturados para raiz
- `app/services/crawler.py` - Usa `get_logger()`
- `app/services/bigquery.py` - Usa `get_logger()`
- `scripts/bigquery_teste.py` - Completamente refatorado com JSON logs
- `scripts/crawler_teste.py` - Completamente refatorado com JSON logs

#### Remoção de Prints
- Todos os `print()` em scripts foram substituídos por `logger.info()` / `logger.warning()` / `logger.error()`
- Emojis removidos (mantém-se funcionais em logs estruturados via extra fields)
- Mensagens resumidas e estruturadas

### Mudanças

#### Requirements
- Adicionado `python-json-logger` para serialização JSON
- Dependência necessária para Cloud Logging integration

#### Importações
- `from app.core.logging import configure_logging, get_logger` em módulos apropriados
- Remoção de `import logging` em favor de `from app.core.logging import get_logger`

#### Loggers
- Todos os `logging.getLogger(__name__)` foram substituídos por `get_logger(__name__)`
- Logger raiz configurado automaticamente em `app/main.py`
- Verbosidade de bibliotecas externas reduzida (urllib3, google, google.cloud)

### Benefícios

- ✅ Compatível com GCP Cloud Logging
- ✅ Filtros estruturados em ferramentas de observabilidade
- ✅ Contexto completo (execution_id, task_id) em cada log
- ✅ Timestamps precisos para correlação
- ✅ Sem perda de informações de debugging
- ✅ Pronto para migração para produção em cloud

### Exemplo de Log Estruturado

```json
{
  "timestamp": "2026-02-10T23:07:58.532793+00:00",
  "level": "info",
  "module": "app.routes.collect",
  "message": "Collection task scheduled",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "execution_id": "a1b2c3d4",
  "sources_count": 2,
  "estimated_time_seconds": 45
}
```

---

## [1.1.0] - 2026-02-10

### 🌐 API REST com FastAPI

Release focada em transformar a aplicação em serviço web, mantendo compatibilidade com execução batch.

### Adicionado

#### API REST Completa
- Endpoint `GET /` - Informações básicas da API
- Endpoint `GET /health` - Health check com verificação BigQuery
- Endpoint `POST /collect` - Coleta assíncrona com parâmetros
- Endpoint `GET /collect/{task_id}` - Consulta resultado de tasks
- Documentação automática (Swagger UI + ReDoc)

#### Coleta Assíncrona
- BackgroundTasks do FastAPI para requisições não-bloqueantes
- Cache em memória para resultados de tasks
- Estimativa de tempo de execução
- Suporte a coleta sem persistência BigQuery

#### Schemas de API
- `HealthResponse` - Status da API e serviços
- `CollectRequest` - Parâmetros de coleta com validação
- `CollectResponse` - Aceitação de task (HTTP 202)
- `CollectResult` - Resultado final da coleta
- `ErrorResponse` - Respostas de erro padronizadas

#### Tratamento de Erros
- Exception handlers para HTTPException e exceções genéricas
- Respostas JSON padronizadas com timestamp
- Logging estruturado com contexto completo
- Serialização correta de datetime

#### Refatoração de Código
- Arquivo `app/main.py` reduzido de 329 → 76 linhas (76% menor)
- Nova pasta `app/routes/` com rotas separadas:
  - `root.py` - Endpoint raiz
  - `health.py` - Health check
  - `collect.py` - Endpoints de coleta
- Registro centralizado de routers em `__init__.py`

#### Containerização
- Dockerfile atualizado: `CMD` inicia uvicorn (API padrão)
- Docker Compose expõe porta 8000
- Restart policy `unless-stopped` para API sempre rodando
- Suporte contínuo para execução de scripts batch

### Mudado

- `app/main.py` - Refatorado para usar routers (arquitetura mais limpa)
- `Dockerfile` - CMD agora inicia `uvicorn app.main:app`
- `docker-compose.yml` - Mapeamento de porta, restart policy
- `README.md` - Nova seção completa de API REST com 200+ linhas
- `scripts/bigquery_teste.py` - Auto-descoberta de credenciais em `secrets/`

### Corrigido

- ❌ Bug: `datetime` não JSON serializable em respostas de erro
  - ✅ Solução: Usar `.model_dump(mode="json")` nos exception handlers
  
- ❌ Bug: Nome de arquivo JSON hardcoded no docker-compose
  - ✅ Solução: Remover e fazer auto-descoberta no script
  
- ❌ Bug: Informações sensíveis expostas no README
  - ✅ Solução: Substituir por placeholders genéricos
  
- ❌ Bug: GOOGLE_APPLICATION_CREDENTIALS hardcoded no bigquery_teste.py
  - ✅ Solução: Buscar automaticamente arquivos .json em `secrets/`

### Documentação

- Adicionada seção "🌐 API REST com FastAPI" no README
- Exemplos completos de uso (cURL, Python)
- Tabela de parâmetros e validações
- Códigos HTTP e estrutura de erro
- Diagrama de containers Docker
- Arquivo RELEASE_v1.1.0.md com notas detalhadas

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
