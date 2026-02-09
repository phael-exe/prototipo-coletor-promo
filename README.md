# Desafio Técnico: Coletor de promoções do Mercado Livre

## 📋 Visão Geral

Protótipo de um coletor de promoções do Mercado Livre que realiza:
- **Coleta** de produtos via web scraping
- **Normalização** dos dados em um modelo consistente
- **Persistência** no BigQuery (em desenvolvimento)
- **Deduplicação** para evitar registros repetidos (em desenvolvimento)

## 🏗️ Arquitetura

```
prototipo-coletor-promo/
├── app/
│   ├── core/
│   │   └── config.py          # Configurações via variáveis de ambiente
│   ├── schemas/
│   │   └── product.py         # Schema Pydantic dos produtos
│   └── services/
│       └── crawler.py         # Serviço de web scraping
├── scripts/
│   └── crawler_teste.py       # Script de teste da coleta
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
```

### 3. Testar a coleta

```bash
python scripts/crawler_teste.py
```

## 📦 Módulos Implementados

### Web Scraping (`app/services/crawler.py`)

Serviço de coleta que:
- Faz requisições HTTP com User-Agent configurável
- Extrai dados do HTML usando BeautifulSoup
- Implementa retry com backoff exponencial (tenacity)
- Suporta busca por query ou URL direta

**Campos extraídos:**
| Campo | Descrição |
|-------|----------- |
| `item_id` | ID único do produto (ex: MLB12345678) |
| `title` | Título do produto |
| `price` | Preço atual |
| `original_price` | Preço original (se houver desconto) |
| `url` | Link direto para o produto |
| `image_url` | URL da imagem principal |
| `currency` | Moeda (BRL) |

### Schema (`app/schemas/product.py`)

Modelo Pydantic para validação e normalização dos dados.

## 🔧 Configurações (`app/core/config.py`)

| Variável | Descrição | Default |
|----------|-----------|----------|
| `USER_AGENT` | User-Agent para requisições | Chrome Linux |
| `MAX_RETRIES` | Tentativas máximas em caso de falha | 3 |
| `RETRY_MIN_SECONDS` | Tempo mínimo entre retries | 2 |
| `RETRY_MAX_SECONDS` | Tempo máximo entre retries | 10 |

## 📝 Próximos Passos

- [ ] Completar normalização (adicionar `marketplace`, `source`, `discount_percent`, `collected_at`, `dedupe_key`, `execution_id`)
- [ ] Integração com BigQuery
- [ ] Implementar deduplicação
- [ ] API FastAPI com endpoint `/health`
- [ ] Containerização (Dockerfile)
- [ ] Deploy no GCP (Cloud Run)

## 🛠️ Tecnologias

- **Python 3.12**
- **Requests** - Requisições HTTP
- **BeautifulSoup4** - Parsing de HTML
- **Pydantic** - Validação de dados
- **Tenacity** - Retry com backoff

---

> Desenvolvido para o processo seletivo PromoZone

