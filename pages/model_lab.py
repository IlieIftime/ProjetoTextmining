import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from config import settings
import base64
import re

dash.register_page(__name__, path='/model-lab', name='Laboratório de Modelos')

# --- Funções Auxiliares ---

def hex_to_rgba(hex_color, opacity=0.2):
    """Converte hex para rgba com opacidade para linhas mais claras."""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join([c*2 for c in hex_color])
    rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"

def render_report_table(report_text, model_color):
    """
    Converte o texto cru do classification_report numa tabela HTML estilizada.
    Mantém os números intactos, mas organiza em grelha.
    """
    lines = [l.strip() for l in report_text.split('\n') if l.strip()]
    if not lines: return html.Div("Relatório vazio")

    # Cor para as bordas (mais clara)
    border_color = hex_to_rgba(model_color, 0.3)
    cell_style = {'border': f'1px solid {border_color}', 'padding': '8px', 'textAlign': 'center'}
    header_style = {'border': f'1px solid {border_color}', 'padding': '8px', 'textAlign': 'center', 'backgroundColor': hex_to_rgba(model_color, 0.05), 'fontWeight': 'bold'}
    
    # Cabeçalho
    # O sklearn report começa com: "              precision    recall  f1-score   support"
    # Vamos forçar um cabeçalho fixo para garantir alinhamento
    headers = ["Classe", "Precision", "Recall", "F1-Score", "Support"]
    
    table_header = html.Thead(html.Tr([html.Th(h, style=header_style) for h in headers]))
    
    table_rows = []
    
    # Processar linhas
    # Pular a primeira linha se for o cabeçalho original do texto
    start_idx = 1 if 'precision' in lines[0] else 0
    
    for line in lines[start_idx:]:
        parts = line.split()
        row_cells = []
        
        # Lógica de alinhamento baseada no formato padrão do sklearn
        if len(parts) == 5:
            # Linhas normais: [Classe, P, R, F1, S]
            # Ex: "generated 0.99 0.98 0.99 100"
            row_cells = [html.Td(p, style=cell_style) for p in parts]
            
        elif len(parts) == 6 and parts[0] == 'macro' and parts[1] == 'avg':
            # Linha Macro Avg: [macro, avg, P, R, F1, S] -> Juntar "macro avg"
            row_cells = [html.Td("macro avg", style=cell_style)] + [html.Td(p, style=cell_style) for p in parts[2:]]
            
        elif len(parts) == 6 and parts[0] == 'weighted' and parts[1] == 'avg':
            # Linha Weighted Avg
            row_cells = [html.Td("weighted avg", style=cell_style)] + [html.Td(p, style=cell_style) for p in parts[2:]]
            
        elif len(parts) == 3 and parts[0] == 'accuracy':
            # Linha Accuracy: [accuracy, score, support]
            # Precisa alinhar: Classe="accuracy", P="", R="", F1=score, S=support
            row_cells = [
                html.Td("accuracy", style=cell_style),
                html.Td("", style=cell_style), # Empty Precision
                html.Td("", style=cell_style), # Empty Recall
                html.Td(parts[1], style=cell_style), # F1 column holds accuracy score usually
                html.Td(parts[2], style=cell_style)  # Support
            ]
        else:
            # Fallback para linhas estranhas
            row_cells = [html.Td(" ".join(parts), colSpan=5, style=cell_style)]

        table_rows.append(html.Tr(row_cells))

    return dbc.Table(
        [table_header, html.Tbody(table_rows)],
        bordered=False, # Usamos bordas customizadas
        hover=True,
        responsive=True,
        style={'border': f'2px solid {model_color}', 'borderRadius': '5px', 'overflow': 'hidden'}
    )

def parse_classification_report(filepath):
    """Lê ficheiro e extrai métricas para o radar/tabela geral."""
    metrics = {'Accuracy': 0.0, 'Precision': 0.0, 'Recall': 0.0, 'F1-Score': 0.0, 'Support': 0}
    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
        for line in lines:
            parts = line.split()
            if not parts: continue
            if 'accuracy' in parts:
                try: metrics['Accuracy'] = float(parts[-2])
                except: pass
            if 'macro' in parts and 'avg' in parts:
                try:
                    metrics['Precision'] = float(parts[2])
                    metrics['Recall'] = float(parts[3])
                    metrics['F1-Score'] = float(parts[4])
                    metrics['Support'] = int(parts[5])
                except: pass
    except Exception as e:
        print(f"Erro ao ler report {filepath}: {e}")
    return metrics

def get_metrics_dataframe():
    data = []
    for model_name in settings.MODEL_NAMES:
        _, report_path = settings.get_diagnostic_paths(model_name)
        if report_path and report_path.exists():
            m = parse_classification_report(report_path)
            m['Model'] = model_name
            m['Training Time (s)'] = "N/A"
            data.append(m)
        else:
            data.append({'Model': model_name, 'Accuracy': 0, 'Precision': 0, 'Recall': 0, 'F1-Score': 0, 'Support': 0, 'Training Time (s)': 'N/A'})
    return pd.DataFrame(data)

