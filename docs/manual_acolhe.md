# Acolhe
## Documentação do projeto e guia de validação

Português para recomeçar · Global Solution FIAP 2026.2 · CitizenTech

**Equipe**
- Tomáz Versolato Carballo · RM 551417
- Rony Ken Nagai · RM 551549
- Aksel Viktor Caminha Rae · RM 99011
- Ian Xavier Kuraoka · RM 98860

**Versão:** 0.1 · 7 de novembro de 2026
**Público:** equipe de desenvolvimento, professores avaliadores e futuros parceiros de acolhimento.
**Estado:** documentação da implementação inicial. Cada requisito acadêmico exige evidência própria. Código, simulação e plano de teste não demonstram, isoladamente, conclusão da disciplina.

## Sumário

1. Visão geral e problema
2. Escopo e experiência de uso
3. Arquitetura e fluxo de dados
4. Organização do repositório
5. Instalação e operação local
6. Integrações por disciplina
7. Estratégia e procedimentos de teste
8. Privacidade e segurança
9. Indicadores e demonstração
10. Pendências e critérios de entrega
11. Referências e rastreabilidade

# 1 Visão geral e problema

O Acolhe é um protótipo de acolhimento linguístico em português e espanhol para crianças hispanofalantes de 6 a 10 anos recém-chegadas ao Brasil. A proposta aproxima palavras do cotidiano, atividades curtas e orientação de mobilidade segura. Professores, responsáveis e voluntários participam como mediadores. O produto não substitui o acompanhamento pedagógico, a orientação de trânsito de um adulto nem serviços públicos oficiais.

A barreira linguística pode dificultar a participação nas atividades escolares e a comunicação em situações cotidianas. Esta é a hipótese de problema do projeto, ainda sujeita a validação com pessoas que convivem com o público. Não foram inventadas entrevistas, depoimentos, números de crianças atendidas ou resultados de aprendizagem.

O MVP combina uma aplicação web progressiva, atividades bilíngues e módulos separados de IA generativa, visão computacional, engenharia de dados, automação, infraestrutura e robótica. A separação permite demonstrar partes locais e registrar explicitamente o que depende de modelo, treinamento, infraestrutura externa ou hardware.

O modelo de sustentabilidade proposto é institucional: secretarias de educação, ONGs de acolhimento e organizações de impacto podem contratar ou financiar o serviço. Isso é uma hipótese comercial, não receita, parceria ou contrato firmado. A relação com os ODS 4, 10 e 11 é uma justificativa de propósito; não constitui comprovação de impacto.

# 2 Escopo e experiência de uso

## 2.1 Jornada prevista

1. O mediador apresenta a atividade e seleciona português ou espanhol.
2. A criança inicia uma sessão pseudônima, sem cadastro nominal.
3. Escolhe uma das cinco lições do MVP e responde a uma atividade.
4. O backend valida a resposta e registra a tentativa. A interface apresenta retorno acolhedor.
5. O progresso reúne tentativas e acertos; não deve ser interpretado como avaliação clínica, diagnóstico ou domínio do idioma.
6. O assistente de mobilidade consulta conteúdo curado. Quando não há fonte suficiente ou o modelo não está disponível, a interface deve informar a limitação.
7. A demonstração de robótica traduz eventos da atividade em respostas pedagógicas simuladas ou, futuramente, físicas.
8. Um adulto consulta resultados agregados e o relatório local de automação.

## 2.2 Limites do MVP

O modo offline oferece o conteúdo que tiver sido previamente armazenado no navegador. Operações que dependem do backend, como salvar tentativas ou consultar a IA local, exigem conexão com o servidor. O protótipo não deve confirmar gravação quando a rede falhar. Não há promessa de sincronização automática de respostas feitas offline.

Detecção de objetos reais depende de modelo treinado e de inferência verificada. Uma demonstração sem modelo deve estar identificada como simulação ou indisponibilidade, sem transformar rótulos de exemplo em resultados de uma câmera.

O robô físico ainda precisa de integração, montagem segura e teste real. A ponte H, os motores e as baterias mencionados pela equipe não comprovam a existência de sensor adicional nem o funcionamento do sistema integrado.

