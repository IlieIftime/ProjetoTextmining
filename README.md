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
├── app.py              # Ponto de entrada da aplicação
└── requirements.txt    # Dependências do projeto
```

## Setup

## Setup

### 1. Instale o Git LFS:
  ```bash
   git lfs install
   ```

### 2. Clone o repositório (o Git LFS irá buscar automaticamente os ficheiros grandes):
 ```bash
git clone https://github.com/IlieIftime/ProjetoTextmining.git
cd ProjetoTextmining
   ```

### 3.  Clonar os dataset para correr o notebook:
  ```bash
   git lfs pull
   ```

### 4. Crie um ambiente virtual:
   ```bash
   python -m venv .venv
   ```

### 5. Ative o ambiente virtual:
   Windows:
   ```bash
   .venv\Scripts\activate
   ```

   Linux/Mac:
  ```bash
  source .venv/bin/activate
  ```

### 6. Instale as dependências:
```bash
pip install -r requirements.txt
```

### 7. Execute a aplicação:
```bash
python app.py
```

   
