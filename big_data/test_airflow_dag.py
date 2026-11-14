"""Execute the real Airflow DAG task bodies without a scheduler.

A minimal stand-in for airflow.sdk runs every @task eagerly in dependency order,
so the DAG's own code (copy/validate, medallion, official integration) is
exercised on CI and on Windows, where Airflow 3 cannot run (needs POSIX fcntl).
This is NOT evidence of a scheduler run; capture that in Airflow itself.
"""
from contextlib import closing
import os, runpy, shutil, sqlite3, sys, tempfile, types, unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parent.parent
CALLS = []

def _stub_sdk():
    sdk = types.ModuleType('airflow.sdk')
    def task(fn):
        def bind(task_id):
            def call(*args):
                CALLS.append(task_id); return fn(*args)
            return call
        wrapper = bind(fn.__name__); wrapper.override = lambda task_id: bind(task_id)
        return wrapper
    def dag(**kwargs):
        def decorate(fn):
            def build():
                fn(); return types.SimpleNamespace(**kwargs)
            return build
        return decorate
    sdk.task, sdk.dag = task, dag
    return {'airflow': types.ModuleType('airflow'), 'airflow.sdk': sdk}

class AirflowDagExecutionTests(unittest.TestCase):
    def run_dag(self, root):
        CALLS.clear()
        with mock.patch.dict(sys.modules, _stub_sdk()), mock.patch.dict(os.environ, {'ACOLHE_ROOT': str(root)}):
            return runpy.run_path(str(REPO / 'big_data' / 'airflow' / 'acolhe_dag.py'))['acolhe_dag']

    def test_branches_then_medallion_then_official_and_rerun_is_idempotent(self):
        from big_data.pipeline import create_demo
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); shutil.copytree(REPO / 'big_data', root / 'big_data', ignore=shutil.ignore_patterns('output', 'staging', 'official_snapshots', '__pycache__'))
            create_demo(root / 'big_data' / 'input')
            dag = self.run_dag(root)
            self.assertEqual(dag.dag_id, 'acolhe_medallion')
            self.assertEqual(CALLS, ['ingest_demand', 'ingest_services', 'medallion', 'integrate_official'])
            db_path = root / 'big_data' / 'output' / 'warehouse.db'
            with closing(sqlite3.connect(db_path)) as db:
                before = [db.execute(f'select count(*) from {t}').fetchone()[0] for t in ('bronze', 'silver', 'batches')]
            self.run_dag(root)  # Airflow retry / re-execution of the same batch
            with closing(sqlite3.connect(db_path)) as db:
                after = [db.execute(f'select count(*) from {t}').fetchone()[0] for t in ('bronze', 'silver', 'batches')]
            self.assertEqual(before, [8, 4, 4]); self.assertEqual(before, after)

    def test_ingest_never_copies_metadata(self):
        """Regression: real Airflow worker (UID 50000) got EPERM from shutil.copystat."""
        from big_data.pipeline import create_demo
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); shutil.copytree(REPO / 'big_data', root / 'big_data', ignore=shutil.ignore_patterns('output', 'staging', 'official_snapshots', '__pycache__'))
            create_demo(root / 'big_data' / 'input')
            def deny(*a, **k): raise PermissionError(1, 'Operation not permitted')
            with mock.patch('shutil.copystat', deny), mock.patch('os.utime', deny):
                self.run_dag(root); self.run_dag(root)  # second run: identical files skipped
            self.assertEqual(sorted(p.name for p in (root / 'big_data' / 'staging').iterdir()),
                             ['demand_2026-11-05.csv', 'demand_2026-11-06.csv', 'services_2026-11-05.csv', 'services_2026-11-06.csv'])

    def test_invalid_columns_fail_ingest_task(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); (root / 'big_data' / 'input').mkdir(parents=True)
            shutil.copy(REPO / 'big_data' / 'pipeline.py', root / 'big_data' / 'pipeline.py')
            (root / 'big_data' / 'input' / 'demand_2026-11-05.csv').write_text('a,b\n1,2\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'Invalid columns'):
                self.run_dag(root)
