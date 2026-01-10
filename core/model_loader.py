import os
# Forçar compatibilidade com Keras 2 (necessário para carregar modelos antigos em TF 2.16+)
os.environ['TF_USE_LEGACY_KERAS'] = '1'

import sys
import joblib
import tensorflow as tf
from config import settings

# Aumenta o limite de recursão para carregar modelos complexos
try:
    sys.setrecursionlimit(3000)
    print("Limite de recursão aumentado para 3000.")
except (ValueError, RuntimeError):
    print("Aviso: Não foi possível aumentar o limite de recursão.")

_LOADED_MODELS = {}
_VECTORIZER = None

def load_vectorizer():
    global _VECTORIZER
    if _VECTORIZER is None:
        path = settings.VECTORIZER_PATH
        if path.exists():
            try:
                _VECTORIZER = joblib.load(path)
                print(f"Vectorizer carregado de {path}")
            except Exception as e:
                print(f"Erro ao carregar vectorizer: {e}")
        else:
            print(f"Vectorizer não encontrado em {path}")
    return _VECTORIZER

def load_model(model_name):
    global _LOADED_MODELS
    
    if model_name in _LOADED_MODELS:
        return _LOADED_MODELS[model_name]
    
    path = settings.MODEL_PATHS.get(model_name)
    if not path or not path.exists():
        print(f"Modelo {model_name} não encontrado em {path}")
        return None
        
    try:
        if 'XGB' in model_name:
            try:
                import xgboost
            except ImportError:
                print(f"AVISO: A biblioteca 'xgboost' é necessária para o modelo {model_name}. Instale com: pip install xgboost")

        if str(path).endswith('.keras') or str(path).endswith('.h5'):
            try:
                model = tf.keras.models.load_model(path)
            except Exception as e:
                print(f"Aviso: Falha no carregamento padrão de {model_name}. Tentando com compile=False... Erro: {e}")
                try:
                    model = tf.keras.models.load_model(path, compile=False)
                except Exception as e2:
                    print(f"ERRO CRÍTICO: Falha ao carregar {model_name}. O modelo será ignorado. Erro: {e2}")
                    return None
        else:
            model = joblib.load(path)
            
        _LOADED_MODELS[model_name] = model
        print(f"Modelo {model_name} carregado com sucesso.")
        return model
    except Exception as e:
        print(f"Erro ao carregar modelo {model_name}: {e}")
        return None

def get_available_models():
    return settings.MODEL_NAMES
