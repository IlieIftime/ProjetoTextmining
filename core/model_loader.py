import joblib
import tensorflow as tf
from config import settings
import os

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
        if str(path).endswith('.keras') or str(path).endswith('.h5'):
            model = tf.keras.models.load_model(path)
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
