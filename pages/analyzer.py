import dash
from dash import dcc, html, Input, Output, State, callback, ALL, no_update
import dash_bootstrap_components as dbc
from core import analysis_engine
from config import settings
import pandas as pd
import time
import random
import requests
from bs4 import BeautifulSoup
import newspaper
from newspaper import Article
import base64

dash.register_page(__name__, path='/', name='Analisador Interativo')

# --- Funções Auxiliares de UI ---

def get_verdict_icon(prediction):
    """Retorna o ícone base64 correspondente à predição."""
    filename = "ai.png" if prediction == "AI" else "humano.png"
    path = settings.BASE_DIR / 'img' / filename
    if path.exists():
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f"data:image/png;base64,{encoded}"
    return ""

def render_stars(confidence):
    """Converte confiança (0.5-1.0) em 5 estrelas."""
    score = int((confidence - 0.5) * 2 * 5) + 1
    if score > 5: score = 5
    if score < 1: score = 1
    
    stars = []
    for i in range(5):
        if i < score:
            stars.append(html.Span("★", className="text-warning", style={"fontSize": "1.2rem"}))
        else:
            stars.append(html.Span("☆", className="text-muted", style={"fontSize": "1.2rem"}))
    
    return html.Div(stars + [html.Span(f" {confidence:.1%}", className="ms-2 small text-muted")])

def truncate_tokens(text, max_tokens):
    tokens = text.split()
    if len(tokens) > max_tokens:
        return " ".join(tokens[:max_tokens]) + "..."
    return text

# --- Funções Auxiliares de Geração de Conteúdo ---

def generate_dynamic_text(query):
    """Gera texto longo pseudo-realista para artigos de fallback."""
    sentences = [
        f"The recent developments in {query} have sparked a global debate.",
        "Experts argue that this technology is reshaping the landscape of modern industry.",
        "However, concerns regarding privacy and ethical implications remain prevalent.",
        f"Data shows a significant increase in interest towards {query} over the last quarter.",
        "Companies are investing heavily to stay ahead of the curve.",
        "The impact on the job market is yet to be fully understood.",
        "Innovation in this sector is moving at an unprecedented pace.",
        f"Critics suggest that {query} might be overhyped, but the evidence suggests otherwise.",
        "Regulatory bodies are scrambling to create frameworks for this new reality.",
        "Future projections indicate a compound annual growth rate of 20%.",
        "User adoption has exceeded initial expectations by a wide margin.",
        "This marks a turning point in how we interact with digital systems.",
        f"Understanding the nuances of {query} is crucial for future success.",
        "The integration of AI into this field has unlocked new possibilities.",
        "Sustainability remains a key challenge that needs to be addressed.",
        "Investors are watching closely as the market evolves.",
        "New startups are emerging to tackle these specific problems.",
        "The academic community is divided on the long-term effects."
    ]
    selected = random.sample(sentences, k=random.randint(8, 15))
    return " ".join(selected)

def generate_varied_comment(query):
    """Gera um comentário único combinando partes de frases."""
    openers = [
        f"I honestly think {query} is fascinating.",
        "This article completely misses the point about the risks.",
        "Finally, someone is talking about this!",
        f"I've been following {query} for years and this is new to me.",
        "Great analysis, but I disagree with the conclusion.",
        "This is exactly what I was afraid of.",
        "Does anyone else feel like this is overhyped?",
        f"The potential for {query} is limitless.",
        "I'm skeptical about these claims.",
        "Very insightful read.",
        "This is just the tip of the iceberg.",
        "I'm not sure I agree with the author here."
    ]
    middles = [
        "The technology is moving way too fast for regulations to keep up.",
        "We need to consider the human cost of this transition.",
        "It will fundamentally change how we work.",
        "I've seen similar trends fail in the past.",
        "The data clearly supports this view.",
        "People are overreacting to the news.",
        "My company is already implementing this strategy.",
        "It's a total game changer for the industry.",
        "There are too many variables to predict the outcome.",
        "We should be focusing on the ethical implications.",
        "The economic impact will be massive."
    ]
    closers = [
        "Time will tell who is right.",
        "Thanks for sharing this.",
        "What do you guys think?",
        "Absolutely incredible.",
        "Scary stuff to be honest.",
        "We need to be careful moving forward.",
        "Can't wait to see what happens next year.",
        "Keep up the good work.",
        "Disappointing analysis overall.",
        "Spot on.",
        "This needs more attention."
    ]
    return f"{random.choice(openers)} {random.choice(middles)} {random.choice(closers)}"

