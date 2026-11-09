# Acolhe: plano de implementação

Objetivo: PWA PT/ES integrada para acolhimento linguístico e mobilidade segura, com evidências honestas por disciplina.
Arquitetura: Python 3.12 stdlib, SQLite local, frontend HTML/CSS/JS sem dependências, módulos de IA/dados/robô desacoplados. Originais preservados na pasta pai.

1. Testar e implementar sessão pseudônima, lições e tentativas validadas.
2. PWA acessível com cinco lições, progresso, assistente de mobilidade e painel. Offline oferece lições; gravação exige rede e não finge sincronização.
3. Integrar serviços GenAI, visão, robô simulado, ouro e RPA. Não confundir fallback com LLM nem sintético com dados reais.
4. Testar API real HTTP, limites, arquivos estáticos, privacidade e segurança.
5. Preparar documentação e infraestrutura; registrar quais executaram e quais dependem de conta, hardware, modelo/dataset ou publicação.

Revisão: sessão inválida, envio repetido, resposta errada, caminho fora do static, JSON malformado, endpoint sem modelo, leitura ouro ausente, rede offline.
