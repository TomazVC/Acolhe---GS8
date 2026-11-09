# Registro de testes e evidências

Este registro não marca testes como executados. Preencher uma linha por execução real e vincular o arquivo bruto, captura ou log correspondente.

| Campo | Valor a registrar |
|---|---|
| Identificador | T01, T02 ou outro ID único |
| Data e hora | Incluir fuso |
| Responsável | Nome de quem executou |
| Versão | Commit ou cópia identificada do código |
| Ambiente | Sistema, Python, navegador e dependências relevantes |
| Pré-condições | Banco, configuração, modelo e hardware presentes |
| Comando ou passos | Sequência reproduzível |
| Resultado esperado | Definido antes da execução |
| Resultado observado | Comportamento efetivamente visto |
| Evidência | Caminho relativo para log, screenshot ou vídeo |
| Situação | Aprovado, reprovado, bloqueado ou não executado |
| Limite da prova | O que este teste não demonstra |

## Checklist de aceite

- [ ] Núcleo e API com testes realmente descobertos e executados.
- [ ] PT e ES conferidos manualmente.
- [ ] Offline testado após carga prévia e sem gravação fictícia.
- [ ] Interface revisada por teclado e em tela estreita.
- [ ] RPA com sucesso, erro e log revisados.
- [ ] GenAI com modelo local, comparação e erros observados.
- [ ] Visão com treinamento customizado e conjunto separado.
- [ ] Big Data com fontes reais e dois lotes de dias de coleta diferentes no Databricks.
- [ ] Infraestrutura e métricas/alerta executados.
- [ ] Robô físico com sensor real, segurança e IA integrada.
- [ ] Todos os arquivos de evidência sem dados pessoais indevidos.

Não editar resultados antigos para parecerem mais recentes. Criar novo registro após correção. Não incluir senhas, tokens ou informação de crianças em evidências.


## T02 - Correcao de idioma e regressao completa

- Data UTC: 2026-11-07T13:36:14.784806+00:00.
- Responsavel: validacao automatizada local do projeto.
- Ambiente: Windows-11-10.0.26200-SP0; Python 3.12.10.
- Versao: copia local sem Git; hashes SHA-256 dos arquivos Python e JavaScript no log abaixo.
- Pre-condicoes: bancos sinteticos e diretorios temporarios criados pela suite; sem banco de uso, modelo, hardware ou servico externo.
- Comandos: `python -B -m unittest discover -v`; `node --check app/static/app.js`; `node --check app/static/sw.js`.
- Esperado: atividades PT e ES na mesma sessao agrupadas separadamente, historico preservado, idioma invalido rejeitado, migracao de banco antigo e idempotencia mantidas, nenhuma regressao na suite.
- Observado: 48 testes aprovados; verificacoes de sintaxe JavaScript aprovadas; todos os comandos com codigo 0.
- Evidencia bruta e identidade dos arquivos: [verificacao-20261107T133614Z.json](evidencias/verificacao-20261107T133614Z.json).
- Regressao: antes da correcao, os dois novos testes HTTP falharam: ambas as tentativas eram atribuidas a PT e idioma invalido era aceito. Depois da correcao ambos passaram. Essa execucao inicial consta do terminal; o arquivo vinculado preserva a execucao final.
- Situacao: aprovado para este escopo automatizado.
- Limite: nao testa interacao visual no navegador, service worker offline, tela estreita, teclado, voz, LLM real, treinamento de visao, hardware, Docker, nuvem ou CI. Nao e evidencia de conclusao integral da entrega.

O checklist original acima e um roteiro de aceite geral e permanece sem marcar itens que exigem validacao manual ou externa. A verificacao automatizada de nucleo e API esta registrada nesta entrada.


## T03 - Sessao expirada e COPY INTO (2026-11-07T16:51:12Z)

- Correcao: sessao expirada limpa progresso local antigo antes da nova sessao; COPY INTO emite aliases explicitos para as seis colunas de CSV e usa mode=FAILFAST.
- Preservacao: guardas SHA-256 conferidas antes das alteracoes e durante a validacao; README Big Data ja estava atualizado por outra revisao e foi preservado. Nenhuma edicao em vision/.
- Regressao: novo teste frontend falhou antes (progresso 1/1 em vez de 0/1 apos expirar) e passou depois. Novo teste do SQL emitido falhou antes por alias ausente e passou depois.
- Executado: python -B -m unittest discover -v: 61 testes descobertos, 60 aprovados e 1 skip (dependencia opcional PyYAML de treinamento ausente). Nao declarar 61 testes aprovados.
- Executado: node --test tests/frontend.test.cjs: 11 aprovados; node --check app/static/app.js: codigo 0. AST dos arquivos Python envolvidos valido.
- Evidencia bruta, ambiente e hashes: [revisao-sessao-copy-20261107T165112Z.json](evidencias/revisao-sessao-copy-20261107T165112Z.json).
- Limites: o teste COPY INTO executa somente a geracao local do SQL, sem Spark/Delta; nao comprova compatibilidade runtime Databricks. Testes frontend usam Node VM com DOM/rede controlados, nao navegador real. Airflow, Databricks, visual/offline e treinamento continuam sem evidencia real nesta revisao.
