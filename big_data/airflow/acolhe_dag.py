"""Airflow 3 DAG: two independent ingestion branches, then medallion.
Mount repo at ACOLHE_ROOT on every worker. Not executed in this delivery.
"""
import csv, hashlib, os
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
            # Content-only atomic copy. shutil.copy2 also copies timestamps/mode, which
            # only the file owner may do: it raised EPERM when the worker UID (50000 in
            # the official image) differed from the staging file owner. Identical files
            # are skipped, so retries and re-runs do not rewrite staging.
            data=path.read_bytes(); dest=target/path.name
            if dest.exists() and hashlib.sha256(dest.read_bytes()).digest()==hashlib.sha256(data).digest(): continue
            tmp=target/(path.name+'.tmp'); tmp.write_bytes(data); os.replace(tmp,dest)
        return len(paths)
    @task
    def medallion(demand_batches,service_batches):
        import sys
        root=Path(os.environ['ACOLHE_ROOT']); sys.path.insert(0,str(root))
        from big_data.pipeline import run
        return run(root/'big_data'/'staging',root/'big_data'/'output')['totals']
    @task
    def integrate_official(totals):
        # Real OBMigra + IBGE snapshots (collected by acolhe_official_snapshots).
        import sys
        root=Path(os.environ['ACOLHE_ROOT']); sys.path.insert(0,str(root))
        snapshots=root/'big_data'/'official_snapshots'
        if not (snapshots/'manifests').is_dir(): return {'status':'skipped_no_official_snapshots','totals':totals}
        from big_data.official_integration import integrate
        return {'status':'integrated','totals':totals,**integrate(snapshots,root/'big_data'/'output')['counts']}
    integrate_official(medallion(ingest.override(task_id='ingest_demand')('demand'),ingest.override(task_id='ingest_services')('services')))

acolhe_dag=acolhe()
