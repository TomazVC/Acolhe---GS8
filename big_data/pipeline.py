from contextlib import closing
"""Offline reproducible medallion pipeline. Demo inputs are explicitly synthetic."""
import argparse, csv, hashlib, json, sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

SOURCES = ('demand', 'services')
LANGUAGES = ('pt', 'es', 'en')

def create_demo(folder):
    folder=Path(folder); folder.mkdir(parents=True,exist_ok=True)
    for day,delta in [('2026-11-05',0),('2026-11-06',10)]:
        for source in SOURCES:
            rows=[['sp','Sao Paulo','es',(100+delta) if source=='demand' else (12+delta),day,'true'],
                  ['pr','Parana','pt',(70+delta) if source=='demand' else (8+delta),day,'true']]
            with (folder/f'{source}_{day}.csv').open('w',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow(['record_id','region','language','count','snapshot_date','synthetic']); w.writerows(rows)

def validated(row):
    # R1: required business key and territory; R2: supported language;
    # R3: nonnegative integer metric and valid ISO date; explicit provenance.
    if not row.get('record_id','').strip() or not row.get('region','').strip(): raise ValueError('required key/region')
    if row.get('language') not in LANGUAGES: raise ValueError('unsupported language')
    count=int(row['count'])
    if count<0: raise ValueError('negative count')
    date.fromisoformat(row['snapshot_date'])
    if row.get('synthetic') not in ('true','false'): raise ValueError('missing provenance flag')
    return count

def run(input_dir, output_dir):
    input_dir=Path(input_dir); output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(output_dir/'warehouse.db')) as db, db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS bronze (source TEXT, file_hash TEXT, row_number INTEGER, payload TEXT, PRIMARY KEY(source,file_hash,row_number));
        CREATE TABLE IF NOT EXISTS batches (source TEXT,file_hash TEXT,filename TEXT, PRIMARY KEY(source,file_hash));
        CREATE TABLE IF NOT EXISTS silver (source TEXT,record_id TEXT,region TEXT,language TEXT,count INTEGER,snapshot_date TEXT,synthetic INTEGER, PRIMARY KEY(source,record_id));
        CREATE TABLE IF NOT EXISTS quarantine (source TEXT,file_hash TEXT,row_number INTEGER,reason TEXT, PRIMARY KEY(source,file_hash,row_number));
        """)
        for source in SOURCES:
            files=sorted(input_dir.glob(source+'_*.csv'))
            if not files: raise FileNotFoundError(f'No input for {source}: {input_dir}')
            for path in files:
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                if db.execute('SELECT 1 FROM batches WHERE source=? AND file_hash=?',(source,digest)).fetchone(): continue
                with path.open(encoding='utf-8-sig',newline='') as f:
                    for n,row in enumerate(csv.DictReader(f),1):
                        db.execute('INSERT OR IGNORE INTO bronze VALUES(?,?,?,?)',(source,digest,n,json.dumps(row,ensure_ascii=False)))
                        try: count=validated(row)
                        except (ValueError,KeyError,TypeError) as error:
                            db.execute('INSERT OR IGNORE INTO quarantine VALUES(?,?,?,?)',(source,digest,n,str(error))); continue
                        db.execute("""INSERT INTO silver VALUES(?,?,?,?,?,?,?) ON CONFLICT(source,record_id) DO UPDATE SET region=excluded.region,language=excluded.language,count=excluded.count,snapshot_date=excluded.snapshot_date,synthetic=excluded.synthetic WHERE excluded.snapshot_date >= silver.snapshot_date""",(source,row['record_id'].strip(),row['region'].strip(),row['language'],count,row['snapshot_date'],row['synthetic']=='true'))
                db.execute('INSERT INTO batches VALUES(?,?,?)',(source,digest,path.name))
        db.executescript("""
        DROP TABLE IF EXISTS fact_indicators; DROP TABLE IF EXISTS dim_region; DROP TABLE IF EXISTS dim_language;
        CREATE TABLE dim_region AS SELECT row_number() OVER(ORDER BY region) AS region_id,region FROM silver GROUP BY region;
        CREATE TABLE dim_language AS SELECT row_number() OVER(ORDER BY language) AS language_id,language FROM silver GROUP BY language;
        CREATE TABLE fact_indicators AS SELECT s.source,s.record_id,r.region_id,l.language_id,s.count,s.snapshot_date,s.synthetic FROM silver s JOIN dim_region r USING(region) JOIN dim_language l USING(language);
        """)
        def grouped(column):
            return [{column:k,'demand':d,'services':s} for k,d,s in db.execute(f"SELECT {column},SUM(CASE WHEN source='demand' THEN count ELSE 0 END),SUM(CASE WHEN source='services' THEN count ELSE 0 END) FROM silver GROUP BY {column} ORDER BY {column}")]
        totals=dict(db.execute('SELECT source,SUM(count) FROM silver GROUP BY source'))
        summary={'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),'synthetic':bool(db.execute('SELECT COALESCE(MAX(synthetic),0) FROM silver').fetchone()[0]),'source_batches':db.execute('SELECT COUNT(*) FROM batches').fetchone()[0],'totals':totals,'by_region':grouped('region'),'by_language':grouped('language'),'quality':{'rejected':db.execute('SELECT COUNT(*) FROM quarantine').fetchone()[0]},'provenance':{'mode':'normalized CSV imports; supplied demo data are synthetic','sources':list(SOURCES)}}
        temporary=output_dir/'summary.tmp'; temporary.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8'); temporary.replace(output_dir/'summary.json')
        for table in ('dim_region','dim_language','fact_indicators'):
            cursor=db.execute(f'SELECT * FROM {table}')
            with (output_dir/f'{table}.csv').open('w',newline='',encoding='utf-8') as f:
                writer=csv.writer(f); writer.writerow([c[0] for c in cursor.description]); writer.writerows(cursor)
    return summary

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--input',default='big_data/input'); parser.add_argument('--output',default='big_data/output'); parser.add_argument('--demo',action='store_true'); args=parser.parse_args()
    if args.demo: create_demo(args.input)
    print(json.dumps(run(args.input,args.output),ensure_ascii=False,indent=2))
