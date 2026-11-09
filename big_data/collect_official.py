"""Fetch official non-personal reference sources. Never alters demo gold.
Real UTC retrieval time is generated internally; no backdating option exists.
"""
import argparse,csv,gzip,hashlib,json,re,uuid
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen

OBMIGRA_PAGE='https://www.gov.br/mj/pt-br/assuntos/seus-direitos/migracoes/portal-de-imigracao-laboral/obmigra-1/relatorios-obmigra/dados-consolidados/2025'
SOURCES={
 'ibge':{'id':'ibge_municipalities_sp','url':'https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios','extension':'json','publisher':'IBGE','purpose':'Territorial reference only; not migration demand or service capacity','license_status':'specific_api_license_not_verified','license_evidence_url':'https://servicodados.ibge.gov.br/api/docs/localidades','restriction':'Local research reference; verify dataset-specific reuse terms before redistribution.'},
 'obmigra':{'id':'obmigra_consolidated_2025','url':OBMIGRA_PAGE+'/Dados2025.pdf','extension':'pdf','publisher':'OBMigra / Ministerio da Justica e Seguranca Publica','purpose':'Published aggregate statistical report, preserved unmodified; not integrated as a tabular source','license_status':'official_page_declares_CC_BY_ND_3_0','license_url':'https://creativecommons.org/licenses/by-nd/3.0/','license_evidence_url':OBMIGRA_PAGE,'license_checked_at':'2026-11-07','restriction':'Preserve original and attribution; do not imply unrestricted adaptation or dataset-specific license.'}}

def normalize_municipalities(rows):
    if not isinstance(rows,list) or not rows: raise ValueError('Expected nonempty municipality list')
    result=[]; seen=set()
    for row in rows:
        try:
            identifier=int(row['id']); name=row['nome'].strip()
            uf=(row.get('microrregiao') or {}).get('mesorregiao',{}).get('UF')
            if not uf: uf=row['regiao-imediata']['regiao-intermediaria']['UF']
            state_id=int(uf['id']); code=uf['sigla']; state=uf['nome']
            if not name or identifier in seen or state_id!=35 or not re.fullmatch(r'[A-Z]{2}',code): raise ValueError('Invalid/duplicate territory')
        except (KeyError,AttributeError,TypeError,ValueError) as error: raise ValueError('Invalid/duplicate municipality') from error
        seen.add(identifier)
        result.append({'municipality_id':identifier,'municipality':name,'state_id':state_id,'state_code':code,'state':state})
    return sorted(result,key=lambda r:r['municipality_id'])

def save_snapshot(root,spec,content,http):
    root=Path(root); now=datetime.now(timezone.utc); stamp=now.strftime('%Y%m%dT%H%M%S%fZ')+'_'+uuid.uuid4().hex[:12]
    digest=hashlib.sha256(content).hexdigest()
    relative=Path('raw')/spec['id']/(digest+'.'+spec['extension']); target=root/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest()!=digest: raise ValueError('Existing raw snapshot hash mismatch')
    else:
        with target.open('xb') as f: f.write(content)
    manifest={**spec,'retrieved_at':now.isoformat(),'retrieval_day_utc':now.date().isoformat(),'sha256':digest,'bytes':len(content),'raw_path':relative.as_posix(),'synthetic':False,'http':http}
    folder=root/'manifests'; folder.mkdir(parents=True,exist_ok=True)
    (folder/f'{stamp}_{spec["id"]}.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest

def collect(source,root):
    spec=SOURCES[source]
    request=Request(spec['url'],headers={'User-Agent':'Acolhe-academic-reference/1.0','Accept-Encoding':'identity'})
    with urlopen(request,timeout=60) as response:
        content=response.read(30*1024*1024+1)
        if len(content)>30*1024*1024: raise ValueError('Source exceeds 30 MiB limit')
        if content[:2]==b'\x1f\x8b': content=gzip.decompress(content)
        http={'status':response.status,'content_type':response.headers.get('Content-Type'),'last_modified':response.headers.get('Last-Modified'),'etag':response.headers.get('ETag'),'final_url':response.url}
    if source=='ibge': rows=normalize_municipalities(json.loads(content))
    elif not content.startswith(b'%PDF-'): raise ValueError('Expected official PDF; received other content')
    manifest=save_snapshot(root,spec,content,http)
    if source=='ibge':
        folder=Path(root)/'normalized'/manifest['retrieval_day_utc']; folder.mkdir(parents=True,exist_ok=True)
        with (folder/'municipalities_sp.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        manifest['normalized_records']=len(rows)
    return manifest

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--source',choices=['ibge','obmigra','all'],default='all'); parser.add_argument('--output',default='big_data/official_snapshots'); args=parser.parse_args()
    failures=0
    for source in SOURCES if args.source=='all' else [args.source]:
        try: print(json.dumps(collect(source,args.output),ensure_ascii=False,indent=2))
        except Exception as error:
            failures+=1; print(json.dumps({'source':source,'status':'failed','error_type':type(error).__name__,'error':str(error)}))
    raise SystemExit(1 if failures else 0)
