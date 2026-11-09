# COCO: auditoria e viabilidade de treino

Verificação em 2026-11-07, no computador Tomáz. Nenhum treino executado.

## Evidências obtidas

A GPU RTX 3050 6 GB estava acessível, com 5864 MiB livres na consulta. Esse hardware é candidato a um experimento YOLO11n com batch pequeno, mas CUDA/PyTorch e consumo efetivo ainda não foram testados. Não instalar a stack pesada antes de ter dados aprovados evita um download sem treino viável.

O endpoint HTTPS images.cocodataset.org falhou por certificado incompatível com o hostname. A verificação TLS não foi desativada. Usou-se o espelho fast.ai listado oficialmente em https://registry.opendata.aws/fast-ai-coco/ com HTTPS válido: https://fast-ai-coco.s3.amazonaws.com/annotations_trainval2017.zip .

O membro annotations/instances_val2017.json foi obtido por intervalos HTTP, com validação ZIP/CRC pelo zipfile: somente 6.529.779 bytes transferidos do arquivo remoto de 252.907.541 bytes. Metadados locais: 19.987.840 bytes, 5000 imagens e 36781 anotações. SHA-256: e8c7f7908f1d7278341fae127d0da654f102f11bd7b21d8aeefa635b8c810b6f.

As 12 classes do serviço existem no COCO. Filtrar licença 4 (CC BY 2.0 declarada no dataset), ausência de anotação person e caixas não crowd deixa candidatas: mochila 0; cadeira 40; livro 17; garrafa 25; copo 24; colher 18; garfo 18; tigela 42; relógio 23; guarda-chuva 6; ônibus 4; semáforo 11. Não somar como imagens únicas. Ausência de anotação person não prova ausência de pessoas.

## Uma foto verificada individualmente

COCO image_id 1993, Flickr 3223600591, Hôtel Le Priori, autor Joe Shlabotnik. Página original: https://www.flickr.com/photos/joeshlabotnik/3223600591/ . O objeto ImageObject da página declarou https://creativecommons.org/licenses/by/2.0/ . Foram guardados URL, autoria, evidência estruturada da licença, horário de verificação e hashes. Uma foto de 186781 bytes foi baixada para inspeção: quarto com cadeiras, cama e mesa, sem pessoas visíveis. A foto continua fora do treino: conferir tamanho/recorte em relação às caixas COCO e completar os splits primeiro.

Os arquivos estão em vision/data/coco-audit-20261107. O diretório contém metadados, lista de candidatas e a foto review-3223600591.jpg com seu JSON de procedência. Não redistribuir sem os créditos e condições aplicáveis. Anotações COCO: CC BY 4.0; fotografias têm licenças próprias. Fonte: https://cocodataset.org/dataset/termsofuse.htm .

## O que falta para um treino honesto

A amostra ainda não cobre todas as classes. O filtro CC-BY sem pessoas anotadas não fornece mochilas no val2017. É necessário ampliar a curadoria para o treino original, ou revisar individualmente fotos com adultos e excluir crianças, ou coletar fotos próprias autorizadas. Não renomear classes nem repetir a mesma fotografia em splits para contornar essa falta.

Não houve instalação de PyTorch/Ultralytics, obtenção de pesos, criação de contas, publicação, treinamento, inferência real ou métricas de detecção. A presença de GPU e de metadados não comprova um modelo. Um piloto futuro deve ser rotulado como diagnóstico, com seed e hashes registrados, antes de qualquer avaliação de qualidade.
