"""Run the Acolhe Databricks notebooks through the official CLI and record evidence.

    databricks auth login --host https://<workspace> --profile acolhe
    python3 big_data/databricks/run_evidence.py --profile acolhe --branch 'Aksel+Ian'

Creates/updates a Git folder from the public repo, runs 00_setup_volume, then
medallion for 2026-11-05, 2026-11-06 and a repeat of 2026-11-06 on serverless,
capturing table counts after each run, DESCRIBE HISTORY and the gold queries via
a SQL warehouse. Writes big_data/evidence/databricks_<UTC date>.md.
"""
import argparse, json, re, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

REPO_URL = 'https://github.com/TomazVC/Acolhe---GS8'
TABLES = ('bronze', 'silver', 'quarantine', 'fact_indicators', 'dim_region', 'dim_language', 'gold_official_context', 'dim_municipality')

def cli(*args, profile, parse=True):
    r = subprocess.run(['databricks', *args, '-p', profile] + (['-o', 'json'] if parse else []), capture_output=True, text=True)
    if r.returncode: raise RuntimeError(f'databricks {" ".join(args[:3])} failed: {r.stderr.strip()[-800:]}')
    return json.loads(r.stdout) if parse and r.stdout.strip() else r.stdout

def sql(statement, warehouse, profile):
    body = json.dumps({'statement': statement, 'warehouse_id': warehouse, 'wait_timeout': '50s', 'on_wait_timeout': 'CONTINUE'})
    res = cli('api', 'post', '/api/2.0/sql/statements', '--json', body, profile=profile)
    while res['status']['state'] in ('PENDING', 'RUNNING'):
        time.sleep(3); res = cli('api', 'get', f"/api/2.0/sql/statements/{res['statement_id']}", profile=profile)
    if res['status']['state'] != 'SUCCEEDED': return None, res['status'].get('error', {}).get('message', res['status']['state'])
    cols = [c['name'] for c in res['manifest']['schema']['columns']]
    return (cols, res.get('result', {}).get('data_array', []) or []), None

def counts(ns, warehouse, profile):
    out = {}
    for t in TABLES:
        r, err = sql(f'SELECT COUNT(*) FROM {ns}.{t}', warehouse, profile)
        out[t] = int(r[1][0][0]) if r else 0 if 'TABLE_OR_VIEW_NOT_FOUND' in (err or '') else f'erro: {err}'
    return out

def run_notebook(path, params, profile, name):
    spec = {'run_name': name, 'tasks': [{'task_key': 'nb', 'notebook_task': {'notebook_path': path, 'base_parameters': params}}]}
    started = datetime.now(timezone.utc)
    run = cli('jobs', 'submit', '--json', json.dumps(spec), '--timeout', '30m', profile=profile)
    state = run.get('state', {})
    return {'name': name, 'params': params, 'run_id': run.get('run_id'), 'started_utc': started.isoformat(timespec='seconds'),
            'result': state.get('result_state'), 'message': state.get('state_message', ''), 'url': run.get('run_page_url')}

