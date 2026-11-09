"""Learning domain: no names, images, audio or child profiles are retained."""
import json, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path

def pair(pt,es): return {'pt':pt,'es':es}
LESSONS = [
 {'id':'casa','icon':'🏠','title':pair('Perto de casa','Cerca de casa'),'word':'copo','translation':'vaso','intro':pair('Um copo para beber água. Repita: copo.','Un vaso para beber agua. Repite: copo.'),'question':pair('Qual palavra significa vaso em português?','¿Qué palabra significa vaso en portugués?'),'options':['Copo','Cadeira','Livro'],'answer':0},
 {'id':'escola','icon':'🎒','title':pair('Vamos à escola','Vamos a la escuela'),'word':'mochila','translation':'mochila','intro':pair('Na mochila, levo meu caderno.','En la mochila llevo mi cuaderno.'),'question':pair('Onde guardamos o caderno?','¿Dónde guardamos el cuaderno?'),'options':['Copo','Mochila','Cadeira'],'answer':1},
 {'id':'amigos','icon':'👋','title':pair('Novos amigos','Nuevos amigos'),'word':'bom dia','translation':'buenos días','intro':pair('Bom dia! Meu nome é... Como você se chama?','¡Buenos días! Mi nombre es... ¿Cómo te llamas?'),'question':pair('Como cumprimentar de manhã?','¿Cómo saludar por la mañana?'),'options':['Boa noite','Até amanhã','Bom dia'],'answer':2},
 {'id':'mobilidade','icon':'🚦','title':pair('Caminho seguro','Camino seguro'),'word':'faixa de pedestres','translation':'paso de peatones','intro':pair('Atravesse com um adulto, na faixa. Observe o sinal de pedestres e espere os veículos pararem.','Cruza con una persona adulta por el paso de peatones. Observa la señal peatonal y espera a que los vehículos se detengan.'),'question':pair('Com quem devemos atravessar a rua?','¿Con quién debemos cruzar la calle?'),'options':['Correndo sozinho','Com um adulto','Sem olhar'],'answer':1},
 {'id':'ajuda','icon':'💬','title':pair('Posso pedir ajuda','Puedo pedir ayuda'),'word':'por favor','translation':'por favor','intro':pair('Não entendi. Pode repetir, por favor? Procure um adulto de confiança.','No entendí. ¿Puede repetir, por favor? Busca a una persona adulta de confianza.'),'question':pair('O que dizer quando não entende?','¿Qué decir cuando no entiendes?'),'options':['Pode repetir, por favor?','Vou embora sem avisar','Não posso perguntar'],'answer':0},
]

def public_lessons(): return [{k:v for k,v in x.items() if k!='answer'} for x in LESSONS]

class Store:
 def __init__(self,path):
  self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
  with self.connect(purge=False) as db:
   db.executescript("CREATE TABLE IF NOT EXISTS sessions(id TEXT PRIMARY KEY, language TEXT NOT NULL, created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE, lesson_id TEXT NOT NULL, correct INTEGER NOT NULL, created_at TEXT NOT NULL, request_id TEXT NOT NULL, UNIQUE(session_id,request_id));")
   if 'language' not in {row['name'] for row in db.execute('PRAGMA table_info(attempts)')}:
    db.execute('ALTER TABLE attempts ADD COLUMN language TEXT')
   db.execute('DELETE FROM sessions WHERE created_at < ?',((datetime.now(timezone.utc)-timedelta(days=7)).isoformat(),))
 @contextmanager
 def connect(self,purge=True):
  db=sqlite3.connect(self.path,timeout=10); db.row_factory=sqlite3.Row; db.execute('PRAGMA foreign_keys=ON')
  try:
   if purge:
    with db: db.execute('DELETE FROM sessions WHERE created_at < ?',((datetime.now(timezone.utc)-timedelta(days=7)).isoformat(),))
   with db: yield db
  finally: db.close()
 def session(self,language):
  if language not in ('pt','es'): raise ValueError('Idioma inválido / Idioma inválido')
  sid=uuid.uuid4().hex
  with self.connect() as db: db.execute('INSERT INTO sessions VALUES(?,?,?)',(sid,language,datetime.now(timezone.utc).isoformat()))
  return {'id':sid,'language':language}
 def attempt(self,sid,lesson_id,option,request_id,language=None):
  if language is not None and language not in ('pt','es'): raise ValueError('Idioma invalido')
  if not isinstance(sid,str) or len(sid)!=32: raise ValueError('Sessão inválida')
  lesson=next((x for x in LESSONS if x['id']==lesson_id),None)
  if lesson is None or type(option)!=int or not 0<=option<len(lesson['options']): raise ValueError('Exercício ou opção inválida')
  if not isinstance(request_id,str) or not 1<=len(request_id)<=80: raise ValueError('Identificador inválido')
  with self.connect() as db:
   db.execute('BEGIN IMMEDIATE') # Serialize idempotency lookup plus insert.
   session=db.execute('SELECT id,language FROM sessions WHERE id=?',(sid,)).fetchone()
   if not session: raise ValueError('Sessão expirada. Comece novamente.')
   old=db.execute('SELECT id,correct,lesson_id FROM attempts WHERE session_id=? AND request_id=?',(sid,request_id)).fetchone()
   if old:
    if old['lesson_id']!=lesson_id: raise ValueError('Identificador já utilizado')
    return {'id':old['id'],'correct':bool(old['correct'])}
   attempt_id=uuid.uuid4().hex; correct=option==lesson['answer']
   db.execute('INSERT INTO attempts(id,session_id,lesson_id,correct,created_at,request_id,language) VALUES(?,?,?,?,?,?,?)',(attempt_id,sid,lesson_id,int(correct),datetime.now(timezone.utc).isoformat(),request_id,language or session['language']))
  return {'id':attempt_id,'correct':correct}
 def summary(self):
  with self.connect() as db:
   row=db.execute('SELECT COUNT(*) AS attempts,COALESCE(SUM(correct),0) AS correct FROM attempts').fetchone()
   sessions=db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
  return {'attempts':row['attempts'],'correct':row['correct'],'sessions':sessions,'data_kind':'local_demo_sessions','retention_days':7}
 def delete_session(self,sid):
  with self.connect() as db: db.execute('DELETE FROM sessions WHERE id=?',(sid,))
