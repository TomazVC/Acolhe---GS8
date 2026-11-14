# DevSecOps Acolhe

## Execução local
Na raiz, `python -m app.server` inicia a aplicação (porta 8080). `docker compose up --build` é o caminho container. `docker compose --profile monitoring up --build` acrescenta Prometheus em http://localhost:9090. A aplicação fica restrita ao loopback do host na porta 8080. Container não root, filesystem somente leitura no Compose, capabilities removidas e no-new-privileges. Não foi possível executar Docker aqui: daemon indisponível; estes arquivos ainda exigem build e smoke test.

## Execucao local verificada (2026-11-14 UTC, Windows 11, sem Docker)
Ferramentas portateis, mesmas versoes da CI quando ha binario Windows: Terraform 1.17.2, Gitleaks 8.24.2, Prometheus/promtool 3.2.1, Node 22.23.5, Trivy 0.76.1 (o binario Windows da 0.60.0 nao existe mais; hash conferido com o checksums oficial), Semgrep 1.185.0 (1.111.0 nao suporta Windows).

| Verificacao | Resultado |
|---|---|
| `python -B -m unittest discover` | todos aprovados (ver VERIFICATION) |
| `node --check` + `node --test tests/frontend.test.cjs` | 11/11 |
| `terraform fmt -check`, `init -backend=false`, `validate` | ok / valido |
| `trivy config .` HIGH/CRITICAL (Dockerfile, Dockerfile.candidate, Terraform) | 0 achados |
| `gitleaks dir .` | nenhum vazamento |
| `semgrep --config devsecops/semgrep.yml app robot rpa big_data` | 0 achados apos excecao revisada (abaixo) |
| `promtool check config/rules` + `promtool test rules alerts.test.yml` | SUCCESS (3 cenarios) |

**Execucao barrada e corrigida (local).** Ao ampliar o escopo do Semgrep para `rpa` e `big_data`, a regra `no-dynamic-evaluation` barrou um `exec()` real em `big_data/test_copy_statement.py`. Era o teste executando o AST do proprio notebook contra um stub, sem entrada externa; recebeu excecao revisada `nosemgrep` com justificativa, sem retirar a pasta do scan. Ensaio adicional: arquivo com `eval()` e token no formato GitHub -> semgrep exit 1 e gitleaks exit 1 (BLOQUEADO); arquivo removido -> ambos exit 0 (APROVADO). Para a evidencia oficial, repita no GitHub: branch com o arquivo de ensaio, PR com o run vermelho, commit removendo, run verde. Guarde os dois links.

**Quatro sinais de ouro ao vivo.** App + Prometheus 3.2.1 nativos, 70 s de carga (6 clientes, 12.708 requisicoes reais incluindo tentativas do quiz). Consultas PromQL: latencia media 0,015 s; trafego 174 req/s; erros 0; saturacao 1 requisicao ativa. Essa leitura revelou um defeito: o proprio scrape de `/metrics` contava como requisicao ativa, logo a saturacao nunca chegava a 0. Corrigido em `app/server.py` com teste `test_metrics_four_golden_signals_idle_saturation_is_zero`.

**Alerta disparado.** Com o app parado, `AcolheUnavailable` passou de inactive -> pending -> firing no Prometheus real (ver VERIFICATION para horarios). Sem Alertmanager: o alerta aparece em `/alerts` do Prometheus; nenhuma mensagem e enviada.

**Persistencia corrigida.** O banco ficava em `/tmp` (tmpfs) e se perdia a cada recriacao. Agora `ACOLHE_DB=/data/acolhe.db`, diretorio `/data` do UID 10001 e volume nomeado `acolhe-data` no Compose; o filesystem continua read-only. `docker compose down -v` apaga os dados (direito de eliminacao LGPD). No Azure, o Terraform monta um compartilhamento Azure Files em `/data`, com `nobrl` para o lock do SQLite funcionar sobre SMB, dono UID 10001 e `max_replicas = 1`, garantindo um unico escritor. A conta de armazenamento so aceita a sub-rede do Container Apps (firewall Deny, service endpoint), TLS 1.2 e criptografia de infraestrutura. Para escalar alem de 1 replica, migrar para banco gerenciado (por exemplo, PostgreSQL Flexible Server).