def get_image_src(filename):
    path = settings.ASSETS_DIR / 'plots' / 'evaluation' / filename
    if path.exists():
        encoded = base64.b64encode(open(path, 'rb').read()).decode('ascii')
        return f"data:image/png;base64,{encoded}"
    return ""

# --- Layout ---
layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        # --- COLUNA DA BARRA LATERAL DE CONTROLOS ---
        dbc.Col(
            dbc.Card([
                dbc.CardHeader("Painel de Controlo"),
                dbc.CardBody([
                    html.H5("Selecionar Modelos", className="card-title"),
                    dcc.Checklist(
                        id='model-lab-checklist',
                        options=[
                            {'label': html.Span(f' {name}', style={'color': settings.MODEL_COLORS.get(name, 'black'), 'fontWeight': '500'}), 
                             'value': name} 
                            for name in settings.MODEL_NAMES
                        ],
                        value=settings.MODEL_NAMES,
                        labelStyle={'display': 'block', 'marginBottom': '8px', 'cursor': 'pointer'}
                    ),
                ])
            ], className="sidebar-card shadow-sm border-0"),
            width=12, lg=3, className="mb-4"
        ),

        # --- COLUNA DO CONTEÚDO PRINCIPAL ---
        dbc.Col(
            [
                html.H2("Laboratório de Modelos: Análise Comparativa", className="mb-3"),
                html.P("Explore e compare a performance dos diferentes algoritmos de classificação.", className="text-muted mb-4"),
                
                # 1. Tabela de Performance Geral
                dbc.Card([
                    dbc.CardHeader("Tabela de Performance Geral (Dados Extraídos dos Relatórios)"),
                    dbc.CardBody(dag.AgGrid(
                        id="metrics-table-lab",
                        columnDefs=[
                            {"field": "Model", "headerName": "Modelo", "sortable": True, "filter": True, "pinned": "left", "width": 250},
                            {"field": "Accuracy", "headerName": "Accuracy", "sortable": True, "valueFormatter": {"function": "d3.format('.4f')(params.value)"}},
                            {"field": "Precision", "headerName": "Macro Precision", "sortable": True, "valueFormatter": {"function": "d3.format('.4f')(params.value)"}},
                            {"field": "Recall", "headerName": "Macro Recall", "sortable": True, "valueFormatter": {"function": "d3.format('.4f')(params.value)"}},
                            {"field": "F1-Score", "headerName": "Macro F1", "sortable": True, "valueFormatter": {"function": "d3.format('.4f')(params.value)"}},
                            {"field": "Support", "headerName": "Support", "sortable": True},
                        ],
                        defaultColDef={"resizable": True},
                        dashGridOptions={"domLayout": "autoHeight"},
                    ))
                ], className="mb-4 shadow-sm border-0"),
                
                # 2. Gráficos Comparativos
                dbc.Card([
                    dbc.CardHeader("Visualizações Comparativas"),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.H5("Radar de Performance (Macro Avg)", className="text-center"),
                                dcc.Graph(id='radar-chart-lab', style={"height": "400px"})
                            ], width=6),
                            dbc.Col([
                                html.H5("Curvas ROC Combinadas", className="text-center"),
                                html.Img(src=get_image_src("combined_roc_curves.png"), style={"width": "100%", "borderRadius": "8px", "boxShadow": "0 4px 8px rgba(0,0,0,0.1)"})
                            ], width=6)
                        ], className="mb-4"),
                        
                        dbc.Row([
                            dbc.Col([
                                html.H5("Análise de Sensibilidade (Comprimento do Texto)", className="text-center"),
                                html.Img(src=get_image_src("sensitivity_analysis.png"), style={"width": "100%", "borderRadius": "8px", "boxShadow": "0 4px 8px rgba(0,0,0,0.1)"})
                            ], width=12)
                        ])
                    ])
                ], className="mb-4 shadow-sm border-0"),
                
                # 3. Diagnósticos Individuais
                dbc.Card([
                    dbc.CardHeader("Diagnósticos Individuais por Modelo"),
                    dbc.CardBody(dcc.Loading(html.Div(id='individual-diagnostics-lab')))
                ], className="shadow-sm border-0 mb-4"),
                
                # 4. Comentário Final
                dcc.Markdown("""
                    ***
                    ### Análise Conclusiva do Laboratório de Modelos
                    
                    A análise comparativa apresentada neste dashboard revela uma história clara: para a tarefa de distinguir texto humano de IA com o dataset fornecido, os **modelos lineares aplicados a representações TF-IDF de alta dimensão (como o LinearSVC) não são apenas eficazes, são o estado-da-arte.**
                    
                    O **Gráfico Radar Comparativo** demonstra visualmente a supremacia do `TFIDF + LinearSVC` e do `SafeTFIDF + XGBoost`, que formam a "fronteira de performance" em quase todas as métricas. As **Curvas ROC e Precision-Recall**, ambas concentradas no canto superior esquerdo (para ROC) e superior direito (para P-R), confirmam o poder discriminatório excecional de todos os modelos baseados em n-gramas, com valores de AUC consistentemente acima de 0.999.
                    
                    A **Análise de Sensibilidade** adiciona uma camada de nuance: enquanto o LinearSVC e o XGBoost dominam em textos de comprimento médio a longo, a simplicidade do Naive Bayes torna-o um concorrente surpreendentemente robusto em textos muito curtos, onde a estrutura sintática é menos relevante.
                    
                    Em suma, este laboratório valida que, embora existam múltiplas abordagens viáveis, a combinação de uma representação de features inteligente (TF-IDF com n-gramas) e um classificador robusto (LinearSVC) oferece uma solução que é, simultaneamente, de performance máxima, computacionalmente eficiente e altamente fiável.
                """, style={'marginTop': '30px', 'color': '#495057', 'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '8px', 'borderLeft': '5px solid #0d6efd'})
            ],
            width=12, lg=9,
        ),
    ]),
])

