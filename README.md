# AI/Human Text Analysis Studio

Estudo de **text mining e classificação supervisionada** para analisar diferenças entre textos escritos por humanos e textos gerados por sistemas de inteligência artificial. O projeto combina um notebook de investigação com uma aplicação web interativa construída em Dash.

> **Aviso importante:** este é um projeto experimental e académico. As previsões dos modelos não constituem prova definitiva sobre a autoria de um texto. O desempenho depende do dataset, do pré-processamento, do domínio textual e dos modelos utilizados.

## Índice

- [Visão geral](#visão-geral)
- [Objetivos](#objetivos)
- [Estrutura do repositório](#estrutura-do-repositório)
- [Notebook de investigação](#notebook-de-investigação)
- [Dados](#dados)
- [Pré-processamento](#pré-processamento)
- [Modelos avaliados](#modelos-avaliados)
- [Avaliação e artefactos](#avaliação-e-artefactos)
- [Aplicação Dash](#aplicação-dash)
- [Instalação](#instalação)
- [Execução rápida](#execução-rápida)
- [Executar o notebook](#executar-o-notebook)
- [Executar a aplicação web](#executar-a-aplicação-web)
- [Configuração e modo de debug](#configuração-e-modo-de-debug)
- [Limitações e reprodutibilidade](#limitações-e-reprodutibilidade)
- [Licença e direitos de autor](#licença-e-direitos-de-autor)

## Visão geral

O repositório implementa um fluxo completo de análise de texto:

1. carregamento do dataset original, limpo ou de debug;
2. limpeza e normalização dos textos;
3. análise exploratória dos dados;
4. treino de vários modelos de classificação;
5. comparação através de métricas de avaliação;
6. análise de sensibilidade para textos de diferentes comprimentos;
7. exportação de métricas, tabelas, gráficos e modelos;
8. classificação de texto introduzido pelo utilizador;
9. visualização dos resultados através de uma aplicação Dash;
10. classificação de texto obtido a partir da web, quando a funcionalidade e a ligação de rede estão disponíveis.

O notebook apresenta o estudo metodológico completo. A aplicação Dash disponibiliza uma interface mais acessível para consultar resultados, explorar modelos e analisar textos.

## Objetivos

- Investigar se características lexicais e estatísticas permitem distinguir textos humanos de textos gerados por IA.
- Comparar representações textuais tradicionais, embeddings e modelos de aprendizagem automática.
- Avaliar o comportamento dos modelos com métricas como accuracy, precision, recall, F1-score e ROC-AUC, quando calculadas pelo notebook.
- Explorar diferenças de comprimento, vocabulário, diversidade lexical, POS tagging e entidades nomeadas.
- Disponibilizar uma interface para experimentar classificações e consultar os resultados do estudo.

## Estrutura do repositório

A estrutura principal atualmente utilizada pelo projeto é semelhante à seguinte:

```text
ProjetoTextmining/
├── app.py                         # Ponto de entrada da aplicação Dash
├── requirements.txt               # Dependências principais da aplicação
├── text_mining_study_VF.ipynb     # Notebook principal do estudo
├── README.md
├── Copyright.txt
├── data/                          # Dataset original
├── data_cleaned/                  # Dataset com texto pré-processado
├── data_debug/                    # Subsets menores para testes
├── assets/                        # Recursos da aplicação e artefactos exportados
│   ├── data_exports/              # CSVs e relatórios exportados
│   ├── models/                    # Alguns modelos treinados
│   ├── vectorizers/               # Vectorizers persistidos
│   └── top_completo/              # Rankings lexicais e coeficientes
├── models/                        # Outros modelos treinados
├── config/
│   └── settings.py                # Caminhos, artefactos e configuração global
├── core/                          # Lógica central da aplicação
├── pages/                         # Páginas da aplicação Dash
├── img/                           # Imagens utilizadas pela aplicação
└── .gitattributes / .gitignore
```

Algumas pastas podem conter ficheiros adicionais ou artefactos gerados durante a execução. Para confirmar a versão exata da estrutura, consulte sempre a árvore atual do repositório.

## Notebook de investigação

O ficheiro [`text_mining_study_VF.ipynb`](text_mining_study_VF.ipynb) está organizado nas seguintes fases:

1. introdução e definição do problema;
2. imports e configuração do ambiente;
3. carregamento do dataset;
4. limpeza e pré-processamento;
5. análise exploratória dos dados (EDA);
6. divisão em treino e teste;
7. treino de seis abordagens de modelação;
8. avaliação e comparação dos resultados;
9. análise de sensibilidade;
10. gráficos de treino e teste;
11. classificação de texto introduzido pelo utilizador;
12. gravação de gráficos, tabelas e modelos;
13. dashboards e classificação de texto obtido da web;
14. conclusões, limitações e possibilidades de trabalho futuro.

A execução completa pode ser demorada, especialmente durante a limpeza de centenas de milhares de textos, o treino dos modelos e o processamento linguístico adicional.

## Dados

O notebook procura os dados pelas seguintes localizações relativas à raiz do repositório:

| Caminho | Finalidade |
| --- | --- |
| `data/AI_Human.csv` | Dataset original |
| `data_cleaned/AI_Human_sample_cleaned.csv` | Dataset com a coluna `clean_text` pré-calculada |
| `data_debug/AI_Human_debug_subset.csv` | Subset menor para desenvolvimento e testes |

O dataset utilizado pelo notebook contém, pelo menos, as seguintes colunas:

| Coluna | Descrição |
| --- | --- |
| `text` | Texto original |
| `generated` | Variável-alvo: `0` para texto humano e `1` para texto gerado |
| `clean_text` | Texto normalizado para análise e modelação |

Numa execução registada no notebook, o dataset limpo tinha `487235` linhas e três colunas. Este valor é apenas uma observação daquela execução e pode mudar se os dados forem atualizados.

Os ficheiros de dados podem ser grandes. Quando aplicável, utilize Git LFS para obter os ficheiros completos:

```bash
git lfs install
git lfs pull
```

## Pré-processamento

A função `clean_text_english` aplica operações adequadas ao corpus em inglês:

- conversão para minúsculas;
- remoção de números;
- remoção de pontuação;
- normalização de espaços;
- remoção de stopwords do NLTK e do scikit-learn;
- remoção de tokens muito curtos;
- stemming com `SnowballStemmer("english")`.

O notebook recalcula atualmente a coluna `clean_text` durante a execução principal, mesmo quando essa coluna já existe. Para evitar trabalho desnecessário em execuções futuras, pode ser preferível utilizar diretamente o dataset limpo ou adaptar essa célula para respeitar uma flag de limpeza.

## Modelos avaliados

O estudo compara as seguintes abordagens:

| Modelo | Representação / técnica |
| --- | --- |
| Bag of Words + Logistic Regression | Frequência de termos e regressão logística |
| TF-IDF + LinearSVC | Pesos TF-IDF e classificador linear SVM |
| TF-IDF + Multinomial Naive Bayes | TF-IDF e Naive Bayes multinomial |
| Word2Vec + Logistic Regression | Embeddings Word2Vec agregados e regressão logística |
| TF-IDF + XGBoost | Features textuais e classificador XGBoost |
| TF-IDF + rede neuronal | Features textuais e uma rede neuronal Keras/TensorFlow |

Os nomes dos artefactos persistidos e alguns detalhes de configuração estão centralizados em [`config/settings.py`](config/settings.py).

## Avaliação e artefactos

O notebook calcula e/ou exporta resultados de avaliação, incluindo:

- accuracy, precision, recall e F1-score;
- matriz de confusão;
- curvas ROC e ROC-AUC, quando aplicável;
- relatórios de classificação;
- comparação final dos modelos;
- histórico de treino da rede neuronal;
- análise de sensibilidade para textos curtos e longos;
- rankings de tokens distintivos por classe;
- coeficientes relevantes dos modelos lineares;
- gráficos e tabelas para utilização no dashboard.

Os caminhos esperados para vários destes ficheiros estão definidos em `config/settings.py`, sobretudo em `assets/data_exports/`, `assets/top_completo/`, `assets/models/` e `assets/vectorizers/`.

Os valores de desempenho não são fixados neste README: dependem dos dados disponíveis, da configuração usada e da execução do notebook. Consulte os ficheiros exportados ou a página **Resumo do Estudo** da aplicação para os resultados concretos da execução atual.

## Aplicação Dash

A aplicação é inicializada por [`app.py`](app.py) e utiliza Dash, Dash Bootstrap Components e Plotly. A navegação inclui:

- **Analisador Interativo**: análise e classificação de texto;
- **Laboratório de Modelos**: exploração dos modelos e métricas;
- **Resumo do Estudo**: consulta dos principais resultados, gráficos e conclusões.

A configuração dos caminhos de dados, modelos e vectorizers encontra-se em [`config/settings.py`](config/settings.py). Os caminhos são construídos a partir da raiz do projeto, o que permite executar a aplicação a partir do repositório clonado.

## Instalação

### 1. Clonar o repositório

```bash
git clone https://github.com/IlieIftime/ProjetoTextmining.git
cd ProjetoTextmining
```

Se os dados ou modelos forem geridos por Git LFS:

```bash
git lfs install
git lfs pull
```

### 2. Criar e ativar um ambiente virtual

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Windows CMD:

```bat
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as dependências da aplicação

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

O `requirements.txt` cobre as dependências principais da aplicação Dash, incluindo pandas, Plotly, scikit-learn, TensorFlow, XGBoost, newspaper3k, requests e Beautiful Soup.

### Dependências adicionais do notebook

O notebook importa também bibliotecas que não estão todas declaradas no `requirements.txt`, incluindo componentes de NLTK, Gensim, spaCy, Matplotlib, Seaborn, WordCloud, tqdm, textstat, SHAP e `duckduckgo_search`.

Para executar todas as células do notebook, instale os pacotes adicionais necessários no mesmo ambiente, por exemplo:

```bash
python -m pip install matplotlib seaborn tqdm wordcloud nltk gensim spacy textstat shap duckduckgo_search
```

Depois, descarregue os recursos necessários do NLTK:

```bash
python -c "import nltk; nltk.download('stopwords')"
```

Algumas células podem também requerer um modelo spaCy ou recursos adicionais. Instale-os apenas se forem utilizados pela versão atual do notebook:

```bash
python -m spacy download en_core_web_sm
```

> Estas dependências adicionais são documentadas aqui para refletir o notebook atual; o ficheiro `requirements.txt` não é alterado por este README.

## Execução rápida

Para abrir a aplicação web:

```bash
python app.py
```

Depois, abra no navegador o endereço indicado pelo Dash, normalmente `http://127.0.0.1:8050/`.

Para abrir o notebook:

```bash
jupyter notebook text_mining_study_VF.ipynb
```

ou:

```bash
jupyter lab text_mining_study_VF.ipynb
```

## Executar o notebook

1. Garanta que está na raiz do repositório.
2. Confirme que existe pelo menos um dos ficheiros de dados esperados.
3. Instale as dependências principais e as dependências adicionais do notebook.
4. Abra `text_mining_study_VF.ipynb`.
5. Execute as células por ordem.
6. Para uma primeira execução, considere ativar o modo de debug antes de treinar todos os modelos.
7. Verifique os artefactos exportados antes de iniciar a aplicação Dash.

A execução integral pode consumir bastante memória e tempo. Recomenda-se guardar os resultados gerados e utilizar o dataset limpo quando possível.

## Executar a aplicação web

A partir da raiz do repositório e com o ambiente virtual ativo:

```bash
python app.py
```

A aplicação usa `use_pages=True`, pelo que as páginas disponíveis em `pages/` são descobertas pelo Dash. Para uma execução correta, mantenha a estrutura de diretórios e os artefactos esperados em `assets/`, `models/`, `data/` e `data_cleaned/`.

As funcionalidades que consultam artigos ou realizam pesquisa/web scraping podem depender de acesso à Internet, da disponibilidade do site remoto e da compatibilidade do conteúdo obtido.

## Configuração e modo de debug

No notebook, as principais flags de execução são:

```python
FAST_MODE = False
USE_DEBUG_DATASET = False
N_PER_CLASS = 225000
```

- `USE_DEBUG_DATASET = True`: utiliza `data_debug/AI_Human_debug_subset.csv` quando o ficheiro existe.
- `FAST_MODE = True`: cria um subset amostrado por classe a partir do dataset carregado.
- `N_PER_CLASS`: define o número máximo de exemplos por classe usados no subset.

Para desenvolvimento local, uma configuração mais pequena pode ser adequada:

```python
FAST_MODE = True
USE_DEBUG_DATASET = True
N_PER_CLASS = 1000
```

Depois de alterar estas flags, execute novamente as células de carregamento e de modelação para garantir que todos os resultados pertencem ao mesmo subset.

## Limitações e reprodutibilidade

- Um detector treinado neste dataset pode aprender características específicas do corpus em vez de generalizar para outros temas, autores, épocas ou modelos generativos.
- A classificação é probabilística e pode produzir falsos positivos e falsos negativos.
- A limpeza com stemming remove informação linguística e pode afetar a interpretabilidade.
- Os resultados dependem da divisão treino/teste, da amostragem, dos hiperparâmetros e das versões das bibliotecas.
- Os modelos não devem ser utilizados isoladamente em decisões académicas, profissionais, legais ou disciplinares.
- A análise web depende de rede, disponibilidade dos sites, robots.txt, estrutura HTML e qualidade do texto extraído.
- TensorFlow, XGBoost e bibliotecas NLP podem exigir versões compatíveis de Python e de dependências nativas.
- Para reproduzir resultados, mantenha os mesmos dados, flags, `random_state`, versões de bibliotecas e artefactos exportados.

Antes de interpretar os resultados, confirme se os ficheiros usados pela aplicação correspondem à mesma execução do notebook, especialmente `final_model_comparison.csv`, os relatórios de avaliação e os modelos persistidos.

## Licença e direitos de autor

Consulte [`Copyright.txt`](Copyright.txt) para as informações de direitos de autor fornecidas com o projeto. Se pretender reutilizar o código, os dados ou os artefactos treinados, verifique também as licenças dos respetivos datasets, bibliotecas e fontes externas.

## Estado do projeto

Projeto académico/de investigação em evolução. O notebook constitui a referência principal para o processo experimental; a aplicação Dash apresenta os resultados e disponibiliza funcionalidades interativas baseadas nos artefactos gerados.