def search_serpapi(query, max_results=15):
    """Busca URLs reais usando SerpAPI (Google Search) com retry logic."""
    api_key = "ea185215718b65c4fb026572a36db641d8f327a9d4e6f55752ee8d1544340dca"
    endpoint = "https://serpapi.com/search"

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "num": max_results,
        "hl": "en"
    }

    for attempt in range(3):  # 3 tentativas
        try:
            res = requests.get(endpoint, params=params, timeout=10)
            res.raise_for_status()  # Garante que erros HTTP sejam capturados
            data = res.json()

            if "organic_results" in data and data["organic_results"]:
                urls = [item["link"] for item in data["organic_results"] if "link" in item]
                if urls:
                    print(f"[DEBUG] {len(urls)} URLs encontradas (SerpAPI)")
                    return urls

            print(f"[DEBUG] Nenhum resultado orgânico na tentativa {attempt+1}")
            if "error" in data:
                print(f"    [SERPAPI ERROR] {data['error']}")
            if attempt < 2:
                time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"[DEBUG] SerpAPI tentativa {attempt + 1} falhou: {type(e).__name__}")
            if attempt < 2:
                time.sleep(1)

    print("[DEBUG] Falha total na busca com SerpAPI após 3 tentativas.")
    return []


def extract_article_image(article_obj, base_url):
    """Extrai imagem do artigo com múltiplas estratégias robustas."""
    from urllib.parse import urljoin, quote

    # 1. Tenta obter top_image do newspaper
    if article_obj.top_image and 'http' in article_obj.top_image:
        try:
            resp = requests.head(article_obj.top_image, timeout=3, allow_redirects=True)
            if resp.status_code == 200:
                print(f"[DEBUG] Imagem encontrada via top_image: {article_obj.top_image[:60]}")
                return article_obj.top_image
        except:
            pass

    try:
        soup = BeautifulSoup(article_obj.html, 'html.parser')

        # 2. Meta tags (OpenGraph, Twitter Card) - Prioridade 1
        meta_tags = [
            ('og:image', 'property'),
            ('og:image:url', 'property'),
            ('og:image:secure_url', 'property'),
            ('twitter:image', 'name'),
            ('twitter:image:src', 'name'),
            ('image', 'name'),
        ]

        for tag_name, tag_type in meta_tags:
            if tag_type == 'property':
                meta = soup.find('meta', property=tag_name)
            else:
                meta = soup.find('meta', attrs={'name': tag_name})

            if meta and meta.get('content'):
                img_url = urljoin(base_url, meta.get('content'))
                try:
                    if 'http' in img_url:
                        resp = requests.head(img_url, timeout=3, allow_redirects=True)
                        if resp.status_code == 200:
                            print(f"[DEBUG] Imagem encontrada via meta tag: {tag_name}")
                            return img_url
                except:
                    pass

        # 3. Picture/img dentro de article/main - Prioridade 2
        main_candidates = [
            soup.find('article'),
            soup.find('main'),
            soup.find('div', class_=lambda x: x and 'content' in x.lower()),
            soup.find('div', class_=lambda x: x and 'post' in x.lower()),
            soup.find('div', class_=lambda x: x and 'entry' in x.lower()),
        ]

        for main_content in main_candidates:
            if not main_content:
                continue

            for img in main_content.find_all('img')[:10]:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    img_url = urljoin(base_url, src)
                    try:
                        if 'http' in img_url:
                            resp = requests.head(img_url, timeout=3, allow_redirects=True)
                            if resp.status_code == 200:
                                print(f"[DEBUG] Imagem encontrada em article/main")
                                return img_url
                    except:
                        pass

        # 4. Imagens com classes típicas de destaque - Prioridade 3
        img_classes = ['hero', 'featured', 'main', 'lead', 'cover', 'thumbnail', 'header']
        for img in soup.find_all('img')[:30]:
            img_class = img.get('class', [])
            img_class_str = ' '.join(img_class) if isinstance(img_class, list) else str(img_class)

            if any(cls in img_class_str.lower() for cls in img_classes):
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    img_url = urljoin(base_url, src)
                    try:
                        if 'http' in img_url:
                            resp = requests.head(img_url, timeout=3, allow_redirects=True)
                            if resp.status_code == 200:
                                print(f"[DEBUG] Imagem encontrada via classe destaque")
                                return img_url
                    except:
                        pass

        # 5. Primeira imagem grande encontrada - Fallback
        for img in soup.find_all('img')[:40]:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if src and ('http' in src or src.startswith('/')):
                img_url = urljoin(base_url, src)
                try:
                    if 'http' in img_url:
                        resp = requests.head(img_url, timeout=3, allow_redirects=True)
                        if resp.status_code == 200:
                            print(f"[DEBUG] Imagem encontrada (primeira válida)")
                            return img_url
                except:
                    pass

    except Exception as e:
        print(f"[DEBUG] Erro ao extrair imagem: {e}")

    # Fallback: Imagem gerada
    title_slug = quote((article_obj.title or 'article')[:50])
    print(f"[DEBUG] Usando imagem gerada como fallback")
    return f"https://image.pollinations.ai/prompt/{title_slug}?width=400&height=200&nologo=true"

