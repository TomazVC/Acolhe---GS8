# Acolhe


## Equipe

- Tomáz Versolato Carballo — RM 551417
- Rony Ken Nagai — RM 551549
- Aksel Viktor Caminha Rae — RM 99011
- Ian Xavier Kuraoka — RM 98860



Português para recomeçar. Protótipo acadêmico da Global Solution FIAP 2026.2, CitizenTech, para acolhimento linguístico em português/espanhol e orientações educativas de mobilidade segura.



**Estado:** MVP local com módulos demonstrativos. Não é um produto validado para uso com crianças nem uma entrega acadêmica integralmente comprovada. Use adultos e dados fictícios nesta fase. O código está publicado em https://github.com/TomazVC/Acolhe---GS8. Isso não publica o aplicativo na internet nem comprova um ambiente de produção.



## Ficha técnica



- Versão da API: 0.1.0; Python 3.12, biblioteca padrão, SQLite e servidor HTTP local.

- Interface: HTML/CSS/JavaScript sem instalação de pacotes; cinco lições PT/ES, síntese de voz do navegador e service worker.

- Persistência: sessões pseudônimas, tentativas, acertos e idioma por tentativa. Exclusão por sessão; expurgo após sete dias nas operações do banco, não por agendador independente.

- Integrações: recuperação lexical de conteúdo curado, adaptador opcional Ollama, contrato de visão, robô simulado, pipeline de dados e RPA local.

- Infraestrutura preparada: Docker/Compose, GitHub Actions, Terraform Azure e métricas Prometheus. Configuração não equivale a infraestrutura executada.

- Documentação: [manual PDF](docs/manual_acolhe.pdf), [fonte Markdown](docs/manual_acolhe.md) e [registro de testes](docs/registro_testes.md).



## Executar localmente



Abra um terminal na pasta `acolhe`, com Python 3.12 disponível:



```powershell

python --version

python -B -m app.server

```



Abra http://127.0.0.1:8080. No Windows, `Iniciar-Acolhe.cmd` executa o mesmo servidor. Encerre com Ctrl+C. Não é necessário instalar dependências para o MVP padrão ou sua suíte Python. Não abra index.html diretamente, pois a aplicação precisa da API.



O servidor usa loopback por padrão. Se a porta já estiver ocupada, escolha outra sem interromper processos desconhecidos:



```powershell

$env:PORT="8081"

python -B -m app.server

```



`ACOLHE_DB` altera o caminho do banco; o padrão é `data/acolhe.db`. Faça cópia de segurança antes de atualizar instalações com dados relevantes. A primeira abertura pelo código atual acrescenta a coluna de idioma de tentativa a bancos antigos, sem excluir suas atividades. Tentativas antigas continuam atribuídas ao idioma original da sessão, pois não é possível reconstruir mudanças de idioma que não foram registradas.



O service worker prepara as lições para leitura offline após uma primeira carga bem-sucedida. Respostas e assistente precisam de conexão com o servidor; não há fila de sincronização offline. A verificação manual desse fluxo em navegador continua pendente. HTTPS é necessário para PWA fora de localhost.



## Testar



```powershell

python -B -m unittest discover -v

node --test tests/frontend.test.cjs
node --check app/static/app.js

node --check app/static/sw.js

```



Node é opcional para executar os testes de frontend em ambiente controlado e verificar sintaxe JavaScript; isso não substitui revisão no navegador real. Os testes Python usam bancos e diretórios temporários, inclusive um servidor HTTP em porta local temporária. Não precisam do banco de uso, hardware, dataset ou Ollama. A suíte verifica contratos e indisponibilidade explícita dos módulos que ainda não possuem modelo; não comprova inferência real, qualidade pedagógica ou funcionamento visual.



Na validação de 7 de novembro de 2026, às 16:51:12 UTC, a suíte Python descobriu 61 testes: 60 aprovados e 1 ignorado por ausência da dependência opcional PyYAML de treinamento. Os 11 testes Node do frontend passaram. A sintaxe JavaScript também foi aprovada. Consulte a entrada T03 de [registro de testes](docs/registro_testes.md) e o [log com hashes](docs/evidencias/revisao-sessao-copy-20261107T165112Z.json). Resultados são específicos daquele estado do código; não comprovam execução real de navegador, Airflow, Databricks ou modelos.



## Arquitetura e pastas



1. `app/static/`: interface e cache offline. O idioma selecionado acompanha cada resposta enviada.

2. `app/server.py`: rotas JSON, validação de entrada, arquivos estáticos, cabeçalhos de segurança e métricas.

3. `app/core.py`: lições, sessão, retenção e gravação idempotente SQLite.

4. `genai/`: corpus autoral bilíngue, recuperação, avaliações e comparação opcional de LLM local. Sem modelo configurado, o modo é `retrieval_only`, não geração por LLM.

5. `vision/`: classes, serviço indisponível sem checkpoint e roteiro de treinamento real.

6. `robot/`: feedback simulado; não abre serial nem movimenta motores.

7. `big_data/`: pipeline demonstrativo, consultas SQL, exemplos Airflow/Databricks e saída sintética.

