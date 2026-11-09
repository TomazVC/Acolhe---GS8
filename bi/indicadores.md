# Indicadores do Acolhe

Nenhum valor de impacto é assumido neste arquivo. As definições abaixo orientam a coleta e a interpretação. O relatório RPA atual fornece somente os agregados que realmente constam em sua saída.

## Indicadores disponíveis no relatório local

**Sessões registradas:** contagem de linhas de sessão no banco consultado. Unidade: sessões. Não representa crianças únicas nem pessoas atendidas. Informar início e fim do período ou dizer que é o total acumulado do banco de demonstração.

**Tentativas registradas:** contagem das tentativas persistidas. Unidade: tentativas. Reenvios e repetições exigem regra explícita antes de comparar períodos.

**Acertos:** soma das tentativas marcadas como corretas. Unidade: tentativas corretas. Acerto pode resultar de repetição ou acaso; não equivale a palavra aprendida.

**Taxa de acerto:** acertos / tentativas. Unidade: percentual. Quando tentativas = 0, mostrar “sem tentativas” no painel. A saída técnica pode armazenar zero para evitar divisão por zero; isso não significa desempenho de 0% observado.

**Tentativas por idioma:** contagem de tentativas agrupadas pelo idioma selecionado no envio de cada atividade. Trocar PT/ES não reclassifica tentativas anteriores. Registros antigos sem idioma por tentativa usam o idioma original da sessão como fallback; mudanças históricas não registradas não podem ser reconstruídas. Idioma selecionado não comprova nacionalidade, língua materna ou origem migratória.

## Indicadores propostos que exigem coleta adicional

**Conclusão de lição:** sessões que completaram todas as atividades obrigatórias de uma lição / sessões que iniciaram essa lição. Requer regra de início e conclusão e tratamento de repetição.

**Retenção semanal:** sessões ou participantes elegíveis com atividade na semana seguinte / total elegível na semana inicial. A unidade precisa ser estável. Com identificadores descartáveis não é possível inferir retenção de pessoas. Definir semana, fuso, janela e base legal antes de coletar identidade persistente.

**Tempo ativo:** soma dos intervalos com evidência de interação, excluindo inatividade por regra documentada. Não usar apenas tempo entre abrir e fechar página como atenção da criança.

**Aprendizagem:** comparação pedagógica de tarefas equivalentes antes e depois, revisadas por educador. Depende de desenho de avaliação; não pode ser calculada honestamente apenas a partir do log atual.

**Disponibilidade do serviço:** verificações bem-sucedidas / verificações esperadas em janela definida. Requer monitor externo ou coleta de uptime verificável. Não confundir com disponibilidade de LLM ou câmera.

## Leitura de dados públicos

Uma contagem de registros migratórios não equivale automaticamente à quantidade de crianças que precisam do produto. Fontes com unidade municipal e fontes de atendimentos não devem ser unidas como se fossem registros individuais. Documentar chave, período, granularidade, duplicidade e cobertura antes de tirar conclusões.

Dados sintéticos precisam de rótulo visível em gráficos e exportações. Dados reais agregados exigem fonte, licença, data de extração e transformação. Não combinar dados observados e sintéticos em um mesmo total sem separação explícita.

## Perguntas para validar o negócio

1. Qual instituição enfrenta o problema e possui orçamento?
2. Quem decide e quem opera o produto no dia a dia?
3. Qual resultado pedagógico é útil e mensurável sem exposição indevida?
4. Que infraestrutura existe no local e como o MVP funciona sem internet?
5. Quais custos de hardware, suporte e manutenção foram realmente levantados?
6. Que evidência permitiria iniciar, ajustar ou interromper um piloto?

A equipe ainda precisa responder essas perguntas com pesquisa real. Não há preço, contrato, parceria ou previsão de receita confirmados.
