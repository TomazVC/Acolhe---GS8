# DevSecOps Acolhe

## Execução local
Na raiz, `python -m app.server` inicia a aplicação (porta 8080). `docker compose up --build` é o caminho container. `docker compose --profile monitoring up --build` acrescenta Prometheus em http://localhost:9090. A aplicação fica restrita ao loopback do host na porta 8080. Container não root, filesystem somente leitura no Compose, capabilities removidas e no-new-privileges. Não foi possível executar Docker aqui: daemon indisponível; estes arquivos ainda exigem build e smoke test.

## Pipeline
`.github/workflows/devsecops.yml` executa testes da aplicação e robô, Gitleaks no histórico, Semgrep com regras locais, build, Trivy imagem e IaC. HIGH/CRITICAL bloqueiam; não há `continue-on-error`. Imagem testada é um artefato e o deploy utiliza esse mesmo tar. As tags de ferramentas estão fixadas em versões; endurecimento futuro: validar versões atuais e substituir tags por digests/SHA aprovados. Não alegar ausência de vulnerabilidades antes de rodar os scanners. Regras Semgrep locais são uma base pequena, não uma auditoria completa.

Deploy não ocorre em push/PR: depende de execução manual com deploy=true, branch main, DEPLOY_ENABLED=true e environment production. Configure no GitHub required reviewers e proteção de main ANTES de habilitar a variável. YAML sozinho não cria regra de aprovação. O deploy publica a imagem no GHCR e atualiza um Azure Container App já criado. O GHCR deve estar público ou o Container App precisa de acesso explicitamente configurado ao registro privado; o exemplo Terraform pressupõe imagem pública. Configurar OIDC Azure com identidade de privilégio mínimo, secrets AZURE_CLIENT_ID/AZURE_TENANT_ID/AZURE_SUBSCRIPTION_ID e vars AZURE_RESOURCE_GROUP/AZURE_CONTAINER_APP. Nenhuma conta, secret, permissão, ambiente GitHub ou recurso foi criado. Publicação/infra requerem autorização separada.

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

O Docker usa ACOLHE_DB=/tmp/acolhe.db para compatibilidade com filesystem read-only. Dados são efêmeros e se perdem na recriação do container; para persistir, provisionar volume gravável UID10001, configurar ACOLHE_DB e rever retenção/privacidade. As integrações genai/vision/rpa também são copiadas à imagem.
