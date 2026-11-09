# GenAI: tutor bilíngue e mobilidade segura

## Estado real
Implementado e executado: recuperação lexical determinística, resposta curada offline, recusa, JSON e citações; avaliação e testes.
**Não executado: LLM local, comparação baseline/RAG/agente e avaliação humana.**
O serviço Ollama não iniciou no diagnóstico do ambiente (Access denied). Não foi contornada a restrição. O ambiente CP5 antigo aponta para Python WindowsApps que não inicia. Não existem pesos incluídos aqui.

## Rodar
Na raiz acolhe:
```powershell
python -m unittest genai.tests.test_service
python -m genai.evaluate
python -m genai.execute_notebook
```

Para usar um Ollama já configurado pelo usuário, com modelo disponível:
```powershell
$env:ACOLHE_OLLAMA_MODEL="nome-exato-do-modelo-local"
python -m genai.compare --model $env:ACOLHE_OLLAMA_MODEL
```
O cliente usa exclusivamente 127.0.0.1:11434. Não instala, baixa pesos, inicia serviço nem envia perguntas à nuvem. Não habilitar a variável até o servidor estar funcional.

## Contrato
`answer(question, language="pt")` aceita pt/es e devolve answer, sources, mode.
- retrieval_only: frase curada recuperada, **não é geração por LLM**.
- local_llm_rag: retorno do Ollama, JSON validado e IDs restritos aos documentos recuperados.
- refusal: entrada inválida, fora do escopo, proteção ou falha no LLM.
Falha no LLM nunca é substituída silenciosamente por texto curado.

## Experimentos
`compare.py` executa três variantes com o mesmo modelo/pergunta: sem contexto, RAG e agente de uma ferramenta. O agente pede ao LLM a escolha retrieve/refuse, executa a recuperação e registra o rastro. Sem Ollama, apenas reporta blocked; não inventa respostas.
O notebook 01_retrieval.ipynb tem outputs gerados por execução Python real. O notebook 02_local_llm.ipynb é um roteiro **não executado**, com outputs vazios.

Corpus: oito microlições autorais PT/ES, CC-BY-4.0, revisão pedagógica pendente. A fonte citada é o corpus autoral, não uma instituição externa. Conjunto de avaliação: 16 questões manuais, incluindo paráfrases difíceis. Não é benchmark independente, avaliação de factualidade ou prova de qualidade pedagógica.

## Limites de segurança e próximos passos
Filtros de termos não são garantia contra prompt injection ou alucinação. As citações validam IDs, não comprovam que cada frase é suportada. Para uso real com crianças: revisão humana do corpus e respostas, teste adversarial bilíngue, consentimento responsável e política de retenção. Não coletar endereço/nome/foto. Não usar para decisão de travessia ou navegação autônoma.
Completar: configurar LLM autorizado; executar todas as variantes sobre o mesmo conjunto; avaliar correção, suporte por fonte, JSON, recusa, latência; registrar pelo menos cinco erros **do LLM** após execução. Os erros atuais documentados são de recuperação, não de geração.
