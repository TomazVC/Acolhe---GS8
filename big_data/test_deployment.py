import ast, unittest
from pathlib import Path

class DeploymentContractTests(unittest.TestCase):
    def test_airflow_three_public_sdk(self):
        tree=ast.parse(Path('big_data/airflow/acolhe_dag.py').read_text(encoding='utf-8'))
        modules=[node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
        self.assertIn('airflow.sdk',modules)
        self.assertNotIn('airflow.decorators',modules)
    def test_bronze_copy_into_silver_merge(self):
        text=Path('big_data/databricks/medallion.py').read_text(encoding='utf-8')
        self.assertIn('COPY INTO {bronze}',text)
        self.assertNotIn('DeltaTable.forName(spark,bronze)',text)
        self.assertIn('DeltaTable.forName(spark,silver)',text)
