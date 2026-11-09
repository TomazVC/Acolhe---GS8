# DevSecOps Acolhe

## ExecuÃ§Ã£o local
Na raiz, `python -m app.server` inicia a aplicaÃ§Ã£o (porta 8080). `docker compose up --build` Ã© o caminho container. `docker compose --profile monitoring up --build` acrescenta Prometheus em http://localhost:9090. A aplicaÃ§Ã£o fica restrita ao loopback do host na porta 8080. Container nÃ£o root, filesystem somente leitura no Compose, capabilities removidas e no-new-privileges. NÃ£o foi possÃ­vel executar Docker aqui: daemon indisponÃ­vel; estes arquivos ainda exigem build e smoke test.

## Pipeline
`.github/workflows/devsecops.yml` executa testes da aplicaÃ§Ã£o e robÃ´, Gitleaks no histÃ³rico, Semgrep com regras locais, build, Trivy imagem e IaC. HIGH/CRITICAL bloqueiam; nÃ£o hÃ¡ `continue-on-error`. Imagem testada Ã© um artefato e o deploy utiliza esse mesmo tar. As tags de ferramentas estÃ£o fixadas em versÃµes; endurecimento futuro: validar versÃµes atuais e substituir tags por digests/SHA aprovados. NÃ£o alegar ausÃªncia de vulnerabilidades antes de rodar os scanners. Regras Semgrep locais sÃ£o uma base pequena, nÃ£o uma auditoria completa.

Deploy nÃ£o ocorre em push/PR: depende de execuÃ§Ã£o manual com deploy=true, branch main, DEPLOY_ENABLED=true e environment production. Configure no GitHub required reviewers e proteÃ§Ã£o de main ANTES de habilitar a variÃ¡vel. YAML sozinho nÃ£o cria regra de aprovaÃ§Ã£o. O deploy publica a imagem no GHCR e atualiza um Azure Container App jÃ¡ criado. O GHCR deve estar pÃºblico ou o Container App precisa de acesso explicitamente configurado ao registro privado; o exemplo Terraform pressupÃµe imagem pÃºblica. Configurar OIDC Azure com identidade de privilÃ©gio mÃ­nimo, secrets AZURE_CLIENT_ID/AZURE_TENANT_ID/AZURE_SUBSCRIPTION_ID e vars AZURE_RESOURCE_GROUP/AZURE_CONTAINER_APP. Nenhuma conta, secret, permissÃ£o, ambiente GitHub ou recurso foi criado. PublicaÃ§Ã£o/infra requerem autorizaÃ§Ã£o separada.

## IaC Azure (exemplo real, NÃƒO aplicado)
`terraform/main.tf` declara resource group, Container Apps environment e Container App com HTTPS, escala 0..1 e robÃ´ simulado. Requer assinatura Azure, quota/regiÃ£o e imagem publicada. Pode gerar cobranÃ§as mesmo em laboratÃ³rio: custo nÃ£o estimado nesta entrega. NÃ£o execute apply sem orÃ§amento e aprovaÃ§Ã£o.

SequÃªncia manual de validaÃ§Ã£o: `terraform fmt -check`, `terraform init -backend=false`, `terraform validate`; depois plano revisado em ambiente autorizado. Copiar terraform.tfvars.example localmente e substituir valores, nunca versionar tfvars/state/plano com dados reais. Antes de uso compartilhado, configurar backend remoto seguro com locking, restringir RBAC e emitir lockfile de provedores apÃ³s init. CLI Terraform ausente aqui: fmt/validate/plan/apply nÃ£o executados. O exemplo nÃ£o Ã© uma implantaÃ§Ã£o comprovada.

## Observabilidade: quatro mÃ©tricas
- acolhe_requests_total: volume de requisiÃ§Ãµes; `rate(acolhe_requests_total[5m])`.
- acolhe_attempts_total: tentativas educacionais; `increase(acolhe_attempts_total[1h])`.
- acolhe_errors_total: falhas da aplicaÃ§Ã£o; taxa relativa Ã s requisiÃ§Ãµes.
- acolhe_uptime_seconds: tempo de vida do processo, Ãºtil para detectar reinÃ­cios.

Prometheus coleta `/metrics` a cada 15s. Alertas: indisponibilidade por 2min e taxa de erros >5% por 5min. Verificar com `promtool check config` e `promtool check rules` ao ter container disponÃ­vel. Alertas aparecem no Prometheus; entrega externa exige Alertmanager/destinatÃ¡rio autorizado, NÃƒO configurados. NÃ£o hÃ¡ envio de mensagens.

