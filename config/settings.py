# config/settings.py
from pathlib import Path
import pandas as pd

# --- PATHS ABSOLUTOS ---
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / 'assets'
MODELS_ORIGINAL_DIR = BASE_DIR / 'models'
DATA_EXPORTS_DIR = ASSETS_DIR / 'data_exports'

# --- MAPEAMENTO EXPLÍCITO DE CADA ARTEFACTO DE DADOS ---
DATA_PATHS = {
    # --- EDA ---
    'class_distribution': DATA_EXPORTS_DIR / 'eda_class_distribution.csv',
    'text_length_stats': DATA_EXPORTS_DIR / 'eda_text_length_stats.csv',
    'lexical_diversity_means': DATA_EXPORTS_DIR / 'eda_lexical_diversity_means.csv',
    'pos_tagging_means': DATA_EXPORTS_DIR / 'eda_pos_tagging_means.csv',
    'ner_stats': DATA_EXPORTS_DIR / 'eda_ner_stats.csv',
    
    # --- Rankings Extensivos ---
    'distinctive_ai': ASSETS_DIR / 'top_completo' / 'top_200_distinctive_tokens_ai.csv',
    'distinctive_human': ASSETS_DIR / 'top_completo' / 'top_200_distinctive_tokens_human.csv',
    'coeffs_ai': ASSETS_DIR / 'top_completo' / 'top_200_coefficients_ai.csv',
    'coeffs_human': ASSETS_DIR / 'top_completo' / 'top_200_coefficients_human.csv',
    
    # --- Avaliação de Modelos ---
    'model_comparison': DATA_EXPORTS_DIR / 'final_model_comparison.csv',
    'ann_history': DATA_EXPORTS_DIR / 'ann_training_history.csv',
    'sensitivity_short': DATA_EXPORTS_DIR / 'eval_sensitivity_short_texts.csv',
    'sensitivity_long': DATA_EXPORTS_DIR / 'eval_sensitivity_long_texts.csv',
}

# --- FUNÇÃO DE CARREGAMENTO ROBUSTO ---
def load_data(path, **kwargs):
    if not path.exists():
        if path.parent.name == 'data_exports':
             alt_path = path.parent.parent / path.name
             if alt_path.exists():
                 return pd.read_csv(alt_path, **kwargs)
        print(f"AVISO: Ficheiro de dados não encontrado: {path}.")
        return pd.DataFrame()
    try:
        return pd.read_csv(path, **kwargs)
    except Exception as e:
        print(f"ERRO ao ler {path}: {e}")
        return pd.DataFrame()

# --- CARREGAMENTO GLOBAL DE DADOS ---
DF_CLASS_DIST = load_data(DATA_PATHS['class_distribution'])
DF_LEN_STATS = load_data(DATA_PATHS['text_length_stats'])
DF_LEXICAL = load_data(DATA_PATHS['lexical_diversity_means'])
DF_POS = load_data(DATA_PATHS['pos_tagging_means'])
DF_NER = load_data(DATA_PATHS['ner_stats'])

DF_METRICS = load_data(DATA_PATHS['model_comparison'])
DF_ANN_HISTORY = load_data(DATA_PATHS['ann_history'])
DF_SENS_SHORT = load_data(DATA_PATHS['sensitivity_short'])
DF_SENS_LONG = load_data(DATA_PATHS['sensitivity_long'])

DF_DISTINCTIVE_AI = load_data(DATA_PATHS['distinctive_ai'])
DF_DISTINCTIVE_HUMAN = load_data(DATA_PATHS['distinctive_human'])
DF_COEFFS_AI = load_data(DATA_PATHS['coeffs_ai'])
DF_COEFFS_HUMAN = load_data(DATA_PATHS['coeffs_human'])

# --- MAPEAMENTO DE MODELOS (CORRIGIDO) ---
MODEL_PATHS = {
    'BoW + LogisticRegression': MODELS_ORIGINAL_DIR / 'bow_lr_model.joblib',
    'Word2Vec + LogisticRegression': MODELS_ORIGINAL_DIR / 'w2v_lr_model.joblib',
    'TF-IDF + NaiveBayes': MODELS_ORIGINAL_DIR / 'tfidf_nb_model.joblib',
    'TF-IDF + LinearSVC': MODELS_ORIGINAL_DIR / 'tfidf_svm_model.joblib', # Corrigido
    'SafeTFIDF + XGBoost': ASSETS_DIR / 'models' / 'xgb_safe_model.joblib', # Corrigido
    'SafeTFIDF + ANN': ASSETS_DIR / 'models' / 'ann_safe_model.keras',
}
VECTORIZER_PATH = ASSETS_DIR / 'vectorizers' / 'safe_vectorizer.joblib'

# --- CONFIGURAÇÕES GLOBAIS ---
MODEL_NAMES = [
    'BoW + LogisticRegression',
    'Word2Vec + LogisticRegression',
    'TF-IDF + NaiveBayes',
    'TF-IDF + LinearSVC',
    'SafeTFIDF + XGBoost',
    'SafeTFIDF + ANN'
]

MODEL_COLORS = {
    'BoW + LogisticRegression': '#1f77b4',
    'Word2Vec + LogisticRegression': '#ff7f0e',
    'TF-IDF + NaiveBayes': '#2ca02c',
    'TF-IDF + LinearSVC': '#d62728',
    'SafeTFIDF + XGBoost': '#9467bd',
    'SafeTFIDF + ANN': '#e377c2',
    # Variações
    'BoW+LogisticRegression': '#1f77b4',
    'Word2Vec+LogisticRegression': '#ff7f0e',
    'TFIDF+NaiveBayes': '#2ca02c',
    'TFIDF+LinearSVC': '#d62728',
    'SafeTFIDF+XGBoost': '#9467bd',
    'SafeTFIDF+ANN': '#e377c2'
}

# --- HELPER PARA ARQUIVOS DE DIAGNÓSTICO ---
def get_diagnostic_paths(model_name):
    """Retorna caminhos para CM e Report, lidando com variações de nome."""
    clean_name = model_name.replace(' ', '').replace('-', '')
    clean_name_plus = model_name.replace(' ', '').replace('-', '') 
    clean_name_no_plus = clean_name.replace('+', '') 
    
    cm_path = None
    for name in [model_name, clean_name, clean_name_plus, clean_name_no_plus]:
        p = DATA_EXPORTS_DIR / f'eval_cm_{name}.csv'
        if p.exists():
            cm_path = p
            break
            
    report_path = None
    for name in [model_name, clean_name, clean_name_plus, clean_name_no_plus]:
        p = DATA_EXPORTS_DIR / f'eval_report_{name}.txt'
        if p.exists():
            report_path = p
            break
            
    return cm_path, report_path