# --- Callbacks ---

DF_METRICS_PARSED = get_metrics_dataframe()

@callback(
    Output("metrics-table-lab", "rowData"),
    Input("model-lab-checklist", "value")
)
def update_metrics_table(selected_models):
    if not selected_models: return []
    df = DF_METRICS_PARSED
    filtered = df[df['Model'].isin(selected_models)]
    return filtered.to_dict("records")

@callback(
    Output("radar-chart-lab", "figure"),
    Input("model-lab-checklist", "value")
)
def update_radar_chart(selected_models):
    if not selected_models: return go.Figure()
    
    fig = go.Figure()
    categories = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    
    df = DF_METRICS_PARSED
    
    for model in selected_models:
        row = df[df['Model'] == model]
        if row.empty: continue
        
        values = [row.iloc[0][col] for col in categories]
        values += [values[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories + [categories[0]],
            fill='toself',
            name=model,
            line_color=settings.MODEL_COLORS.get(model, '#000'),
            opacity=0.6
        ))

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0.8, 1.0])),
        margin=dict(t=30, b=30, l=40, r=40),
        legend=dict(orientation="h", y=-0.1)
    )
    
    return fig

@callback(
    Output("individual-diagnostics-lab", "children"),
    Input("model-lab-checklist", "value")
)
def update_individual_diagnostics(selected_models):
    if not selected_models: return html.Div("Nenhum modelo selecionado.")
    
    children = []
    
    for model in selected_models:
        cm_path, report_path = settings.get_diagnostic_paths(model)
        model_color = settings.MODEL_COLORS.get(model, '#000')
        
        header = html.Div([
            html.H4(model, style={'color': model_color, 'borderBottom': f'3px solid {model_color}', 'paddingBottom': '10px', 'display': 'inline-block'}),
        ], className="mt-5 mb-4")
        
        content_row = []
        
        # 1. Matriz de Confusão
        if cm_path:
            try:
                df_cm = pd.read_csv(cm_path, index_col=0)
                fig_cm = px.imshow(df_cm, text_auto=True, color_continuous_scale='Blues', title="Matriz de Confusão")
                fig_cm.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                content_row.append(dbc.Col(dcc.Graph(figure=fig_cm, config={'displayModeBar': False}), width=6))
            except Exception as e:
                content_row.append(dbc.Col(dbc.Alert(f"Erro ao carregar CM: {e}", color="warning"), width=6))
        else:
            content_row.append(dbc.Col(html.P("Matriz de Confusão não encontrada.", className="text-muted"), width=6))
            
        # 2. Radar Individual
        row = DF_METRICS_PARSED[DF_METRICS_PARSED['Model'] == model]
        if not row.empty:
            categories = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
            values = [row.iloc[0][col] for col in categories]
            values += [values[0]]
            
            fig_radar_single = go.Figure(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill='toself',
                name=model,
                line_color=model_color
            ))
            fig_radar_single.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0.8, 1.0])),
                height=300,
                title="Perfil de Performance",
                margin=dict(t=40, b=20, l=40, r=40),
                showlegend=False
            )
            content_row.append(dbc.Col(dcc.Graph(figure=fig_radar_single, config={'displayModeBar': False}), width=6))
        
        # 3. Relatório de Texto (Agora como Tabela Estilizada)
        if report_path:
            try:
                with open(report_path, 'r') as f:
                    report_text = f.read()
                
                # Usar a nova função de renderização de tabela
                report_table = render_report_table(report_text, model_color)
                
                report_col = dbc.Col([
                    html.H6("Relatório Detalhado", className="mt-3"),
                    report_table
                ], width=12)
            except Exception as e:
                report_col = dbc.Col(html.P(f"Erro ao processar relatório: {e}"), width=12)
        else:
            report_col = dbc.Col(html.P("Relatório não encontrado."), width=12)

        children.append(header)
        children.append(dbc.Row(content_row))
        children.append(dbc.Row(report_col))
        
        # 4. Histórico ANN
        if 'ANN' in model:
            img_src = get_image_src("ann_training_curves.png")
            if img_src:
                children.append(dbc.Row(dbc.Col(
                    html.Img(src=img_src, style={"width": "100%", "borderRadius": "8px", "marginTop": "20px", "border": "1px solid #ddd"}),
                    width=12
                )))
            
    return children