O serviço local não deve ser exposto à internet como aplicação de produção antes de revisar autenticação, autorização, proteção de dados, limites de requisições, TLS, retenção e configurações de implantação.

# 3 Arquitetura e fluxo de dados

## 3.1 Componentes

A arquitetura inicial usa backend Python com biblioteca padrão e persistência SQLite, além de frontend HTML, CSS e JavaScript. Os módulos especializados ficam desacoplados para que a ausência de uma dependência não seja confundida com um resultado válido.

**Interface PWA:** apresenta lições PT/ES, progresso, assistente e painel. O service worker deve armazenar somente os recursos previstos, sem tratar respostas pessoais da API como conteúdo público de cache.

**Backend local:** valida entrada, controla sessões, recebe tentativas e responde aos pedidos da interface. Os contratos efetivos e os comandos de inicialização devem ser conferidos no README da versão executada.

**SQLite:** armazena o estado local do protótipo. Identificadores de sessão são pseudônimos: não devem ser descritos como anonimização irreversível.

**GenAI:** recupera conteúdo de mobilidade e, quando configurado, chama uma LLM local. A resposta deve indicar fontes e permitir recusa. Recuperação lexical determinística e LLM são operações distintas.

**Visão:** prepara o contrato de identificação de objetos e o caminho para treinamento e inferência customizados. Resultados só podem ser apresentados como reais quando produzidos pelo modelo e associados ao conjunto de avaliação.

**Big Data:** organiza ingestão, qualidade e camadas bronze, prata e ouro. Um pipeline SQLite local é demonstração de lógica; não substitui a execução obrigatória em Databricks.

**RPA:** lê o banco da aplicação em modo de consulta, produz relatório agregado local e registra início, conclusão ou falha. O fluxo não envia mensagens automaticamente.

**Robótica:** converte eventos em respostas previstas e distingue simulação de hardware. Ausência de sensor ou conexão real deve permanecer visível.

## 3.2 Fluxos principais

Aprendizagem: navegador → backend → validação → SQLite → resposta pedagógica → atualização do progresso.

Assistente: pergunta → verificação de escopo → recuperação de fontes → contexto para LLM local, se disponível → validação do formato → resposta com fontes ou recusa.

Dados: fontes → ingestão paralela → bronze incremental → regras e MERGE na prata → fato e dimensões na ouro → consultas e painel.

Relatório: banco local existente → leitura agregada → geração de JSON e texto → gravação local → log do resultado.

Robô: evento da atividade e leitura do sensor → regras de segurança → ação de incentivo → confirmação ou timeout. O caminho físico precisa de evidência independente do simulador.

# 4 Organização do repositório

- `docs/`: documentação técnica, plano de validação e roteiros de demonstração.
- `bi/`: narrativa de negócio, roteiro do pitch e definições de indicadores.
- `genai/`: recuperação, integração com LLM local e avaliação.
- `vision/`: visão computacional, treinamento e testes.
- `big_data/`: fontes, pipeline, modelos e consultas analíticas.
- `rpa/`: robô de relatório local, testes e especificação do processo.
- `robot/`: simulador, serviço e firmware do protótipo físico.
- `devsecops/`: infraestrutura, monitoramento e orientações de implantação, quando presentes.
- `tests/`: testes do núcleo da aplicação.

Os documentos originais ficam na pasta pai e não devem ser substituídos. O logo original está em `../logo-png.png`. A identidade visual usa teal `#168C86` e peach `#F2A97A`; contraste e legibilidade têm prioridade sobre a aplicação de cores.

# 5 Instalação e operação local

## 5.1 Preparação

Use a versão de Python indicada no README do repositório e execute os comandos a partir da raiz `acolhe`. O comando do servidor é `python -m app.server`, com acesso local em `http://127.0.0.1:8080`. O núcleo foi planejado para Python 3.12, sem bibliotecas de terceiros. Módulos de treinamento, Airflow, Spark, Docker e LLM podem exigir ambientes próprios e dependências separadas.

