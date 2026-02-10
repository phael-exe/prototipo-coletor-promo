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
    GCP_DATASET_ID=promocoes_teste

# Muda para usuário não-root
USER appuser

# Comando padrão: executa o script principal
CMD ["python3", "scripts/bigquery_teste.py"]

