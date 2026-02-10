# 📊 Structured JSON Logging Guide

Este documento descreve o sistema de logging estruturado em JSON implementado no projeto.

## 🎯 Objetivo

Migrar de logs em texto simples para JSON estruturado, facilitando:
- Integração com GCP Cloud Logging
- Filtragem e busca de logs estruturados
- Correlação de eventos via execution_id e task_id
- Monitoramento e alertas em tempo real

## 🏗️ Arquitetura

### Módulo Principal: `app/core/logging.py`

```python
from app.core.logging import configure_logging, get_logger

# Configuração (normalmente feita em app/main.py)
configure_logging(level="INFO")

# Criar logger por módulo
logger = get_logger(__name__)
```

### CustomJsonFormatter

Classe personalizada que estende `pythonjsonlogger.JsonFormatter` com:
- ✅ Timestamps em ISO 8601 com timezone UTC
- ✅ Normalização de níveis para minúsculas
- ✅ Nome do módulo em campo `module`
- ✅ Suporte a `execution_id` quando disponível
- ✅ Tratamento correto de exceções

## 📋 Campos JSON Padrão

Todo log estruturado inclui:

```json
{
  "timestamp": "2026-02-10T23:08:35.328215+00:00",
  "level": "info",
  "name": "app.routes.collect",
  "module": "app.routes.collect",
  "message": "Collection task scheduled",
  
  // Campos opcionais via extra={}
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "execution_id": "a1b2c3d4",
  "sources_count": 2,
  "estimated_time_seconds": 45
}
```

### Campos Obrigatórios

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `timestamp` | string (ISO 8601) | Quando o log foi gerado (UTC) |
| `level` | string | Nível do log (debug, info, warning, error, critical) |
| `name` | string | Logger name (geralmente `__name__`) |
| `module` | string | Nome do módulo que gerou o log |
| `message` | string | Mensagem principal |

### Campos Opcionais (Via `extra={}`)

Podem ser adicionados ao chamar o logger:

```python
logger.info("Task completed", extra={
    "task_id": task_id,
    "execution_id": execution_id,
    "total_products": 150,
    "duration_seconds": 45.3
})
```

## 💻 Como Usar

### 1. Configurar no Startup (app/main.py)

```python
from app.core.logging import configure_logging, get_logger

# Configura o logger raiz
configure_logging(level="INFO")

# Cria logger para o módulo
logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API",
               extra={"project": settings.PROJECT_NAME})
    yield
    logger.info("Shutting down API")
```

### 2. Usar em Módulos Específicos

```python
from app.core.logging import get_logger

logger = get_logger(__name__)

def process_data(user_id, items):
    logger.info("Processing user data",
               extra={
                   "user_id": user_id,
                   "item_count": len(items)
               })
    
    try:
        # ... código ...
    except Exception as e:
        logger.error("Processing failed",
                    extra={"error": str(e), "user_id": user_id},
                    exc_info=True)
```

### 3. Adicionar Contexto

```python
# Log simples
logger.info("User logged in")

# Com contexto
logger.info("User logged in", extra={
    "user_id": "12345",
    "ip_address": "192.168.1.1",
    "session_id": "abc123"
})
```

## 📊 Exemplos Reais

### Coleta de Produtos

```python
logger.info("Starting collection task",
           extra={
               "task_id": task_id,
               "execution_id": execution_id,
               "sources": ["monitor gamer", "ps5"],
               "limit_per_source": 100
           })
```

Resultado JSON:
```json
{
  "timestamp": "2026-02-10T23:08:35.328215+00:00",
  "level": "info",
  "name": "app.routes.collect",
  "module": "app.routes.collect",
  "message": "Starting collection task",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "execution_id": "a1b2c3d4",
  "sources": ["monitor gamer", "ps5"],
  "limit_per_source": 100
}
```

### Health Check

