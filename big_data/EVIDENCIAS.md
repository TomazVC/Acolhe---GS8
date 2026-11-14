# Evidencias Big Data (geradas em 2026-11-14 02:31 UTC)

Gerado por `python -B -m big_data.evidence` com o pipeline real em um warehouse temporario. Reproduzivel.

## Contagens por lote e reexecucao (camada demonstrativa, synthetic=true)

| Etapa | batches | bronze | silver | quarantine | fact_indicators |
|---|---|---|---|---|---|
| Antes (vazio) | 0 | 0 | 0 | 0 | 0 |
| Depois do lote 2026-11-05 | 2 | 4 | 4 | 0 | 4 |
| Depois do lote 2026-11-06 | 4 | 8 | 4 | 0 | 4 |
| Reexecucao (mesmos arquivos) | 4 | 8 | 4 | 0 | 4 |

Leitura: cada lote traz um arquivo por fonte (2 arquivos, 4 linhas brutas) e o bronze imutavel acumula 4 -> 8 linhas. A prata faz UPSERT por (fonte, record_id): o segundo lote atualiza as mesmas 4 chaves em vez de duplica-las. A reexecucao nao altera nenhuma contagem: arquivos com hash ja registrado sao ignorados.

## Fontes reais (OBMigra 2025 + IBGE)

| Etapa | official_batches | silver_official_indicator | dim_municipality | gold_official_context |
|---|---|---|---|---|
| Integracao oficial | 2 | 7 | 645 | 7 |
| Reexecucao oficial | 2 | 7 | 645 | 7 |

## Consultas ouro interpretadas

### Consulta 1

```sql
SELECT r.region, SUM(f.count) AS demand FROM fact_indicators f JOIN dim_region r USING(region_id) WHERE source='demand' GROUP BY r.region ORDER BY demand DESC
```

| region | demand |
|---|---|
| Sao Paulo | 110 |
| Parana | 80 |

Interpretacao: Demanda demonstrativa por territorio: Sao Paulo concentra a maior demanda sintetica. Mostra o agrupamento ouro, nao a realidade.

### Consulta 2

```sql
SELECT r.region, SUM(f.count) AS services FROM fact_indicators f JOIN dim_region r USING(region_id) WHERE source='services' GROUP BY r.region ORDER BY services DESC
```

| region | services |
|---|---|
| Sao Paulo | 22 |
| Parana | 18 |

Interpretacao: Servicos demonstrativos por territorio: oferta sintetica por regiao, para comparar com a consulta 1.

### Consulta 3

```sql
SELECT l.language,SUM(f.count) AS demand FROM fact_indicators f JOIN dim_language l USING(language_id) WHERE source='demand' GROUP BY l.language
```

| language | demand |
|---|---|
| es | 110 |
| pt | 80 |

Interpretacao: Demanda por idioma: espanhol predomina na base sintetica, coerente com o publico-alvo hispanofalante do Acolhe.

### Consulta 4

```sql
SELECT r.region, SUM(CASE WHEN source='demand' THEN count ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN source='services' THEN count ELSE 0 END),0) AS demand_per_service FROM fact_indicators f JOIN dim_region r USING(region_id) GROUP BY r.region
```

| region | demand_per_service |
|---|---|
| Parana | 4.44 |
| Sao Paulo | 5.00 |

Interpretacao: Demanda por unidade de servico: indicador ilustrativo de pressao sobre a oferta; nao e estimativa causal nem de capacidade.

### Consulta 5

```sql
SELECT source,MIN(snapshot_date) AS oldest_snapshot,MAX(snapshot_date) AS newest_snapshot,SUM(CASE WHEN synthetic THEN 1 ELSE 0 END) AS synthetic_records,COUNT(*) AS records FROM fact_indicators GROUP BY source
```

| source | oldest_snapshot | newest_snapshot | synthetic_records | records |
|---|---|---|---|---|
| demand | 2026-11-06 | 2026-11-06 | 2 | 2 |
| services | 2026-11-06 | 2026-11-06 | 2 | 2 |

Interpretacao: Proveniencia e atualidade: todos os registros da camada demonstrativa estao marcados como sinteticos; a data mostra o snapshot mais recente aplicado pelo UPSERT.

### Consulta 6

```sql
SELECT t.value AS refugee_requests, c.value AS children_pct, ROUND(t.value*c.value/100.0) AS estimated_children_requests FROM gold_official_context t JOIN gold_official_context c ON c.indicator_id='refugee_requests_children_0_11_pct' WHERE t.indicator_id='refugee_requests_total'
```

| refugee_requests | children_pct | estimated_children_requests |
|---|---|---|
| 75600.00 | 16.00 | 12096.00 |

Interpretacao: Dado real (OBMigra 2025): pedidos de refugio multiplicados pela parcela de criancas de 0 a 11 anos dao uma estimativa da ordem de grandeza de criancas solicitantes no Brasil, o publico potencial do Acolhe.

### Consulta 7

```sql
SELECT ROUND(r.value*100.0/q.value,1) AS recognized_per_100_requests FROM gold_official_context r JOIN gold_official_context q ON q.indicator_id='refugee_requests_total' WHERE r.indicator_id='refugee_recognized_total'
```

| recognized_per_100_requests |
|---|
| 12.20 |

Interpretacao: Dado real (OBMigra 2025): reconhecimentos por 100 pedidos. As coortes diferem (decisoes de 2025 incluem pedidos antigos), entao o numero e indicativo.

### Consulta 8

```sql
SELECT (SELECT COUNT(*) FROM dim_municipality WHERE state_code='SP') AS ibge_sp_municipalities, (SELECT COUNT(*) FROM dim_region) AS demo_regions
```

| ibge_sp_municipalities | demo_regions |
|---|---|
| 645 | 2 |

Interpretacao: Cobertura territorial: os 645 municipios de SP vindos do IBGE contra as regioes presentes na base demonstrativa; mostra o quanto falta para cobertura real.

## Contrato entregue ao MVP

```json
{
  "synthetic": true,
  "source_batches": 4,
  "totals": {
    "demand": 190,
    "services": 40
  },
  "quality": {
    "rejected": 0
  }
}
```