Não coloque tokens, senhas, arquivos de crianças, imagens pessoais nem credenciais de nuvem no repositório. Crie configurações locais a partir dos exemplos fornecidos e mantenha os valores privados fora do controle de versão.

Antes de iniciar, confirme a disponibilidade da porta definida no README. Inicie o servidor conforme seu comando documentado e abra o endereço localhost informado pelo processo. Não se deve apresentar a URL local como MVP público.

## 5.2 Primeira verificação

Selecione um idioma, inicie uma sessão de teste e conclua ao menos uma atividade. Confira se o progresso mudou conforme a resposta. Reinicie o servidor e verifique a persistência prevista. Repita com resposta incorreta: o retorno deve ajudar a tentar novamente, sem humilhação ou penalização física.

Abra os módulos de IA, visão e robô e confira os estados exibidos. Quando um componente estiver ausente, o estado correto é indisponível ou simulado. Uma aparência funcional não comprova que LLM, câmera ou hardware estão operando.

## 5.3 Relatório local de progresso

O módulo RPA implementa uma leitura em modo somente consulta. Seu comando é:

`python -m rpa.robot --db data/acolhe.db --output rpa/output`

Execute após criar o banco pelo MVP e registrar uma tentativa. A rotina gera `progress.json`, `progress.md` e `robot.log` na pasta de saída. O caminho do banco deve corresponder à configuração real do servidor. O relatório agrega sessões, tentativas, acertos e distribuição pelo idioma de cada tentativa; não dispara e-mail. Registros antigos sem esse campo usam o idioma original da sessão, sem reconstruir trocas históricas não registradas.

O teste de falha deve usar um caminho inexistente em uma pasta de teste. O processo deve sair com erro e registrar `report_failed`, sem criar um relatório que pareça ter sido concluído com sucesso. Preserve relatórios anteriores com data de geração: um arquivo antigo não prova a execução atual.

## 5.4 Diagnóstico

Se o servidor não iniciar, registre comando, versão do Python, porta e mensagem de erro. Se o progresso não persistir, confira o caminho e permissões do banco. Se a IA recusar, diferencie falta de fonte, escopo proibido, modelo ausente e falha de conexão. Se o navegador mostrar conteúdo antigo, revise o service worker e teste uma nova sessão sem apagar evidência necessária.

Para qualquer falha, reproduza com dados sintéticos mínimos e preserve o log. Não inclua conteúdo pessoal em capturas de tela de diagnóstico.

# 6 Integrações por disciplina

## 6.1 Generative AI for Engineering

O recorte técnico é mobilidade segura no cotidiano, porque aprendizagem de português isolada pode não satisfazer o domínio restrito do enunciado. A equipe precisa validar esse enquadramento com o professor.

A avaliação deve comparar baseline, RAG e agente com a mesma base de perguntas. Cada pergunta deve registrar resposta esperada, documento relevante, resultado recuperado, formato de saída, fontes e eventual recusa. Recall@1 mede a fração de perguntas com documento relevante na primeira posição; Recall@3 mede a fração com documento relevante entre as três primeiras. O denominador e o conjunto de avaliação devem acompanhar qualquer percentual.

A LLM deve rodar localmente e ter modelo, versão, parâmetros e ambiente registrados. Uma rotina de recuperação ou um template sem inferência não conta como execução de LLM. São necessárias evidências de JSON válido, fontes, recusas justificadas e análise de pelo menos cinco erros reais. Não transforme casos de teste planejados em erros observados.

## 6.2 Big Data

O requisito inclui duas fontes, sendo ao menos uma API pública ou base aberta, tarefas paralelas no Airflow 3 e dois lotes no Databricks provenientes de dias de coleta diferentes. A bronze deve usar Auto Loader ou COPY INTO, preservar entrada e metadados e não duplicar dados na reexecução; a prata deve aplicar MERGE e pelo menos três regras de qualidade; a ouro deve conter uma fato, duas dimensões e cinco consultas SQL.

