"""Airflow 3: two official read-only acquisitions in parallel. Not activated."""
import os
from pathlib import Path
from datetime import datetime,timedelta,timezone
from airflow.sdk import dag,task

@dag(dag_id='acolhe_official_snapshots',schedule='0 4 * * *',start_date=datetime(2026,11,7,tzinfo=timezone.utc),catchup=False,max_active_runs=1,default_args={'retries':2,'retry_delay':timedelta(minutes=3)},tags=['acolhe','official-reference'])
def official_snapshots():
    @task
    def acquire(source):
        import sys
        root=Path(os.environ['ACOLHE_ROOT']); sys.path.insert(0,str(root))
        from big_data.collect_official import collect
        return collect(source,root/'big_data'/'official_snapshots')
    @task
    def summarize(territory,report):
        return {'source_count':2,'retrieved_at':[territory['retrieved_at'],report['retrieved_at']],
                'status':'Reference snapshots only; not integrated migration/service gold',
                'license_review_pending':territory['license_status']}
    summarize(acquire.override(task_id='collect_ibge_territory')('ibge'),acquire.override(task_id='collect_obmigra_report')('obmigra'))

official_sources_dag=official_snapshots()
