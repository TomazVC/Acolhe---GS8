# Checklist Big Data, RPA e DevSecOps (Ian e Aksel)

Itens copiados de "OrganizaÃ§Ã£o de Tarefas" (p.5-6). VerificaÃ§Ã£o local em 2026-11-14 UTC.
Legenda: âœ… feito e verificado Â· ðŸŸ¡ feito localmente, falta evidÃªncia no ambiente exigido Â· â›” depende de conta/ambiente da equipe

## Big Data
| # | Item | Status | EvidÃªncia / o que falta |
|---|---|---|---|
| B1 | Segunda coleta em dia diferente; validar fontes, formatos e licenÃ§as | âœ… | Coleta 2026-11-14 (1Âª em 2026-11-07). Formatos validados (JSON IBGE normalizado, assinatura `%PDF-`, SHA-256). LicenÃ§as revisadas em `OFFICIAL_SOURCES.md`. Falta: copiar os manifestos de 07/11 da mÃ¡quina da 1Âª coleta. |
| B2 | Executar Airflow e Databricks; ingestÃ£o, qualidade, reexecuÃ§Ã£o sem duplicidade | âœ… Airflow / âœ… Databricks (dia 1) | Databricks Free (serverless), 2026-11-14: `00_setup_volume` e `medallion` 05/11, 06/11 e reexecuÃ§Ã£o = SUCCESS. Bronze 4â†’8â†’8, prata 4â†’4â†’4; `DESCRIBE HISTORY` mostra 4 COPY INTO e nenhuma versÃ£o nova na reexecuÃ§Ã£o. As 8 consultas batem com o SQLite (`big_data/evidence/databricks_20261114.md`). Falta: rodar `python3 big_data/databricks/run_evidence.py` em outro dia real. Airflow 3.1 real (WSL2 + Docker): os 2 DAGs com success, 2 execuÃ§Ãµes com contagens idÃªnticas, ramos paralelos (`big_data/evidence/airflow_run_20261114.txt`). Corrigidos 2 defeitos que sÃ³ apareceram no scheduler real. Falta: prints da UI em localhost:8081; Databricks (conta) em 2 dias + `DESCRIBE HISTORY`. |
| B3 | Upload manual ao Volume do Databricks Free | âœ… | `00_setup_volume` copia os CSVs da pasta Git para `/Volumes/workspace/acolhe/data/input` (sem integraÃ§Ã£o com o Airflow). |
| B4 | Identificar sintÃ©ticos da Ouro; integrar dados reais; registrar consultas SQL | âœ… | `official_integration.py`: 7 indicadores OBMigra (com pÃ¡gina) e 645 municÃ­pios IBGE; `official_context.synthetic=false`, camada demo segue `synthetic=true`. 8 consultas em `queries.sql`. |
| B5 | PDF com contagens antes/depois, consultas interpretadas, link GitHub | ðŸŸ¡ | `EVIDENCIAS.md` gerado por `python -B -m big_data.evidence`: contagens vazio â†’ lote 1 â†’ lote 2 â†’ reexecuÃ§Ã£o, mais as 8 consultas com resultado e interpretaÃ§Ã£o. Falta: montar o PDF com prints do Airflow/Databricks. |

## RPA
| # | Item | Status | EvidÃªncia / o que falta |
|---|---|---|---|
| R1 | Fluxo completo app â†’ automaÃ§Ã£o â†’ MVP | âœ… | `rpa/demo_e2e.py` (servidor HTTP real + robÃ´ + `/api/automation`); o painel mostra totais e decisÃ£o. |
| R2 | CenÃ¡rios de sucesso, decisÃ£o e falha com logs | âœ… | `rpa/evidence/<timestamp>/` (e2e.json, robot.log, progress.md); 8 testes do robÃ´. |
| R3 | Decidir e documentar agendamento | âœ… | `--every N` embutido (testado) e `schtasks`/cron documentados. DecisÃ£o: agendamento do SO nÃ£o ativado na mÃ¡quina da equipe. |
| R4 | PDF com BPMN, PDD, evidÃªncias, links; vÃ­deo â‰¤ 3 min | ðŸŸ¡ | BPMN com gateway de decisÃ£o e BPMNDI (abre no bpmn.io); PDD no README; roteiro atualizado em `docs/roteiros_videos.md`. Falta: gravar o vÃ­deo e montar o PDF. |

## DevSecOps
| # | Item | Status | EvidÃªncia / o que falta |
|---|---|---|---|
| D1 | Executar e validar Docker, Terraform, CI/CD e scanners | âœ… local / ðŸŸ¡ GitHub | `bash devsecops/ci_local.sh`: pipeline idÃªntico Ã  CI (Gitleaks, Semgrep 1.111, build, 73 testes na imagem, smoke, Trivy 0.60 imagem e IaC) = ALL GATES PASSED. Terraform fmt/validate âœ…, promtool âœ…. GitHub Actions na branch Aksel+Ian, todos os passos verdes: https://github.com/TomazVC/Acolhe---GS8/actions/runs/43548910363 |
| D2 | Pipeline barrado e corrigido; deploy automÃ¡tico | âœ… / ðŸŸ¡ | Local: Semgrep barrou `exec()` real e Trivy barrou CRITICAL AZU-0012 no storage, ambos corrigidos; ensaio eval+token BLOQUEADO â†’ APROVADO. Deploy automÃ¡tico em push na `main`. Falta: repetir no GitHub (PR vermelho â†’ commit â†’ verde). |
| D3 | URL pÃºblica e persistÃªncia adequada | âœ… persistÃªncia / â›” URL | `bash devsecops/persistence_check.sh`: dados sobrevivem a `compose down/up` (1/1 â†’ 1/1), rootfs read-only, UID 10001. Azure Files `/data` no Terraform. Falta: conta Azure + OIDC + `terraform apply` â†’ URL pÃºblica. |
| D4 | Quatro mÃ©tricas de ouro e alerta real | âœ… | Prometheus real: latÃªncia 0,015 s, trÃ¡fego 174 req/s, erros 0, saturaÃ§Ã£o; `AcolheUnavailable` firing. Dashboard Grafana com 4 painÃ©is. Falta: prints para o PDF (repetir os comandos). |
| D5 | PDF Ãºnico: links, arquitetura, custos, responsabilidade compartilhada, LGPD | ðŸŸ¡ | SeÃ§Ãµes prontas em `devsecops/README.md` (custos com preÃ§os da API Azure). Falta: montar o PDF com URL pÃºblica e links. |

## Comandos de verificaÃ§Ã£o (todos com exit 0 em 2026-11-14)
```
python -B -m unittest discover                 # 74 testes
bash devsecops/ci_local.sh                     # WSL2/Docker: pipeline da CI
bash devsecops/persistence_check.sh            # WSL2/Docker: persistÃªncia + Prometheus
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
