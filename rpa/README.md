# RPA em Python: relatorio agregado de aprendizagem

## PDD (Process Definition Document)
Objetivo: retirar a consolidacao manual de progresso sem transmitir dados a terceiros. Dono do processo: equipe Acolhe. Entrada: SQLite local `data/acolhe.db`, tabelas sessions(id,language,created_at) e attempts(id,session_id,lesson_id,correct,created_at). Saida: progress.json, progress.md e robot.log em rpa/output. Credenciais: nenhuma. Disparo: comando manual; agendamento nao foi ativado.

Pre-condicoes: executar o MVP e concluir pelo menos uma atividade para demonstrar; banco vazio e permitido. Fluxo: validar existencia -> conectar em modo somente leitura -> agregar sessoes/tentativas/acertos por idioma -> escrever JSON atomico e Markdown -> registrar sucesso. Erro: registrar tipo sem dados pessoais e terminar com codigo 1. Ausencia do banco nunca cria um banco vazio. Locks aguardam ate 10 segundos. Reexecucao substitui relatorios, nao duplica atividades. O banco de origem nao e alterado.

```
python -B -m rpa.robot
python -B -m rpa.robot --db data/acolhe.db --output rpa/output
python -B -m unittest rpa.test_robot -v
```

Regras: correct=1 indica acerto; outros valores contam como tentativa sem acerto. Precisao=acertos/tentativas; zero tentativas produz 0. Nenhum ID de sessao/tentativa e exportado. Relatorio e agregado, mas grupos pequenos ainda podem revelar contexto; manter em acesso local restrito e definir retencao antes de uso real. Nao ha e-mail, upload, mensagem, tomada de decisao ou sistema externo no processo. O log acumula metadados tecnicos; equipe deve definir rotacao/retencao no uso real.

## BPMN textual
Inicio -> validar banco -> gateway banco existe?
Nao -> registrar erro -> fim com falha.
Sim -> ler/agregar somente leitura -> gateway consulta funcionou?
Nao -> registrar erro -> fim com falha.
Sim -> gerar relatorios locais -> registrar sucesso -> fim com sucesso.
Modelo BPMN 2.0 sem coordenadas graficas em processo.bpmn, importavel em modeladores que suportem auto-layout. O robo executa a logica Python; o XML documenta o processo.

## Fluxo completo demonstrado (2026-11-14)
```
python -B -m rpa.demo_e2e --evidence rpa/evidence       # app real -> robo -> MVP
python -B -m rpa.robot --every 3600                       # agendamento embutido (a cada hora)
```
`demo_e2e.py` sobe o servidor HTTP real, cria sessoes e responde o quiz pela API, roda o robo sobre o mesmo SQLite e le `/api/automation`, a mesma rota que o painel "Acompanhamento automatico" exibe. Ele registra tres cenarios:
1. Sucesso: 5/5 acertos, decisao `progresso_adequado`; o MVP mostra os mesmos totais.
2. Decisao: 3 erros em `mobilidade` deixam a licao abaixo de 60% de acerto (com pelo menos 3 tentativas), o status vira `reforco_recomendado` e a licao aparece para revisao no painel.
3. Falha: banco inexistente gera `FileNotFoundError` e `report_failed` no log, sem criar banco; o MVP continua servindo o ultimo relatorio valido.
A evidencia fica em `rpa/evidence/<timestamp>/` (e2e.json, robot.log, progress.md). Sao respostas roteirizadas da equipe, nao dados de criancas.

Agendamento: `--every N` repete a cada N segundos, e `--runs` limita o numero de execucoes. Para usar o agendador do sistema, rode no Windows `schtasks /Create /SC HOURLY /TN AcolheRPA /TR "python -B -m rpa.robot"` com a pasta do projeto como diretorio de trabalho, ou no Linux uma linha de cron. O agendamento no sistema nao foi ativado por esta equipe.
`processo.bpmn` agora traz o gateway da regra de negocio e coordenadas BPMNDI; abre direto em bpmn.io ou no Camunda Modeler para o print do PDF.

## Testes e aceite
Os testes usam banco temporario sintetico. Verificam calculo e ausencia de IDs no arquivo, mais falha por banco inexistente sem criar banco. Para evidencia integrada: inicie app, responda quiz, rode comando acima, confira totais e log. Nao apresentar o teste sintetico como execucao com dados de usuarios reais. Pendencias: captura em video, avaliacao do professor sobre Python em substituicao a ferramenta RPA, e agendamento apenas se solicitado.

## Idioma por atividade
Novas tentativas guardam o idioma selecionado no envio. O relatorio usa esse idioma sem reclassificar respostas anteriores quando a interface muda entre PT e ES. Bancos antigos sem a coluna continuam legiveis e usam o idioma inicial da sessao; nao e possivel reconstruir trocas antigas nao registradas.
