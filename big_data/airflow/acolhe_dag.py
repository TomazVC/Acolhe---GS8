"""Airflow 3 DAG: two independent ingestion branches, then medallion.
Mount repo at ACOLHE_ROOT on every worker. Not executed in this delivery.
"""
import csv, os, shutil
from pathlib import Path
from datetime import datetime,timedelta,timezone
from airflow.sdk import dag,task

@dag(dag_id='acolhe_medallion',schedule='0 3 * * *',start_date=datetime(2026,11,5,tzinfo=timezone.utc),catchup=False,max_active_runs=1,default_args={'retries':2,'retry_delay':timedelta(minutes=2)},tags=['acolhe','synthetic-demo'])
def acolhe():
    @task
    def ingest(source):
        root=Path(os.environ['ACOLHE_ROOT'])
        origin=Path(os.environ.get('ACOLHE_IMPORT_DIR',str(root/'big_data'/'input')))
        target=root/'big_data'/'staging'; target.mkdir(parents=True,exist_ok=True)
        paths=sorted(origin.glob(source+'_*.csv'))
        if not paths: raise FileNotFoundError(f'No {source} source files')
        for path in paths:
            with path.open(encoding='utf-8-sig',newline='') as handle:
                names=csv.DictReader(handle).fieldnames
                required={'record_id','region','language','count','snapshot_date','synthetic'}
                if not names or not required.issubset(names): raise ValueError(f'Invalid columns in {path.name}')
            shutil.copy2(path,target/path.name)
        return len(paths)
    @task
    def medallion(demand_batches,service_batches):
        import sys
        root=Path(os.environ['ACOLHE_ROOT']); sys.path.insert(0,str(root))
        from big_data.pipeline import run
        return run(root/'big_data'/'staging',root/'big_data'/'output')['totals']
    medallion(ingest.override(task_id='ingest_demand')('demand'),ingest.override(task_id='ingest_services')('services'))

acolhe_dag=acolhe()
