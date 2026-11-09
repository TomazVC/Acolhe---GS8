# Robô Acolhe: integração segura derivada do Talos

## Equipe

- Tomáz Versolato Carballo — RM 551417
- Rony Ken Nagai — RM 551549
- Aksel Viktor Caminha Rae — RM 99011
- Ian Xavier Kuraoka — RM 98860

## Estado real e limite de entrega
Software simulado funcional; hardware NÃO validado. Na última sessão Talos, ACKs foram recebidos mas o usuário relatou que nenhum motor se moveu. Não inferir movimento por ACK, não aumentar tensão/PWM/pulsos para tentar corrigir. Nenhuma porta serial foi aberta e nenhum firmware foi gravado nesta entrega. O gateway rejeita qualquer modo diferente de `simulate`.

## Fluxo e IA
A aplicação avalia a resposta educacional e chama `robot.service.react(correct, present)`. Acerto representa braço/motor2; nova tentativa representa cabeça/motor1, sempre com mensagem encorajadora. A presença modifica `learning_mode` e `ai_context`: ausente pausa a interação e devolve ação stop. Esses campos servem como contexto de entrada ao tutor; não são inferência emocional ou diagnóstico. O LLM não recebe acesso a GPIO/comandos seriais. O resultado inclui `simulated: true` e `physical_verified: false`.

Executar na raiz:

    python -m unittest robot.test_robot -v
    python -m robot.simulator --correct
    python -m robot.simulator --absent

Sete testes cobrem mapeamento, presença, tipos estritos e bloqueio de modo físico. A simulação de presença não é leitura de sensor real.

## Hardware e sensor adicional proposto
Base Uno + L298N + motores DC + LCD1602 paralelo. Pinagem preservada do Talos: cabeça ENA D5 / IN1 D2 / IN2 D3; braço ENB D6 / IN3 D4 / IN4 D7. LCD RS D8, E D9, D4..D7 em D10..D13. Proposta adicional: PIR de saída digital compatível com Uno em A0; VCC e GND conforme especificação do modelo adquirido. PIR detecta movimento, não prova presença estática. Considerar atraso de aquecimento e perda de detecção antes de integrar fisicamente.

`firmware/acolhe_safe/acolhe_safe.ino` é uma referência independente, não substitui o firmware Talos existente. Serial 9600: `?` versão, `p` presença, `y` acerto, `n` nova tentativa, `x` parada. Motores permanecem LOW em todos os caminhos, inclusive boot. LCD exibe feedback, porém o funcionamento real também está pendente. Compilar e gravar só em sessão separada autorizada; esta fonte não foi compilada.

## Checklist físico antes de qualquer habilitação
1. Fotografar montagem real e identificar ponte H, visor, motores e bateria.
2. Medir alimentação, continuidade de GND e confirmar jumpers ENA/ENB e regulador com documentação do módulo. Não conectar duas fontes 5V concorrentes.
3. Validar LCD/contraste e sensor isoladamente, com supervisão e sem alimentação de motores.
4. Implementar parada física e proteção mecânica; manter pessoas afastadas das partes móveis.
5. Após autorização, criar adaptador serial separado com handshake exato, timeout, limitação de frequência e fail-safe. Não interpretar texto livre do LLM como comando.
6. Só então testar microgestos supervisionados. Talos anterior usava PWM160/35ms, sem encoder: não garante ângulo nem retorno. Não reutilizar esses valores sem verificar a montagem.

## Evidência de entrega
Testes Python e CLI simulada executados localmente. Firmware, PIR, LCD e motores: pendentes de bancada. Vídeo real e fotos de montagem: pendentes. Não apresentar a simulação como demonstração física.