def scrape_real_comments(url, max_comments=5):
    """Tenta extrair comentários reais da página com múltiplas estratégias."""
    comments_list = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    try:
        response = requests.get(url, headers=headers, timeout=6, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove scripts e styles
        for script in soup(["script", "style"]):
            script.decompose()

        # Estratégias múltiplas para encontrar comentários
        comment_strategies = [
            # Estratégia 1: Classes com 'comment'
            lambda: soup.find_all(class_=lambda x: x and 'comment' in x.lower()),
            # Estratégia 2: Data attributes
            lambda: soup.find_all(attrs={'data-qa': lambda x: x and 'comment' in str(x).lower()}),
            # Estratégia 3: itemprop
            lambda: soup.find_all(attrs={'itemprop': 'comment'}),
            # Estratégia 4: Divs dentro de seções de comentários
            lambda: soup.find_all('div', class_=lambda x: x and any(c in str(x).lower() for c in ['response', 'feedback', 'discussion', 'thread', 'review'])),
            # Estratégia 5: Li com comentários
            lambda: soup.find_all('li', class_=lambda x: x and 'comment' in x.lower()),
        ]

        for strategy in comment_strategies:
            if len(comments_list) >= max_comments:
                break

            try:
                elements = strategy()
                for elem in elements[:max_comments]:
                    # Extrai texto do comentário
                    text_elem = elem.find('p') or elem.find('span', class_=lambda x: x and 'text' in str(x).lower()) or elem.find('div')

                    if text_elem:
                        comment_text = text_elem.get_text(strip=True)
                        # Validação de comprimento
                        if 15 < len(comment_text) < 800 and comment_text not in comments_list:
                            comments_list.append(comment_text)

                    if len(comments_list) >= max_comments:
                        break
            except:
                pass

    except requests.Timeout:
        print(f"[DEBUG] Timeout ao extrair comentários (URL muito lenta)")
    except requests.ConnectionError:
        print(f"[DEBUG] Erro de conexão ao extrair comentários")
    except Exception as e:
        print(f"[DEBUG] Erro ao extrair comentários reais: {type(e).__name__}")

    return comments_list

def extract_article_comments(article_text, article_url, query, selected_model, max_comments=5):
    """Extrai comentários reais da página ou gera baseado no conteúdo."""
    comments = []

    # Tentativa 1: Extrair comentários reais da página
    real_comments = scrape_real_comments(article_url, max_comments)

    if real_comments:
        print(f"[DEBUG] {len(real_comments)} comentários reais encontrados")
        for comment_text in real_comments[:max_comments]:
            try:
                c_analysis = analysis_engine.analyze_text(comment_text, model_name=selected_model)
                comments.append({
                    "text": comment_text[:500],  # Limita tamanho
                    "prediction": c_analysis.get('prediction', 'N/A'),
                    "confidence": c_analysis.get('confidence', 0.0),
                    "source": "real"
                })
            except:
                pass

    # Fallback: Comentários baseados no conteúdo do artigo
    if len(comments) < max_comments:
        try:
            sentences = [s.strip() for s in article_text.split('.') if 20 < len(s.strip()) < 200][:10]

            for j in range(max_comments - len(comments)):
                base_sentence = random.choice(sentences) if sentences else query

                comment_templates = [
                    f"I completely agree with '{base_sentence[:50]}...' This is an important point.",
                    f"Interesting perspective on {query}. However, I think there's more to consider.",
                    f"This article raises valid concerns about {query} that we need to address.",
                    f"Great insight! The point about {base_sentence[:40]}... really resonates.",
                    f"I disagree with some parts, but overall good analysis of {query}.",
                    f"Finally someone is covering this aspect of {query}!",
                    f"This makes sense, especially regarding '{base_sentence[:45]}...'",
                    f"Thought-provoking read. We should be discussing {query} more.",
                ]

                c_text = random.choice(comment_templates)
                c_analysis = analysis_engine.analyze_text(c_text, model_name=selected_model)

                comments.append({
                    "text": c_text,
                    "prediction": c_analysis.get('prediction', 'N/A'),
                    "confidence": c_analysis.get('confidence', 0.0),
                    "source": "contextual"
                })
        except Exception as e:
            print(f"[DEBUG] Erro ao gerar comentários contextuais: {e}")

    # Fallback final: Comentários genéricos
    while len(comments) < max_comments:
        c_text = generate_varied_comment(query)
        c_analysis = analysis_engine.analyze_text(c_text, model_name=selected_model)
        comments.append({
            "text": c_text,
            "prediction": c_analysis.get('prediction', 'N/A'),
            "confidence": c_analysis.get('confidence', 0.0),
            "source": "generated"
        })

    return comments[:max_comments]

# --- Layout ---
layout = dbc.Container([
    # Seletor de Modelo Global
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H6("Modelo de Classificação Ativo", className="card-subtitle mb-2 text-muted"),
                    dcc.Dropdown(
                        id='model-selector-analyzer',
                        options=[{'label': m, 'value': m} for m in settings.MODEL_NAMES],
                        value='TF-IDF + LinearSVC' if 'TF-IDF + LinearSVC' in settings.MODEL_NAMES else settings.MODEL_NAMES[0],
                        clearable=False,
                        style={'fontSize': '1.1rem'}
                    )
                ])
            ], className="mb-4 shadow-sm border-0")
        ], width=12)
    ]),

    dbc.Tabs([
        # --- ABA 1: MURAL INTERATIVO ---
        dbc.Tab(label="Mural Interativo", children=[
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.H4("Entrada de Texto", className="card-title"),
                            dcc.Textarea(
                                id='mural-input',
                                placeholder="Cole o texto aqui para análise...",
                                style={'width': '100%', 'height': '150px'},
                                className="mb-3"
                            ),
                            dbc.Button("Analisar", id='btn-analyze', color="primary", className="w-100"),
                        ])
                    ], className="mb-4 shadow-sm"),
                    html.Div(id='mural-output')
                ], width=8),
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("Raio-X Linguístico"),
                        dbc.CardBody(
                            html.Div(
                                id='mural-stats-panel',
                                children=html.P("Clique numa palavra do mural para ver insights.", className="text-muted")
                            )
                        )
                    ], className="shadow-sm sticky-top", style={"top": "20px"})
                ], width=4)
            ], className="mt-4")
        ]),
        
        # --- ABA 2: SONDA WEB ---
        dbc.Tab(label="Sonda Web", children=[
            dbc.Row([
                dbc.Col([
                    html.H4("Sonda Web", className="my-4"),
                    dbc.InputGroup([
                        dbc.Input(id="scraper-query", placeholder="Digite um tópico para buscar notícias..."),
                        dbc.Button("Buscar e Analisar", id="btn-scraper", color="secondary")
                    ], className="mb-4"),
                    
                    dbc.Row([
                        dbc.Col(
                            dbc.RadioItems(
                                id="view-mode-selector",
                                options=[
                                    {"label": "Visão Detalhada (Sequencial)", "value": "detailed"},
                                    {"label": "Visão Geral (Dashboard)", "value": "overall"},
                                ],
                                value="detailed",
                                inline=True,
                                className="mb-3"
                            )
                        )
                    ]),

                    dcc.Loading(
                        html.Div(id="scraper-output")
                    ),
                    
                    dcc.Store(id="scraper-data-store")
                ], width=12)
            ])
        ])
    ])
], fluid=True)