Fontes candidatas citadas no planejamento incluem SisMigra, IBGE e dados do CRAI. A equipe deve verificar disponibilidade, licença, esquema, periodicidade, granularidade e adequação ao objetivo antes de usá-las. Snapshot repetido de uma fonte estática não é atualização real do fenômeno. Dados sintéticos locais servem para testar a engenharia, não para afirmar distribuição de migrantes ou demanda pública.

Guarde data e hora das execuções, IDs de jobs, logs, contagens antes e depois, regras aplicadas e saídas SQL. Databricks precisa ser comprovado por execução real, não apenas pelo notebook preparado.

## 6.3 Business Intelligence

O pitch deve demonstrar o problema, usuário, pagador, proposta, MVP, indicadores e limites em até cinco minutos. A equipe precisa aparecer, publicar o vídeo como não listado no YouTube e testar o link em janela anônima (páginas 41 e 42), e a demonstração deve usar a versão que efetivamente funciona. Publicação e acesso público são etapas separadas, pendentes até validação do endereço e das permissões.

Os indicadores definidos em `bi/indicadores.md` distinguem uso, desempenho em atividade e retenção. Não afirmar palavras aprendidas apenas a partir de acertos. Não apresentar números sintéticos de um dashboard como impacto observado.

## 6.4 Computer Vision

A entrega requer treinamento customizado e evidência do conjunto de dados, classes, separação treino/validação/teste, parâmetros e resultados. Use objetos do cotidiano compatíveis com as atividades. Imagens de crianças não são necessárias para reconhecer objetos e devem ser evitadas.

Registrar erros reais de predição, objetos fora do escopo, condições de iluminação e limiar de confiança. O resumo de 250 palavras e o objetivo de 50 palavras devem acompanhar o PDF solicitado, com números apenas após a avaliação. Um classificador genérico ou stub não substitui treinamento customizado.

## 6.5 RPA

O processo automatizado consolida o progresso agregado em arquivos locais. O PDD deve documentar início, entradas, pré-condições, regras, saídas, exceções e responsáveis. O BPMN deve mostrar o fluxo e as saídas de falha. Envio a professor, e-mail e agendamento não devem ser alegados quando não implementados e autorizados.

A demonstração de até três minutos deve incluir uma execução bem-sucedida e uma falha controlada com log. O script de demonstração está em `docs/roteiros_videos.md`.

## 6.6 DevSecOps

Docker, Terraform e CI devem ter finalidade clara e configuração revisável. A presença de arquivos não prova build, scan, aplicação de infraestrutura ou deploy. Registre as saídas reais, os achados de segurança e o tratamento dado a cada um. Deploy exige destino, configuração e validação do serviço.

O monitoramento deve mostrar quatro métricas e pelo menos um alerta. Exemplos de métricas operacionais são requisições, erros, latência e disponibilidade, desde que realmente coletadas e com unidade e janela definidas. Métricas de negócio não substituem automaticamente as operacionais exigidas.

## 6.7 Maker

O requisito físico inclui um sensor adicional real integrado à decisão de IA. Motores, ponte H, cabeça e braço são componentes de atuação, não sensores. Uma opção de projeto é sensor de presença ou distância, a validar com o hardware disponível.

Antes de energizar, conferir tensão, corrente, alimentação, aterramento, limites mecânicos e proteção das partes móveis. Testes com pessoas devem ser supervisionados por adultos. O robô deve apoiar a criança com dicas e incentivo; não perseguir, assustar, constranger nem executar movimento inseguro para recuperar atenção.

A documentação oficial de Maker deve ser entregue como link GitHub, com nomes no README e link do vídeo. O enunciado não aceita PDF, DOCX ou arquivo compactado em substituição ao repositório (página 58). Este manual é apoio, não substituto dessa entrega.

A demonstração de até seis minutos deve mostrar leitura real do sensor, integração com a aplicação, decisão e ação, além do comportamento seguro quando a comunicação falhar. Vídeo de simulador não comprova hardware integrado.

# 7 Estratégia e procedimentos de teste

## 7.1 Camadas de verificação

**Unidade:** regras de correção, sessões, recuperação, agregação, tratamento de falhas e decisões do simulador.

