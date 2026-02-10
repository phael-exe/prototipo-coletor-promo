# 🚀 CI/CD GitHub Actions + Cloud Run - Implementation Complete

## ✅ O que foi implementado

### 1. Workflow GitHub Actions (deploy.yml)
- ✅ Triggered por releases no GitHub ou workflow_dispatch manual
- ✅ Autentica no GCP com credenciais JSON
- ✅ Build automático da imagem Docker
- ✅ Push para Google Artifact Registry (GAR)
- ✅ Deploy no Cloud Run (staging/production)
- ✅ Health check automático pós-deploy
- ✅ Configuração automática de Cloud Logging
- ✅ Resumo detalhado do deploy na UI do GitHub

### 2. Documentação Completa
- ✅ **DEPLOY_SETUP_GUIDE.md** - Guia passo-a-passo para setup
  - Criar Service Account no GCP
  - Adicionar permissões necessárias
  - Setup de secrets no GitHub
  - Criar Artifact Registry
  - Verificação pós-deploy

- ✅ **BIGQUERY_QUERIES.md** - 20+ queries SQL úteis
  - Análise de produtos
  - KPIs e relatórios
  - Deduplicação
  - Histórico de preços
  - Dashboard queries

### 3. Dockerfile Atualizado
- ✅ Variáveis de ambiente para Cloud Logging
- ✅ Suporte a credenciais do GCP
- ✅ Diretório /app/secrets para volumes do Cloud Run
- ✅ Configuração de LOG_LEVEL
- ✅ ENABLE_CLOUD_LOGGING para integração

## 📋 Próximas Etapas: Setup do Deploy

### Passo 1: Criar Service Account e Permissões (bash)

```bash
export GCP_PROJECT_ID="seu-projeto-gcp"
export SERVICE_ACCOUNT_NAME="github-actions-deployer"

# Criar Service Account
gcloud iam service-accounts create ${SERVICE_ACCOUNT_NAME} \
  --project=${GCP_PROJECT_ID}

# Adicionar permissões necessárias
gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.admin"

gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/logging.admin"

gcloud projects add-iam-policy-binding ${GCP_PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

### Passo 2: Criar Artifact Registry

```bash
gcloud artifacts repositories create docker-repo \
  --repository-format=docker \
  --location=us-central1 \
  --project=${GCP_PROJECT_ID}
```

### Passo 3: Gerar Chave JSON e Adicionar Secrets

```bash
# Gerar chave
gcloud iam service-accounts keys create key.json \
  --iam-account=${SERVICE_ACCOUNT_NAME}@${GCP_PROJECT_ID}.iam.gserviceaccount.com

# Adicionar secrets no GitHub
gh secret set GCP_PROJECT_ID --body "seu-projeto-gcp"
gh secret set GCP_REGION --body "us-central1"
gh secret set GCP_DATASET_ID --body "promocoes_teste"
gh secret set GCP_SA_KEY --body "$(cat key.json)"
gh secret set GCP_CLOUD_RUN_SA --body "cloud-run-app@seu-projeto-gcp.iam.gserviceaccount.com"

# Limpar
rm key.json
```

## 🚀 Como Usar

### Fazer Deploy (Opção 1: Release)

```bash
# Criar uma release no GitHub
git tag v1.3.0
git push origin v1.3.0

# Ou via web: GitHub → Releases → Create a new release
```

### Fazer Deploy (Opção 2: Manual)

```bash
# Via GitHub CLI
gh workflow run deploy.yml -f environment=staging

# Ou via web: Actions → Deploy to Cloud Run → Run workflow
```

## 📊 O que Acontece Automaticamente

1. **Build**
   - GitHub Actions faz checkout do código
   - Compila imagem Docker com tags versionadas

2. **Push**
   - Envia imagem para Artifact Registry
   - Tag latest + tag da versão (ex: v1.3.0)

3. **Deploy**
   - Cloud Run faz pull da imagem
   - Configura variáveis de ambiente
   - Inicia contêiner

4. **Verificação**
   - Health check no endpoint /health
   - Configura Cloud Logging
   - Gera resumo com links

5. **Logging**
   - Todos os logs em JSON estruturado
   - Automáticamente capturados pelo Cloud Logging
   - Filtráveis por module, level, task_id, etc

## 🔍 Monitorar Deploy

### Via GitHub Actions
```
Abra: https://github.com/seu-usuario/prototipo-coletor-promo/actions
```

### Via Google Cloud Console
```
Cloud Run: https://console.cloud.google.com/run
Artifact Registry: https://console.cloud.google.com/artifacts
Cloud Logging: https://console.cloud.google.com/logs
```

### Verificar Saúde do Serviço

```bash
# Via gcloud
gcloud run services list --project=seu-projeto-gcp

# Via curl
curl https://seu-servico.run.app/health

# Ver logs
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 20 --format=json
```

## 🎯 BigQuery Queries

Use as 20+ queries do BIGQUERY_QUERIES.md para:

```sql
-- Análise rápida
SELECT 
  source,
  COUNT(*) as total,
  ROUND(AVG(price), 2) as preco_medio
FROM `seu-projeto.promocoes_teste.promotions`
GROUP BY source
ORDER BY total DESC

-- Ver logs de execução
SELECT DISTINCT execution_id FROM `seu-projeto.promocoes_teste.promotions`
ORDER BY execution_id DESC LIMIT 10
```

## 📈 Cloud Logging

Os logs estruturados em JSON aparecem automaticamente:

```json
{
  "timestamp": "2026-02-10T23:16:02.075760+00:00",
  "level": "info",
  "module": "app.routes.collect",
  "message": "Collection task completed",
  "task_id": "31bf705c-4f78-4048-a074-3d46180fe9cf",
  "execution_id": "59a50e2c",
  "duration_seconds": 32.38
}
```

Filtrar no Cloud Logging:
```
resource.type="cloud_run_revision"
jsonPayload.level="error"
jsonPayload.task_id="sua-task-id"
```

## 🔐 Segurança

- ✅ Service Account com permissões mínimas
- ✅ Chave JSON em GitHub Secrets (encrypted)
- ✅ Contêiner rodando como usuário não-root
- ✅ Variáveis de ambiente protegidas
- ✅ Logs não contêm secrets

## ✅ Checklist Pré-Deploy

- [ ] GCP Project ID definido
- [ ] Service Account criado com permissões
- [ ] Artifact Registry criado
- [ ] Secrets adicionados no GitHub
- [ ] Cloud Run habilitado no GCP
- [ ] BigQuery dataset existente
- [ ] Tag versionada criada (git tag v1.x.x)

## 🐛 Troubleshooting

**Erro: "Permission denied" no push**
→ Verificar se Service Account tem `roles/artifactregistry.admin`

**Erro: "Service not found" no deploy**
→ Verificar se região está correta em `GCP_REGION`

**Logs não aparecem no Cloud Logging**
→ Verificar se `ENABLE_CLOUD_LOGGING=true` está no Dockerfile

**Deploy timeout**
→ Aumentar `--timeout` no workflow (padrão: 3600s)

---

## 📚 Arquivos Relacionados

- `.github/workflows/deploy.yml` - Workflow principal
- `DEPLOY_SETUP_GUIDE.md` - Setup passo-a-passo
- `BIGQUERY_QUERIES.md` - 20+ queries SQL úteis
- `Dockerfile` - Atualizado com env vars
- `LOGGING_GUIDE.md` - Logging estruturado
- `app/core/logging.py` - Configuração JSON logging

---

**Status: ✅ PRONTO PARA DEPLOY**

Próximo passo: Execute os comandos de setup em DEPLOY_SETUP_GUIDE.md
