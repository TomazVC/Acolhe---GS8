# Big Data: Acolhe

## Estado e honestidade dos dados
Executado localmente em Python 3.12 + SQLite. Os indicadores de demanda/servicos do MVP sao inteiramente SINTETICOS: nao representam refugiados reais, demanda real nem capacidade de atendimento. Duas fontes logicas de demonstracao (`demand` e `services`), nao duas bases publicas ja integradas. Referencias oficiais adicionais foram adquiridas separadamente em official_snapshots; veja OFFICIAL_SOURCES.md. Nao houve execucao Airflow ou Databricks, nem criacao de conta/cluster. Isso permanece pendente para evidencia academica.

## Rodar e testar
Na raiz acolhe:
```
python -B -m big_data.pipeline --demo
python -B -m unittest big_data.test_pipeline -v
```
O primeiro comando gera 4 CSVs: 2 fontes x datas 2026-11-05 e 2026-11-06. Sao datas dos dados, NAO comprovacao de execucoes em dois dias. A segunda data atualiza as mesmas chaves. Repetir nao duplica bronze nem prata. Resultado esperado: bronze=8, prata=4; demanda=190, servicos=40. `output/warehouse.db` e CSVs exportados permitem auditoria; `output/summary.json` e o contrato consumido pelo MVP.

## Arquitetura
CSV -> bronze imutavel por hash do arquivo + numero da linha -> prata UPSERT por (source,record_id) priorizando snapshot mais recente -> ouro fato + dimensoes territorio e idioma -> JSON da aplicacao.
Bronze preserva payload bruto. Arquivos novos sao incrementais; arquivos identicos sao ignorados. Correcoes no mesmo dia substituem prata na ordem lexicografica dos arquivos; produtores devem evitar conflitos de chave/data ou publicar snapshot de data mais recente. A quarentena registra rejeicoes por lote/linha. Nao ha exclusao logica automatica: ausencia em lote nao remove registros anteriores.

Regras de qualidade: (1) chave e territorio obrigatorios; (2) idioma pt/es/en; (3) contagem inteira nao negativa, data ISO e marcacao de origem explicita. Registros invalidos permanecem bronze e entram quarentena. Os testes cobrem lote repetido, atualizacao, ouro e rejeicao. As cinco consultas em queries.sql usam as tabelas ouro. Grao do fato: indicador mais recente por fonte/chave; nao e uma serie historica. Bronze preserva o historico.

## Contrato de integracao
Schema v1: generated_at UTC, synthetic boolean (verdadeiro se qualquer registro for sintetico), source_batches inteiro, totals {demand,services}, by_region [{region,demand,services}], by_language [{language,demand,services}], quality.rejected, provenance. A tela deve manter selo de dados demonstrativos quando synthetic=true. Os indicadores nao decidem elegibilidade individual e nao devem ser apresentados como estatisticas oficiais.

## Adaptador de fontes reais
A interface de ingestao real e CSV normalizado, sem requisicoes de rede ou credenciais. Exporte dados permitidos, documente licenca, data e transformacoes, e grave `demand_YYYY-MM-DD.csv` e `services_YYYY-MM-DD.csv` em uma pasta nova. Cabecalho obrigatorio:
```
record_id,region,language,count,snapshot_date,synthetic
```
Use synthetic=false SOMENTE quando a linha vier de fonte real verificada. Rode `python -m big_data.pipeline --input caminho --output big_data/output_real`. Nao misture a base demonstrativa com a real. Os arquivos reais devem conter apenas agregados, nunca nomes, documentos ou identificadores de pessoas. O adaptador normalizado nao faz correspondencia automatica entre conceitos/idiomas de bases oficiais.

Possiveis fontes para pesquisa futura: portal de dados UNHCR (https://www.unhcr.org/refugee-statistics/) e CadSUAS/MDS (https://aplicacoes.mds.gov.br/cadsuas/). Disponibilidade, granularidade, permissao e mapeamento ainda precisam de validacao; nao sao afirmadas como fontes dos CSVs entregues.

## Airflow
`airflow/acolhe_dag.py`: alvo Airflow 3 (`from airflow.sdk import dag, task`), nao instalado/executado nesta entrega. Instale em Linux/WSL/container seguindo as instrucoes oficiais. Monte o repositorio em todos os workers, configure ACOLHE_ROOT e opcional ACOLHE_IMPORT_DIR; coloque o DAG no dags_folder. Duas tarefas irmas ingest_demand e ingest_services copiam/validam arquivos em paralelo; medallion depende das duas. Requer executor com pelo menos 2 slots; max_active_runs=1 evita corrida SQLite. Agenda diaria 03:00 UTC, retries=2. O DAG executa o pipeline LOCAL, nao envia jobs Databricks. A integracao com Databricks Jobs e uma etapa pendente, e nao deve ser inferida pelo desenho.

## Databricks
Importe databricks/medallion.py como notebook; configure catalog.schema e paths de um Unity Catalog Volume existente ao qual tenha acesso. Carregue os 4 CSVs no volume (upload requer sua autorizacao). Execute batch_date=2026-11-05 e depois 2026-11-06; repita a segunda execucao e confira contagens. Para a exigencia de dias de execucao diferentes, agende e execute em dois dias reais e capture logs/timestamps, nao apenas dois valores de widget. O notebook implementa bronze incremental com COPY INTO (force=false), prata MERGE com deduplicacao, quarentena e ouro Delta. Copie o summary.json do volume para output somente depois de conferir origem e schema. Nao ha credenciais em codigo.

## Evidencias pendentes
- Selecionar/adquirir duas fontes reais compativeis se exigidas pelo professor.
- Executar DAG, registrar grafico com branches paralelos e logs.
- Executar notebook em Databricks em dois dias distintos e guardar historico Delta (`DESCRIBE HISTORY`) e contagens antes/depois/reexecucao.
- Executar e capturar as cinco consultas ouro no workspace.
- Validar custeio e permissao do ambiente antes de provisionar infraestrutura.

Referencias tecnicas consultadas em 2026-11-07: https://docs.databricks.com/aws/en/delta/merge ; https://docs.databricks.com/aws/en/delta/tutorial ; https://airflow.apache.org/docs/task-sdk/stable/ ; https://docs.databricks.com/aws/en/ingestion/cloud-object-storage/copy-into/examples .

## Atualizacao dos requisitos (PDF p.34-35)
Airflow foi ajustado para API publica 3.x. Databricks usa COPY INTO na bronze; o MERGE continua somente na prata. COPY INTO lembra arquivos ja ingeridos: nao altere um arquivo apos ingestao, publique correcao sob novo caminho/data. Nao use force=true para demonstrar idempotencia. O notebook requer schema vazio/compatível; se executou uma versao anterior com esquema diferente, use outro schema e preserve a evidencia antiga. As verificacoes locais de configuracao sao estaticas, nao equivalem a execucao Airflow/Spark.

Um segundo DAG, airflow/official_sources_dag.py, prepara aquisicoes IBGE e OBMigra em tarefas paralelas e so resume proveniencia. Nao fabrica uma uniao semantica dessas referencias com demanda/oferta e nao foi ativado. A agenda descrita no arquivo nao esta instalada em nenhum scheduler.
