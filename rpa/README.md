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

## Testes e aceite
Os testes usam banco temporario sintetico. Verificam calculo e ausencia de IDs no arquivo, mais falha por banco inexistente sem criar banco. Para evidencia integrada: inicie app, responda quiz, rode comando acima, confira totais e log. Nao apresentar o teste sintetico como execucao com dados de usuarios reais. Pendencias: captura em video, avaliacao do professor sobre Python em substituicao a ferramenta RPA, e agendamento apenas se solicitado.

## Idioma por atividade
Novas tentativas guardam o idioma selecionado no envio. O relatorio usa esse idioma sem reclassificar respostas anteriores quando a interface muda entre PT e ES. Bancos antigos sem a coluna continuam legiveis e usam o idioma inicial da sessao; nao e possivel reconstruir trocas antigas nao registradas.
