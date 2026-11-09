import tempfile, unittest
from pathlib import Path
from app.core import Store, LESSONS

class CoreTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.store=Store(Path(self.tmp.name)/'test.db')
 def tearDown(self): self.tmp.cleanup()
 def test_five_bilingual_lessons(self):
  self.assertEqual(len(LESSONS),5)
  for lesson in LESSONS:
   self.assertTrue(lesson['title']['pt']); self.assertTrue(lesson['title']['es'])
 def test_real_attempt_and_summary(self):
  sid=self.store.session('es')['id']
  result=self.store.attempt(sid,'casa',0,'request-1')
  self.assertTrue(result['correct']); self.assertEqual(self.store.summary()['attempts'],1)
 def test_idempotent_attempt(self):
  sid=self.store.session('pt')['id']
  one=self.store.attempt(sid,'casa',1,'same')
  two=self.store.attempt(sid,'casa',1,'same')
  self.assertEqual(one,two); self.assertEqual(self.store.summary()['attempts'],1)
 def test_invalid_session_rejected(self):
  with self.assertRaises(ValueError): self.store.attempt('unknown','casa',0,'a')
 def test_invalid_option_rejected(self):
  sid=self.store.session('pt')['id']
  for answer in [-1,3,True,'0']:
   with self.assertRaises(ValueError): self.store.attempt(sid,'casa',answer,'bad')
 def test_language_rejected(self):
  with self.assertRaises(ValueError): self.store.session('xx')
 def test_delete_session(self):
  sid=self.store.session('pt')['id']; self.store.attempt(sid,'casa',0,'a')
  self.store.delete_session(sid); self.assertEqual(self.store.summary()['attempts'],0)

 def test_expired_session_rejected_without_restart(self):
  sid=self.store.session('pt')['id']
  with self.store.connect() as db: db.execute("UPDATE sessions SET created_at='2000-01-01T00:00:00+00:00' WHERE id=?",(sid,))
  with self.assertRaises(ValueError): self.store.attempt(sid,'casa',0,'expired')

 def test_summary_prunes_expired_sessions_and_answers(self):
  sid=self.store.session('pt')['id']; self.store.attempt(sid,'casa',0,'old')
  with self.store.connect() as db: db.execute("UPDATE sessions SET created_at='2000-01-01T00:00:00+00:00' WHERE id=?",(sid,))
  self.assertEqual(self.store.summary()['sessions'],0)
  self.assertEqual(self.store.summary()['attempts'],0)

 def test_structured_session_id_rejected(self):
  with self.assertRaises(ValueError): self.store.attempt({'id':'bad'},'casa',0,'invalid')

 def test_concurrent_duplicate_is_idempotent(self):
  from concurrent.futures import ThreadPoolExecutor
  from threading import Barrier
  sid=self.store.session('pt')['id']; barrier=Barrier(8)
  def submit(_):
   barrier.wait()
   return self.store.attempt(sid,'casa',0,'same-concurrent')
  with ThreadPoolExecutor(max_workers=8) as executor: results=list(executor.map(submit,range(8)))
  self.assertTrue(all(result==results[0] for result in results))
  self.assertEqual(self.store.summary()['attempts'],1)

 def test_migration_preserves_old_attempts(self):
  import sqlite3
  from contextlib import closing
  from datetime import datetime,timezone
  from rpa.robot import generate_report
  path=Path(self.tmp.name)/'legacy.db'; sid='a'*32; now=datetime.now(timezone.utc).isoformat()
  with closing(sqlite3.connect(path)) as db,db:
   db.executescript('CREATE TABLE sessions(id TEXT PRIMARY KEY, language TEXT NOT NULL, created_at TEXT NOT NULL); CREATE TABLE attempts(id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, lesson_id TEXT NOT NULL, correct INTEGER NOT NULL, created_at TEXT NOT NULL, request_id TEXT NOT NULL, UNIQUE(session_id,request_id));')
   db.execute('INSERT INTO sessions VALUES(?,?,?)',(sid,'pt',now))
   db.execute('INSERT INTO attempts VALUES(?,?,?,?,?,?)',('old',sid,'casa',1,now,'old-request'))
  migrated=Store(path)
  migrated.attempt(sid,'escola',1,'new-request','es')
  Store(path) # Reopening must be safe and keep all records.
  report=generate_report(path,Path(self.tmp.name)/'legacy-report')
  self.assertEqual(report['by_language'],[{'language':'es','attempts':1,'correct':1},{'language':'pt','attempts':1,'correct':1}])

 def test_default_language_and_duplicate_keep_original_language(self):
  sid=self.store.session('pt')['id']
  first=self.store.attempt(sid,'casa',0,'same')
  self.assertEqual(self.store.attempt(sid,'casa',0,'same','es'),first)
  with self.store.connect() as db:
   self.assertEqual(db.execute('SELECT language FROM attempts').fetchone()['language'],'pt')
  self.assertEqual(self.store.summary()['attempts'],1)
