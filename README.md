# Desafio Técnico: Coletor de promoções do Mercado Livre

[![CI](https://github.com/phaelzin/prototipo-coletor-promo/actions/workflows/ci.yml/badge.svg)](https://github.com/phaelzin/prototipo-coletor-promo/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/phaelzin/prototipo-coletor-promo?include_prereleases)](https://github.com/phaelzin/prototipo-coletor-promo/releases)
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
└── requirements.txt           # Dependências Python
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
- [ ] API FastAPI com endpoint `/health`
- [ ] Dockerfile e docker-compose
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

### v0.3.0 - Coleta Multi-Fonte com Paginação
- Implementado `fetch_from_sources()` para coleta de múltiplas queries
- Implementado `fetch_products_paginated()` com paginação dinâmica
- Suporte a 3 fontes simultâneas: monitor gamer, iphone, ps5
- Estatísticas de coleta por fonte

### v0.2.0 - Integração BigQuery
- Criado serviço `BigQueryService` para persistência
- Schema da tabela `promotions` com todos os campos do desafio
- **Deduplicação** via verificação pré-inserção com `dedupe_key`
- Inserção via LOAD JOB (compatível com free tier GCP)
- Métodos de estatísticas e busca de produtos recentes

### v0.1.0 - MVP Coleta
- Serviço de web scraping com BeautifulSoup
- Normalização de dados com Pydantic
- Retry com backoff exponencial (tenacity)
- Extração de preço, desconto, vendedor, imagem

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
git tag -a v0.3.0 -m "Release v0.3.0 - Coleta Multi-Fonte"
git push origin v0.3.0
```

O GitHub Actions criará automaticamente a release com os artefatos.

---

> Desenvolvido para o processo seletivo PromoZone