from contextlib import closing
import tempfile, unittest, sqlite3
from pathlib import Path
from rpa.robot import generate_report

class RobotTests(unittest.TestCase):
    def test_aggregate_without_identifiers(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); db=p/'app.db'
            with closing(sqlite3.connect(db)) as c, c:
                c.executescript("CREATE TABLE sessions(id TEXT,language TEXT,created_at TEXT); CREATE TABLE attempts(id TEXT,session_id TEXT,lesson_id TEXT,correct INTEGER,created_at TEXT); INSERT INTO sessions VALUES('private-id','pt','2026-11-05'); INSERT INTO attempts VALUES('a','private-id','welcome',1,'2026-11-05');")
            result=generate_report(db,p/'out')
            self.assertEqual(result['totals']['attempts'],1)
            self.assertEqual(result['totals']['accuracy'],1.0)
            self.assertNotIn('private-id',(p/'out'/'progress.json').read_text())
    def test_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with self.assertRaises(FileNotFoundError): generate_report(p/'absent.db',p/'out')
            self.assertFalse((p/'absent.db').exists())

    def test_empty_database_reports_zero(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with closing(sqlite3.connect(p/'empty.db')) as db, db:
                db.executescript('CREATE TABLE sessions(id TEXT,language TEXT,created_at TEXT); CREATE TABLE attempts(id TEXT,session_id TEXT,lesson_id TEXT,correct INTEGER,created_at TEXT);')
            report=generate_report(p/'empty.db',p/'out')
            self.assertEqual(report['totals']['accuracy'],0)
            self.assertEqual(report['by_language'],[])

    def test_bad_schema_logs_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)
            with closing(sqlite3.connect(p/'wrong.db')) as db: pass
            with self.assertRaises(sqlite3.OperationalError): generate_report(p/'wrong.db',p/'out')
            self.assertIn('report_failed',(p/'out'/'robot.log').read_text())
            self.assertFalse((p/'out'/'progress.json').exists())

    def test_decision_rule(self):
        from rpa.robot import decide
        self.assertEqual(decide(0,[])['status'],'sem_atividade')
        low={'lesson_id':'x','attempts':3,'accuracy':0.33}; few={'lesson_id':'y','attempts':2,'accuracy':0.0}; good={'lesson_id':'z','attempts':5,'accuracy':0.8}
        self.assertEqual(decide(10,[low,few,good])['lessons_to_review'],['x'])  # 2 attempts is too few to judge
        self.assertEqual(decide(7,[few,good])['status'],'progresso_adequado')

    def test_session_without_attempts_reports_zero_not_null(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); db=p/'app.db'
            with closing(sqlite3.connect(db)) as c, c:
                c.executescript("CREATE TABLE sessions(id TEXT,language TEXT,created_at TEXT); CREATE TABLE attempts(id TEXT,session_id TEXT,lesson_id TEXT,correct INTEGER,created_at TEXT); INSERT INTO sessions VALUES('s','es','2026-11-05');")
            report=generate_report(db,p/'out')
            self.assertEqual(report['by_language'],[{'language':'es','attempts':0,'correct':0}])
            self.assertIn('sem_atividade',(p/'out'/'progress.md').read_text(encoding='utf-8'))

    def test_end_to_end_app_robot_mvp(self):
        from rpa.demo_e2e import run_demo
        with tempfile.TemporaryDirectory() as d:
            result=run_demo(d)
            steps={s['step']:s for s in result['steps']}
            self.assertEqual(steps['0_mvp_before_robot']['automation'],{'status':'not_generated'})
            self.assertEqual(steps['1_success']['mvp'],{'sessions':1,'attempts':5,'correct':5,'accuracy':1.0})
            self.assertEqual(steps['2_decision']['mvp_decision']['lessons_to_review'],['mobilidade'])
            self.assertEqual(steps['3_failure']['error'],'FileNotFoundError'); self.assertFalse(steps['3_failure']['db_created'])
            self.assertTrue(any('report_failed' in l for l in result['robot_log']))
            self.assertTrue(any('decision status=reforco_recomendado' in l for l in result['robot_log']))

    def test_builtin_schedule_runs_n_times(self):
        import subprocess, sys
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); db=p/'app.db'
            with closing(sqlite3.connect(db)) as c, c:
                c.executescript("CREATE TABLE sessions(id TEXT,language TEXT,created_at TEXT); CREATE TABLE attempts(id TEXT,session_id TEXT,lesson_id TEXT,correct INTEGER,created_at TEXT);")
            r=subprocess.run([sys.executable,'-B','-m','rpa.robot','--db',str(db),'--output',str(p/'out'),'--every','1','--runs','2'],capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertEqual((p/'out'/'robot.log').read_text().count('report_completed'),2)
