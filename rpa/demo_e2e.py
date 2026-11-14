"""End-to-end RPA flow: activity in the app -> robot -> result consumed by the MVP.

Runs the REAL HTTP server and the REAL robot against the same SQLite file and
records three scenarios as evidence: success, business decision and failure.

    python -B -m rpa.demo_e2e                       # isolated temp DB (default)
    python -B -m rpa.demo_e2e --evidence rpa/evidence

The answers are scripted test activity by the team, not data from children.
"""
import argparse, json, shutil, sys, tempfile, threading, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from app.server import create_server
from app.core import LESSONS
from rpa.robot import generate_report

def call(base, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(base + path, data=data, headers={'Content-Type': 'application/json'} if data else {})
    with urllib.request.urlopen(req, timeout=5) as r: return json.loads(r.read())

def answer(base, sid, lesson, correct, n):
    right = next(l['answer'] for l in LESSONS if l['id'] == lesson)
    option = right if correct else (right + 1) % 3
    return call(base, '/api/attempts', {'session_id': sid, 'lesson_id': lesson, 'option': option, 'request_id': f'demo-{lesson}-{n}', 'language': 'pt'})

def run_demo(workdir):
    workdir = Path(workdir); db = workdir / 'acolhe.db'; out = workdir / 'rpa_output'
    server = create_server('127.0.0.1', 0, db_path=db, automation_path=out / 'progress.json')
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{server.server_port}'; steps = []
    def log(step, **data):
        steps.append({'step': step, 'at': datetime.now(timezone.utc).isoformat(), **data}); print(f'[{step}]', json.dumps(data, ensure_ascii=False), flush=True)
    try:
        log('0_mvp_before_robot', automation=call(base, '/api/automation'))
        # 1. Activity in the app: one child-session (test) answers every lesson correctly.
        sid = call(base, '/api/sessions', {'language': 'pt'})['id']
        for n, lesson in enumerate(l['id'] for l in LESSONS): answer(base, sid, lesson, True, n)
        report = generate_report(db, out)
        log('1_success', decision=report['decision'], totals=report['totals'], mvp=call(base, '/api/automation')['totals'])
        # 2. Decision branch: 'mobilidade' gets 3 wrong answers -> below 60% -> flagged for review.
        sid2 = call(base, '/api/sessions', {'language': 'es'})['id']
        for n in range(3): answer(base, sid2, 'mobilidade', False, 100 + n)
        report = generate_report(db, out)
        mvp = call(base, '/api/automation')
        log('2_decision', decision=report['decision'], mvp_decision=mvp['decision'])
        # 3. Failure branch: database missing -> robot logs error, no DB is created, MVP keeps last good report.
        missing = workdir / 'nao_existe.db'
        try: generate_report(missing, out); failed = None
        except FileNotFoundError as e: failed = type(e).__name__
        log('3_failure', error=failed, db_created=missing.exists(), mvp_still_serves=call(base, '/api/automation')['decision']['status'])
        log_lines = (out / 'robot.log').read_text(encoding='utf-8').splitlines()
        return {'steps': steps, 'robot_log': log_lines, 'progress_md': (out / 'progress.md').read_text(encoding='utf-8')}
    finally:
        server.shutdown(); server.server_close()

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--evidence', help='Folder to save evidence JSON/log/report'); a = p.parse_args()
    with tempfile.TemporaryDirectory() as d:
        result = run_demo(d)
        if a.evidence:
            folder = Path(a.evidence) / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'); folder.mkdir(parents=True)
            (folder / 'e2e.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            (folder / 'robot.log').write_text('\n'.join(result['robot_log']) + '\n', encoding='utf-8')
            (folder / 'progress.md').write_text(result['progress_md'], encoding='utf-8')
            print('evidence saved to', folder)
    ok = [s['step'] for s in result['steps']] == ['0_mvp_before_robot', '1_success', '2_decision', '3_failure']
    sys.exit(0 if ok else 1)
