"""Checks emitted SQL only; does not validate Databricks execution."""
import ast
from pathlib import Path
import unittest

class CopyStatementTests(unittest.TestCase):
 def test_emitted_copy_preserves_column_names_and_rejects_malformed_csv(self):
  tree=ast.parse(Path('big_data/databricks/medallion.py').read_text(encoding='utf-8'))
  loop=next(node for node in tree.body if isinstance(node,ast.For) and isinstance(node.target,ast.Name) and node.target.id=='source')
  class Capture:
   def __init__(self): self.statements=[]
   def sql(self,statement): self.statements.append(statement)
  spark=Capture()
  # Reviewed exception: executes this repository's own notebook AST against a capture stub,
  # never external input.
  exec(compile(ast.Module(body=[loop],type_ignores=[]),'<copy-statement>','exec'),{'spark':spark,'bronze':'main.acolhe.bronze','input_path':'/Volumes/main/acolhe/data/input','batch_date':'2026-11-05'})  # nosemgrep: devsecops.no-dynamic-evaluation
  self.assertEqual(len(spark.statements),2)
  for source,statement in zip(('demand','services'),spark.statements):
   self.assertIn(source+'_2026-11-05.csv',statement)
   for column in ('record_id','region','language','count','snapshot_date','synthetic'):
    self.assertIn(f'CAST({column} AS STRING) AS {column}',statement)
   self.assertIn("'mode' = 'FAILFAST'",statement)
   self.assertIn("'force' = 'false'",statement)