def table(cols, rows):
    return '\n'.join(['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)] + ['| ' + ' | '.join('' if v is None else str(v) for v in r) + ' |' for r in rows])

def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--profile', default='acolhe'); p.add_argument('--branch', default='main')
    p.add_argument('--namespace', default='workspace.acolhe'); p.add_argument('--out', default='big_data/evidence'); a = p.parse_args()
    me = cli('current-user', 'me', profile=a.profile)['userName']
    folder = f'/Users/{me}/Acolhe-GS8'
    repos = [r for r in cli('repos', 'list', '--path-prefix', folder, profile=a.profile) or [] if r.get('path') == folder]
    repo = repos[0] if repos else cli('repos', 'create', REPO_URL, 'gitHub', '--path', folder, profile=a.profile)
    cli('repos', 'update', str(repo['id']), '--branch', a.branch, profile=a.profile, parse=False)
    head = cli('repos', 'get', str(repo['id']), profile=a.profile)
    print(f"git folder ok: branch={head.get('branch')} commit={head.get('head_commit_id', '')[:7]}", flush=True)
    wh = cli('warehouses', 'list', profile=a.profile)[0]['id']
    nb = f'{folder}/big_data/databricks'
    cat, sch = a.namespace.split('.')
    vol = f'/Volumes/{cat}/{sch}/data'
    steps, snapshots = [], [('Antes', counts(a.namespace, wh, a.profile))]
    plan = [('00_setup_volume', {'catalog': cat, 'schema': sch}, None)] + [
        ('medallion', {'batch_date': d, 'schema': a.namespace, 'input_path': f'{vol}/input', 'output_path': f'{vol}/output'}, label)
        for d, label in (('2026-11-05', 'Depois do lote 2026-11-05'), ('2026-11-06', 'Depois do lote 2026-11-06'), ('2026-11-06', 'Reexecucao do lote 2026-11-06'))]
    for notebook, params, label in plan:
        step = run_notebook(f'{nb}/{notebook}', params, a.profile, f'acolhe-{notebook}-{params.get("batch_date", "setup")}')
        steps.append(step); print(f"{notebook} {params.get('batch_date', '')}: {step['result']} {step['url']}", flush=True)
        if step['result'] != 'SUCCESS': print(step['message']); break
        if label: snapshots.append((label, counts(a.namespace, wh, a.profile))); print('  ', snapshots[-1][1], flush=True)
    history = {t: sql(f'DESCRIBE HISTORY {a.namespace}.{t}', wh, a.profile) for t in ('bronze', 'silver')}
    qtext = re.sub(r'--[^\n]*', '', Path('big_data/queries.sql').read_text(encoding='utf-8'))
    results = []
    for i, q in enumerate(s.strip() for s in qtext.split(';') if s.strip()):
        qualified = re.sub(r'\b(fact_indicators|dim_region|dim_language|gold_official_context|dim_municipality)\b', rf'{a.namespace}.\1', q)
        results.append((i + 1, qualified, *sql(qualified, wh, a.profile)))
    now = datetime.now(timezone.utc)
    md = [f'# Evidencias Databricks ({now:%Y-%m-%d %H:%M} UTC)', '',
          f'Workspace Databricks Free Edition (serverless). Git folder da branch `{head.get("branch")}`, commit `{head.get("head_commit_id", "")[:7]}`. Gerado por `big_data/databricks/run_evidence.py`.', '',
          '## Execucoes', '', table(['Notebook', 'Parametros', 'Inicio (UTC)', 'Resultado', 'Run'], [(s['name'], json.dumps(s['params']), s['started_utc'], s['result'], s['url']) for s in steps]), '',
          '## Contagens antes, depois de cada lote e na reexecucao', '', table(['Etapa', *TABLES], [(n, *[c[t] for t in TABLES]) for n, c in snapshots]), '']
    for t, (r, err) in history.items():
        md += [f'## DESCRIBE HISTORY {t}', '']
        md += [table(['version', 'timestamp', 'operation', 'operationMetrics'], [(row[r[0].index('version')], row[r[0].index('timestamp')], row[r[0].index('operation')], (row[r[0].index('operationMetrics')] or '')[:160]) for row in r[1]]) if r else f'Erro: {err}', '']
    md += ['## Consultas ouro no Databricks', '']
    for n, q, r, err in results:
        md += [f'### Consulta {n}', '', '```sql', q, '```', '', table(*r) if r else f'Erro: {err}', '']
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    path = out / f'databricks_{now:%Y%m%d}.md'; path.write_text('\n'.join(md), encoding='utf-8'); print('written', path)
    return 0 if steps and all(s['result'] == 'SUCCESS' for s in steps) and all(r for _, _, r, _ in results) else 1

if __name__ == '__main__':
    sys.exit(main())