**Integração:** contrato HTTP, persistência, chamadas entre backend e módulos, leitura do banco pelo RPA e consumo do resultado analítico.

**Interface:** navegação PT/ES, uso por teclado, feedback, apresentação de erros, responsividade e comportamento offline.

**Especializadas:** treinamento e inferência CV, avaliação comparativa de LLM, execução Airflow/Databricks, scans e infraestrutura, sensor e robô físicos.

**Aceitação:** demonstração do percurso completo por uma pessoa que não escreveu o código, com registro de obstáculos e revisão pedagógica.

## 7.2 Execução de testes automatizados

A partir da raiz do projeto, execute `python -B -m unittest discover -v` para descobrir a suíte Python completa. Execute `node --test tests/frontend.test.cjs` para os casos de frontend em Node VM e `node --check app/static/app.js` para sintaxe. Os testes de frontend usam DOM e rede controlados; não substituem a validação visual em navegador.

Evidência da revisão de 7 de novembro de 2026, às 16:51:12 UTC: 61 testes Python descobertos, com 60 aprovados e 1 ignorado porque PyYAML, dependência opcional de treinamento, estava ausente. Os 11 testes Node passaram; a verificação de sintaxe JavaScript terminou com código zero. O log e os hashes estão em `docs/evidencias/revisao-sessao-copy-20261107T165112Z.json`, referenciados na entrada T03 de `docs/registro_testes.md`. Isso não comprova execução real de Airflow, Databricks, modelo de visão ou navegador.

Registre data/hora, comando exato, versão do runtime, revisão do código, código de saída e saída completa. Um código de saída zero sem testes encontrados não demonstra aprovação. Conte os testes descobertos e identifique skips. Resultados de uma versão anterior não validam alterações posteriores.

## 7.3 Roteiro manual mínimo

- T01: iniciar sessão em PT e ES; observar os textos e a identidade da sessão. Esperado: idioma respeitado e ausência de cadastro nominal.
- T02: responder corretamente e incorretamente; observar feedback e totais. Esperado: correção coerente e incentivo respeitoso.
- T03: repetir a submissão ou usar uma sessão inválida. Esperado: comportamento definido, sem progressão fraudulenta silenciosa.
- T04: enviar JSON malformado e campos inválidos. Esperado: erro controlado, sem traceback ou gravação indevida.
- T05: tentar caminho estático fora da pasta pública. Esperado: recusa, sem leitura arbitrária de arquivos.
- T06: carregar lições, desligar rede e repetir navegação. Esperado: conteúdo previamente armazenado disponível; ações remotas informadas como indisponíveis.
- T07: consultar IA com pergunta suportada, fora do escopo e sem fonte. Esperado: fontes quando cabível e recusa explícita quando necessária.
- T08: operar IA sem modelo configurado. Esperado: não simular resposta de LLM real.
- T09: executar RPA com banco válido e inexistente. Esperado: saída agregada no sucesso e log de falha no erro.
- T10: carregar painel sem arquivo ouro. Esperado: estado vazio ou indisponível, sem números inventados.
- T11: simular presença, ausência e falha de comunicação do robô. Esperado: estado seguro e identificação de simulação.
- T12: navegar por teclado em tela estreita. Esperado: foco visível, controles legíveis e ausência de sobreposição.

O arquivo `docs/registro_testes.md` fornece o registro de evidências. Os resultados devem ser preenchidos após executar o caso, sem trocar esperado por observado.

# 8 Privacidade e segurança

A aplicação envolve um público infantil. A demonstração deve usar dados sintéticos e objetos, sem nomes, documentos, fotos de crianças ou localização individual. Sessões pseudônimas ainda podem constituir dados pessoais dependendo do contexto e das possibilidades de associação.

Antes de um piloto real, definir finalidade, base legal, responsabilidades, informações aos responsáveis, retenção, exclusão, direitos dos titulares e controles de acesso. Isso exige revisão adequada ao contexto; o protótipo não é uma certificação de conformidade com a LGPD.