# --- Callbacks: Mural Interativo ---
@callback(
    Output('mural-output', 'children'),
    Input('btn-analyze', 'n_clicks'),
    State('mural-input', 'value'),
    State('model-selector-analyzer', 'value'), # Novo State
    prevent_initial_call=True
)
def update_mural(n_clicks, text, selected_model):
    if not text: return dbc.Alert("Por favor, insira um texto.", color="warning")
    
    # Usar o modelo selecionado
    result = analysis_engine.analyze_text(text, model_name=selected_model)
    if 'error' in result: return dbc.Alert(f"Erro na análise: {result['error']}", color="danger")
    
    verdict_color = "danger" if result['prediction'] == 'AI' else "success"
    icon_src = get_verdict_icon(result['prediction'])
    
    verdict_card = dbc.Card([
        dbc.CardBody([
            html.Div([
                html.Img(src=icon_src, style={"height": "60px", "width": "60px", "borderRadius": "50%", "marginRight": "15px", "objectFit": "cover"}),
                html.Div([
                    html.H2(f"Veredito: {result['prediction']}", className=f"text-{verdict_color} mb-0"),
                    render_stars(result['confidence'])
                ])
            ], className="d-flex align-items-center justify-content-center mb-3"),
            html.P(f"Modelo: {result['model_used']}", className="text-center small text-muted")
        ])
    ], className="mb-4 border-primary")
    
    visual_tokens = analysis_engine.tokenize_for_mural_display(text)
    mural_elements = []
    for i, token in enumerate(visual_tokens):
        is_word = token.strip() != '' and any(c.isalnum() for c in token)
        style = {'cursor': 'pointer' if is_word else 'default', 'margin': '0 1px' if is_word else '0', 'padding': '1px 2px' if is_word else '0', 'borderRadius': '3px', 'display': 'inline-block'}
        clean_token = analysis_engine.clean_text_english(token) if is_word else ""
        
        if is_word and clean_token:
            elem_id = {'type': 'mural-token', 'index': i, 'token': clean_token}
            mural_elements.append(html.Span(token, id=elem_id, style=style, className="mural-token-hover", n_clicks=0))
        else:
            mural_elements.append(html.Span(token, style=style))
            
    return html.Div([verdict_card, dbc.Card([dbc.CardBody(mural_elements, style={'lineHeight': '2.0', 'fontSize': '1.1rem'})])])

