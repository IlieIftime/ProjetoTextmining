import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from config import settings
import base64

dash.register_page(__name__, path='/study-summary', name='Resumo do Estudo')

# --- Layout Helpers ---
def create_kpi_card(title, value, color="primary"):
    return dbc.Card(
        dbc.CardBody([
            html.H5(title, className="card-title text-muted"),
            html.H2(value, className=f"text-{color}")
        ]),
        className="mb-4 shadow-sm"
    )

def get_image_src(filename):
    """Helper to load image from assets/plots/eda"""
    path = settings.ASSETS_DIR / 'plots' / 'eda' / filename
    if path.exists():
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f"data:image/png;base64,{encoded}"
    return ""

# --- Visualizations ---
def get_class_dist_fig():
    df = settings.DF_CLASS_DIST
    if df.empty: return go.Figure()
    
    col_name = 'label'
    if 'label' not in df.columns:
        if 'generated' in df.columns: col_name = 'generated'
        elif 'class' in df.columns: col_name = 'class'
    
    if col_name not in df.columns: return go.Figure()
        
    color_map = {'generated': '#EF553B', 'human': '#636EFA', 
                 1: '#EF553B', 0: '#636EFA',
                 '1': '#EF553B', '0': '#636EFA',
                 'AI': '#EF553B', 'Human': '#636EFA'}
                 
    fig = px.pie(df, names=col_name, values='count', title='Distribuição de Classes',
                 color=col_name, color_discrete_map=color_map)
    return fig

def get_radar_figs():
    """
    Gera dois gráficos de radar (AI vs Human) comparando métricas normalizadas.
    Métricas: N Documentos, Média Tokens, Diversidade Léxica.
    """
    # 1. Extração de Dados (com valores default seguros)
    metrics = {
        'AI': {'docs': 0, 'tokens': 0, 'lexical': 0},
        'Human': {'docs': 0, 'tokens': 0, 'lexical': 0}
    }
    
    # Helper robusto para identificar classe
    def get_key(val):
        s = str(val).lower().strip()
        # Lista abrangente de identificadores de IA
        if s in ['generated', 'ai', '1', '1.0', 'true', 'bot', 'synthetic']:
            return 'AI'
        # Tentar conversão numérica para float (ex: 1.0)
        try:
            if float(s) == 1.0:
                return 'AI'
        except:
            pass
        return 'Human'
    
    # --- Docs (Volume) ---
    if not settings.DF_CLASS_DIST.empty:
        df = settings.DF_CLASS_DIST
        col = 'label' if 'label' in df.columns else df.columns[0]
        val = 'count' if 'count' in df.columns else df.columns[1]
        for _, row in df.iterrows():
            metrics[get_key(row[col])]['docs'] = row[val]

    # --- Tokens (Extensão) ---
    if not settings.DF_LEN_STATS.empty:
        df = settings.DF_LEN_STATS
        # Formato long: metric='mean', value=X, label=Y
        if 'metric' in df.columns and 'value' in df.columns:
            df_mean = df[df['metric'] == 'mean']
            col = 'label' if 'label' in df_mean.columns else df_mean.columns[0]
            for _, row in df_mean.iterrows():
                metrics[get_key(row[col])]['tokens'] = row['value']
        # Formato wide: mean=X, label=Y
        elif 'mean' in df.columns:
            col = 'label' if 'label' in df.columns else df.columns[0]
            for _, row in df.iterrows():
                metrics[get_key(row[col])]['tokens'] = row['mean']

    # --- Lexical (Riqueza) ---
    if not settings.DF_LEXICAL.empty:
        df = settings.DF_LEXICAL
        # Identificar coluna de label
        col_label = 'label'
        if 'label' not in df.columns:
            if 'generated' in df.columns: col_label = 'generated'
            elif 'class' in df.columns: col_label = 'class'
            else: col_label = df.columns[0] # Fallback
            
        # Identificar coluna de valor (mean)
        col_val = 'mean'
        if 'mean' not in df.columns:
            # Pegar a primeira coluna numérica que não seja o label
            numerics = df.select_dtypes(include=['number']).columns
            for c in numerics:
                if c != col_label and c != 'Unnamed: 0':
                    col_val = c
                    break
        
        if col_val in df.columns:
            # Agrupar por label para garantir um único valor
            df_grp = df.groupby(col_label)[col_val].mean().reset_index()
            for _, row in df_grp.iterrows():
                metrics[get_key(row[col_label])]['lexical'] = row[col_val]

    # 2. Normalização (Percentagem do Total)
    categories = ['Volume (Docs)', 'Extensão (Tokens)', 'Riqueza (Léxica)']
    
    # Evitar divisão por zero e garantir floats
    total_docs = float(metrics['AI']['docs'] + metrics['Human']['docs']) or 1.0
    total_tokens = float(metrics['AI']['tokens'] + metrics['Human']['tokens']) or 1.0
    total_lexical = float(metrics['AI']['lexical'] + metrics['Human']['lexical']) or 1.0
    
    ai_values = [
        metrics['AI']['docs'] / total_docs,
        metrics['AI']['tokens'] / total_tokens,
        metrics['AI']['lexical'] / total_lexical
    ]
    
    human_values = [
        metrics['Human']['docs'] / total_docs,
        metrics['Human']['tokens'] / total_tokens,
        metrics['Human']['lexical'] / total_lexical
    ]
    
    # Fechar o loop do radar
    ai_values += [ai_values[0]]
    human_values += [human_values[0]]
    categories += [categories[0]]

    # 3. Construção dos Gráficos
    def create_radar(values, color, title):
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            line_color=color,
            name=title
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1], # Forçar escala de 0 a 100%
                    tickformat='.0%',
                    tickfont=dict(size=10),
                ),
                angularaxis=dict(
                    tickfont=dict(size=11)
                )
            ),
            title=dict(text=title, font=dict(size=14)),
            margin=dict(t=40, b=20, l=40, r=40),
            height=280,
            showlegend=False
        )
        return fig

    fig_ai = create_radar(ai_values, '#EF553B', 'Perfil IA')
    fig_human = create_radar(human_values, '#636EFA', 'Perfil Humano')
    
    return fig_ai, fig_human

