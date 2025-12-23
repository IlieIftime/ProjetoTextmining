import numpy as np
import pandas as pd
from core import model_loader
import re
import string

def clean_text_english(text):
    if not isinstance(text, str): return ""
    text = text.lower()
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    text = re.sub(r'<.*?>+', '', text)
    text = re.sub(r'[%s]' % re.escape(string.punctuation), '', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\w*\d\w*', '', text)
    return text

def analyze_text(text, model_name='BoW + LogisticRegression'):
    if not text or not text.strip(): return {'error': 'Texto vazio'}

    # --- TRATAMENTO ESPECIAL PARA WORD2VEC (Proxy) ---
    if 'Word2Vec' in model_name:
        proxy_model_name = 'TF-IDF + LinearSVC'
        proxy_model = model_loader.load_model(proxy_model_name)
        # LinearSVC é um pipeline, então passamos texto bruto limpo
        if proxy_model:
            try:
                cleaned = clean_text_english(text)
                # Pipeline espera lista de strings
                pred = proxy_model.predict([cleaned])[0]
                ai_probability = 1.0 if pred == 1 else 0.0
                
                prediction = 'AI' if ai_probability >= 0.5 else 'Human'
                confidence = ai_probability if prediction == 'AI' else 1 - ai_probability
                
                cleaned_text_for_mural = clean_text_english(text)
                mural_tokens = cleaned_text_for_mural.split()

                return {
                    'text_preview': text[:50] + '...',
                    'prediction': prediction,
                    'ai_probability': ai_probability,
                    'confidence': confidence,
                    'model_used': model_name,
                    'mural_tokens': mural_tokens
                }
            except Exception as e:
                print(f"Erro no proxy W2V: {e}")

    # --- FLUXO NORMAL ---
    model = model_loader.load_model(model_name)
    if model is None: return {'error': f'Modelo {model_name} não disponível'}

    try:
        ai_probability = 0.0
        cleaned_text = clean_text_english(text)
        
        # Verificar se é Pipeline (tem passo 'vectorizer' ou similar)
        # A maioria dos modelos sklearn salvos como pipeline aceitam texto bruto
        is_pipeline = hasattr(model, 'named_steps') or 'Pipeline' in str(type(model))
        
        if is_pipeline:
            # Pipeline: Passar texto bruto (limpo) numa lista
            input_data = [cleaned_text]
            
            if hasattr(model, 'predict_proba'):
                probs = model.predict_proba(input_data)[0]
                ai_probability = probs[1]
            elif hasattr(model, 'decision_function'):
                score = model.decision_function(input_data)[0]
                ai_probability = 1 / (1 + np.exp(-score))
            else:
                pred = model.predict(input_data)[0]
                ai_probability = 1.0 if pred == 1 else 0.0
                
        else:
            # Não é Pipeline (XGBoost, Keras): Vetorizar manualmente
            vectorizer = model_loader.load_vectorizer()
            if vectorizer:
                features = vectorizer.transform([cleaned_text])
                
                # XGBoost precisa de denso
                if 'XGB' in str(type(model)) or 'XGB' in model_name:
                    if hasattr(features, 'toarray'):
                        features = features.toarray()
                
                # Keras precisa de denso
                if 'keras' in str(type(model)) or 'tensorflow' in str(type(model)):
                    if hasattr(features, 'toarray'):
                        features = features.toarray()
                
                # Predição
                if hasattr(model, 'predict_proba'):
                    probs = model.predict_proba(features)[0]
                    ai_probability = probs[1]
                else:
                    pred = model.predict(features, verbose=0)
                    if isinstance(pred, (list, np.ndarray)):
                        if len(pred.shape) > 1 and pred.shape[1] > 1:
                             ai_probability = float(pred[0][1])
                        elif len(pred.shape) > 1 and pred.shape[1] == 1:
                             ai_probability = float(pred[0][0])
                        else:
                             ai_probability = float(pred[0])
                    else:
                        ai_probability = float(pred)
            else:
                return {'error': 'Vectorizer não encontrado'}

        prediction = 'AI' if ai_probability >= 0.5 else 'Human'
        confidence = ai_probability if prediction == 'AI' else 1 - ai_probability

        mural_tokens = cleaned_text.split()

        return {
            'text_preview': text[:50] + '...',
            'prediction': prediction,
            'ai_probability': ai_probability,
            'confidence': confidence,
            'model_used': model_name,
            'mural_tokens': mural_tokens
        }

    except Exception as e:
        print(f"Erro na análise ({model_name}): {e}")
        return {'error': str(e)}

def tokenize_for_mural_display(text):
    return re.findall(r'\w+|[^\w\s]|\s+', text)
