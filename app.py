import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from config import settings
import base64

# Inicialização da App
app = dash.Dash(
    __name__, 
    use_pages=True, 
    external_stylesheets=[dbc.themes.BOOTSTRAP, "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap"],
    suppress_callback_exceptions=True
)
server = app.server

# Carregar Logotipo
logo_path = settings.BASE_DIR / 'img' / 'capa_projeto_tm.png'
encoded_logo = ""
if logo_path.exists():
    encoded_logo = base64.b64encode(open(logo_path, 'rb').read()).decode('ascii')
    logo_src = f"data:image/png;base64,{encoded_logo}"
else:
    logo_src = ""

# --- Navbar ---
navbar = dbc.Navbar(
    dbc.Container([
        html.A(
            dbc.Row([
                # Aumentado height para 60px
                dbc.Col(html.Img(src=logo_src, height="60px", className="me-3 rounded-circle") if logo_src else None),
                dbc.Col(dbc.NavbarBrand("AI/Human Text Analysis Studio", className="ms-2", style={'fontSize': '1.5rem'})),
            ], align="center", className="g-0"),
            href="/",
            style={"textDecoration": "none"},
        ),
        dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
        dbc.Collapse(
            dbc.Nav([
                dbc.NavItem(dbc.NavLink("Analisador Interativo", href="/", active="exact")),
                dbc.NavItem(dbc.NavLink("Laboratório de Modelos", href="/model-lab", active="exact")),
                dbc.NavItem(dbc.NavLink("Resumo do Estudo", href="/study-summary", active="exact")),
            ], className="ms-auto", navbar=True),
            id="navbar-collapse",
            navbar=True,
        ),
    ]),
    color="dark",
    dark=True,
    className="mb-4 shadow-sm",
    style={'padding': '10px 0'} # Mais padding vertical
)

# --- Layout Principal ---
app.layout = html.Div([
    navbar,
    dash.page_container
], style={'fontFamily': 'Inter, sans-serif', 'backgroundColor': '#f8f9fa', 'minHeight': '100vh'})

if __name__ == '__main__':
    print("Iniciando servidor...")
    app.run_server(debug=True)
