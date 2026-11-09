from contextlib import closing
"""Read-only SQLite reporting robot. No email, external writes or identifiers."""
import argparse, json, logging, sqlite3
from datetime import datetime,timezone
from pathlib import Path

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
            languages=[{'language':lang,'attempts':n,'correct':c} for lang,n,c in db.execute(f'SELECT {language},COUNT(a.id),SUM(CASE WHEN a.correct=1 THEN 1 ELSE 0 END) FROM sessions s LEFT JOIN attempts a ON a.session_id=s.id GROUP BY {language} ORDER BY {language}')]
        report={'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'local aggregate only; no personal identifiers','totals':{'sessions':sessions,'attempts':attempts,'correct':correct,'accuracy':round(correct/attempts,4) if attempts else 0},'by_language':languages}
        temp=output_dir/'progress.tmp'; temp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8'); temp.replace(output_dir/'progress.json')
        (output_dir/'progress.md').write_text(f"# Relatorio local Acolhe\n\nSessoes: {sessions}\nTentativas: {attempts}\nAcertos: {correct}\nTaxa de acerto: {report['totals']['accuracy']:.1%}\n\nDados agregados. Nao enviado a terceiros.\n",encoding='utf-8')
        logger.info('report_completed attempts=%s',attempts)
        return report
    except Exception as error:
        logger.error('report_failed type=%s',type(error).__name__)
        raise
    finally:
        logger.removeHandler(handler); handler.close()

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--db',default='data/acolhe.db'); p.add_argument('--output',default='rpa/output'); a=p.parse_args()
    try: print(json.dumps(generate_report(a.db,a.output),ensure_ascii=False,indent=2))
    except (OSError,sqlite3.Error) as error: p.exit(1,f'RPA failed: {error}\n')
