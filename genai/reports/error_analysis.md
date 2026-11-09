# Cinco erros observados de recuperação

Execução: python -m genai.execute_notebook. Evidência completa: retrieval.json e notebook 01_retrieval.ipynb. O conjunto contém 16 perguntas manuais; as cinco abaixo retornaram lista vazia. Recall@1 e Recall@3 = 11/16 = 0,6875.

1. "Posso ir para o outro lado?" → esperado crossing. Paráfrase não contém rua/travessia; falta compreensão semântica. Mitigação proposta: embeddings multilíngues e pergunta de esclarecimento sem orientar deslocamento.
2. "Cadê quem estava comigo?" → esperado lost. Situação de separação implícita. Mitigação: adicionar variantes revisadas por responsáveis e testar ambiguidade.
3. "Quero me acomodar" → esperado chair. Sinonímia sem tokens compartilhados. Mitigação: recuperação semântica e avaliação de falsos positivos.
4. "Preciso me hidratar" → esperado bottle. Necessidade não nomeia objeto. Mitigação: cobrir relações funcionais em corpus revisado, sem presumir condições de saúde.
5. "Saludamos al amanecer" → esperado greeting. Paráfrase espanhola fora do vocabulário do corpus. Mitigação: ampliar revisão bilíngue.

São falhas reais executadas do recuperador, não erros de LLM. As mitigações não foram implementadas ou medidas. A avaliação é pequena e construída pela equipe, sem generalização estatística.
Um caso positivo, "Onde coloco meu estojo?", recupera mochila por sobreposição lexical de "meu", um indício de correspondência espúria. Revisar stopwords e adicionar negativos antes de aumentar a confiança nas métricas.
