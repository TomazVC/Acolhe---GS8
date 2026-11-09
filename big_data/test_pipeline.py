from contextlib import closing
import tempfile, unittest, sqlite3
from pathlib import Path
from big_data.pipeline import run, create_demo

class PipelineTests(unittest.TestCase):
    def test_two_batches_idempotent_and_gold(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); create_demo(p/'input')
            first=run(p/'input',p/'output'); second=run(p/'input',p/'output')
            self.assertEqual(first['totals'], second['totals'])
            self.assertTrue(first['synthetic'])
            self.assertEqual(first['source_batches'],4)
            self.assertEqual(first['totals']['demand'],190)
            with closing(sqlite3.connect(p/'output'/'warehouse.db')) as db:
                self.assertEqual(db.execute('select count(*) from bronze').fetchone()[0],8)
                self.assertEqual(db.execute('select count(*) from silver').fetchone()[0],4)
    def test_quality_rejects_invalid_rows(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); create_demo(p/'input')
            f=p/'input'/'demand_2026-11-05.csv'
            with f.open('a',encoding='utf-8') as out: out.write('bad,,xx,-1,2026-11-05,true\n')
            result=run(p/'input',p/'output')
            self.assertEqual(result['quality']['rejected'],1)

    def test_all_quality_rules(self):
        from big_data.pipeline import validated
        base={'record_id':'x','region':'SP','language':'pt','count':'1','snapshot_date':'2026-11-05','synthetic':'true'}
        for field,value in [('record_id',''),('region',' '),('language','xx'),('count','-1'),('count','1.5'),('snapshot_date','not-a-date'),('synthetic','unknown')]:
            with self.subTest(field=field,value=value):
                with self.assertRaises(ValueError): validated(dict(base,**{field:value}))

    def test_five_gold_queries_execute(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d); create_demo(p/'input'); run(p/'input',p/'output')
            queries=Path(__file__).with_name('queries.sql').read_text(encoding='utf-8')
            statements=[statement for statement in queries.split(';') if 'SELECT' in statement]
            self.assertEqual(len(statements),5)
            with closing(sqlite3.connect(p/'output'/'warehouse.db')) as db:
                for statement in statements:
                    self.assertTrue(db.execute(statement).fetchall())
