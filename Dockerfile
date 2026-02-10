# Stage 1: Builder - instala dependências
FROM python:3.12-slim as builder

# Instala dependências de sistema necessárias para compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copia apenas requirements.txt primeiro (otimização de cache)
COPY requirements.txt .

# Cria virtualenv e instala dependências
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime - imagem final otimizada
FROM python:3.12-slim

# Cria usuário não-root por segurança
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Copia o virtualenv do builder
COPY --from=builder /opt/venv /opt/venv

# Copia o código da aplicação
COPY app/ ./app/
COPY scripts/ ./scripts/

# Configura PATH para usar o virtualenv
ENV PATH="/opt/venv/bin:$PATH"

# Variáveis de ambiente padrão (podem ser sobrescritas)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    GCP_PROJECT_ID=promozone-ml \
    GCP_DATASET_ID=promocoes_teste \
    LOG_LEVEL=INFO \
    ENABLE_CLOUD_LOGGING=true

# Cria diretório para secrets (credenciais GCP)
RUN mkdir -p /app/secrets && chmod 700 /app/secrets && \
    chown -R appuser:appuser /app

# Muda para usuário não-root
USER appuser

# Expõe porta da API
EXPOSE 8000

# Comando padrão: inicia a API FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

