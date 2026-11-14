# Evidencias Databricks (2026-11-14 03:10 UTC)

Workspace Databricks Free Edition (serverless). Git folder da branch `Aksel+Ian`, commit `c9ce9ad`. Gerado por `big_data/databricks/run_evidence.py`.

## Execucoes

| Notebook | Parametros | Inicio (UTC) | Resultado | Run |
|---|---|---|---|---|
| acolhe-00_setup_volume-setup | {"catalog": "workspace", "schema": "acolhe"} | 2026-11-14T03:04:25+00:00 | SUCCESS | https://dbc-f8b0fc62-f5ec.cloud.databricks.com/?o=7474655582396358#job/1081971935593187/run/572157616406883 |
| acolhe-medallion-2026-11-05 | {"batch_date": "2026-11-05", "schema": "workspace.acolhe", "input_path": "/Volumes/workspace/acolhe/data/input", "output_path": "/Volumes/workspace/acolhe/data/output"} | 2026-11-14T03:05:18+00:00 | SUCCESS | https://dbc-f8b0fc62-f5ec.cloud.databricks.com/?o=7474655582396358#job/79615211273559/run/1053924725131862 |
| acolhe-medallion-2026-11-06 | {"batch_date": "2026-11-06", "schema": "workspace.acolhe", "input_path": "/Volumes/workspace/acolhe/data/input", "output_path": "/Volumes/workspace/acolhe/data/output"} | 2026-11-14T03:07:15+00:00 | SUCCESS | https://dbc-f8b0fc62-f5ec.cloud.databricks.com/?o=7474655582396358#job/767054600616397/run/1045120412193743 |
| acolhe-medallion-2026-11-06 | {"batch_date": "2026-11-06", "schema": "workspace.acolhe", "input_path": "/Volumes/workspace/acolhe/data/input", "output_path": "/Volumes/workspace/acolhe/data/output"} | 2026-11-14T03:08:41+00:00 | SUCCESS | https://dbc-f8b0fc62-f5ec.cloud.databricks.com/?o=7474655582396358#job/879754940110724/run/404656285714961 |

## Contagens antes, depois de cada lote e na reexecucao

| Etapa | bronze | silver | quarantine | fact_indicators | dim_region | dim_language | gold_official_context | dim_municipality |
|---|---|---|---|---|---|---|---|---|
| Antes | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Depois do lote 2026-11-05 | 4 | 4 | 0 | 4 | 2 | 2 | 7 | 645 |
| Depois do lote 2026-11-06 | 8 | 4 | 0 | 4 | 2 | 2 | 7 | 645 |
| Reexecucao do lote 2026-11-06 | 8 | 4 | 0 | 4 | 2 | 2 | 7 | 645 |

## DESCRIBE HISTORY bronze

| version | timestamp | operation | operationMetrics |
|---|---|---|---|
| 4 | 2026-11-14T03:07:35.000Z | COPY INTO | {"numFiles":"1","numOutputRows":"2","numOutputBytes":"2517","numSkippedCorruptFiles":"0"} |
| 3 | 2026-11-14T03:07:32.000Z | COPY INTO | {"numFiles":"1","numOutputRows":"2","numOutputBytes":"2508","numSkippedCorruptFiles":"0"} |
| 2 | 2026-11-14T03:05:50.000Z | COPY INTO | {"numFiles":"1","numOutputRows":"2","numOutputBytes":"2511","numSkippedCorruptFiles":"0"} |
| 1 | 2026-11-14T03:05:47.000Z | COPY INTO | {"numFiles":"1","numOutputRows":"2","numOutputBytes":"2507","numSkippedCorruptFiles":"0"} |
| 0 | 2026-11-14T03:05:36.000Z | CREATE TABLE | {} |

## DESCRIBE HISTORY silver