```python
try:
    bq = BigQueryService()
    bq.client.get_dataset(bq.dataset_id)
    logger.info("BigQuery health check passed",
               extra={"service": "bigquery"})
except Exception as e:
    logger.error("BigQuery health check failed",
                extra={"service": "bigquery", "error": str(e)},
                exc_info=True)
```

### Tratamento de Erros

```python
except Exception as e:
    logger.error("Critical error during search",
                extra={
                    "query": search_term,
                    "limit": limit,
                    "error_type": type(e).__name__
                },
                exc_info=True)  # Inclui stack trace
```

## 🔍 Filtragem em Cloud Logging

No GCP Cloud Logging, você pode filtrar logs com:

```
resource.type="cloud_run_revision"
jsonPayload.level="error"
jsonPayload.task_id="550e8400-e29b-41d4-a716-446655440000"
```

## 📚 Níveis de Log

| Nível | Uso | Exemplo |
|-------|-----|---------|
| `DEBUG` | Informações detalhadas de debug | Valores de variáveis, fluxo de execução |
| `INFO` | Eventos importantes | Startup, task iniciada, operação concluída |
| `WARNING` | Situações inesperadas | Falha em serviço opcional, retry automático |
| `ERROR` | Erros que não interrompem execução | Falha ao conectar BigQuery, dados inválidos |
| `CRITICAL` | Erros críticos | Falha ao iniciar aplicação |

## 🛠️ Configuração

### Mudar Nível de Log

```python
from app.core.logging import configure_logging

# Em production
configure_logging(level="INFO")

# Em desenvolvimento
configure_logging(level="DEBUG")
```

### Adicionar Campos Customizados

O formatter já adiciona automaticamente:
- `timestamp` - ISO 8601
- `level` - minúsculas
- `module` - nome do logger

Você pode adicionar quantos campos desejar via `extra`:

```python
logger.info("Custom event", extra={
    "custom_field_1": "value1",
    "custom_field_2": 12345,
    "custom_field_3": ["list", "of", "values"]
})
```

## 🚀 Integração com Cloud Logging

Os logs JSON são automaticamente compatíveis com:
- **GCP Cloud Logging** (recomendado)
- **AWS CloudWatch** (com configuração adicional)
- **Datadog** (com agente)
- **ELK Stack** (Elasticsearch, Logstash, Kibana)

### Exemplo Deploy em Cloud Run

```bash
# Build e push da imagem
docker build -t gcr.io/seu-projeto/coletor .
docker push gcr.io/seu-projeto/coletor

# Deploy no Cloud Run
gcloud run deploy coletor \
  --image gcr.io/seu-projeto/coletor \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

Logs aparecerão automaticamente em Cloud Logging com campos estruturados.

## ✅ Checklist de Implementação

- [x] Criar `app/core/logging.py` com CustomJsonFormatter
- [x] Atualizar `requirements.txt` com `python-json-logger`
- [x] Configurar logging em `app/main.py`
- [x] Atualizar todos os imports de logger (`get_logger`)
- [x] Substituir `print()` por `logger.info()` em scripts
- [x] Adicionar campos estruturados (execution_id, task_id, etc)
- [x] Testar saída JSON de logs
- [x] Remover logs com emojis (mantém-se em extra fields)
- [x] Documentar em CHANGELOG.md

## 📝 Notas Importantes

1. **Não misture logging e print()**: Use logger em toda parte
2. **Sempre inclua contexto relevante**: task_id, user_id, execution_id
3. **Use exc_info=True para exceções**: `logger.error(..., exc_info=True)`
4. **Timestamps são automáticos**: Não adicione manualmente
5. **Níveis normalizados**: Use lowercase ao filtrar (info, warning, error)

## 🔗 Referências

- [python-json-logger](https://github.com/mdomenicodos/python-json-logger)
- [GCP Cloud Logging](https://cloud.google.com/logging/docs)
- [Python logging docs](https://docs.python.org/3/library/logging.html)
