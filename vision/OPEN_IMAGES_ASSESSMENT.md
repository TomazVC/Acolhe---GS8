# Avaliação verificável de Open Images V7

Data: 2026-11-07. Pesquisa de metadados oficiais, sem download de fotografias e sem treinamento.

## Resultado

Open Images V7 é candidato parcial para as classes atuais. O CSV oficial de classes com bounding boxes corresponde a 11 dos 12 nomes de vision/service.py. Não existe classe exata Cup. Coffee cup, Mug e Measuring cup têm significados mais específicos e não devem ser renomeados silenciosamente para copo/vaso. O COCO continua candidato mais direto para preservar o contrato atual, mas suas licenças individuais ainda precisam ser verificadas.

## Verificação reproduzível

Foi lido por HTTPS o CSV oficial https://storage.googleapis.com/openimages/v7/oidv7-class-descriptions-boxable.csv e contado o arquivo de caixas de validação indicado pela página V7: https://storage.googleapis.com/openimages/v5/validation-annotations-bbox.csv . A versão v5 no caminho é o link fornecido pela página V7, não uma versão presumida.

Classe | MID | Imagens de validação | Caixas
--- | --- | ---: | ---:
backpack | /m/01940j | 24 | 32
chair | /m/01mzpv | 311 | 827
book | /m/0bt_c3 | 95 | 720
bottle | /m/04dr76w | 207 | 498
cup | ausente | não aplicável | não aplicável
spoon | /m/0cmx8 | 52 | 73
fork | /m/0dt3t | 37 | 50
bowl | /m/04kkgm | 49 | 82
clock | /m/01x3z | 21 | 24
umbrella | /m/0hnnb | 27 | 35
bus | /m/01bjv | 82 | 103
traffic light | /m/015qff | 22 | 65

Contagens incluem todos os registros dessas classes, antes de filtros IsGroupOf, IsDepiction e qualidade. Imagens podem aparecer em mais de uma classe; não somar como imagens únicas. Estas contagens não representam fotografias baixadas ou aprovadas para uso.

## Licença e privacidade

A documentação oficial declara anotações CC BY 4.0 e imagens listadas como CC BY 2.0, mas expressamente não garante a licença de cada imagem. Fonte: https://storage.googleapis.com/openimages/web/factsfigures_v7.html#licenses .

Antes de usar uma foto, verificar a licença na página original e guardar ImageID, OriginalLandingURL, autor, título, licença, data de verificação e hash do arquivo. O CSV de informações fornece esses campos, mas sua presença não equivale à verificação individual. Não foi aprovada nenhuma fotografia nesta investigação. Excluir cenas identificáveis de crianças; imagens sem marcação Person não garantem ausência de pessoas. Fazer inspeção visual antes da inclusão.

## Ambiente e modelo

Python 3.12.10. GPU detectada por nvidia-smi: NVIDIA GeForce RTX 3050 6GB Laptop GPU, 6144 MiB. Não instalados no Python verificado: torch, ultralytics, Pillow, FiftyOne e PyYAML. Nenhuma instalação foi realizada.

O script atual usa YOLO11n com pesos yolo11n.pt. A documentação oficial confirma suporte a treino e validação: https://docs.ultralytics.com/models/yolo11/ . Revisar AGPL-3.0 e eventual licença Enterprise antes de distribuição, sem presumir que uso acadêmico elimina obrigações: https://www.ultralytics.com/license . Nenhum termo foi aceito, nenhuma conta criada e nenhum peso obtido.

## Testes executados e pendências

python -B -m unittest vision.tests.test_service -v: 3 testes passaram. Isso só comprova os contratos testados, não detecção real, qualidade nem treinamento.

Não houve treino, inferência real ou cálculo de mAP. Para avançar: selecionar dataset que cubra as 12 classes sem alterar semântica; curar licenças e privacidade por fotografia; reservar splits sem duplicatas; preparar ambiente isolado com dependências oficiais; rodar treino pequeno de diagnóstico e avaliação, mantendo-o separado de um modelo validado.

Riscos encontrados por leitura, ainda sem alteração de código: train.py compara conjuntos de nomes na procedência mas não verifica ordem/nome no YAML; status() considera pronto apenas pela existência de dois arquivos; a cópia final de best.pt e model_manifest.json pode sobrescrever artefatos anteriores. Endurecer esses pontos antes de promover um experimento ao serviço. O script exige as 12 classes; não contornar essa verificação para encaixar um subconjunto incompleto.


Atualização posterior: as três fragilidades de código descritas acima foram corrigidas em train.py e service.py, com regressões e suíte completa de 55 testes aprovada. Ver README.md desta pasta. Os bloqueios de dataset, curadoria, dependências de treinamento e ausência de métricas reais permanecem.