# --- Page Layout ---
fig_radar_ai, fig_radar_human = get_radar_figs()

layout = dbc.Container([
    html.H1("Resumo do Estudo: Análise de 500k Documentos", className="my-4"),
    
    # KPIs
    dbc.Row([
        dbc.Col(create_kpi_card("Total Documentos", "489,123", "info"), width=3),
        dbc.Col(create_kpi_card("Textos Humanos", "267,580", "success"), width=3),
        dbc.Col(create_kpi_card("Textos IA", "221,543", "danger"), width=3),
        dbc.Col(create_kpi_card("Modelos Treinados", "6", "warning"), width=3),
    ]),

    # Row 1: Distribuição e Histograma
    dbc.Row([
        dbc.Col(dcc.Graph(figure=get_class_dist_fig()), width=6),
        dbc.Col([
            html.H5("Distribuição de Comprimento de Texto", className="text-center mb-3"),
            html.Img(src=get_image_src("text_length_histograms.png"), style={"width": "100%", "borderRadius": "8px", "boxShadow": "0 4px 8px rgba(0,0,0,0.1)"})
        ], width=6),
    ], className="mb-5"),

    # Row 2: Diversidade Léxica (Zoom Out) e Radars
    dbc.Row([
        # Coluna da Imagem (Reduzida)
        dbc.Col([
            html.H5("Diversidade Léxica (Boxplot)", className="text-center mb-3"),
            html.Div(
                html.Img(src=get_image_src("lexical_diversity_boxplot.png"), 
                         style={"width": "100%", "borderRadius": "8px", "boxShadow": "0 4px 8px rgba(0,0,0,0.1)"}),
                style={"width": "60%", "margin": "0 auto"} # Zoom out effect
            )
        ], width=6),
        
        # Coluna dos Radars
        dbc.Col([
            html.H5("Perfil Comparativo Normalizado", className="text-center mb-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(figure=fig_radar_ai, config={'displayModeBar': False}), width=6),
                dbc.Col(dcc.Graph(figure=fig_radar_human, config={'displayModeBar': False}), width=6),
            ])
        ], width=6),
    ], className="mb-5"),
    
    # Top Tokens Section
    html.H3("Termos Distintivos", className="my-4"),
    dbc.Row([
        dbc.Col([
            html.H5("Top Indicadores IA"),
            html.Div(
                dbc.Table.from_dataframe(settings.DF_DISTINCTIVE_AI.head(10), striped=True, bordered=True, hover=True)
                if not settings.DF_DISTINCTIVE_AI.empty else "Dados não disponíveis"
            )
        ], width=6),
        dbc.Col([
            html.H5("Top Indicadores Humanos"),
            html.Div(
                dbc.Table.from_dataframe(settings.DF_DISTINCTIVE_HUMAN.head(10), striped=True, bordered=True, hover=True)
                if not settings.DF_DISTINCTIVE_HUMAN.empty else "Dados não disponíveis"
            )
        ], width=6),
    ])

], fluid=True)