Evite enviar imagens, perguntas identificáveis e progresso individual a terceiros. A LLM local reduz um caminho de transmissão, mas não elimina riscos de logs, backups, arquivos temporários ou exposição da rede. Revisar também armazenamento no navegador e sincronização de pastas.

Não persistir segredos em código, Terraform state versionado, imagens Docker ou logs. Não expor métricas detalhadas e relatórios administrativos sem avaliação de acesso. Nenhuma publicação deve incluir bancos locais com dados de uso reais.

# 9 Indicadores e demonstração

O painel deve responder perguntas verificáveis: quantas sessões de demonstração ocorreram, quantas tentativas foram registradas, qual proporção foi correta e qual o período observado. Cada gráfico deve explicitar fonte, período, unidade e natureza sintética ou observada dos dados.

Taxa de acerto não prova aprendizagem; sessões não equivalem a pessoas únicas; tempo de página não equivale a atenção; retenção só existe com comparação entre períodos e identificação apropriada. O arquivo de indicadores registra essas diferenças e as dependências de coleta.

Antes de gravar, crie dados exclusivamente de demonstração, confirme todos os caminhos exibidos, feche arquivos privados e ensaie com cronômetro. Não edite o vídeo para esconder falhas e apresentar uma integração não existente. Diga quando a tela usa simulador e quais etapas dependem de execução externa.

# 10 Pendências e critérios de entrega

## 10.1 Pendências que não podem ser resolvidas apenas com arquivos

- Validar com o professor o recorte de mobilidade da GenAI.
- Validar o problema e o conteúdo com professor, ONG ou outro mediador real; registrar consentimento para uso de falas ou imagens.
- Disponibilizar e executar uma LLM local; avaliar baseline, RAG e agente e analisar cinco erros reais.
- Selecionar fontes reais, executar Airflow 3 e carregar no Databricks dois lotes de dias de coleta diferentes, preservando evidências.
- Reunir dataset autorizado, treinar modelo de visão e medir desempenho em conjunto separado.
- Montar sensor adicional e robô, integrar IA e verificar segurança com hardware real.
- Executar infraestrutura, scans e monitoramento; revisar e publicar o MVP quando autorizado.
- Gravar os vídeos com a equipe e validar os links de entrega.
- Revisar os requisitos no PDF original e submeter o material nos canais da instituição.

## 10.2 Critério para declarar concluído

Uma entrega está concluída somente quando o artefato existe, foi executado ou revisado no contexto correto, atende ao requisito e tem evidência rastreável. Preparado significa que o arquivo ou roteiro existe. Testado localmente significa que um teste local foi executado com resultado registrado. Validado externamente significa que a dependência real, como Databricks ou hardware, foi comprovada. Esses estados não são intercambiáveis.

A equipe deve preencher responsável, prazo e evidência para cada pendência. Não há atribuição individual definitiva neste documento. O enunciado confirma entrega até 19 de novembro às 23h55 no Teams de cada disciplina (página 24). Um integrante faz cada envio, com a mesma equipe e produto nas sete disciplinas. Repositórios e aplicações precisam estar públicos e funcionando durante a correção, até uma semana após o encerramento. O vídeo BI deve ficar não listado no YouTube, acessível pelo link. Confirmar eventual atualização no portal antes de submeter.

# 11 Referências e rastreabilidade

1. `../Desafio-FIAP-GS-CitizenTech 4ES.pdf`: enunciado institucional original e autoridade para critérios de avaliação.
2. `../GSFinal.md`: proposta de acolhimento linguístico, público, hipóteses de fontes e justificativa do robô.
3. `../prompt-inicial.txt`: histórico do planejamento, equipe, prazo informado e restrição de domínio da GenAI.
4. `IMPLEMENTATION_PLAN.md`: decisões técnicas da implementação inicial.
5. READMEs, testes e evidências dos módulos: contratos e execução da versão do código efetivamente usada.

Os números de RM foram fornecidos pela equipe. Fontes públicas mencionadas como candidatas não foram tratadas como coleta concluída. Divergências entre planejamento e enunciado devem ser resolvidas a favor do enunciado e, quando necessário, com orientação do professor.

