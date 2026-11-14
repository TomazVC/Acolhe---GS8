#!/usr/bin/env bash
# Trigger both Acolhe DAGs in the local Airflow 3 container and print run/task states + counts.
# Usage (repo root): docker compose -f big_data/airflow/compose.airflow.yaml up -d
#                    bash big_data/airflow/run_evidence.sh [runs]
set -uo pipefail
cd "$(dirname "$0")/../.."
C="docker compose -f big_data/airflow/compose.airflow.yaml exec -T airflow"
RUNS=${1:-2}
echo "== waiting for API + DAG parsing"
for i in $(seq 1 80); do curl -fsS http://127.0.0.1:8081/api/v2/monitor/health >/dev/null 2>&1 && break; sleep 3; done
for i in $(seq 1 40); do $C airflow dags list 2>/dev/null | grep -q acolhe_medallion && break; sleep 3; done
$C airflow version
$C airflow dags list 2>/dev/null | grep -E 'dag_id|acolhe'
$C airflow dags list-import-errors 2>/dev/null | tail -3
counts(){ python3 - <<'PY'
import sqlite3
try:
    db=sqlite3.connect('big_data/output/warehouse.db')
    print('   counts', {t: db.execute(f'select count(*) from {t}').fetchone()[0] for t in ('batches','bronze','silver','quarantine','fact_indicators','official_batches','silver_official_indicator','dim_municipality')})
except Exception as e: print('   counts n/a:', e)
PY
}
run_dag(){ # dag_id
  $C airflow dags unpause "$1" >/dev/null 2>&1
  out=$($C airflow dags trigger "$1" -o plain 2>/dev/null | tail -1); run_id=$(echo "$out" | awk '{for(i=1;i<=NF;i++) if($i ~ /^manual__/) print $i}')
  echo "-- $1 triggered: ${run_id:-?}"
  for i in $(seq 1 100); do
    st=$($C airflow dags state "$1" "$run_id" 2>/dev/null | tail -1)
    case "$st" in success|failed) break;; esac; sleep 3
  done
  echo "   dag run state: $st"
  $C airflow tasks states-for-dag-run "$1" "$run_id" -o plain 2>/dev/null | awk '{print "   task",$0}' | grep -v -i 'dag_id'
}
echo "== counts before"; counts
for n in $(seq 1 "$RUNS"); do echo "== acolhe_medallion execution $n"; run_dag acolhe_medallion; counts; done
echo "== acolhe_official_snapshots (real IBGE + OBMigra acquisition, in parallel)"; run_dag acolhe_official_snapshots
echo "== manifests by retrieval day"; python3 - <<'PY'
import json,glob,collections
c=collections.Counter(json.load(open(f))['retrieval_day_utc'] for f in glob.glob('big_data/official_snapshots/manifests/*.json')); print('  ',dict(sorted(c.items())))
PY
