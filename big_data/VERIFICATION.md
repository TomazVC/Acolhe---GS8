# Verificacao local - 2026-11-07 UTC

Python 3.12.10, Windows. Executados:
- python -B -m big_data.pipeline --demo: JSON gerado com demand=190, services=40, source_batches=4, synthetic=true.
- python -B -m unittest big_data.test_pipeline rpa.test_robot -v: 8 testes aprovados.
- python -B -m unittest discover -v: 27 testes aprovados no estado disponivel do projeto.
- ast.parse em todos os .py de big_data/ e rpa/: sintaxe valida.
- xml.etree.ElementTree.parse em rpa/processo.bpmn: XML bem formado (nao equivale a validacao por engine BPMN).
- As cinco consultas SQL foram executadas sobre o ouro SQLite pelo teste test_five_gold_queries_execute.

O primeiro ciclo de testes identificou conexoes SQLite nao fechadas no Windows; foram corrigidas com contextlib.closing e a suite foi repetida com sucesso.

Nao executado: scheduler Airflow, ambiente Spark/Databricks, importacao BPMN em modelador, coleta de fontes reais ou execucoes em dois dias reais. Sintaxe Python validada nao prova compatibilidade runtime desses ambientes. Nenhuma conta foi criada nem dado enviado.


## Revisao apos reconexao - 2026-11-07 UTC
- Airflow usa airflow.sdk (versao 3); notebook bronze usa COPY INTO force=false; prata continua Delta MERGE.
- Testes novos: 2 contratos estaticos de implantacao + 3 testes do coletor oficial, aprovados. Os testes detectaram e corrigiram colisao de nomes de manifesto em capturas com timestamp igual (sufixo UUID preserva ambos).
- python -B -m unittest discover -v: 60 testes, 59 aprovados e 1 ignorado por dependencia opcional PyYAML ausente; nenhuma falha.
- ast.parse de todos os Python em big_data: valido.
- Coleta real em 2026-11-07: IBGE/SP 645 municipios, 284370 bytes; OBMigra PDF agregado 11428175 bytes. Ambos HTTP 200; hashes recalculados conferem com manifestos.
- Referencias oficiais mantidas fora do ouro demonstrativo. Nenhuma alegacao de dois dias reais, licenca IBGE verificada, ou segunda base tabular ja integrada.
- Nao executado Airflow ou Databricks. Contratos estaticos nao substituem testes de runtime. Segundo dia real, licencas especificas e harmonizacao tabular continuam pendentes em OFFICIAL_SOURCES.md.


## Verificacao Big Data + RPA + DevSecOps - 2026-11-14 UTC
Windows 11, Python 3.12.10, Node 22.23.5, sem Docker nem WSL.
- `python -B -m unittest discover`: 73 testes, todos aprovados (eram 61); inclui o gerador de evidencias. Checklist completo em `docs/CHECKLIST_BigData_RPA_DevSecOps.md`. Novos: integracao oficial (4), execucao do DAG Airflow (2), robo RPA (5: regra de decisao, sessao sem tentativas, fluxo completo, agendamento embutido), metricas HTTP (1).
- `node --test tests/frontend.test.cjs`: 11/11.
- Pipeline demonstrativo executado duas vezes: bronze=8, prata=4, lotes=4, quarentena=0 nas duas; as 5 consultas ouro retornam linhas.
- Coleta oficial do segundo dia real: 2026-11-14T02:02Z. IBGE HTTP 200, 645 municipios, 284.370 bytes; OBMigra HTTP 200, 11.428.175 bytes. Mesmos tamanhos da coleta de 2026-11-07.
- Integracao oficial executada duas vezes: 7 indicadores / 645 municipios / 2 lotes nas duas; consultas 6 a 8 executadas.
- Airflow 3.1.0 instalado: DAG analisado, topologia confirmada (2 ramos paralelos -> medallion -> integrate_official). `airflow db migrate` falha no Windows (`ModuleNotFoundError: fcntl`). Execucao no scheduler continua pendente e exige WSL2/Docker.
- Databricks: nao executado (exige conta e upload manual ao Volume). O notebook ganhou uma celula para os CSVs oficiais.
- Monitoramento ao vivo (Prometheus 3.2.1 nativo): 12.708 requisicoes em 70 s; latencia media 0,015 s, trafego 174 req/s, erros 0, saturacao 1 (antes da correcao do gauge). App parado: `AcolheUnavailable` passou a pending em 2026-11-14T02:16:42Z e depois a firing (severity=critical, value 0). `promtool test rules`: SUCCESS.
- Airflow real (WSL2 + Docker, imagem oficial apache/airflow:3.1.0-python3.12, `big_data/airflow/compose.airflow.yaml`): a primeira execucao real FALHOU em `ingest_demand`/`ingest_services` com `PermissionError [Errno 1]` em `acolhe_dag.py:23 -> shutil.copy2 -> copystat`. O worker roda como UID 50000 e o arquivo de staging pertencia a outro UID; copiar timestamps e permissoes exige ser dono. O teste com stub nao pegava isso. Corrigido com copia apenas do conteudo, atomica, que pula arquivos identicos (SHA-256), e com o teste de regressao `test_ingest_never_copies_metadata`. `big_data/staging/` entrou no .gitignore.
- Defeitos encontrados e corrigidos: `exec()` em teste detectado pelo Semgrep ampliado (excecao revisada); gauge de saturacao contava o proprio scrape; robo exportava `correct: null` em sessao sem tentativas; README DevSecOps com UTF-8 duplamente codificado (28 linhas); banco do container efemero; deploy apenas manual.
