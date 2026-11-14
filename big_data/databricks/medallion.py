# Databricks notebook source
# Databricks Runtime / serverless with Delta. Defaults target Free Edition (catalog "workspace").
# Run 00_setup_volume first; then run with batch_date=2026-11-05, 2026-11-06 and repeat to show idempotency.
# COMMAND ----------
from delta.tables import DeltaTable
from pyspark.sql import functions as F, Window
import re,json
from pathlib import Path
from datetime import date,datetime,timezone

dbutils.widgets.text('input_path','/Volumes/workspace/acolhe/data/input')
dbutils.widgets.text('output_path','/Volumes/workspace/acolhe/data/output')
dbutils.widgets.text('schema','workspace.acolhe')
dbutils.widgets.text('batch_date','2026-11-05')
input_path=dbutils.widgets.get('input_path').rstrip('/')
output_path=dbutils.widgets.get('output_path').rstrip('/')
namespace=dbutils.widgets.get('schema')
batch_date=dbutils.widgets.get('batch_date'); date.fromisoformat(batch_date)
assert re.fullmatch(r'[A-Za-z_]\w*\.[A-Za-z_]\w*',namespace),'Use catalog.schema identifiers'
spark.sql(f'CREATE SCHEMA IF NOT EXISTS {namespace}')
# COMMAND ----------
# COPY INTO tracks loaded file paths and skips them on subsequent executions.
# Input files are immutable; publish corrections under a NEW filename/date.
assert input_path.startswith('/Volumes/') and "'" not in input_path and "\\" not in input_path, 'Use a Unity Catalog volume path without quotes'
bronze=f'{namespace}.bronze'
spark.sql(f"""CREATE TABLE IF NOT EXISTS {bronze} (
 record_id STRING, region STRING, language STRING, count STRING,
 snapshot_date STRING, synthetic STRING, source STRING, batch_date STRING
) USING DELTA""")
for source in ('demand','services'):
    file_path=f'{input_path}/{source}_{batch_date}.csv'
    spark.sql(f"""COPY INTO {bronze}
    FROM (SELECT CAST(record_id AS STRING) AS record_id, CAST(region AS STRING) AS region,
                 CAST(language AS STRING) AS language, CAST(count AS STRING) AS count,
                 CAST(snapshot_date AS STRING) AS snapshot_date, CAST(synthetic AS STRING) AS synthetic,
                 '{source}' AS source, '{batch_date}' AS batch_date
          FROM '{file_path}')
    FILEFORMAT = CSV
    FORMAT_OPTIONS ('header' = 'true', 'inferSchema' = 'false', 'mode' = 'FAILFAST')
    COPY_OPTIONS ('force' = 'false')""")
# Bronze ingestion is COPY INTO, NOT MERGE. Silver retains business-key MERGE.
# COMMAND ----------
raw=spark.table(bronze)
raw=raw.withColumn('row_hash',F.sha2(F.to_json(F.struct(*[F.col(c) for c in raw.columns])),256))
clean=(raw.withColumn('record_id',F.trim('record_id')).withColumn('region',F.trim('region'))
    .withColumn('metric',F.expr('try_cast(count as BIGINT)'))
    .withColumn('day',F.expr('try_cast(snapshot_date as DATE)')))
valid=F.coalesce((F.length('record_id')>0)&(F.length('region')>0)&F.col('language').isin('pt','es','en')&(F.col('metric')>=0)&F.col('count').rlike('^[0-9]+$')&F.col('day').isNotNull()&F.col('synthetic').isin('true','false'),F.lit(False))
# Rules: required key/territory; allowed language; valid nonnegative integer/date/provenance.
clean.filter(~valid).write.format('delta').mode('overwrite').saveAsTable(f'{namespace}.quarantine')
window=Window.partitionBy('source','record_id').orderBy(F.col('day').desc(),F.col('batch_date').desc(),F.col('row_hash').desc())
latest=(clean.filter(valid).withColumn('rn',F.row_number().over(window)).filter('rn=1')
    .select('source','record_id','region','language',F.col('metric').alias('count'),F.col('day').alias('snapshot_date'),(F.col('synthetic')=='true').alias('synthetic')))
