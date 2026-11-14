from contextlib import closing
"""Read-only SQLite reporting robot. No email, external writes or identifiers."""
import argparse, json, logging, sqlite3, time
from datetime import datetime,timezone
from pathlib import Path

REVIEW_ACCURACY=0.6   # business rule: lessons below 60% accuracy need educator review
REVIEW_MIN_ATTEMPTS=3 # ...but only with enough attempts to be meaningful

def decide(attempts,lessons):
    """BPMN gateway 'Ha atividade? / Licao abaixo da meta?'. Returns status + lessons to review."""
    if attempts==0: return {'status':'sem_atividade','action':'Nenhuma atividade registrada; nada a consolidar.','lessons_to_review':[]}
    review=[l['lesson_id'] for l in lessons if l['attempts']>=REVIEW_MIN_ATTEMPTS and l['accuracy']<REVIEW_ACCURACY]
    if review: return {'status':'reforco_recomendado','action':'Revisar com educadores as licoes abaixo da meta de acerto.','lessons_to_review':review}
    return {'status':'progresso_adequado','action':'Sem intervencao necessaria.','lessons_to_review':[]}

def generate_report(database,output_dir):
    database=Path(database).resolve(); output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    logger=logging.getLogger('acolhe.rpa'); logger.setLevel(logging.INFO)
    handler=logging.FileHandler(output_dir/'robot.log',encoding='utf-8'); handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s')); logger.addHandler(handler)
    try:
        logger.info('report_started')
        if not database.is_file(): raise FileNotFoundError('Application database does not exist; start the MVP and complete an exercise first.')
        with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=10)) as db:
            db.execute('PRAGMA query_only=ON')
            attempts,correct=db.execute('SELECT COUNT(*),COALESCE(SUM(CASE WHEN correct=1 THEN 1 ELSE 0 END),0) FROM attempts').fetchone()
            sessions=db.execute('SELECT COUNT(*) FROM sessions').fetchone()[0]
            # Older databases have only session language; never rewrite their history.
            has_language=any(row[1]=='language' for row in db.execute('PRAGMA table_info(attempts)'))
            language='COALESCE(a.language,s.language)' if has_language else 's.language'
            languages=[{'language':lang,'attempts':n,'correct':c} for lang,n,c in db.execute(f'SELECT {language},COUNT(a.id),COALESCE(SUM(CASE WHEN a.correct=1 THEN 1 ELSE 0 END),0) FROM sessions s LEFT JOIN attempts a ON a.session_id=s.id GROUP BY {language} ORDER BY {language}')]
            lessons=[{'lesson_id':lid,'attempts':n,'correct':c,'accuracy':round(c/n,4)} for lid,n,c in db.execute('SELECT lesson_id,COUNT(*),COALESCE(SUM(CASE WHEN correct=1 THEN 1 ELSE 0 END),0) FROM attempts GROUP BY lesson_id ORDER BY lesson_id')]
        decision=decide(attempts,lessons)
        logger.info('decision status=%s review=%s',decision['status'],','.join(decision['lessons_to_review']) or '-')
        report={'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'local aggregate only; no personal identifiers','totals':{'sessions':sessions,'attempts':attempts,'correct':correct,'accuracy':round(correct/attempts,4) if attempts else 0},'by_language':languages,'by_lesson':lessons,'decision':decision}
        temp=output_dir/'progress.tmp'; temp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); temp.replace(output_dir/'progress.json')
        review='\n'.join(f"- {l}" for l in decision['lessons_to_review']) or '- nenhuma'
        (output_dir/'progress.md').write_text(f"# Relatorio local Acolhe\n\nSessoes: {sessions}\nTentativas: {attempts}\nAcertos: {correct}\nTaxa de acerto: {report['totals']['accuracy']:.1%}\n\n## Decisao: {decision['status']}\n{decision['action']}\n\nLicoes para revisar:\n{review}\n\nDados agregados. Nao enviado a terceiros.\n",encoding='utf-8')
        logger.info('report_completed attempts=%s',attempts)
        return report
    except Exception as error:
        logger.error('report_failed type=%s',type(error).__name__)
        raise
    finally:
        logger.removeHandler(handler); handler.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--db',default='data/acolhe.db'); p.add_argument('--output',default='rpa/output')
    p.add_argument('--every',type=int,default=0,help='Built-in schedule: rerun every N seconds (0 = run once)')
    p.add_argument('--runs',type=int,default=0,help='With --every: stop after N runs (0 = until Ctrl+C)'); a=p.parse_args()
    if a.every<0 or a.runs<0: p.error('--every/--runs must be >= 0')
    done=failures=0
    try:
        while True:
            try: print(json.dumps(generate_report(a.db,a.output),ensure_ascii=False,indent=2),flush=True)
            except (OSError,sqlite3.Error) as error:
                failures+=1; print(f'RPA failed: {error}',flush=True)
                if not a.every: p.exit(1)
            done+=1
            if not a.every or (a.runs and done>=a.runs): break
            time.sleep(a.every)
    except KeyboardInterrupt: pass
    if failures: p.exit(1)