@callback(
    Output('mural-stats-panel', 'children'),
    Input({'type': 'mural-token', 'index': ALL, 'token': ALL}, 'n_clicks'),
    prevent_initial_call=True
)
def update_token_stats(n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered: return no_update
    triggered_id = ctx.triggered_id
    if not triggered_id or 'token' not in triggered_id: return no_update
    token = triggered_id['token']
    
    insights = []
    if not settings.DF_DISTINCTIVE_AI.empty:
        col = 'feature' if 'feature' in settings.DF_DISTINCTIVE_AI.columns else settings.DF_DISTINCTIVE_AI.columns[0]
        match = settings.DF_DISTINCTIVE_AI[settings.DF_DISTINCTIVE_AI[col] == token]
        if not match.empty:
            insights.append(dbc.ListGroupItem([html.Div([html.H5("Indicador de IA", className="mb-1 text-danger"), html.P("Top 200 IA.", className="mb-1"), html.Small(f"Ranking: #{match.index[0]+1}")])]))
    
    if not settings.DF_DISTINCTIVE_HUMAN.empty:
        col = 'feature' if 'feature' in settings.DF_DISTINCTIVE_HUMAN.columns else settings.DF_DISTINCTIVE_HUMAN.columns[0]
        match = settings.DF_DISTINCTIVE_HUMAN[settings.DF_DISTINCTIVE_HUMAN[col] == token]
        if not match.empty:
            insights.append(dbc.ListGroupItem([html.Div([html.H5("Indicador Humano", className="mb-1 text-success"), html.P("Comum em humanos.", className="mb-1"), html.Small(f"Ranking: #{match.index[0]+1}")])]))

    if not settings.DF_COEFFS_AI.empty:
        col = 'feature' if 'feature' in settings.DF_COEFFS_AI.columns else settings.DF_COEFFS_AI.columns[0]
        match = settings.DF_COEFFS_AI[settings.DF_COEFFS_AI[col] == token]
        if not match.empty:
            coef = match.iloc[0]['coefficient'] if 'coefficient' in match.columns else "N/A"
            insights.append(dbc.ListGroupItem([html.H6("Peso no Modelo"), html.P(f"Contribuição IA: {coef}")]))

    return html.Div([html.H3(token, className="mb-3 border-bottom pb-2"), dbc.ListGroup(insights)]) if insights else html.Div([html.H5(token), html.P("Sem insights estatísticos.")])

# --- Callbacks: Sonda Web ---

@callback(
    Output("scraper-data-store", "data"),
    Input("btn-scraper", "n_clicks"),
    State("scraper-query", "value"),
    State('model-selector-analyzer', 'value'),
    prevent_initial_call=True
)
def fetch_scraper_data(n_clicks, query, selected_model):
    if not query: return no_update
    
    data = []
    real_urls = search_serpapi(query, max_results=15)  # Busca mais URLs para maior cobertura
    processed_urls = set()

    print(f"\n{'='*60}")
    print(f"[SONDA WEB] Iniciando busca por: {query}")
    print(f"[SONDA WEB] Total de URLs encontradas: {len(real_urls)}")
    print(f"{'='*60}")

    # FASE 1: Web scraping robusto de artigos reais
    for idx, url in enumerate(real_urls, 1):
        if len(data) >= 5:
            break

        if url in processed_urls:
            continue
        processed_urls.add(url)

        print(f"\n[{idx}] Processando: {url[:60]}...")

        try:
            # Download e parse com retry
            article = None
            for attempt in range(2):
                try:
                    config = newspaper.Config()
                    config.request_timeout = 8
                    article = Article(url, config=config, keep_article_html=True)
                    article.download()
                    article.parse()
                    break
                except Exception as e:
                    print(f"Tentativa {attempt + 1}: {type(e).__name__}")
                    if attempt == 0:
                        time.sleep(1)

            if not article:
                print(f"Falha no download/parse")
                continue

            # Validações de conteúdo
            if not article.text or len(article.text) < 150:
                print(f"Conteúdo muito curto ({len(article.text) if article.text else 0} chars)")
                continue

            if not article.title or len(article.title) < 5:
                print(f"Título inválido")
                continue

            print(f"Artigo: {article.title[:50]}...")
            print(f"Conteúdo: {len(article.text)} caracteres")

            # Análise do artigo
            art_analysis = analysis_engine.analyze_text(article.text, model_name=selected_model)
            
            # Extração robusta de imagem
            base_url = article.source_url if hasattr(article, 'source_url') else url
            img_url = extract_article_image(article, base_url)

            # Extração de comentários (reais > contextuais > genéricos)
            comments = extract_article_comments(article.text, url, query, selected_model, max_comments=5)
            print(f"Comentários: {len(comments)} ({comments[0].get('source', 'unknown') if comments else 'nenhum'})")

            # Adiciona artigo real aos dados
            data.append({
                "id": len(data),
                "title": article.title,
                "url": url,
                "image": img_url,
                "text": article.text,
                "prediction": art_analysis.get('prediction', 'N/A'),
                "confidence": art_analysis.get('confidence', 0.0),
                "comments": comments,
                "source": "real"
            })
            print(f"Artigo real adicionado (ID: {len(data)-1})")

        except Exception as e:
            print(f"Erro: {type(e).__name__}: {str(e)[:60]}")
            continue

    # FASE 2: Fallback - apenas se não conseguiu artigos reais suficientes
    print(f"\n{'='*60}")
    print(f"[STATUS] Artigos reais encontrados: {len(data)}/5")
    print(f"{'='*60}")

    while len(data) < 5:
        i = len(data)
        print(f"\n[FALLBACK] Gerando artigo sintético #{i+1}...")

        try:
            # Gera conteúdo pseudo-realista apenas como fallback
            full_text = generate_dynamic_text(query) + " " + generate_dynamic_text(query)
            art_analysis = analysis_engine.analyze_text(full_text, model_name=selected_model)

            # Comentários em fallback
            comments = []
            for j in range(5):
                c_text = generate_varied_comment(query)
                c_analysis = analysis_engine.analyze_text(c_text, model_name=selected_model)
                comments.append({
                    "text": c_text,
                    "prediction": c_analysis.get('prediction', 'N/A'),
                    "confidence": c_analysis.get('confidence', 0.0),
                    "source": "generated"
                })

            # Imagem gerada como fallback
            from urllib.parse import quote
            img_url = f"https://image.pollinations.ai/prompt/{quote(query + ' concept ' + str(i))}?width=400&height=200&nologo=true&seed={random.randint(0, 100000)}"

            data.append({
                "id": i,
                "title": f"Analysis: {query} #{i+1}",
                "url": f"#generated-{i}",
                "image": img_url,
                "text": full_text,
                "prediction": art_analysis.get('prediction', 'N/A'),
                "confidence": art_analysis.get('confidence', 0.0),
                "comments": comments,
                "source": "generated"
            })
            print(f"Artigo sintético adicionado (ID: {i})")

        except Exception as e:
            print(f"Erro ao gerar fallback: {e}")
            # Fallback extremo: artigo mínimo
            data.append({
                "id": i,
                "title": f"Report about {query}",
                "url": f"#fallback-{i}",
                "image": "https://image.pollinations.ai/prompt/placeholder?width=400&height=200",
                "text": f"Information about {query}.",
                "prediction": "N/A",
                "confidence": 0.0,
                "comments": [],
                "source": "generated"
            })

    print(f"\n{'='*60}")
    print(f"[CONCLUSÃO] Total de itens retornados: {len(data)}")
    print(f"{'='*60}\n")

    return data

@callback(
    Output("scraper-output", "children"),
    [Input("scraper-data-store", "data"),
     Input("view-mode-selector", "value")],
    prevent_initial_call=True
)
def render_scraper_results(data, view_mode):
    if not data: return html.Div()
        
    if view_mode == "overall":
        cols = []
        for item in data:
            comment_badges = []
            for c in item['comments']:
                color = "danger" if c['prediction'] == 'AI' else "success"
                comment_badges.append(html.Span("●", className=f"text-{color} me-1", style={"fontSize": "1.5rem", "cursor": "help", "title": f"{c['prediction']}"}))
            
            icon_src = get_verdict_icon(item['prediction'])
            
            card = dbc.Card([
                dbc.CardImg(src=item['image'], top=True, style={"height": "120px", "objectFit": "cover"}),
                dbc.CardBody([
                    html.H6(item['title'], className="card-title text-truncate"),
                    html.Div([
                        html.Img(src=icon_src, style={"height": "30px", "width": "30px", "borderRadius": "50%", "marginRight": "8px"}),
                        html.Span(item['prediction'], className=f"fw-bold text-{'danger' if item['prediction'] == 'AI' else 'success'}"),
                    ], className="d-flex align-items-center mb-2"),
                    render_stars(item['confidence']),
                    html.Hr(),
                    html.Small("Comentários:", className="text-muted d-block"),
                    html.Div(comment_badges)
                ])
            ], className="h-100 shadow-sm")
            cols.append(dbc.Col(card, width=2))
        return dbc.Row(cols, className="g-2 row-cols-1 row-cols-md-5")

    else:
        rows = []
        for item in data:
            comments_rows = []
            for c in item['comments']:
                c_color = "danger" if c['prediction'] == 'AI' else "success"
                comments_rows.append(html.Tr([
                    html.Td(truncate_tokens(c['text'], 50)),
                    html.Td([
                        html.Div(c['prediction'], className=f"text-{c_color} fw-bold"),
                        render_stars(c['confidence'])
                    ])
                ]))
            
            comments_table = dbc.Table(
                [html.Thead(html.Tr([html.Th("Comentário (50 tokens)"), html.Th("Classificação")])),
                 html.Tbody(comments_rows)],
                bordered=True, hover=True, size="sm", className="mb-0"
            )
            
            icon_src = get_verdict_icon(item['prediction'])
            
            card = dbc.Card([
                dbc.Row([
                    dbc.Col(dbc.CardImg(src=item['image'], className="img-fluid rounded-start", style={"height": "100%", "objectFit": "cover"}), width=3),
                    dbc.Col(dbc.CardBody([
                        html.H4(item['title']),
                        html.A(item['url'], href=item['url'], target="_blank", className="small text-muted mb-2 d-block"),
                        html.P(truncate_tokens(item['text'], 250), className="card-text text-justify"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.H5("Veredito do Artigo:", className="mt-2"),
                                html.Div([
                                    html.Img(src=icon_src, style={"height": "50px", "width": "50px", "borderRadius": "50%", "marginRight": "15px"}),
                                    html.H3(item['prediction'], className=f"text-{'danger' if item['prediction'] == 'AI' else 'success'} mb-0"),
                                ], className="d-flex align-items-center mb-2"),
                                render_stars(item['confidence'])
                            ], width=4),
                            dbc.Col([
                                html.H6("Análise de Comentários", className="mt-2"),
                                dbc.Accordion([
                                    dbc.AccordionItem(
                                        comments_table,
                                        title=f"Ver 5 Comentários Analisados"
                                    )
                                ], start_collapsed=True)
                            ], width=8)
                        ])
                    ]), width=9)
                ], className="g-0")
            ], className="mb-4 shadow")
            rows.append(card)
        return html.Div(rows)
