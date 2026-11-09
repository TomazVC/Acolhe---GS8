# Visão: vocabulário por objetos

## Estado real
12 classes definidas; contrato de inferência e workflow de treino preparados.
**Nenhum treinamento, checkpoint customizado, métrica de detecção ou inferência real foi executado.** A API retorna indisponível, nunca uma detecção fictícia.
Python global não tem torch/Pillow/ultralytics. PyYAML 6.0.3 foi instalado apenas em vision/.test-deps para validar o parser em testes, não no Python global. O venv CP5 histórico não inicia. Dataset Food101 encontrado localmente é inadequado às classes e não foi usado como evidência.

## Classes e segurança
Mochila, cadeira, livro, garrafa, copo, colher, garfo, tigela, relógio, guarda-chuva, ônibus e semáforo.
Labels em PT/ES em service.py. Caderno não está coberto por book; será expansão com dados próprios.
Semáforo é apenas um objeto para vocabulário: não inferimos sua cor, permissão de travessia nem rota segura. Sem reconhecimento facial, identidade ou gravação de imagens.

## Dataset real necessário
Candidato: COCO 2017 (https://cocodataset.org/#download). As 12 classes existem no COCO.
**Candidato ainda não baixado nem licenças individuais verificadas.** Anotações COCO usam CC-BY-4.0; fotografias têm licenças próprias, portanto verificar o campo licenses de cada imagem antes de reutilizar/distribuir. Não declarar todas as fotografias CC-BY.
Planejamento: filtrar classes, selecionar imagens com licença compatível, manter créditos/image_id/source/license em inventário; remapear categorias para 0..11, converter caixas para YOLO normalizado, remover duplicatas.
Separar por image_id antes de augmentations: treino/validação/teste 70/15/15 com seed 42; não reaproveitar teste para tuning. Auditar distribuição por classe/ambiente e evitar imagens identificáveis de crianças.
Copiar dataset.example.yaml e provenance.example.json e preencher com evidências reais. O exemplo contém real_images=false de propósito.

## Execução quando dependências/dados estiverem disponíveis
```powershell
python -m unittest vision.tests.test_service
# Em ambiente aprovado com PyTorch apropriado e dependências de requirements.txt:
python -m vision.train --dataset vision/data/dataset.yaml --provenance vision/data/provenance.json --epochs 40
```
Treino usa transferência de yolo11n.pt, seed 42 e teste separado. O Ultralytics pode obter pesos oficiais na primeira execução; revisar compatibilidade da licença AGPL/comercial com a distribuição. Treino customizado é obrigatório; pesos COCO sozinhos não cumprem a entrega.
Resultados reais vão a runs/ e artifacts/. O script grava hash do checkpoint/dataset, procedência e métricas do conjunto teste. A pasta de saída de artefatos deve ser inexistente: a reserva exclusiva falha se já houver qualquer diretório com esse nome. Use --output vision/artifacts-experimento-02 para outro experimento. Arquivos finais são abertos exclusivamente, sem sobrescrever. Uma execução interrompida pode deixar uma pasta parcial; ela não será reutilizada automaticamente.

## Serviço e avaliação
status() só informa ready=true após verificar manifesto JSON, trained_on_real_images=true, ordem das classes, SHA-256 do checkpoint, dependências, carregamento por YOLO e nomes das classes do próprio modelo. Isso não comprova qualidade: quality_validated permanece false. predict(bytes) repete as verificações antes da inferência.
Em caso de ausência: ModelUnavailable. Com checkpoint: objetos, caixas, confiança e traduções; limiar 0,5, limite de arquivo 8 MiB/20 megapixels, sem armazenamento. Dependências ausentes também impedem inferência.
Antes da entrega acadêmica: confirmar classes do YAML correspondem à procedência; contar imagens/objetos por split; mAP50/mAP50-95, precisão/recall por classe; matriz de confusão; cinco erros reais com imagens licenciadas; testar luz baixa/oclusão e objetos não conhecidos. Esses resultados **estão pendentes**.


## Proteções verificadas em 2026-11-07

O YAML é carregado com PyYAML SafeLoader, recusando chaves duplicadas. names deve ser uma lista na ordem de service.LABELS ou um mapa com IDs inteiros 0..11 e os mesmos nomes nessa ordem. Não aceita IDs em texto, classes extras, faltantes, duplicadas ou reordenadas. nc, quando presente, deve ser o inteiro 12. train, val e test precisam ser declarados; a procedência deve listar as mesmas classes em ordem. Essas verificações precedem a construção do modelo e qualquer obtenção de pesos.

Ainda não há auditoria automática de pixels, licenças, contagens ou sobreposição dos splits. O campo real_images é uma declaração de procedência, não prova independente de curadoria. O hash detecta alterações no checkpoint, não autentica sua origem. Usar somente checkpoints locais próprios e confiáveis. status carrega o modelo para verificar compatibilidade, podendo consumir tempo e memória; a checagem não executa uma imagem de teste.

Teste completo executado com PyYAML isolado: 55 testes passaram, sem skips, em 5,392 s. Os testes do carregador de modelo usam stubs deliberadamente; não representam execução de YOLO real. Sem treino, inferência real ou métricas de qualidade.

Comando reproduzível a partir da raiz:

```powershell
python -B -c "import sys,unittest;sys.path.insert(0,'vision/.test-deps');suite=unittest.defaultTestLoader.discover('.');r=unittest.TextTestRunner(verbosity=2).run(suite);sys.exit(not r.wasSuccessful())"
```

Sem PyYAML, somente o teste de parser YAML é explicitamente ignorado; os demais testes não precisam da stack de treinamento. Copias anteriores dos dois módulos estão em arquivos .py.before-guards, excluídos de versionamento.