**Gate barrou a propria correcao.** A primeira versao do armazenamento persistente foi barrada pelo Trivy: CRITICAL AZU-0012, conta de armazenamento sem regras de rede. Corrigido com VNet dedicada e firewall Deny; o MEDIUM AZU-0061 foi corrigido com criptografia de infraestrutura. Riscos aceitos e documentados: AZU-0057 (logging de Queue; o projeto nao usa filas) e AZU-0058 (LRS em vez de GRS, para dados de demonstracao com retencao de 7 dias). Ambos estao abaixo do limiar HIGH/CRITICAL do gate.

**Deploy automatico.** O job `deploy` agora roda em todo push na `main` que passar em todos os gates, desde que `vars.DEPLOY_ENABLED == 'true'`; o disparo manual continua disponivel. Inclui health check pos-deploy contra a URL publica. Na `main` a concorrencia nao cancela um run em andamento, para nao interromper um deploy.

## URL pública (Azure, 2026-11-14)
**https://acolhe-gs8.ambitiousbeach-2f5aaa39.canadacentral.azurecontainerapps.io**

Criada pelo `terraform apply` deste diretório na assinatura Azure for Students, região `canadacentral`, porque a política da assinatura não permite `brazilsouth`. A persistência foi comprovada: os dados gravados pela API pública sobreviveram a dois reinícios do container, o segundo em réplica nova. Detalhes, os 3 defeitos encontrados no deploy real (pacote privado, provedor não registrado, subnet sem delegação) e as correções estão em `evidence/azure_deploy_20261114.md`.

Custos na região usada (Retail Prices API, canadacentral): vCPU US$ 0,000034/s, memória US$ 0,000004/GiB-s, US$ 0,40/milhão de requisições, Azure Files Hot LRS US$ 0,03/GB-mês. Uso de demonstração (40 h ativas/mês): ~US$ 1,60/mês. Sempre ligado: ~US$ 28/mês. Tudo coberto pelo crédito estudantil de US$ 100. As estimativas abaixo, para brazilsouth, ficam como referência.

O deploy automático da CI (`az containerapp update` em push na `main`) usa este mesmo Container App, mas ainda exige que um administrador do repositório configure o OIDC: secrets `AZURE_CLIENT_ID`/`AZURE_TENANT_ID`/`AZURE_SUBSCRIPTION_ID`, vars `AZURE_RESOURCE_GROUP=rg-acolhe-gs8`, `AZURE_CONTAINER_APP=acolhe-gs8` e `DEPLOY_ENABLED=true`. Também é preciso tornar público o pacote GHCR do repositório.

## Docker real no WSL2 (2026-11-14, Ubuntu 26.04, Docker 29.1.3, Compose 2.40)
`bash devsecops/ci_local.sh` reproduz o job `test-and-build` da CI com as mesmas imagens e versoes (Gitleaks 8.24.2, Semgrep 1.111.0, Trivy 0.60.0). Resultado: ALL GATES PASSED, exit 0.
- Build da imagem; 73 testes dentro da imagem (1 ignorado, PyYAML opcional); smoke HTTP `/`, `/logo.png`, `/api/lessons`, `/api/summary`, `/api/gold`, `/metrics` = 200; UID 10001 grava SQLite em `/data`.
- Trivy 0.60.0 imagem: 0 HIGH/CRITICAL. Trivy 0.60.0 IaC: 0 HIGH/CRITICAL.
- Barrado e corrigido de novo: ao ampliar o escopo IaC para o repositorio inteiro, o Trivy 0.60.0 barrou HIGH DS-0017 em `devsecops/Dockerfile.candidate` (a 0.76.1 nao barrava). Esse arquivo e do experimento de imagem-base, nao e publicado, e o achado e falso positivo (`apt-get update` seguido de `upgrade` e limpeza do cache no mesmo RUN). O arquivo foi excluido com justificativa no workflow; Dockerfile de producao, Compose e Terraform continuam escaneados.

`bash devsecops/persistence_check.sh` (Compose com perfil monitoring): 0 sessoes -> 1 sessao/1 tentativa -> `docker compose down` + `up` com container novo -> continua 1/1. Rootfs somente leitura = true, usuario 10001, volume `acolhe-data`. O Prometheus no Docker coleta `app:8080`: `up{job="acolhe"} = 1`.

