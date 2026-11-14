# Checklist Big Data, RPA e DevSecOps (Ian e Aksel)

Itens copiados de "Organização de Tarefas" (p.5-6). Verificação local em 2026-11-14 UTC.
Legenda: ✅ feito e verificado · 🟡 feito localmente, falta evidência no ambiente exigido · ⛔ depende de conta/ambiente da equipe

## Big Data
| # | Item | Status | Evidência / o que falta |
|---|---|---|---|
| B1 | Segunda coleta em dia diferente; validar fontes, formatos e licenças | ✅ | Coleta 2026-11-14 (1ª em 2026-11-07). Formatos validados (JSON IBGE normalizado, assinatura `%PDF-`, SHA-256). Licenças revisadas em `OFFICIAL_SOURCES.md`. Falta: copiar os manifestos de 07/11 da máquina da 1ª coleta. |
| B2 | Executar Airflow e Databricks; ingestão, qualidade, reexecução sem duplicidade | ✅ Airflow / ✅ Databricks (dia 1) | Databricks Free (serverless), 2026-11-14: `00_setup_volume` e `medallion` 05/11, 06/11 e reexecução = SUCCESS. Bronze 4→8→8, prata 4→4→4; `DESCRIBE HISTORY` mostra 4 COPY INTO e nenhuma versão nova na reexecução. As 8 consultas batem com o SQLite (`big_data/evidence/databricks_20261114.md`). Falta: rodar `python3 big_data/databricks/run_evidence.py` em outro dia real. Airflow 3.1 real (WSL2 + Docker): os 2 DAGs com success, 2 execuções com contagens idênticas, ramos paralelos (`big_data/evidence/airflow_run_20261114.txt`). Corrigidos 2 defeitos que só apareceram no scheduler real. Falta: prints da UI em localhost:8081; Databricks (conta) em 2 dias + `DESCRIBE HISTORY`. |
| B3 | Upload manual ao Volume do Databricks Free | ✅ | `00_setup_volume` copia os CSVs da pasta Git para `/Volumes/workspace/acolhe/data/input` (sem integração com o Airflow). |
| B4 | Identificar sintéticos da Ouro; integrar dados reais; registrar consultas SQL | ✅ | `official_integration.py`: 7 indicadores OBMigra (com página) e 645 municípios IBGE; `official_context.synthetic=false`, camada demo segue `synthetic=true`. 8 consultas em `queries.sql`. |
| B5 | PDF com contagens antes/depois, consultas interpretadas, link GitHub | 🟡 | `EVIDENCIAS.md` gerado por `python -B -m big_data.evidence`: contagens vazio → lote 1 → lote 2 → reexecução, mais as 8 consultas com resultado e interpretação. Falta: montar o PDF com prints do Airflow/Databricks. |

## RPA
| # | Item | Status | Evidência / o que falta |
|---|---|---|---|
| R1 | Fluxo completo app → automação → MVP | ✅ | `rpa/demo_e2e.py` (servidor HTTP real + robô + `/api/automation`); o painel mostra totais e decisão. |
| R2 | Cenários de sucesso, decisão e falha com logs | ✅ | `rpa/evidence/<timestamp>/` (e2e.json, robot.log, progress.md); 8 testes do robô. |
| R3 | Decidir e documentar agendamento | ✅ | `--every N` embutido (testado) e `schtasks`/cron documentados. Decisão: agendamento do SO não ativado na máquina da equipe. |
| R4 | PDF com BPMN, PDD, evidências, links; vídeo ≤ 3 min | 🟡 | BPMN com gateway de decisão e BPMNDI (abre no bpmn.io); PDD no README; roteiro atualizado em `docs/roteiros_videos.md`. Falta: gravar o vídeo e montar o PDF. |

## DevSecOps
| # | Item | Status | Evidência / o que falta |
|---|---|---|---|
| D1 | Executar e validar Docker, Terraform, CI/CD e scanners | ✅ local / 🟡 GitHub | `bash devsecops/ci_local.sh`: pipeline idêntico à CI (Gitleaks, Semgrep 1.111, build, 73 testes na imagem, smoke, Trivy 0.60 imagem e IaC) = ALL GATES PASSED. Terraform fmt/validate ✅, promtool ✅. GitHub Actions na branch Aksel+Ian, todos os passos verdes: https://github.com/TomazVC/Acolhe---GS8/actions/runs/43548910363 |
| D2 | Pipeline barrado e corrigido; deploy automático | ✅ / 🟡 | Local: Semgrep barrou `exec()` real e Trivy barrou CRITICAL AZU-0012 no storage, ambos corrigidos; ensaio eval+token BLOQUEADO → APROVADO. Deploy automático em push na `main`. Falta: repetir no GitHub (PR vermelho → commit → verde). |
| D3 | URL pública e persistência adequada | ✅ | **https://acolhe-gs8.ambitiousbeach-2f5aaa39.canadacentral.azurecontainerapps.io**: terraform apply (8 recursos, canadacentral), dados sobreviveram a 2 restarts na nuvem (`devsecops/evidence/azure_deploy_20261114.md`). Local: | `bash devsecops/persistence_check.sh`: dados sobrevivem a `compose down/up` (1/1 → 1/1), rootfs read-only, UID 10001. Azure Files `/data` no Terraform. Falta: conta Azure + OIDC + `terraform apply` → URL pública. |
| D4 | Quatro métricas de ouro e alerta real | ✅ | Prometheus real: latência 0,015 s, tráfego 174 req/s, erros 0, saturação; `AcolheUnavailable` firing. Dashboard Grafana com 4 painéis. Falta: prints para o PDF (repetir os comandos). |
| D5 | PDF único: links, arquitetura, custos, responsabilidade compartilhada, LGPD | 🟡 | Seções prontas em `devsecops/README.md` (custos com preços da API Azure). Falta: montar o PDF com URL pública e links. |

## Comandos de verificação (todos com exit 0 em 2026-11-14)
```
python -B -m unittest discover                 # 74 testes
bash devsecops/ci_local.sh                     # WSL2/Docker: pipeline da CI
bash devsecops/persistence_check.sh            # WSL2/Docker: persistência + Prometheus
docker compose -f big_data/airflow/compose.airflow.yaml up -d && bash big_data/airflow/run_evidence.sh 2
node --test tests/frontend.test.cjs            # 11 testes
python -B -m rpa.demo_e2e --evidence rpa/evidence
python -B -m big_data.evidence
semgrep scan --config devsecops/semgrep.yml --error --metrics=off app robot rpa big_data
gitleaks dir . --redact --exit-code=1
trivy config --exit-code 1 --severity HIGH,CRITICAL .
terraform -chdir=devsecops/terraform fmt -check && terraform -chdir=devsecops/terraform validate
promtool test rules devsecops/monitoring/alerts.test.yml
```
