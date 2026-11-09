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
