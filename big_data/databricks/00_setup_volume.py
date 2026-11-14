# Databricks notebook source
# Acolhe - preparo do Volume (Databricks Free Edition, serverless).
# O Free Edition nao se conecta ao Airflow: os arquivos sao enviados ao Volume a partir
# desta pasta Git (copia explicita, registrada abaixo). Rode uma vez antes de medallion.
# COMMAND ----------
import os, shutil, hashlib
dbutils.widgets.text('catalog', 'workspace')
dbutils.widgets.text('schema', 'acolhe')
catalog = dbutils.widgets.get('catalog'); schema = dbutils.widgets.get('schema')
spark.sql(f'CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}')
spark.sql(f'CREATE VOLUME IF NOT EXISTS {catalog}.{schema}.data')
volume = f'/Volumes/{catalog}/{schema}/data'
# COMMAND ----------
# Fonte: big_data/databricks/data nesta pasta Git (mesmos CSVs de big_data/input e os
# CSVs oficiais gerados por official_integration.py). Arquivos existentes e identicos
# nao sao reescritos: COPY INTO depende de arquivos imutaveis.
here = os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())
src = os.path.join('/Workspace' + here, 'data')
copied = []
for sub, dest in (('', f'{volume}/input'), ('official', f'{volume}/input/official')):
    os.makedirs(dest, exist_ok=True)
    for name in sorted(os.listdir(os.path.join(src, sub))):
        path = os.path.join(src, sub, name)
        if not name.endswith('.csv') or not os.path.isfile(path): continue
        target = os.path.join(dest, name); data = open(path, 'rb').read()
        if os.path.exists(target):
            if hashlib.sha256(open(target, 'rb').read()).digest() == hashlib.sha256(data).digest(): continue
            raise ValueError(f'{target} ja existe com conteudo diferente; publique correcao com novo nome/data')
        with open(target, 'wb') as f: f.write(data)
        copied.append(target)
print('copiados:', copied or 'nenhum (ja presentes)')
display(dbutils.fs.ls(f'{volume}/input')); display(dbutils.fs.ls(f'{volume}/input/official'))
