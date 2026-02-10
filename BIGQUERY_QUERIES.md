# 📊 BigQuery SQL Queries

Coleção de queries úteis para análise de dados de promoções coletadas.

## 🔍 Queries Básicas

### 1. Total de Produtos Coletados

```sql
SELECT 
  COUNT(*) as total_products,
  COUNT(DISTINCT dedupe_key) as unique_products,
  COUNT(DISTINCT execution_id) as total_collections,
  MIN(collected_at) as first_collection,
  MAX(collected_at) as last_collection
FROM `{project}.{dataset}.promotions`
```

### 2. Produtos por Fonte

```sql
SELECT 
  source,
  COUNT(*) as total_products,
  COUNT(DISTINCT dedupe_key) as unique_products,
  COUNT(DISTINCT execution_id) as collections_count,
  AVG(price) as average_price,
  MIN(price) as min_price,
  MAX(price) as max_price
FROM `{project}.{dataset}.promotions`
GROUP BY source
ORDER BY total_products DESC
```

### 3. Produtos em Promoção

```sql
SELECT 
  source,
  COUNT(*) as products_on_sale,
  AVG(discount_percent) as avg_discount,
  MAX(discount_percent) as max_discount,
  ROUND(AVG(price), 2) as avg_sale_price
FROM `{project}.{dataset}.promotions`
WHERE discount_percent IS NOT NULL 
  AND discount_percent > 0
GROUP BY source
ORDER BY products_on_sale DESC
```

### 4. Descontos Mais Altos

```sql
SELECT 
  title,
  source,
  price,
  original_price,
  discount_percent,
  url,
  collected_at
FROM `{project}.{dataset}.promotions`
WHERE discount_percent IS NOT NULL
ORDER BY discount_percent DESC
LIMIT 20
```

### 5. Produtos Mais Caros e Mais Baratos

```sql
-- Top 10 mais caros
SELECT 
  'MAIS_CAROS' as categoria,
  title,
  source,
  price,
  original_price,
  collected_at
FROM `{project}.{dataset}.promotions`
ORDER BY price DESC
LIMIT 10

UNION ALL

-- Top 10 mais baratos
SELECT 
  'MAIS_BARATOS' as categoria,
  title,
  source,
  price,
  original_price,
  collected_at
FROM `{project}.{dataset}.promotions`
WHERE price > 0
ORDER BY price ASC
LIMIT 10
```

## 📈 Analytics

### 6. Distribuição de Preços

```sql
SELECT 
  source,
  CASE 
    WHEN price < 100 THEN 'R$ 0 - 100'
    WHEN price < 500 THEN 'R$ 100 - 500'
    WHEN price < 1000 THEN 'R$ 500 - 1000'
    WHEN price < 5000 THEN 'R$ 1000 - 5000'
    ELSE 'R$ 5000+'
  END as faixa_preco,
  COUNT(*) as quantidade,
  AVG(price) as preco_medio
FROM `{project}.{dataset}.promotions`
GROUP BY source, faixa_preco
ORDER BY source, CAST(SPLIT(faixa_preco, ' ')[OFFSET(1)] as FLOAT64)
```

### 7. Evolução de Coletas por Dia

```sql
SELECT 
  DATE(collected_at) as data,
  source,
  COUNT(*) as produtos_coletados,
  COUNT(DISTINCT execution_id) as num_coletas,
  AVG(price) as preco_medio,
  COUNT(CASE WHEN discount_percent > 0 THEN 1 END) as produtos_promo
FROM `{project}.{dataset}.promotions`
GROUP BY data, source
ORDER BY data DESC, source
```

### 8. Estatísticas por Marketplace

```sql
SELECT 
  marketplace,
  COUNT(*) as total_products,
  COUNT(DISTINCT dedupe_key) as unique_items,
  COUNT(DISTINCT source) as search_terms,
  ROUND(AVG(price), 2) as avg_price,
  ROUND(STDDEV(price), 2) as std_dev_price,
  ROUND(COUNT(CASE WHEN discount_percent > 0 THEN 1 END) / COUNT(*) * 100, 2) as pct_on_sale
FROM `{project}.{dataset}.promotions`
GROUP BY marketplace
ORDER BY total_products DESC
```

## 🔎 Busca Específica

### 9. Pesquisar Produto Específico