8. `rpa/`: leitura do SQLite sem alterar a origem e produção de relatórios agregados locais. Agrupa novas atividades pelo idioma da tentativa; bancos antigos usam idioma da sessão.

9. `bi/`: indicadores e roteiro de pitch. `devsecops/`: infraestrutura, segurança e observabilidade. `tests/`: núcleo e HTTP.



Rotas principais: `GET /api/health`, `/api/lessons`, `/api/summary`, `/api/gold`, `/api/automation`, `/api/vision/status` e `/metrics`; `POST /api/sessions`, `/api/attempts`, `/api/sessions/delete` e `/api/assistant`. O identificador de sessão funciona como credencial da demonstração, não como autenticação de produção.



## Demonstrações auxiliares



Execute a partir da raiz, sabendo que os dois primeiros comandos gravam saídas locais:



```powershell

python -B -m big_data.pipeline --demo

python -B -m rpa.robot

python -B -m robot.simulator --correct

python -B -m robot.simulator --absent

```



O pipeline usa dados sintéticos. O RPA precisa de `data/acolhe.db`, criado ao iniciar o MVP; não cria silenciosamente um banco ausente. Nenhum desses comandos envia resultados a terceiros. Veja [Big Data](big_data/README.md), [RPA](rpa/README.md), [robótica](robot/README.md), [GenAI](genai/README.md) e [visão](vision/README.md) para contratos e limites.



## Docker e infraestrutura



```powershell

docker compose up --build

docker compose --profile monitoring up --build

```



Esses comandos são instruções para ambiente com Docker funcional, não evidência de execução nesta máquina. Compose limita a porta ao loopback. O container executa sem root e usa banco em `/tmp`, **efêmero: recriar o container perde o progresso**. Persistência requer volume e permissões apropriadas antes de uso real. Prometheus usa a porta 9090 quando habilitado.



Não executar Terraform apply, configurar credenciais, publicar imagem ou habilitar deploy sem revisão e autorização específica. Consulte [DevSecOps](devsecops/README.md). O workflow será executado pelo GitHub Actions a cada push em main; consulte o resultado do commit publicado. A presença do workflow não comprova aprovação da CI.



## Privacidade e limites



Não inserir nomes, endereços, fotos, áudio ou dados de crianças. Sessões aleatórias são pseudonimização, não anonimização garantida. Métricas são agregados de demonstração e não representam crianças atendidas. O relatório RPA exige retenção própria, pois é um retrato exportado e não acompanha automaticamente a exclusão de sessões. A demonstração não decide travessia nem substitui um adulto ou serviço de emergência.



Antes de exposição pública: autenticação/autorização, TLS e servidor adequado, limitação de tráfego, proteção de métricas, armazenamento persistente, revisão LGPD e revisão pedagógica humana. Não publicar bancos, dependências de documentação (`docs/.deps/`), intermediários (`docs/qa/`), segredos ou arquivos de estado Terraform. A licença de distribuição do conjunto e das dependências/datasets precisa ser revisada antes de redistribuição.



## Pendências de entrega



- UI: revisão visual PT/ES, teclado, tela estreita, offline, voz e fluxos interrompidos no navegador.

- GenAI: executar LLM local autorizado, comparar baseline/RAG/agente, avaliar respostas e documentar erros reais do modelo.

- Visão: dataset real licenciado, treino customizado, split de teste, métricas e análise de erros. Não existe checkpoint validado.

- Big Data: fontes reais e execuções de coleta em dois dias distintos; execução em Spark/Databricks e Airflow.

- Robótica: bancada, sensor, LCD, alimentação, parada segura, firmware e demonstração física. Simulação não é hardware comprovado.

- DevSecOps: build Docker, CI/scanners, validação Terraform, ambiente autorizado, métricas e alerta demonstrados.

- RPA/BI: evidências integradas, vídeos, validação do problema/negócio e avaliação da adequação do RPA em Python à rubrica.

- Entrega: revisar requisitos disciplinares, links públicos e vídeos antes de qualquer publicação autorizada. PDF, código e roteiros não substituem essas evidências.



## Conteúdo da publicação

O repositório mantém o código, testes, logo fornecido para o projeto, identificação acadêmica da equipe, manual PDF e fontes de documentação. Foram excluídos bancos de uso, segredos, dependências locais, intermediários de PDF, backups, pesos de modelos, fotografias e metadados de datasets e capturas de fontes externas cuja redistribuição não foi validada. Esses arquivos permanecem somente na máquina de origem.

Os CSVs de `big_data/input/` e o resumo de demonstração `big_data/output/summary.json` são sintéticos. O corpus bilíngue em `genai/data/corpus.json` faz parte do projeto e é necessário para o assistente local; os exemplos de configuração em `vision/data/` não incluem imagens. Relatórios históricos que mencionam capturas e datasets locais não significam que esses arquivos estão neste repositório. Para obter novas capturas, consulte `big_data/OFFICIAL_SOURCES.md` e revise as condições da fonte.

A publicação não adiciona uma licença geral de uso ao projeto. As indicações de licença em conteúdos e dependências específicos mantêm seu escopo; revise-as antes de redistribuir ou incorporar material de terceiros.