silver=f'{namespace}.silver'
if not spark.catalog.tableExists(silver): latest.limit(0).write.format('delta').saveAsTable(silver)
(DeltaTable.forName(spark,silver).alias('t').merge(latest.alias('s'),'t.source=s.source AND t.record_id=s.record_id')
 .whenMatchedUpdateAll(condition='s.snapshot_date >= t.snapshot_date').whenNotMatchedInsertAll().execute())
# COMMAND ----------
s=spark.table(silver)
regions=s.select('region').distinct().withColumn('region_id',F.sha2('region',256))
languages=s.select('language').distinct().withColumn('language_id',F.sha2('language',256))
regions.write.format('delta').mode('overwrite').saveAsTable(f'{namespace}.dim_region')
languages.write.format('delta').mode('overwrite').saveAsTable(f'{namespace}.dim_language')
fact=s.join(regions,'region').join(languages,'language').select('source','record_id','region_id','language_id','count','snapshot_date','synthetic')
fact.write.format('delta').mode('overwrite').saveAsTable(f'{namespace}.fact_indicators')
# COMMAND ----------
# Small aggregate exported for the MVP; detailed tables remain in Delta.
def grouped(column):
    rows=s.groupBy(column).pivot('source',['demand','services']).sum('count').fillna(0).orderBy(column).collect()
    return [r.asDict() for r in rows]
summary={'schema_version':1,'generated_at':datetime.now(timezone.utc).isoformat(),
 'synthetic':s.filter('synthetic=true').limit(1).count()>0,
 'source_batches':raw.select('source','batch_date').distinct().count(),
 'totals':{r['source']:r['total'] for r in s.groupBy('source').agg(F.sum('count').alias('total')).collect()},
 'by_region':grouped('region'),'by_language':grouped('language'),
 'quality':{'rejected':spark.table(f'{namespace}.quarantine').count()},
 'provenance':{'mode':'Databricks normalized CSV import','sources':['demand','services']}}
# COMMAND ----------
# Real official context (OBMigra 2025 + IBGE SP). Databricks Free has no Airflow
# connection: upload big_data/output/gold_official_context.csv and
# official_snapshots/normalized/<day>/municipalities_sp.csv to {input_path}/official/.
official_dir=f'{input_path}/official'
def _exists(p):
    try: dbutils.fs.ls(p); return True
    except Exception: return False
if _exists(f'{official_dir}/gold_official_context.csv'):
    for table,file,key in (('gold_official_context','gold_official_context.csv','t.indicator_id=s.indicator_id AND t.territory=s.territory AND t.reference_year=s.reference_year'),
                           ('dim_municipality','municipalities_sp.csv','t.municipality_id=s.municipality_id')):
        if not _exists(f'{official_dir}/{file}'): continue
        bronze_o=f'{namespace}.bronze_{table}'
        spark.sql(f"CREATE TABLE IF NOT EXISTS {bronze_o} USING DELTA")
        spark.sql(f"""COPY INTO {bronze_o} FROM '{official_dir}/{file}' FILEFORMAT = CSV
          FORMAT_OPTIONS ('header'='true','inferSchema'='true') COPY_OPTIONS ('mergeSchema'='true','force'='false')""")
        src=spark.table(bronze_o).dropDuplicates()
        target=f'{namespace}.{table}'
        if not spark.catalog.tableExists(target): src.limit(0).write.format('delta').saveAsTable(target)
        DeltaTable.forName(spark,target).alias('t').merge(src.alias('s'),key).whenMatchedUpdateAll().whenNotMatchedInsertAll().execute()
        print(table, spark.table(target).count(), 'rows')
    oc=spark.table(f'{namespace}.gold_official_context').collect()
    summary['official_context']={'synthetic':False,'reference_year':2025,'indicators':[r.asDict() for r in oc],
        'note':'Indicadores oficiais de contexto; nao somados a camada sintetica.'}
Path(output_path).mkdir(parents=True,exist_ok=True)
Path(output_path,'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
display(fact)
print(json.dumps(summary,ensure_ascii=False,indent=2))