## PendÃªncias e roteiro de evidÃªncia
1. Executar testes e build Docker; capturar healthcheck e usuÃ¡rio UID10001.
2. Publicar repositÃ³rio somente apÃ³s autorizaÃ§Ã£o; executar CI e guardar URL do run e relatÃ³rios de cada scanner.
3. Instalar/validar Terraform em ambiente autorizado; revisar plano e custos antes de aplicar.
4. Configurar environment production com aprovadores e OIDC com menor privilÃ©gio; fazer deploy apenas quando autorizado.
5. Capturar dashboard das quatro mÃ©tricas e alerta disparado em ensaio controlado. NÃ£o simular evidÃªncia como se fosse produÃ§Ã£o.
6. Escopo acadÃªmico: dados de demonstraÃ§Ã£o apenas. Rever autenticaÃ§Ã£o, TLS/proxy, persistÃªncia, LGPD e limites antes de expor a aplicaÃ§Ã£o a usuÃ¡rios reais.

### Quatro sinais de ouro
O dashboard `monitoring/grafana-dashboard.json` pode ser importado em um Grafana existente, selecionando o datasource Prometheus. NÃ£o foi provisionado nem testado no Grafana.
- LatÃªncia: rate(acolhe_request_duration_seconds_sum[5m]) / rate(acolhe_request_duration_seconds_count[5m]), mÃ©dia, nÃ£o p95.
- TrÃ¡fego: rate(acolhe_requests_total[5m]), requisiÃ§Ãµes por segundo.
- Erros: rate(acolhe_errors_total[5m]) / clamp_min(rate(acolhe_requests_total[5m]), 0.001), proporÃ§Ã£o.
- SaturaÃ§Ã£o: acolhe_active_requests, concorrÃªncia como proxy de saturaÃ§Ã£o; nÃ£o mede CPU/memÃ³ria nem percentual de capacidade. Threshold inicial 20 requer calibraÃ§Ã£o por teste de carga.
HÃ¡ regras adicionais de latÃªncia mÃ©dia >1s e concorrÃªncia >20, ambas limiares provisÃ³rios. MÃ©tricas de tentativas/uptime complementam esses sinais, mas nÃ£o os substituem.

O Docker usa ACOLHE_DB=/tmp/acolhe.db para compatibilidade com filesystem read-only. Dados sÃ£o efÃªmeros e se perdem na recriaÃ§Ã£o do container; para persistir, provisionar volume gravÃ¡vel UID10001, configurar ACOLHE_DB e rever retenÃ§Ã£o/privacidade. As integraÃ§Ãµes genai/vision/rpa tambÃ©m sÃ£o copiadas Ã  imagem.


## Primeira CI pÃºblica e correÃ§Ã£o de imagem (2026-11-09)

O run https://github.com/TomazVC/Acolhe---GS8/actions/runs/42685134583, commit `624c6e77c003c88bba8edfc6a1b86f3f5403beed`, aprovou testes Python/Node, Gitleaks, Semgrep e build Docker. O Trivy bloqueou a imagem Debian 13.7: 49 ocorrÃªncias HIGH e nenhuma CRITICAL. SÃ£o ocorrÃªncias por pacote, nÃ£o necessariamente CVEs distintas.

Duas ocorrÃªncias em `zlib1g` tinham atualizaÃ§Ã£o indicada, para `1:1.3.dfsg+really1.3.1-1+deb13u1`. Outras estavam sem versÃ£o corrigida indicada ou com correÃ§Ã£o adiada pelo fornecedor. A imagem passa a aplicar as atualizaÃ§Ãµes disponÃ­veis da distribuiÃ§Ã£o durante o build; a CI busca a imagem-base atual com `--pull`. Isso nÃ£o garante ausÃªncia de vulnerabilidades sem correÃ§Ã£o. O bloqueio HIGH/CRITICAL continua ativo, sem `ignore-unfixed`, exceÃ§Ãµes de CVE ou supressÃ£o de erros. Consulte o run do commit atual antes de considerar a imagem aprovada. Nenhum deploy foi executado.


### Alternativas oficiais avaliadas

O run https://github.com/TomazVC/Acolhe---GS8/actions/runs/42686110502 comparou imagens oficiais com atualização de pacotes, os 61 testes Python dentro de cada container (60 aprovados e 1 ignorado por PyYAML opcional), smoke HTTP e escrita/leitura SQLite com UID 10001, e Trivy com bloqueio HIGH/CRITICAL.

- `python:3.12-slim-bookworm`: testes aprovados, scan com 40 HIGH e 2 CRITICAL. Não adotada.
- `python:3.12-alpine`: testes e smoke aprovados; scan sem achados HIGH/CRITICAL na base Alpine 3.24.4. Adotada com o digest oficial verificado `sha256:e064671ca452259bab50e8e2c7bd896e39e9a343bb06ca25234adf6fe18d0fc7`, mantendo atualização de pacotes Alpine e todas as barreiras de segurança.

A CI principal agora também executa testes dentro da imagem e smoke HTTP/SQLite real antes do scan. A validação cobre o MVP de biblioteca padrão; não valida treinamento YOLO, dependências nativas opcionais, Airflow ou Databricks na imagem Alpine. Novas dependências precisam de nova verificação, pois Alpine usa musl em vez de glibc. O digest deve ser atualizado e revalidado periodicamente; um scan sem achados hoje não garante segurança futura. A branch `ci/evaluate-python-bases` preserva o experimento e não realiza deploy.
