# Fontes oficiais: coleta real separada da demonstracao

## O que foi feito em 2026-11-07 UTC
1. IBGE, API Localidades, municipios de Sao Paulo: HTTP 200, 645 municipios, 284.370 bytes JSON. CSV normalizado apenas com codigo/nome de municipio e UF. Apoio territorial, NAO medida de migrantes, idioma, vagas ou demanda.
2. OBMigra/MJSP, Dados Consolidados da Imigracao no Brasil 2025: HTTP 200, PDF original de 11.428.175 bytes. Relatorio estatistico agregado, NAO microdados de beneficiarios. Original preservado, ainda nao convertido em tabelas nem conectado ao ouro.

Os arquivos ficam em official_snapshots/raw/<fonte>/<SHA256>.<extensao>; manifests registram URL, hora real UTC, status HTTP, formato, hash, tamanho, finalidade e situacao da licenca. O hash endereca o conteudo: coletas iguais nao duplicam o bruto; cada coleta gera manifesto proprio. O CSV IBGE e uma proiecao com colunas territoriais permitidas. Nenhum nome/documento de migrante foi adquirido. Os dois CSVs de demanda/servicos e summary.json do MVP continuam demonstrativos, em pastas distintas.

## Revisao de licencas em 2026-11-14
- IBGE: o Plano de Dados Abertos IBGE 2024-2025 (https://www.ibge.gov.br/np_download/novoportal/documentos_institucionais/Plano_de_Dados_Abertos_IBGE_2024_2025.pdf) lista na p.54 a "Divisao Territorial Brasileira" entre as bases a publicar como dados abertos. Nas p.59-60, define dados abertos como dados sob licenca aberta, com livre reuso e, no maximo, exigencia de credito a autoria. A Biblioteca do IBGE tambem permite usar dados de suas publicacoes desde que o IBGE seja citado como fonte. Status: dado aberto com atribuicao obrigatoria. Citacao usada: "IBGE, API de Localidades (servicodados.ibge.gov.br), acesso em 2026-11-14". Nao foi encontrado documento de licenca especifico da API; o manifesto registra isso.
- OBMigra: a p.4 do proprio relatorio permite reproduzir texto e dados citando a fonte, com reproducoes comerciais proibidas. A pagina oficial declara CC BY-ND 3.0. Por isso extraimos fatos numericos com citacao e pagina, sem publicar o PDF nem tabelas derivadas como obra adaptada. Uso academico, nao comercial.

## Fontes, autoria e licencas
IBGE: https://servicodados.ibge.gov.br/api/v1/localidades/estados/35/municipios . Documentacao: https://servicodados.ibge.gov.br/api/docs/localidades . Acesso tecnico confirmado, mas NAO foi localizada licenca formal especifica da API em fonte oficial. Nao rotulamos CC BY ou dominio publico. A referencia fica local para pesquisa; conferir termos antes de redistribuir. Licencas de jQuery/Bootstrap presentes no HTML da documentacao nao sao licencas dos dados.

OBMigra/MJSP: https://www.gov.br/mj/pt-br/assuntos/seus-direitos/migracoes/portal-de-imigracao-laboral/obmigra-1/relatorios-obmigra/dados-consolidados/2025 . Arquivo vinculado na pagina: Dados2025.pdf. O rodape oficial consultado em 07/11/2026 declara Creative Commons Atribuicao-SemDerivacoes 3.0 Nao Adaptada, https://creativecommons.org/licenses/by-nd/3.0/ . Isso e evidencia da declaracao do site, nao permissao irrestrita de adaptar qualquer anexo. Preservamos o documento original, autoria e link, sem publicar nem transformar suas tabelas. Verificar creditos/termos internos e metodo de extracao antes da integracao tabular.

CRAI: pagina oficial https://prefeitura.sp.gov.br/web/imigrantes_e_trabalho_decente/dados_e_conhecimento_sobre_a_populacao_imigrante informa dados de perfis anonimizados e um painel. Como a tarefa pede evitar dados pessoais e a licenca de reutilizacao especifica nao foi verificada, nao baixamos microdados. A anonimizacao alegada nao foi tratada como garantia de ausencia de risco de reidentificacao.

## Repetir e registrar o segundo dia real
Na raiz acolhe, em outro dia real:
```
python -B -m big_data.collect_official --source all
```
Ou apenas `--source ibge` / `--source obmigra`. O script usa datetime.now UTC, sem opcao para inventar/backdatear coleta. Rodar novamente hoje cria outra coleta NO MESMO DIA; isso nao satisfaz dois dias distintos. Compare retrieval_day_utc nos manifests. O conteudo remoto pode nao mudar: isso e esperado para referencia territorial e relatorio anual, mas o timestamp registra nova verificacao.

Data de coleta nao e data de referencia estatistica. O relatorio 2025 continua relatorio 2025 ao ser baixado em 2026. Nao apresente snapshot como dados atualizados de 2026.

## Pendencias para atender integralmente Big Data
- Confirmar licenca de reutilizacao especifica IBGE e termos dos anexos OBMigra antes de redistribuicao/derivacao.
- Obter segunda base estruturada adequada e harmonizar dimensoes/periodos sem inferir idioma de nacionalidade nem oferta de servicos a partir de municipios.
- Completar coleta em segundo dia real, e execucoes de Airflow 3 e Databricks com evidencias.
- Validar o schema/arquivos COPY INTO e as cinco consultas no runtime Databricks; testes locais nao substituem Spark.
- Conectar fontes reais ao ouro somente apos harmonizacao e revisao. Atual API do MVP permanece synthetic=true.