| version | timestamp | operation | operationMetrics |
|---|---|---|---|
| 3 | 2026-11-14T03:09:05.000Z | MERGE | {"numTargetRowsCopied":"0","numTargetRowsDeleted":"0","numTargetFilesAdded":"1","numTargetBytesAdded":"2995","numTargetBytesRemoved":"2995","numTargetDeletionVe |
| 2 | 2026-11-14T03:07:42.000Z | MERGE | {"numTargetRowsCopied":"0","numTargetRowsDeleted":"0","numTargetFilesAdded":"1","numTargetBytesAdded":"2995","numTargetBytesRemoved":"2254","numTargetDeletionVe |
| 1 | 2026-11-14T03:06:04.000Z | MERGE | {"numTargetRowsCopied":"0","numTargetRowsDeleted":"0","numTargetFilesAdded":"1","numTargetBytesAdded":"2254","numTargetBytesRemoved":"0","numTargetDeletionVecto |
| 0 | 2026-11-14T03:05:59.000Z | CREATE TABLE AS SELECT | {"numFiles":"0","numOutputRows":"0","numOutputBytes":"0"} |

## Consultas ouro no Databricks

### Consulta 1

```sql
SELECT r.region, SUM(f.count) AS demand FROM workspace.acolhe.fact_indicators f JOIN workspace.acolhe.dim_region r USING(region_id) WHERE source='demand' GROUP BY r.region ORDER BY demand DESC
```

| region | demand |
|---|---|
| Sao Paulo | 110 |
| Parana | 80 |

### Consulta 2

```sql
SELECT r.region, SUM(f.count) AS services FROM workspace.acolhe.fact_indicators f JOIN workspace.acolhe.dim_region r USING(region_id) WHERE source='services' GROUP BY r.region ORDER BY services DESC
```

| region | services |
|---|---|
| Sao Paulo | 22 |
| Parana | 18 |

### Consulta 3

```sql
SELECT l.language,SUM(f.count) AS demand FROM workspace.acolhe.fact_indicators f JOIN workspace.acolhe.dim_language l USING(language_id) WHERE source='demand' GROUP BY l.language
```

| language | demand |
|---|---|
| pt | 80 |
| es | 110 |

### Consulta 4

```sql
SELECT r.region, SUM(CASE WHEN source='demand' THEN count ELSE 0 END)*1.0/NULLIF(SUM(CASE WHEN source='services' THEN count ELSE 0 END),0) AS demand_per_service FROM workspace.acolhe.fact_indicators f JOIN workspace.acolhe.dim_region r USING(region_id) GROUP BY r.region
```

| region | demand_per_service |
|---|---|
| Sao Paulo | 5.0000000000000000 |
| Parana | 4.4444444444444444 |

### Consulta 5

```sql
SELECT source,MIN(snapshot_date) AS oldest_snapshot,MAX(snapshot_date) AS newest_snapshot,SUM(CASE WHEN synthetic THEN 1 ELSE 0 END) AS synthetic_records,COUNT(*) AS records FROM workspace.acolhe.fact_indicators GROUP BY source
```

| source | oldest_snapshot | newest_snapshot | synthetic_records | records |
|---|---|---|---|---|
| demand | 2026-11-06 | 2026-11-06 | 2 | 2 |
| services | 2026-11-06 | 2026-11-06 | 2 | 2 |

### Consulta 6

```sql
SELECT t.value AS refugee_requests, c.value AS children_pct, ROUND(t.value*c.value/100.0) AS estimated_children_requests FROM workspace.acolhe.gold_official_context t JOIN workspace.acolhe.gold_official_context c ON c.indicator_id='refugee_requests_children_0_11_pct' WHERE t.indicator_id='refugee_requests_total'
```

| refugee_requests | children_pct | estimated_children_requests |
|---|---|---|
| 75600.0 | 16.0 | 12096.0 |

### Consulta 7

```sql
SELECT ROUND(r.value*100.0/q.value,1) AS recognized_per_100_requests FROM workspace.acolhe.gold_official_context r JOIN workspace.acolhe.gold_official_context q ON q.indicator_id='refugee_requests_total' WHERE r.indicator_id='refugee_recognized_total'
```

| recognized_per_100_requests |
|---|
| 12.2 |

### Consulta 8

```sql
SELECT (SELECT COUNT(*) FROM workspace.acolhe.dim_municipality WHERE state_code='SP') AS ibge_sp_municipalities, (SELECT COUNT(*) FROM workspace.acolhe.dim_region) AS demo_regions
```

| ibge_sp_municipalities | demo_regions |
|---|---|
| 645 | 2 |