## Custos (precos de lista Azure Retail Prices API, brazilsouth, consultados em 2026-11-14)
vCPU ativa US$ 0,000024/s; memoria US$ 0,000003/GiB-s; requisicoes US$ 0,40/milhao. Container 0,25 vCPU e 0,5 GiB, escala 0..1.
- Demonstracao (40 h ativas/mes, 100 mil requisicoes): 36.000 vCPU-s = US$ 0,86; 72.000 GiB-s = US$ 0,22; requisicoes US$ 0,04. Total ~US$ 1,12/mes antes da franquia mensal gratuita do Container Apps, que nesta escala tende a zerar o valor (confirmar a franquia vigente na pagina de precos; a API nao a exibe).
- Pior caso, sempre ligado (730 h): 657.000 vCPU-s = US$ 15,77; 1.314.000 GiB-s = US$ 3,94; ~US$ 19,7/mes mais requisicoes.
- Azure Files (LRS, cota de 1 GiB) para o SQLite: centavos por mes; consultar o preco vigente da regiao antes do `apply`. VNet e service endpoint: sem custo.
- GHCR publico: sem custo. O Terraform nao cria Log Analytics, logo sem custo de ingestao de logs. Configure um orcamento com alerta na assinatura antes do `apply`.

## Arquitetura
```
Dev -> PR -> GitHub Actions [testes Python/Node -> Gitleaks -> Semgrep -> build -> testes na imagem -> smoke HTTP/SQLite -> Trivy imagem -> Trivy IaC]
          \-> push main (gates verdes) -> GHCR (imagem testada) -> az containerapp update -> health check
Usuario -> HTTPS (ingress Azure) -> Container App acolhe (UID 10001, 0..1 replica) -> /data (Azure Files, firewall Deny)
Prometheus -> /metrics (latencia, trafego, erros, saturacao) -> regras de alerta (alerts.yml) -> Grafana (dashboard)
```
Componentes: app Python 3.12 da biblioteca padrao em imagem Alpine fixada por digest; SQLite com retencao de 7 dias; Terraform cria resource group, VNet/sub-rede, conta de armazenamento + share, ambiente e Container App.

## Responsabilidade compartilhada
| Camada | Provedor (Azure/GitHub) | Equipe Acolhe |
|---|---|---|
| Datacenter, hardware, rede fisica, hipervisor | Azure | - |
| Plataforma Container Apps, patches do host, ingress TLS | Azure | escolher regiao, escala e ingress HTTPS-only |
| Runners do GitHub Actions, GHCR | GitHub | fixar versoes das actions/ferramentas, nao expor segredos |
| Imagem do container (base, pacotes) | - | digest fixado, `apk upgrade`, Trivy bloqueando HIGH/CRITICAL, usuario nao root |
| Codigo da aplicacao | - | testes, Semgrep, validacao de entrada, CSP, protecao de origem |
| Identidade e acesso | Entra ID (OIDC) | identidade de deploy com menor privilegio, protecao de branch |
| Dados (SQLite, backups, retencao) | durabilidade do Azure Files (LRS) | classificacao, retencao de 7 dias, exclusao por sessao, firewall do storage |
| Monitoramento | coleta da plataforma | metricas de ouro, regras de alerta, resposta a incidente |

## LGPD
- Dados tratados: id de sessao aleatorio (pseudonimo), idioma, licao, acerto e horario. Nenhum nome, documento, foto, audio ou localizacao. A tela orienta usar adultos e dados de teste no piloto.
- Base legal e finalidade: uso academico demonstrativo. Em uso real com criancas, aplica-se o art. 14 (melhor interesse da crianca e consentimento especifico de um dos pais ou responsavel), alem de revisao do encarregado (DPO).
- Minimizacao e retencao: so o necessario ao exercicio, sessoes apagadas apos 7 dias (`app/core.py`) e botao "Apagar minha sessao de teste" (eliminacao a pedido). O RPA e o Big Data so exportam agregados, sem identificadores (testados).
- Seguranca (art. 46): TLS no ingress, container nao root e somente leitura, storage com firewall e criptografia, segredos fora do repositorio (Gitleaks), CSP e bloqueio de origem cruzada.
- Transferencia internacional (art. 33): a assinatura de estudante so permite regioes fora do Brasil, e o deploy esta em `canadacentral` (Canada). Ha transferencia internacional dos dados pseudonimos de sessao. Mitigacoes: dados minimos sem identificacao direta, retencao de 7 dias, criptografia em repouso e em transito, firewall do storage. Para uso real com criancas, usar `brazilsouth` numa assinatura que permita essa regiao, ou formalizar a base do art. 33 (por exemplo, clausulas-padrao contratuais). O GHCR guarda apenas a imagem, sem dados pessoais.
- Pendente antes de uso real: autenticacao de educadores, protecao do `/metrics`, RIPD (relatorio de impacto), termo de consentimento e politica de privacidade revisados por juridico.

