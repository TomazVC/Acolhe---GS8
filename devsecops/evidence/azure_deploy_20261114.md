# Deploy Azure (2026-11-14 UTC)

**URL pública:** https://acolhe-gs8.ambitiousbeach-2f5aaa39.canadacentral.azurecontainerapps.io

Assinatura Azure for Students, região `canadacentral` (a política "Allowed resource deployment regions" da assinatura só permite northcentralus, canadacentral, spaincentral, italynorth e southafricanorth; `brazilsouth` seria recusada). Terraform 1.13.5 + azurerm 4.81.0, via Azure CLI 2.92.0 (imagens oficiais em Docker no WSL2). O ID da assinatura e o state ficam fora do repositório.

## Recursos (8)
Resource group `rg-acolhe-gs8`; VNet `vnet-acolhe-gs8` + subnet `snet-aca` (/23, delegada a Microsoft.App/environments, service endpoint Storage); storage account (firewall Deny exceto a subnet, TLS 1.2, criptografia de infraestrutura) + share `acolhe-data` de 1 GiB; Container Apps environment `cae-acolhe-gs8` (workload profile Consumption); environment storage; Container App `acolhe-gs8` (0..1 réplica, ingress externo só HTTPS, `/data` montado).

Imagem: `ghcr.io/oslyanka/acolhe-gs8@sha256:549c777b641c2e0ab45fac0fd1f96f12516d8ab9a16d0d1c792cb45825d2f51d`, construída do commit `75453a9` da branch Aksel+Ian e fixada por digest.

## Defeitos encontrados no deploy real e corrigidos
1. Pacote GHCR privado: o pré-check com pull anônimo (HTTP 401/403) barrou o apply antes de criar qualquer coisa; o apply só rodou com HTTP 200.
2. `MissingSubscriptionRegistration: Microsoft.App` (409): a assinatura nova não tinha o provedor registrado. Registrados `Microsoft.App` e `Microsoft.OperationalInsights`.
3. `ManagedEnvironmentSubnetDelegationError` (400): o Azure passou a exigir subnet delegada a `Microsoft.App/environments`. O `main.tf` ganhou a delegação, um workload profile `Consumption` (serverless, escala a zero) e `workload_profile_name` no app. Validado (`terraform validate`) e o gate Trivy continuou em 0 HIGH/CRITICAL antes do novo apply.

Resultado final: `Apply complete! Resources: 3 added, 1 changed, 0 destroyed` (depois dos 5 criados no primeiro apply).

## Verificação na URL pública
| Verificação | Resultado |
|---|---|
| `/api/health` | `{"status":"ok","mode":"academic_demo",...}` |
| `/`, `/logo.png`, `/api/lessons`, `/api/summary`, `/api/gold`, `/api/automation`, `/metrics` | 200 |
| HTTP → HTTPS | 301 para https:// (`allowInsecure=false`) |
| Cabeçalhos | `content-security-policy`, `x-content-type-options: nosniff` |
| Gravação pela API pública | sessão ES + tentativa `casa` = `correct: true` |
| Persistência (SQLite em Azure Files, `nobrl`) | 03:37:45Z sessions=1 attempts=1 → restart → nova réplica `…kz6mk` criada 03:38:09Z → 03:38:20Z sessions=1 attempts=1 |
| Escala | máximo 1 réplica (escritor único do SQLite), mínimo 0 |

## Remover tudo
`terraform destroy` no diretório de trabalho (state local, fora do Git), ou excluir o resource group `rg-acolhe-gs8`.
