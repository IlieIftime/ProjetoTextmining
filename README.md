# AI/Human Text Analysis Studio

## Visão Geral
Aplicação web de análise linguística para distinguir texto gerado por IA de texto humano. O projeto utiliza um backend Python com modelos de Machine Learning e um frontend interativo construído com Plotly Dash.

## Estrutura do Projeto
```
/ai_human_studio/
│
├── assets/             # Dados estáticos, CSS, imagens e exportações de dados
├── models/             # Modelos treinados (arquivos grandes)
├── config/             # Configurações globais
│   └── settings.py     # Mapeamento de artefatos e carregamento de dados
├── core/               # Lógica de negócio e backend
│   ├── analysis_engine.py
│   └── model_loader.py
├── pages/              # Páginas da aplicação Dash
│   ├── analyzer.py
│   ├── model_lab.py     
│   └── study_summary.py
|── Copyright.txt
|── estudo_text_mining_samples2.ipynb
├── app.py              # Ponto de entrada da aplicação
└── requirements.txt    # Dependências do projeto
```

## Setup

1. Crie um ambiente virtual:
   ```bash
   python -m venv .venv
   ```

2. Ative o ambiente virtual:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Execute a aplicação:
   ```bash
   python app.py
   ```
## PS: caso dê erro na linha de run.app_server(debug=True) trocar por app.run(debug=True)
#### Instruções para clonar o repositório e obter ficheiros grandes 
## PS2: Colocar a pasta do projeto no utilizador ou ambiente de trabalho de maneira que não fique várias pastas sobrepostas
Resumo  

##### Os ficheiros grandes do projeto (modelos e CSVs) são geridos com Git LFS. Para obter os ficheiros de csv (datasets) deve ter Git LFS instalado ou executar um passo adicional para baixar os ficheiros LFS.

### 1. Instalar Git LFS (uma vez, se não estiver instalado)
```bash
git lfs install
```
 ### 2. Clonar o repositório (somente se não tiver realizado este passo como 1º passo)
git clone https://github.com/IlieIftime/ProjetoTextmining.git 
```bash
cd ProjetoTextmining
```
 ### 3. Baixar os ficheiros LFS (se quiser obter os datasets para correr o estudo do jupyter notebook)
```bash
git lfs pull
```