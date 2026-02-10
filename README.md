# Desafio Técnico: Coletor de promoções do Mercado Livre

[![CI](https://github.com/phael-exe/prototipo-coletor-promo/actions/workflows/ci.yml/badge.svg)](https://github.com/phael-exe/prototipo-coletor-promo/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/phael-exe/prototipo-coletor-promo?include_prereleases)](https://github.com/phaelzin/prototipo-coletor-promo/releases)
[![Python](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 📋 Visão Geral

Protótipo de um coletor de promoções do Mercado Livre que realiza:
- ✅ **Coleta** de produtos via web scraping com paginação dinâmica
- ✅ **Normalização** dos dados em um modelo consistente (Pydantic)
- ✅ **Persistência** no BigQuery (Google Cloud)
- ✅ **Deduplicação** para evitar registros repetidos

## 🏗️ Arquitetura

```
prototipo-coletor-promo/
├── app/
│   ├── core/
│   │   └── config.py          # Configurações via variáveis de ambiente
│   ├── schemas/
│   │   └── product.py         # Schema Pydantic dos produtos
│   └── services/
│       ├── crawler.py         # Serviço de web scraping
│       └── bigquery.py        # Serviço de persistência BigQuery
├── scripts/
│   ├── crawler_teste.py       # Script de teste da coleta
│   └── bigquery_teste.py      # Script de teste completo (coleta + BigQuery)
├── secrets/                   # Credenciais GCP (não versionado)
├── .env                       # Variáveis de ambiente (não versionado)
├── .env.template              # Template das variáveis necessárias
├── .dockerignore              # Exclusões para build Docker
├── Dockerfile                 # Multi-stage build para Python 3.12
├── docker-compose.yml         # Orquestração de containers
├── requirements.txt           # Dependências Python
├── README.md                  # Este arquivo
├── CHANGELOG.md               # Histórico de mudanças
└── LICENSE                    # Licença MIT
```

### 📦 Estrutura de Containers

```
┌─────────────────────────────────────────────────┐
│         docker-compose.yml                      │
│  ┌───────────────────────────────────────────┐  │
│  │  Service: collector                       │  │
│  │  ┌─────────────────────────────────────┐  │  │
│  │  │ Dockerfile (Multi-stage)            │  │  │
│  │  │ • Stage 1 (Builder): gcc + deps     │  │  │
│  │  │ • Stage 2 (Runtime): app only       │  │  │
│  │  │                                     │  │  │
│  │  │ Image: prototipo-coletor-promo      │  │  │
│  │  └─────────────────────────────────────┘  │  │
│  │         ↓                                   │  │
│  │  Volumes:                                   │  │
│  │  • ./secrets → /app/secrets (ro)           │  │
│  │                                             │  │
│  │  Environment:                               │  │
│  │  • .env file (GCP credentials, API keys)   │  │
│  │  • PYTHONUNBUFFERED=1                      │  │
│  │  • GOOGLE_APPLICATION_CREDENTIALS          │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## 🚀 Como Rodar Localmente

### 1. Clonar e configurar ambiente

```bash
git clone <repo-url>
cd prototipo-coletor-promo

# Criar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou: .venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

```bash
cp .env.template .env
# Editar .env com suas configurações
```

Variáveis necessárias:
```env
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36..."
GCP_PROJECT_ID="seu-projeto-gcp"
GCP_DATASET_ID="seu_dataset"
```

### 3. Configurar credenciais GCP

```bash
mkdir secrets
# Copie o arquivo JSON de credenciais do Service Account para:
# secrets/<seu-arquivo>.json
export GOOGLE_APPLICATION_CREDENTIALS="secrets/<seu-arquivo>.json"
```

### 4. Executar coleta completa

```bash
python scripts/bigquery_teste.py
```

---

## 🐳 Como Rodar com Docker

### 1. Build da imagem

```bash
# Build usando docker-compose
docker compose build

# Ou build manual com Docker
docker build -t prototipo-coletor-promo:latest .
```

### 2. Executar com Docker Compose

```bash
# Rodar uma vez e exibir logs
docker compose up

# Rodar em background
docker compose up -d

# Ver logs de execução
docker compose logs -f collector

# Limpar containers e volumes
docker compose down
```

### 3. Executar com Docker direto

```bash
# Sem variáveis de ambiente
docker run --rm \
  -v ./secrets:/app/secrets:ro \
  -v ./.env:/app/.env:ro \
  prototipo-coletor-promo:latest

# Com variáveis de ambiente passadas explicitamente
docker run --rm \
  -v ./secrets:/app/secrets:ro \
  -e GCP_PROJECT_ID="seu-projeto-gcp" \
  -e GCP_DATASET_ID="seu_dataset" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/secrets/gcp-credentials.json" \
  prototipo-coletor-promo:latest
```

### ⚠️ Configurar credenciais GCP para Docker

A containerização requer que as credenciais GCP estejam acessíveis. Existem duas abordagens:

**Opção A: Montar arquivo JSON (Desenvolvimento local)**

```bash
# Certifique-se de que as credenciais estão em ./secrets/
ls ./secrets/gcp-credentials.json

# Execute com volume mounted
docker compose up
```

**Opção B: Passar JSON como variável de ambiente (Cloud Run recomendado)**

1. Converta o arquivo JSON para variável de ambiente:
```bash
export GCP_CREDENTIALS_JSON=$(cat secrets/gcp-credentials.json | base64)
```

2. Modifique o `Dockerfile` (stage 2) para suportar:
```dockerfile
# No Dockerfile, após ENV PYTHONUNBUFFERED=1
ARG GCP_CREDENTIALS_JSON
RUN if [ -n "$GCP_CREDENTIALS_JSON" ]; then \
      echo "$GCP_CREDENTIALS_JSON" | base64 -d > /app/secrets/credentials.json && \
      export GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/credentials.json; \
    fi
```

3. Build e run:
```bash
docker build --build-arg GCP_CREDENTIALS_JSON="$GCP_CREDENTIALS_JSON" \
  -t prototipo-coletor-promo:latest .
```

### 🔍 Verificar imagem Docker

```bash
# Ver tamanho da imagem
docker images prototipo-coletor-promo

# Inspecionar layers
docker inspect prototipo-coletor-promo:latest

# Ver logs do container
docker logs <container-id>
```

### 📋 Variáveis de ambiente no Docker

O `docker-compose.yml` carrega automaticamente do arquivo `.env`:

```env
FIRECRAWL_API_KEY="fc-ca5e63e06bfa4f14ad7a805e07df09a7"
USER_AGENT="Mozilla/5.0 (X11; Linux x86_64)..."
GCP_PROJECT_ID="promozone-ml"
GCP_DATASET_ID="promocoes_teste"
GOOGLE_APPLICATION_CREDENTIALS="secrets/gcp-credentials.json"
```

**Nota**: Variáveis são sobrescritas pelo `docker-compose.yml` se conflitarem.

### 🚀 Deploy no Google Cloud Run

```bash
# 1. Configure gcloud CLI
gcloud auth login
gcloud config set project SEU-PROJETO-GCP

# 2. Build e push para Artifact Registry
gcloud builds submit --tag gcr.io/SEU-PROJETO/coletor-promo:latest

# 3. Deploy como Cloud Run Job
gcloud run jobs create coletor-promocoes \
  --image gcr.io/SEU-PROJETO/coletor-promo:latest \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --set-env-vars GCP_PROJECT_ID=SEU-PROJETO,GCP_DATASET_ID=promocoes_teste

# 4. Executar job
gcloud run jobs execute coletor-promocoes --region us-central1

# 5. Agendar execução periódica com Cloud Scheduler
gcloud scheduler jobs create app-engine coletor-diario \
  --schedule="0 2 * * *" \
  --http-method=POST \
  --uri=https://SEU-REGION-SEU-PROJETO.cloudfunctions.net/trigger-job \
  --oidc-service-account-email=SEU-EMAIL@iam.gserviceaccount.com
```

---

## 📦 Módulos Implementados

### 🔍 Web Scraping (`app/services/crawler.py`)

Serviço de coleta que:
- Faz requisições HTTP com User-Agent configurável
- Extrai dados do HTML usando BeautifulSoup
- Implementa retry com backoff exponencial (tenacity)
- Suporta **múltiplas fontes** de busca simultâneas
- **Paginação dinâmica** automática

**Métodos principais:**
| Método | Descrição |
|--------|-----------|
| `fetch_from_sources()` | Coleta de múltiplas queries com paginação |
| `fetch_products_paginated()` | Coleta paginada de uma query específica |
| `fetch_products()` | Coleta simples (sem paginação) |

**Campos extraídos:**
| Campo | Descrição |
|-------|-----------|
| `marketplace` | Identificador do marketplace (`mercado_livre`) |
| `item_id` | ID único do produto (ex: `MLB12345678`) |
| `title` | Título do produto |
| `price` | Preço atual |
| `original_price` | Preço original (se houver desconto) |
| `discount_percent` | Percentual de desconto calculado |
| `seller` | Nome do vendedor |
| `url` | Link direto para o produto |
| `image_url` | URL da imagem principal |
| `source` | Query que gerou o item |
| `dedupe_key` | Chave única para deduplicação |
| `execution_id` | ID único da execução |
| `collected_at` | Timestamp da coleta |

---

### 🗄️ BigQuery (`app/services/bigquery.py`)

Serviço de persistência que:
- Cria tabela automaticamente se não existir
- Insere dados via **LOAD JOB** (compatível com free tier)
- Implementa **deduplicação** antes da inserção
- Fornece estatísticas da tabela

**Métodos principais:**
| Método | Descrição |
|--------|-----------|
| `insert_products()` | Insere produtos com deduplicação |
| `ensure_table_exists()` | Garante que a tabela existe |
| `get_stats()` | Retorna estatísticas da tabela |
| `get_recent_products()` | Busca produtos recentes |

---

## 🔑 Estratégia de Deduplicação

A deduplicação é implementada usando a estratégia de **verificação pré-inserção** com `dedupe_key`.

### Composição da `dedupe_key`

```
dedupe_key = f"{marketplace}_{item_id}_{price}"
```

Exemplo: `mercado_livre_MLB1234567_1299.90`

### Fluxo de Deduplicação

```
┌─────────────────┐
│  Produtos       │
│  coletados      │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  1. Extrai dedupe_keys dos produtos │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  2. Consulta BigQuery:              │
│     SELECT DISTINCT dedupe_key      │
│     FROM promotions                 │
│     WHERE dedupe_key IN (...)       │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  3. Filtra produtos novos           │
│     (dedupe_key não existe)         │
└────────┬────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────┐
│  4. Insere apenas produtos novos    │
│     via LOAD JOB                    │
└─────────────────────────────────────┘
```

### Por que essa estratégia?

| Vantagem | Descrição |
|----------|-----------|
| **Simplicidade** | Não requer MERGE ou stored procedures |
| **Performance** | Query de verificação é rápida com IN clause |
| **Atomicidade** | Cada inserção é independente |
| **Free Tier** | Funciona sem streaming insert |
| **Idempotência** | Rodar múltiplas vezes não duplica dados |

### Implementação no código

```python
# app/services/bigquery.py

def insert_products(self, products: List[ProductSchema]) -> dict:
    # 1. Busca dedupe_keys existentes
    existing_keys = self._get_existing_dedupe_keys([p.dedupe_key for p in products])
    
    # 2. Filtra apenas produtos novos
    new_products = [p for p in products if p.dedupe_key not in existing_keys]
    duplicates = len(products) - len(new_products)
    
    # 3. Insere apenas os novos
    # ... (LOAD JOB com NDJSON)
```

### Resultado em execução

```
📊 RESULTADO DA INSERÇÃO:
   ✅ Inseridos:   292
   ⏭️  Duplicados:  8
   ❌ Erros:       0
```

---

## 🔧 Configurações (`app/core/config.py`)

| Variável | Descrição | Default |
|----------|-----------|---------|
| `USER_AGENT` | User-Agent para requisições | Chrome Linux |
| `MAX_RETRIES` | Tentativas máximas em caso de falha | 3 |
| `RETRY_MIN_SECONDS` | Tempo mínimo entre retries | 2 |
| `RETRY_MAX_SECONDS` | Tempo máximo entre retries | 10 |
| `GCP_PROJECT_ID` | ID do projeto GCP | `promozone-ml` |
| `GCP_DATASET_ID` | ID do dataset BigQuery | `promocoes_teste` |

---

## 📊 Exemplo de Execução

```bash
$ python scripts/bigquery_teste.py

======================================================================
🗄️  COLETA MULTI-FONTE COM PAGINAÇÃO + BIGQUERY
======================================================================

📋 CONFIGURAÇÃO:
   Fontes: ['monitor gamer 144hz', 'iphone 16', 'ps5']
   Limite por fonte: 100
   Máx. páginas por fonte: 3

📦 monitor gamer 144hz
   Produtos coletados: 100
   Em promoção: 22
   Preço médio: R$ 1383.64

📦 iphone 16
   Produtos coletados: 100
   Em promoção: 45
   Preço médio: R$ 6862.39

📦 ps5
   Produtos coletados: 100
   Em promoção: 17
   Preço médio: R$ 5087.34

🎯 TOTAL COLETADO: 300 produtos

📊 RESULTADO DA INSERÇÃO:
   ✅ Inseridos:   292
   ⏭️  Duplicados:  8
   ❌ Erros:       0

📈 ESTATÍSTICAS DO BIGQUERY:
   Total de produtos:    302
   Itens únicos:         298
   Produtos em promoção: 84
```

---

## 📝 Próximos Passos

- [x] Web scraping com requests + BeautifulSoup
- [x] Normalização completa (todos os campos do desafio)
- [x] Persistência no BigQuery
- [x] Deduplicação por `dedupe_key`
- [x] Coleta multi-fonte com paginação
- [x] Dockerfile e docker-compose
- [ ] API FastAPI com endpoint `/health`
- [ ] Deploy no Cloud Run (GCP)
- [ ] Logs estruturados (JSON)

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Uso |
|------------|-----|
| Python 3.12 | Linguagem principal |
| requests | Requisições HTTP |
| BeautifulSoup4 | Parsing de HTML |
| Pydantic | Validação e schemas |
| tenacity | Retry com backoff |
| google-cloud-bigquery | Persistência no BigQuery |

---

## 📜 Changelog

### v1.0.0 - Primeira Release (2026-02-09) 🎉

MVP completo do coletor de promoções com todas as funcionalidades core:

- **Coleta Multi-Fonte**: suporte a múltiplas queries simultâneas com paginação dinâmica
- **Persistência BigQuery**: integração completa com Google BigQuery via LOAD JOB
- **Deduplicação**: verificação pré-inserção com `dedupe_key` (marketplace + item_id + price)
- **Normalização**: schema Pydantic com todos os campos do desafio
- **CI/CD**: GitHub Actions para lint, validação e releases automáticas

📊 **Métricas de teste**: 300 produtos coletados, 292 inseridos, 8 duplicatas ignoradas

---

## 📜 Versionamento

Este projeto usa [Semantic Versioning](https://semver.org/). 
Veja o [CHANGELOG.md](CHANGELOG.md) para histórico completo de mudanças.

### Como criar uma release

```bash
# Commit suas mudanças
git add .
git commit -m "feat: nova funcionalidade"

# Crie e push a tag
git tag -a v1.1.0 -m "Release v1.1.0 - Nova Feature"
git push origin v1.1.0
```

O GitHub Actions criará automaticamente a release com os artefatos.

---

> Desenvolvido para o processo seletivo PromoZone