## Pipeline
`.github/workflows/devsecops.yml` executa testes da aplicação e robô, Gitleaks no histórico, Semgrep com regras locais, build, Trivy imagem e IaC. HIGH/CRITICAL bloqueiam; não há `continue-on-error`. Imagem testada é um artefato e o deploy utiliza esse mesmo tar. As tags de ferramentas estão fixadas em versões; endurecimento futuro: validar versões atuais e substituir tags por digests/SHA aprovados. Não alegar ausência de vulnerabilidades antes de rodar os scanners. Regras Semgrep locais são uma base pequena, não uma auditoria completa.

Deploy automatico em push na main (nunca em PR), condicionado a DEPLOY_ENABLED=true e ao environment production; tambem pode ser disparado manualmente com deploy=true. O controle humano fica antes do merge: proteja a `main` com PR obrigatório, 1 revisão e o check "test-and-build" obrigatório. No environment `production`, restrinja o deploy à branch `main` sem required reviewers, senão cada deploy espera aprovação manual e deixa de ser automático. Configure isso no GitHub ANTES de habilitar a variável; o YAML sozinho não cria essas regras. O deploy publica a imagem no GHCR e atualiza um Azure Container App já criado. O GHCR deve estar público ou o Container App precisa de acesso explicitamente configurado ao registro privado; o exemplo Terraform pressupõe imagem pública. Configurar OIDC Azure com identidade de privilégio mínimo, secrets AZURE_CLIENT_ID/AZURE_TENANT_ID/AZURE_SUBSCRIPTION_ID e vars AZURE_RESOURCE_GROUP/AZURE_CONTAINER_APP. Nenhuma conta, secret, permissão, ambiente GitHub ou recurso foi criado. Publicação/infra requerem autorização separada.

## IaC Azure (exemplo real, NÃO aplicado)
`terraform/main.tf` declara resource group, Container Apps environment e Container App com HTTPS, escala 0..1 e robô simulado. Requer assinatura Azure, quota/região e imagem publicada. Pode gerar cobranças mesmo em laboratório: custo não estimado nesta entrega. Não execute apply sem orçamento e aprovação.

Sequência manual de validação: `terraform fmt -check`, `terraform init -backend=false`, `terraform validate`; depois plano revisado em ambiente autorizado. Copiar terraform.tfvars.example localmente e substituir valores, nunca versionar tfvars/state/plano com dados reais. Antes de uso compartilhado, configurar backend remoto seguro com locking, restringir RBAC e emitir lockfile de provedores após init. CLI Terraform ausente aqui: fmt/validate/plan/apply não executados. O exemplo não é uma implantação comprovada.

## Observabilidade: quatro métricas
- acolhe_requests_total: volume de requisições; `rate(acolhe_requests_total[5m])`.
- acolhe_attempts_total: tentativas educacionais; `increase(acolhe_attempts_total[1h])`.
- acolhe_errors_total: falhas da aplicação; taxa relativa às requisições.
- acolhe_uptime_seconds: tempo de vida do processo, útil para detectar reinícios.

Prometheus coleta `/metrics` a cada 15s. Alertas: indisponibilidade por 2min e taxa de erros >5% por 5min. Verificar com `promtool check config` e `promtool check rules` ao ter container disponível. Alertas aparecem no Prometheus; entrega externa exige Alertmanager/destinatário autorizado, NÃO configurados. Não há envio de mensagens.

