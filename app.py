import os
import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, dash_table

DATA_PATH = "data-samples/bateria_pruebas_soc_sample.csv"

app = Dash(__name__)
server = app.server

def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    return pd.DataFrame()

df = load_data()

def find_column(possible_names):
    lower_map = {c.lower(): c for c in df.columns}
    for name in possible_names:
        if name.lower() in lower_map:
            return lower_map[name.lower()]
    return None

category_col = find_column([
    "tipo_evento",
    "categoria",
    "tipo",
    "event_type",
    "category",
    "prueba",
    "test_type"
])

result_col = find_column([
    "resultado",
    "estado",
    "status",
    "result"
])

total_events = len(df)
total_columns = len(df.columns)

if category_col:
    category_counts = df[category_col].fillna("sin_categoria").value_counts().reset_index()
    category_counts.columns = ["categoria", "total"]
else:
    category_counts = pd.DataFrame({
        "categoria": ["dataset_cargado"],
        "total": [total_events]
    })

fig = px.bar(
    category_counts,
    x="categoria",
    y="total",
    title="Eventos SOC por categoria"
)

fig.update_layout(
    paper_bgcolor="#06111f",
    plot_bgcolor="#06111f",
    font_color="#eaf6ff",
    xaxis_title="Categoria",
    yaxis_title="Total"
)

app.layout = html.Div(
    style={
        "background": "linear-gradient(180deg, #050914 0%, #071426 100%)",
        "minHeight": "100vh",
        "color": "#eaf6ff",
        "fontFamily": "Segoe UI, Arial, sans-serif",
        "padding": "32px"
    },
    children=[
        html.Div(
            style={"maxWidth": "1180px", "margin": "0 auto"},
            children=[
                html.Div(
                    "PhisDefense SOC Dashboard Demo",
                    style={
                        "color": "#38f8ff",
                        "fontWeight": "900",
                        "letterSpacing": "0.08em",
                        "textTransform": "uppercase",
                        "marginBottom": "12px"
                    }
                ),

                html.H1(
                    "Dashboard SOC interactivo",
                    style={
                        "fontSize": "44px",
                        "margin": "0 0 12px",
                        "lineHeight": "1"
                    }
                ),

                html.P(
                    "Demo interactiva basada en el dataset SOC publico y sanitizado del proyecto PhisDefense. "
                    "El objetivo es mostrar metricas, categorias y eventos procesados sin depender del servidor original.",
                    style={
                        "color": "#9db5c9",
                        "fontSize": "18px",
                        "maxWidth": "850px"
                    }
                ),

                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "repeat(3, minmax(0, 1fr))",
                        "gap": "16px",
                        "marginTop": "28px",
                        "marginBottom": "28px"
                    },
                    children=[
                        html.Div(
                            style={
                                "background": "rgba(10,25,45,.90)",
                                "border": "1px solid rgba(56,248,255,.22)",
                                "borderRadius": "20px",
                                "padding": "22px"
                            },
                            children=[
                                html.Div("Eventos cargados", style={"color": "#9db5c9"}),
                                html.Div(str(total_events), style={"fontSize": "36px", "fontWeight": "900", "color": "#38f8ff"})
                            ]
                        ),
                        html.Div(
                            style={
                                "background": "rgba(10,25,45,.90)",
                                "border": "1px solid rgba(56,248,255,.22)",
                                "borderRadius": "20px",
                                "padding": "22px"
                            },
                            children=[
                                html.Div("Columnas dataset", style={"color": "#9db5c9"}),
                                html.Div(str(total_columns), style={"fontSize": "36px", "fontWeight": "900", "color": "#38f8ff"})
                            ]
                        ),
                        html.Div(
                            style={
                                "background": "rgba(10,25,45,.90)",
                                "border": "1px solid rgba(56,248,255,.22)",
                                "borderRadius": "20px",
                                "padding": "22px"
                            },
                            children=[
                                html.Div("Categorias detectadas", style={"color": "#9db5c9"}),
                                html.Div(str(len(category_counts)), style={"fontSize": "36px", "fontWeight": "900", "color": "#38f8ff"})
                            ]
                        )
                    ]
                ),

                html.Div(
                    style={
                        "background": "rgba(10,25,45,.90)",
                        "border": "1px solid rgba(255,255,255,.09)",
                        "borderRadius": "24px",
                        "padding": "20px",
                        "marginBottom": "28px"
                    },
                    children=[
                        dcc.Graph(figure=fig)
                    ]
                ),

                html.H2("Tabla SOC sanitizada"),

                dash_table.DataTable(
                    data=df.head(100).to_dict("records"),
                    columns=[{"name": c, "id": c} for c in df.columns],
                    page_size=10,
                    style_table={"overflowX": "auto"},
                    style_header={
                        "backgroundColor": "#0d2340",
                        "color": "#eaf6ff",
                        "fontWeight": "bold",
                        "border": "1px solid #214461"
                    },
                    style_cell={
                        "backgroundColor": "#081827",
                        "color": "#eaf6ff",
                        "border": "1px solid #214461",
                        "fontFamily": "Segoe UI, Arial",
                        "fontSize": "13px",
                        "padding": "8px",
                        "textAlign": "left",
                        "maxWidth": "280px",
                        "whiteSpace": "normal"
                    }
                )
            ]
        )
    ]
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)