```sql
SELECT 
  title,
  marketplace,
  source,
  price,
  original_price,
  discount_percent,
  url,
  collected_at,
  execution_id
FROM `{project}.{dataset}.promotions`
WHERE LOWER(title) LIKE '%iphone%'
ORDER BY discount_percent DESC, price ASC
LIMIT 50
```

### 10. Comparar Preços do Mesmo Produto

```sql
SELECT 
  dedupe_key,
  title,
  marketplace,
  source,
  price,
  original_price,
  collected_at,
  ROW_NUMBER() OVER (PARTITION BY dedupe_key ORDER BY price ASC) as price_rank
FROM `{project}.{dataset}.promotions`
WHERE LOWER(title) LIKE '%monitor%'
ORDER BY dedupe_key, price ASC
```

## 📊 Relatórios

### 11. Relatório Diário de Coletas

```sql
SELECT 
  DATE(collected_at) as data,
  COUNT(*) as total_coletado,
  COUNT(DISTINCT execution_id) as num_execucoes,
  COUNT(DISTINCT source) as num_fontes,
  ARRAY_AGG(DISTINCT source IGNORE NULLS) as fontes,
  ROUND(AVG(price), 2) as preco_medio,
  MIN(price) as preco_minimo,
  MAX(price) as preco_maximo,
  COUNTIF(discount_percent > 0) as produtos_promo,
  ROUND(COUNTIF(discount_percent > 0) / COUNT(*) * 100, 2) as pct_desconto
FROM `{project}.{dataset}.promotions`
WHERE DATE(collected_at) = CURRENT_DATE()
GROUP BY data
```

### 12. Resumo por Execução

```sql
SELECT 
  execution_id,
  COUNT(*) as produtos,
  COUNT(DISTINCT source) as fontes,
  COUNT(DISTINCT marketplace) as marketplaces,
  MIN(collected_at) as inicio,
  MAX(collected_at) as fim,
  TIMESTAMP_DIFF(MAX(collected_at), MIN(collected_at), SECOND) as duracao_segundos,
  ROUND(AVG(price), 2) as preco_medio,
  COUNTIF(discount_percent > 0) as produtos_promo
FROM `{project}.{dataset}.promotions`
GROUP BY execution_id
ORDER BY MIN(collected_at) DESC
LIMIT 20
```

## 🔄 Deduplicação

### 13. Encontrar Duplicatas

```sql
SELECT 
  dedupe_key,
  title,
  COUNT(*) as vezes_coletado,
  ARRAY_AGG(DISTINCT execution_id) as executions,
  MIN(collected_at) as primeira_coleta,
  MAX(collected_at) as ultima_coleta,
  TIMESTAMP_DIFF(MAX(collected_at), MIN(collected_at), HOUR) as horas_entre_coletas
FROM `{project}.{dataset}.promotions`
GROUP BY dedupe_key, title
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC
LIMIT 50
```

### 14. Histórico de Preços de um Produto

```sql
SELECT 
  dedupe_key,
  title,
  collected_at,
  price,
  original_price,
  discount_percent,
  execution_id,
  LAG(price) OVER (PARTITION BY dedupe_key ORDER BY collected_at) as preco_anterior,
  ROUND((price - LAG(price) OVER (PARTITION BY dedupe_key ORDER BY collected_at)) / 
        LAG(price) OVER (PARTITION BY dedupe_key ORDER BY collected_at) * 100, 2) as variacao_pct
FROM `{project}.{dataset}.promotions`
WHERE LOWER(title) LIKE '%ps5%'
ORDER BY collected_at DESC
```

## 🎯 KPIs

### 15. KPI Dashboard Query

```sql
WITH stats AS (
  SELECT 
    COUNT(*) as total_products,
    COUNT(DISTINCT dedupe_key) as unique_products,
    COUNT(DISTINCT execution_id) as total_executions,
    COUNT(DISTINCT DATE(collected_at)) as days_with_data,
    ROUND(AVG(price), 2) as avg_price,
    COUNT(CASE WHEN discount_percent > 0 THEN 1 END) as products_on_sale,
    ROUND(COUNT(CASE WHEN discount_percent > 0 THEN 1 END) / COUNT(*) * 100, 2) as pct_on_sale
  FROM `{project}.{dataset}.promotions`
),
last_24h AS (
  SELECT 
    COUNT(*) as last_24h_products,
    COUNT(DISTINCT execution_id) as last_24h_executions
  FROM `{project}.{dataset}.promotions`
  WHERE collected_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
)
SELECT 
  s.*,
  l.last_24h_products,
  l.last_24h_executions
FROM stats s, last_24h l
```