## Pendências e roteiro de evidência
1. Executar testes e build Docker; capturar healthcheck e usuário UID10001.
2. Publicar repositório somente após autorização; executar CI e guardar URL do run e relatórios de cada scanner.
3. Instalar/validar Terraform em ambiente autorizado; revisar plano e custos antes de aplicar.
4. Configurar environment production com aprovadores e OIDC com menor privilégio; fazer deploy apenas quando autorizado.
5. Capturar dashboard das quatro métricas e alerta disparado em ensaio controlado. Não simular evidência como se fosse produção.
6. Escopo acadêmico: dados de demonstração apenas. Rever autenticação, TLS/proxy, persistência, LGPD e limites antes de expor a aplicação a usuários reais.

### Quatro sinais de ouro
O dashboard `monitoring/grafana-dashboard.json` pode ser importado em um Grafana existente, selecionando o datasource Prometheus. Não foi provisionado nem testado no Grafana.
- Latência: rate(acolhe_request_duration_seconds_sum[5m]) / rate(acolhe_request_duration_seconds_count[5m]), média, não p95.
- Tráfego: rate(acolhe_requests_total[5m]), requisições por segundo.
- Erros: rate(acolhe_errors_total[5m]) / clamp_min(rate(acolhe_requests_total[5m]), 0.001), proporção.
- Saturação: acolhe_active_requests, concorrência como proxy de saturação; não mede CPU/memória nem percentual de capacidade. Threshold inicial 20 requer calibração por teste de carga.
Há regras adicionais de latência média >1s e concorrência >20, ambas limiares provisórios. Métricas de tentativas/uptime complementam esses sinais, mas não os substituem.

O Docker usa ACOLHE_DB=/data/acolhe.db em volume gravavel do UID 10001 (Compose: volume `acolhe-data`), com o restante do filesystem read-only. Retencao de 7 dias aplicada pela aplicacao. As integrações genai/vision/rpa também são copiadas à imagem.


## Primeira CI pública e correção de imagem (2026-11-09)

O run https://github.com/TomazVC/Acolhe---GS8/actions/runs/42685134583, commit `624c6e77c003c88bba8edfc6a1b86f3f5403beed`, aprovou testes Python/Node, Gitleaks, Semgrep e build Docker. O Trivy bloqueou a imagem Debian 13.7: 49 ocorrências HIGH e nenhuma CRITICAL. São ocorrências por pacote, não necessariamente CVEs distintas.

Duas ocorrências em `zlib1g` tinham atualização indicada, para `1:1.3.dfsg+really1.3.1-1+deb13u1`. Outras estavam sem versão corrigida indicada ou com correção adiada pelo fornecedor. A imagem passa a aplicar as atualizações disponíveis da distribuição durante o build; a CI busca a imagem-base atual com `--pull`. Isso não garante ausência de vulnerabilidades sem correção. O bloqueio HIGH/CRITICAL continua ativo, sem `ignore-unfixed`, exceções de CVE ou supressão de erros. Consulte o run do commit atual antes de considerar a imagem aprovada. Nenhum deploy foi executado.


### Alternativas oficiais avaliadas

O run https://github.com/TomazVC/Acolhe---GS8/actions/runs/42686110502 comparou imagens oficiais com atualização de pacotes, os 61 testes Python dentro de cada container (60 aprovados e 1 ignorado por PyYAML opcional), smoke HTTP e escrita/leitura SQLite com UID 10001, e Trivy com bloqueio HIGH/CRITICAL.

- `python:3.12-slim-bookworm`: testes aprovados, scan com 40 HIGH e 2 CRITICAL. Não adotada.
- `python:3.12-alpine`: testes e smoke aprovados; scan sem achados HIGH/CRITICAL na base Alpine 3.24.4. Adotada com o digest oficial verificado `sha256:e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7`, mantendo atualização de pacotes Alpine e todas as barreiras de segurança.

A CI principal agora também executa testes dentro da imagem e smoke HTTP/SQLite real antes do scan. A validação cobre o MVP de biblioteca padrão; não valida treinamento YOLO, dependências nativas opcionais, Airflow ou Databricks na imagem Alpine. Novas dependências precisam de nova verificação, pois Alpine usa musl em vez de glibc. O digest deve ser atualizado e revalidado periodicamente; um scan sem achados hoje não garante segurança futura. A branch `ci/evaluate-python-bases` preserva o experimento e não realiza deploy.
