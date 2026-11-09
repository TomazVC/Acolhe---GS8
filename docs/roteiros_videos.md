# Roteiros dos vídeos técnicos

Roteiros para gravação, não evidências de execução. Ajustar a fala ao estado real dos componentes e ensaiar com cronômetro.

# RPA até três minutos

## 0min00s a 0min25s Processo

Mostrar nome do projeto e objetivo: consolidar o progresso agregado do banco local sem cadastro nominal e sem envio externo. Explicar que o fluxo usa Python, leitura SQL e arquivos de saída. Mostrar PDD e BPMN quando preparados pelo módulo RPA.

## 0min25s a 0min55s Entradas e condições

Mostrar o banco de demonstração criado pelo MVP, sem revelar identificadores de sessões. Explicar as entradas: banco SQLite existente e pasta de saída. Indicar que o acesso é de leitura e que a pasta precisa permitir gravação. Identificar os dados como sintéticos.

## 0min55s a 1min40s Execução válida

Executar, na raiz do projeto:

`python -m rpa.robot --db data/acolhe.db --output rpa/output`

Mostrar o código de saída, `progress.json`, `progress.md` e `robot.log`. Comparar um agregado com o estado conhecido do banco. Mostrar data de geração e os registros `report_started` e `report_completed`. Explicar que sessão não é pessoa e taxa de acerto não comprova aprendizagem.

## 1min40s a 2min25s Falha controlada

Executar com um caminho de banco inexistente e uma pasta de saída separada de teste. Mostrar saída de erro e `report_failed`. Explicar como o operador identifica e corrige o caminho. Não apresentar um relatório antigo como resultado da execução que falhou.

## 2min25s a 2min50s Limites e encerramento

Mostrar a ligação entre processo, código, saídas e log. Dizer se o agendamento ainda está pendente. Não alegar envio semanal por e-mail: o fluxo atual gera arquivos locais. Terminar até 2min50s para margem.

## Evidências para guardar

Comando e versão, log completo, arquivos produzidos, cenário de falha, roteiro do processo e vídeo. Confirmar acesso ao link antes da entrega.

# Maker até seis minutos

## 0min00s a 0min35s Objetivo

Apresentar o robô tutor como apoio a atividades do Acolhe. Explicar que a reação ao erro deve ser uma dica ou incentivo. Não prometer acompanhamento autônomo de crianças.

## 0min35s a 1min20s Hardware

Mostrar os componentes físicos realmente montados: controlador, fonte/baterias, ponte H, motores e sensor adicional. Nomear o sensor e a grandeza medida. Explicar alimentação e limites. Motores e servos são atuadores, não sensores.

Se o sensor ainda não estiver montado, esta parte não está concluída. Uma imagem de circuito ou um simulador não satisfaz a demonstração física.

## 1min20s a 2min15s Sensor real

Mostrar a leitura real mudando com uma condição controlada e segura. Manter visíveis o componente e a leitura correspondente. Registrar unidade, limiar e tratamento de leitura inválida. Não movimentar o robô perto de crianças durante testes de bancada.

## 2min15s a 3min25s Integração com IA

Mostrar a atividade no app, evento enviado, informação usada pela IA e decisão produzida. Distinguir regra programada, recuperação de conteúdo e inferência de modelo. Se a IA não estiver ligada ao hardware, registrar isso como pendência, sem narrar a simulação como integração real.

## 3min25s a 4min35s Ação e retorno

Executar um caso de acerto e um caso de erro. Mostrar uma ação segura e um incentivo apropriado. Explicar como o mediador pode interromper. Evitar movimentos bruscos, força excessiva ou reação punitiva.

## 4min35s a 5min20s Falha e segurança

Demonstrar perda de comunicação ou leitura inválida em condição controlada. Mostrar parada ou estado seguro. Explicar timeout, limites mecânicos e supervisão. Nunca retirar proteção elétrica para encenar uma falha.

## 5min20s a 5min45s Conclusão

Recapitular sensor, decisão e ação efetivamente demonstrados. Exibir pendências restantes. Encerrar até 5min45s para margem.

## Evidências para guardar

Fotos da montagem, diagrama conferido, lista de componentes reais, versão do firmware, leituras com data/hora, eventos da aplicação, casos de segurança e vídeo. Não usar imagens de pessoas sem autorização. Não afirmar hardware concluído com base em testes do simulador.
