# 🚀 GitHub Actions CI/CD Setup Guide

Guia completo para configurar o deploy automático no Cloud Run via GitHub Actions.

## 📋 Pré-requisitos

- ✅ Conta GCP com projeto ativo
- ✅ Artifact Registry habilitado
- ✅ Cloud Run habilitado
- ✅ Repositório GitHub com o código

## 1️⃣ Criar Service Account no GCP

### Passo 1: Criar a Service Account

```bash
# Defina as variáveis
export GCP_PROJECT_ID="seu-projeto-gcp"
export SERVICE_ACCOUNT_NAME="github-actions-deployer"

# Criar Service Account
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
  --project=${GCP_PROJECT_ID} \
  --display-name="GitHub Actions CI/CD Deployer"
```

### Passo 2: Adicionar Permissões Necessárias

```bash
# Permissões no Artifact Registry
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

# Permissões no Cloud Run
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Permissões para passar Service Account ao Cloud Run
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Permissões para Cloud Logging
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.admin"

# Permissões para BigQuery
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

### Passo 3: Criar Chave JSON

```bash
# Criar chave JSON
gcloud iam service-accounts keys create key.json \
  --iam-account=${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --project=${GCP_PROJECT_ID}

# Salvar o conteúdo para adicionar como secret
cat key.json
```

## 2️⃣ Adicionar Secrets no GitHub

### Via GitHub Web UI

1. Vá para: **Settings → Secrets and variables → Actions → New repository secret**

### Via GitHub CLI

```bash
# Configure com seu repositório
export GITHUB_REPO="seu-usuario/prototipo-coletor-promo"

# Adicione os secrets
gh secret set GCP_PROJECT_ID \
  --repo ${GITHUB_REPO} \
  --body "seu-projeto-gcp"

gh secret set GCP_REGION \
  --repo ${GITHUB_REPO} \
  --body "us-central1"

gh secret set GCP_DATASET_ID \
  --repo ${GITHUB_REPO} \
  --body "promocoes_teste"

gh secret set GCP_SA_KEY \
  --repo ${GITHUB_REPO} \
  --body "$(cat key.json)"

gh secret set GCP_CLOUD_RUN_SA \
  --repo ${GITHUB_REPO} \
  --body "cloud-run-sa@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
```

## 3️⃣ Criar Artifact Registry Repository

```bash
# Criar repositório no Artifact Registry
gcloud artifacts repositories create docker-repo \
  --repository-format=docker \
  --location=us-central1 \
  --project=${GCP_PROJECT_ID}

# Verificar
gcloud artifacts repositories list --project=${GCP_PROJECT_ID}
```

## 4️⃣ Criar Cloud Run Service Account (para a aplicação)

```bash
# Criar Service Account para a aplicação
gcloud iam service-accounts create cloud-run-app \
  --project=${GCP_PROJECT_ID} \
  --display-name="Cloud Run Application Service Account"

# Adicionar permissões para BigQuery
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:cloud-run-app@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

# Adicionar permissões para Cloud Logging
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:cloud-run-app@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# Criar credenciais JSON para a aplicação
gcloud iam service-accounts keys create app-credentials.json \
  --iam-account=cloud-run-app@${GCP_PROJECT_ID}.iam.gserviceaccount.com \
  --project=${GCP_PROJECT_ID}

# Adicionar como secret no GitHub
gh secret set GCP_APP_CREDENTIALS \
  --repo ${GITHUB_REPO} \
  --body "$(cat app-credentials.json)"
```

## 5️⃣ Secrets Necessários no GitHub

Adicione estes secrets no repositório:

| Secret | Descrição | Exemplo |
|--------|-----------|---------|
| `GCP_PROJECT_ID` | ID do projeto GCP | `seu-projeto-gcp` |
| `GCP_REGION` | Região GCP | `us-central1` |
| `GCP_DATASET_ID` | Dataset do BigQuery | `promocoes_teste` |
| `GCP_SA_KEY` | Chave JSON da Service Account (GitHub Actions) | Conteúdo do `key.json` |
| `GCP_CLOUD_RUN_SA` | Email da Cloud Run Service Account | `cloud-run-app@seu-projeto-gcp.iam.gserviceaccount.com` |

## 🔧 Configuração no .env (Local)

Para desenvolvimento local, crie um `.env`:

```bash
GCP_PROJECT_ID=seu-projeto-gcp
GCP_DATASET_ID=promocoes_teste
ENVIRONMENT=development
LOG_LEVEL=DEBUG
ENABLE_CLOUD_LOGGING=false
```

## 🚀 Triggering Deployments

### Opção 1: Release no GitHub (Automático)

```bash
# Criar tag e push
git tag v1.2.0
git push origin v1.2.0

# Ou via GitHub Web UI: Releases → Create a new release
```

O workflow `deploy.yml` será disparado automaticamente.

### Opção 2: Manual (workflow_dispatch)

```bash
# Via GitHub CLI
gh workflow run deploy.yml \
  --repo seu-usuario/prototipo-coletor-promo \
  -f environment=staging

# Ou via Web UI: Actions → Deploy to Cloud Run → Run workflow
```

## 📊 Cloud Logging Configuration

O workflow já configura automaticamente:

1. **JSON Structured Logs**: Todos os logs da aplicação em formato JSON
2. **Log Sink**: Separa logs estruturados em um projeto separado
3. **Environment Variables**: Define LOG_LEVEL e ENABLE_CLOUD_LOGGING

### Acessar Logs no GCP

```bash
# Via gcloud CLI
gcloud logging read "resource.type=cloud_run_revision AND jsonPayload.module=~'app.*'" \
  --project=${GCP_PROJECT_ID} \
  --limit 50 \
  --format=json | jq .

# Via Web UI
# https://console.cloud.google.com/logs/query?project=seu-projeto-gcp
```

## ✅ Verificação Pós-Deploy

Após o deploy, verifique:

```bash
# 1. Serviço rodando
gcloud run services list --project=${GCP_PROJECT_ID}

# 2. Health check
curl https://seu-servico.run.app/health

# 3. Logs recentes
gcloud logging read "resource.type=cloud_run_revision" \
  --project=${GCP_PROJECT_ID} \
  --limit 10 \
  --format=json

# 4. BigQuery tables
gcloud bq ls --project_id=${GCP_PROJECT_ID} seu_dataset
```

## 🔐 Limpeza de Chaves

```bash
# Remover arquivos sensíveis
rm -f key.json app-credentials.json

# Revogar chaves antigas (se necessário)
gcloud iam service-accounts keys list \
  --iam-account=${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com

gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com
```

## 📚 Estrutura do Workflow

```yaml
Release Criada
      ↓
Deploy Workflow Iniciado
      ↓
Autenticar no GCP
      ↓
Build Docker Image
      ↓
Push para Artifact Registry
      ↓
Deploy no Cloud Run
      ↓
Verificar Health
      ↓
Configurar Cloud Logging
      ↓
Resumo do Deploy
```

## 🐛 Troubleshooting

### Erro: "Permission denied" ao push

**Solução**: Verifique se a Service Account tem role `roles/artifactregistry.admin`

### Erro: "Service not found" no Cloud Run

**Solução**: Verifique se o nome do serviço corresponde e se a região está correta

### Logs não aparecem no Cloud Logging

**Solução**: Verifique se `ENABLE_CLOUD_LOGGING=true` está setado

### Timeout no health check

**Solução**: Aumente `--timeout` no comando `gcloud run deploy` (padrão: 300s)

## 📖 Próximos Passos

1. ✅ Implementar CI/CD com GitHub Actions
2. ⏳ Adicionar testes automatizados
3. ⏳ Configurar alertas no Cloud Monitoring
4. ⏳ Implementar blue-green deployment
5. ⏳ Adicionar rollback automático

---

**Referências:**
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [GitHub Actions GCP Auth](https://github.com/google-github-actions/auth)
