"""Generate reproducible Big Data evidence: counts per batch, re-execution, gold queries.

    python -B -m big_data.evidence            # writes big_data/EVIDENCIAS.md

Runs the real pipeline in a temporary warehouse, one batch at a time, then the
official integration (needs big_data/official_snapshots from collect_official).
"""
import argparse, json, re, shutil, sqlite3, tempfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from big_data.pipeline import run

HERE = Path(__file__).resolve().parent
TABLES = ('batches', 'bronze', 'silver', 'quarantine', 'fact_indicators')
OFFICIAL = ('official_batches', 'silver_official_indicator', 'dim_municipality', 'gold_official_context')
INTERPRETATION = [
    'Demanda demonstrativa por territorio: Sao Paulo concentra a maior demanda sintetica. Mostra o agrupamento ouro, nao a realidade.',
    'Servicos demonstrativos por territorio: oferta sintetica por regiao, para comparar com a consulta 1.',
    'Demanda por idioma: espanhol predomina na base sintetica, coerente com o publico-alvo hispanofalante do Acolhe.',
    'Demanda por unidade de servico: indicador ilustrativo de pressao sobre a oferta; nao e estimativa causal nem de capacidade.',
    'Proveniencia e atualidade: todos os registros da camada demonstrativa estao marcados como sinteticos; a data mostra o snapshot mais recente aplicado pelo UPSERT.',
    'Dado real (OBMigra 2025): pedidos de refugio multiplicados pela parcela de criancas de 0 a 11 anos dao uma estimativa da ordem de grandeza de criancas solicitantes no Brasil, o publico potencial do Acolhe.',
    'Dado real (OBMigra 2025): reconhecimentos por 100 pedidos. As coortes diferem (decisoes de 2025 incluem pedidos antigos), entao o numero e indicativo.',
    'Cobertura territorial: os 645 municipios de SP vindos do IBGE contra as regioes presentes na base demonstrativa; mostra o quanto falta para cobertura real.',
]

def counts(db_path, tables):
    with closing(sqlite3.connect(db_path)) as db:
        have = {r[0] for r in db.execute("select name from sqlite_master where type='table'")}
        return {t: (db.execute(f'select count(*) from {t}').fetchone()[0] if t in have else 0) for t in tables}

def build(official_root, input_dir):
    work = Path(tempfile.mkdtemp()); stage = work / 'input'; out = work / 'output'; stage.mkdir(); out.mkdir()
    rows = [('Antes (vazio)', {t: 0 for t in TABLES})]
    for day in sorted({p.stem.split('_')[1] for p in Path(input_dir).glob('*_*.csv')}):
        for f in Path(input_dir).glob(f'*_{day}.csv'): shutil.copy2(f, stage / f.name)
        run(stage, out); rows.append((f'Depois do lote {day}', counts(out / 'warehouse.db', TABLES)))
    summary = run(stage, out); rows.append(('Reexecucao (mesmos arquivos)', counts(out / 'warehouse.db', TABLES)))
    official = []
    if (Path(official_root) / 'manifests').is_dir():
        from big_data.official_integration import integrate
        integrate(official_root, out); official.append(('Integracao oficial', counts(out / 'warehouse.db', OFFICIAL)))
        integrate(official_root, out); official.append(('Reexecucao oficial', counts(out / 'warehouse.db', OFFICIAL)))
    sql = re.sub(r'--[^\n]*', '', (HERE / 'queries.sql').read_text(encoding='utf-8'))
    queries = []
    with closing(sqlite3.connect(out / 'warehouse.db')) as db:
        for i, q in enumerate(s.strip() for s in sql.split(';') if s.strip()):
            try:
                cur = db.execute(q); queries.append((i + 1, q, [c[0] for c in cur.description], cur.fetchall(), None))
            except sqlite3.OperationalError as e:
                queries.append((i + 1, q, [], [], str(e)))
    shutil.rmtree(work, ignore_errors=True)
    return rows, official, queries, summary

def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(map(str, headers)) + ' |', '|' + '---|' * len(headers)] +
                     ['| ' + ' | '.join(f'{v:.2f}' if isinstance(v, float) else str(v) for v in r) + ' |' for r in rows])

def render(rows, official, queries, summary):
    md = [f'# Evidencias Big Data (geradas em {datetime.now(timezone.utc):%Y-%m-%d %H:%M} UTC)', '',
          'Gerado por `python -B -m big_data.evidence` com o pipeline real em um warehouse temporario. Reproduzivel.', '',
          '## Contagens por lote e reexecucao (camada demonstrativa, synthetic=true)', '',
          table(['Etapa', *TABLES], [(n, *[c[t] for t in TABLES]) for n, c in rows]), '',
          'Leitura: cada lote traz um arquivo por fonte (2 arquivos, 4 linhas brutas) e o bronze imutavel acumula 4 -> 8 linhas. A prata faz UPSERT por (fonte, record_id): o segundo lote atualiza as mesmas 4 chaves em vez de duplica-las. A reexecucao nao altera nenhuma contagem: arquivos com hash ja registrado sao ignorados.', '']
    if official:
        md += ['## Fontes reais (OBMigra 2025 + IBGE)', '', table(['Etapa', *OFFICIAL], [(n, *[c[t] for t in OFFICIAL]) for n, c in official]), '']
    md += ['## Consultas ouro interpretadas', '']
    for (n, q, cols, res, err), text in zip(queries, INTERPRETATION + [''] * len(queries)):
        md += [f'### Consulta {n}', '', '```sql', q, '```', '']
        md += [f'Erro: {err}' if err else table(cols, res), '', f'Interpretacao: {text}', '']
    md += ['## Contrato entregue ao MVP', '', '```json', json.dumps({k: summary[k] for k in ('synthetic', 'source_batches', 'totals', 'quality')}, ensure_ascii=False, indent=2), '```', '']
    return '\n'.join(md)

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--official', default='big_data/official_snapshots'); p.add_argument('--input', default='big_data/input')
    p.add_argument('--out', default='big_data/EVIDENCIAS.md'); a = p.parse_args()
    rows, official, queries, summary = build(a.official, a.input)
    Path(a.out).write_text(render(rows, official, queries, summary), encoding='utf-8')
    failed = [n for n, *_, err in queries if err]
    print(f'written {a.out}; queries ok={len(queries) - len(failed)} failed={failed}')
    raise SystemExit(1 if failed else 0)