## 🏪 Por Marketplace

### 16. Performance por Marketplace

```sql
SELECT 
  marketplace,
  source,
  COUNT(*) as total_items,
  COUNT(DISTINCT dedupe_key) as unique_items,
  ROUND(AVG(price), 2) as avg_price,
  ROUND(PERCENTILE_CONT(price, 0.5) OVER (PARTITION BY marketplace), 2) as median_price,
  COUNTIF(discount_percent > 0) as on_sale,
  ROUND(COUNTIF(discount_percent > 0) / COUNT(*) * 100, 2) as pct_discount,
  ROUND(AVG(discount_percent), 2) as avg_discount_pct
FROM `{project}.{dataset}.promotions`
GROUP BY marketplace, source
ORDER BY marketplace, total_items DESC
```

### 17. Seller Analysis

```sql
SELECT 
  seller,
  COUNT(*) as total_products,
  COUNT(DISTINCT dedupe_key) as unique_products,
  COUNT(DISTINCT source) as search_terms,
  ROUND(AVG(price), 2) as avg_price,
  COUNTIF(discount_percent > 0) as on_sale,
  ROUND(COUNTIF(discount_percent > 0) / COUNT(*) * 100, 2) as pct_discount
FROM `{project}.{dataset}.promotions`
WHERE seller IS NOT NULL AND seller != ''
GROUP BY seller
ORDER BY total_products DESC
LIMIT 50
```

## ⚡ Otimizações

### 18. Produtos Mais Buscados

```sql
SELECT 
  source,
  COUNT(*) as vezes_encontrado,
  COUNT(DISTINCT execution_id) as coletas_com_resultado,
  ROUND(AVG(price), 2) as preco_medio,
  COUNT(CASE WHEN discount_percent > 0 THEN 1 END) as com_promocao
FROM `{project}.{dataset}.promotions`
GROUP BY source
ORDER BY vezes_encontrado DESC
LIMIT 20
```

### 19. Qualidade dos Dados

```sql
SELECT 
  'total_records' as metrica,
  COUNT(*) as valor
FROM `{project}.{dataset}.promotions`

UNION ALL

SELECT 
  'missing_price',
  COUNTIF(price IS NULL OR price = 0)
FROM `{project}.{dataset}.promotions`

UNION ALL

SELECT 
  'missing_title',
  COUNTIF(title IS NULL OR title = '')
FROM `{project}.{dataset}.promotions`

UNION ALL

SELECT 
  'missing_url',
  COUNTIF(url IS NULL OR url = '')
FROM `{project}.{dataset}.promotions`

UNION ALL

SELECT 
  'invalid_discount',
  COUNTIF(discount_percent < 0 OR discount_percent > 100)
FROM `{project}.{dataset}.promotions`
```

### 20. Timeline de Dados

```sql
SELECT 
  DATE(collected_at) as data,
  COUNT(*) as produtos,
  COUNT(DISTINCT execution_id) as execucoes,
  ROUND(AVG(price), 2) as preco_medio
FROM `{project}.{dataset}.promotions`
GROUP BY data
ORDER BY data DESC
LIMIT 30
```

---

## 🔧 Como Usar

### Substituir variáveis:
- `{project}` → Seu GCP Project ID (ex: `seu-projeto-gcp`)
- `{dataset}` → Seu Dataset BigQuery (ex: `promocoes_teste`)
- `{table}` → Seu nome da tabela (ex: `promotions`)

### Exemplo:
```sql
SELECT * FROM `seu-projeto-gcp.promocoes_teste.promotions` LIMIT 5
```

### Salvar resultados:
```sql
-- No BigQuery UI, clique em "SAVE RESULTS" → "Save to BigQuery Table"
-- Ou via CLI:
bq query --use_legacy_sql=false \
  'SELECT * FROM `seu-projeto-gcp.promocoes_teste.promotions` LIMIT 100' \
  > results.json
```

---

## 📈 Visualização

Crie dashboards no Data Studio:
1. Vá para https://datastudio.google.com
2. Clique em "Create" → "Report"
3. Selecione BigQuery como fonte
4. Escolha suas queries
5. Configure gráficos e tabelas

Exemplo de gráfico útil: Evolução de produtos em promoção por dia
