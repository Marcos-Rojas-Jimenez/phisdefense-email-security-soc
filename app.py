#!/usr/bin/env python3
"""
Dashboard SOC para el TFM de infraestructura segura de correo.

Ejecucion:
    python3 dashboard_soc.py

Acceso:
    http://Render demo

Dependencias:
    pip install dash plotly dash-bootstrap-components pandas

Nota de arquitectura:
    La ruta del CSV se concentra en CSV_PATH para poder cambiar la fuente de
    datos en el futuro sin reescribir el dashboard.
"""

from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Input, Output, dash_table, dcc, html


CSV_PATH = Path("data/bateria_pruebas.csv")
SOC_CSV_PATH = Path("data/bateria_pruebas_soc.csv")

# Alias de columnas. El dashboard intenta adaptarse a distintos CSVs para que
# la migracion posterior al CSV DMARC sea sencilla.
COLUMN_ALIASES = {
    "classification": [
        "classification",
        "clasificacion",
        "clasificacion_real",
        "resultado",
        "resultado_real",
        "tipo_evento",
        "estado",
    ],
    "final_location": [
        "ubicacion_final",
        "ubicacion",
        "destino",
        "carpeta",
        "folder",
        "final_location",
        "disposition",
        "accion",
    ],
    "message_count": [
        "message_count",
        "mensajes",
        "cantidad",
        "count",
        "total",
        "numero_mensajes",
    ],
    "test_id": [
        "id",
        "test_id",
        "prueba",
        "nombre_prueba",
        "archivo",
        "report_id",
    ],
    "spf_result": ["spf_result", "spf", "resultado_spf"],
    "dkim_result": ["dkim_result", "dkim", "resultado_dkim"],
    "dmarc_result": ["dmarc_result", "dmarc", "resultado_dmarc"],
    "expected_classification": [
        "clasificacion_esperada",
        "expected_classification",
        "expected",
        "ground_truth",
        "verdad_real",
        "etiqueta_real",
    ],
    "predicted_classification": [
        "clasificacion_detectada",
        "predicted_classification",
        "prediccion",
        "prediction",
        "resultado_obtenido",
    ],
}

COLORS = {
    "page": "#06111f",
    "page_2": "#08182b",
    "sidebar": "#071426",
    "topbar": "#0a1d33",
    "panel": "#0d2238",
    "panel_2": "#102b47",
    "panel_3": "#133557",
    "border": "#1e4b70",
    "text": "#ecf6ff",
    "muted": "#90a8bf",
    "blue": "#2f8cff",
    "cyan": "#23d7ff",
    "green": "#35d07f",
    "red": "#ff4d67",
    "yellow": "#ffd166",
    "orange": "#ff9f43",
    "purple": "#9b8cff",
}

GRAPH_CONFIG = {"displayModeBar": False, "responsive": True}
DEFAULT_CHART_HEIGHT = 360
DONUT_CHART_HEIGHT = 330
BAR_CHART_HEIGHT = 330
LARGE_CHART_HEIGHT = 310

EVENT_COLORS = {
    "legitimo": COLORS["green"],
    "legitimos": COLORS["green"],
    "legitimate": COLORS["green"],
    "pass": COLORS["green"],
    "ok": COLORS["green"],
    "spoofing": COLORS["red"],
    "suplantacion": COLORS["red"],
    "malicioso": COLORS["red"],
    "fail": COLORS["red"],
    "sospechoso": COLORS["yellow"],
    "sospechosos": COLORS["yellow"],
    "suspicious": COLORS["yellow"],
    "warning": COLORS["orange"],
    "advertencia": COLORS["orange"],
}


def normalize_text(value):
    """Normaliza texto para agrupar categorias de forma estable."""
    if pd.isna(value):
        return ""
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def find_column(df, logical_name):
    """Devuelve la primera columna existente para un nombre logico."""
    normalized_columns = {normalize_text(col): col for col in df.columns}
    for alias in COLUMN_ALIASES.get(logical_name, []):
        if normalize_text(alias) in normalized_columns:
            return normalized_columns[normalize_text(alias)]
    return None


def load_csv(csv_path=CSV_PATH):
    """
    Carga el CSV principal y anade columnas internas normalizadas.

    La funcion devuelve (df, metadata, error). El layout usa metadata para saber
    que columnas reales representan clasificacion, ubicacion final y volumen.
    """
    if not csv_path.exists():
        return pd.DataFrame(), {}, f"No se ha encontrado el CSV en {csv_path}"

    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        return pd.DataFrame(), {}, f"No se pudo leer el CSV en {csv_path}: {exc}"

    df = df.fillna("")
    metadata = {
        "classification": find_column(df, "classification"),
        "final_location": find_column(df, "final_location"),
        "message_count": find_column(df, "message_count"),
        "test_id": find_column(df, "test_id"),
        "spf_result": find_column(df, "spf_result"),
        "dkim_result": find_column(df, "dkim_result"),
        "dmarc_result": find_column(df, "dmarc_result"),
        "expected_classification": find_column(df, "expected_classification"),
        "predicted_classification": find_column(df, "predicted_classification"),
    }

    if metadata["classification"] is None:
        df["_classification"] = "otros"
        metadata["classification"] = "_classification"
    else:
        df["_classification"] = df[metadata["classification"]].apply(normalize_text)

    if metadata["final_location"] is None:
        df["_final_location"] = "sin_ubicacion"
        metadata["final_location"] = "_final_location"
    else:
        df["_final_location"] = df[metadata["final_location"]].apply(normalize_text)

    if metadata["message_count"] is None:
        df["_message_count"] = 1
    else:
        df["_message_count"] = pd.to_numeric(df[metadata["message_count"]], errors="coerce")
        df["_message_count"] = df["_message_count"].fillna(1).astype(int)

    return df, metadata, None


def classify_bucket(value):
    """Mapea clasificaciones del CSV a las categorias ejecutivas del SOC."""
    normalized = normalize_text(value)
    if normalized in {"legitimo", "legitimos", "legitimate", "pass", "ok"}:
        return "legitimos"
    if normalized in {"spoofing", "suplantacion", "malicioso", "fail"}:
        return "spoofing"
    if normalized in {"sospechoso", "sospechosos", "suspicious", "warning", "advertencia"}:
        return "sospechosos"
    return "otros"


def calculate_kpis(df):
    """Calcula las metricas principales de la primera fila."""
    if df.empty:
        return {"total": 0, "legitimos": 0, "spoofing": 0, "otros": 0}

    buckets = df["_classification"].apply(classify_bucket)
    return {
        "total": int(len(df)),
        "legitimos": int((buckets == "legitimos").sum()),
        "spoofing": int((buckets == "spoofing").sum()),
        "otros": int((buckets.isin(["sospechosos", "otros"])).sum()),
    }


def aggregate(df, column):
    """Agrupa una columna usando _message_count para representar volumen."""
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=["categoria", "total"])

    grouped = (
        df.groupby(column, dropna=False)["_message_count"]
        .sum()
        .reset_index()
        .rename(columns={column: "categoria", "_message_count": "total"})
        .sort_values("total", ascending=False)
    )
    grouped["categoria"] = grouped["categoria"].replace("", "sin_valor").fillna("sin_valor")
    return grouped


def empty_figure(title, height=DEFAULT_CHART_HEIGHT):
    """Crea una grafica vacia cuando no hay datos cargados."""
    fig = go.Figure()
    fig.add_annotation(
        text="Sin datos disponibles",
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font={"color": COLORS["muted"], "size": 15},
    )
    fig.update_layout(title=title)
    return apply_chart_theme(fig, height=height)


def apply_chart_theme(fig, height=DEFAULT_CHART_HEIGHT):
    """Aplica estilo comun inspirado en consolas SOC modernas."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor=COLORS["panel"],
        plot_bgcolor=COLORS["panel"],
        font={"family": "Inter, Segoe UI, Arial, sans-serif", "color": COLORS["text"]},
        title={"x": 0.02, "xanchor": "left", "font": {"size": 18, "color": COLORS["text"]}},
        height=height,
        autosize=True,
        margin={"l": 18, "r": 18, "t": 48, "b": 34},
        legend={"orientation": "h", "y": -0.2},
        hoverlabel={"bgcolor": COLORS["panel_2"], "font_size": 13},
    )
    fig.update_xaxes(gridcolor="rgba(144,168,191,0.13)", zerolinecolor=COLORS["border"])
    fig.update_yaxes(gridcolor="rgba(144,168,191,0.13)", zerolinecolor=COLORS["border"])
    return fig


def create_metric_card(title, value, subtitle, accent, icon):
    """Crea una tarjeta KPI para la primera fila del dashboard."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        display_value = f"{value:,}".replace(",", ".")
    else:
        display_value = str(value)

    return dbc.Card(
        dbc.CardBody(
            [
                html.Div([html.Span(icon), html.Span(title)], className="metric-label"),
                html.Div(display_value, className="metric-number"),
                html.Div(subtitle, className="metric-subtitle"),
            ]
        ),
        className="metric-card",
        style={"--accent": accent},
    )


def create_distribution_chart(df):
    """Grafico circular con la distribucion general de eventos."""
    if df.empty:
        return empty_figure("Distribucion de eventos", height=DONUT_CHART_HEIGHT)

    temp = df.copy()
    temp["bucket"] = temp["_classification"].apply(classify_bucket)
    grouped = aggregate(temp, "bucket")

    fig = px.pie(
        grouped,
        names="categoria",
        values="total",
        hole=0.62,
        color="categoria",
        color_discrete_map={
            "legitimos": COLORS["green"],
            "spoofing": COLORS["red"],
            "sospechosos": COLORS["yellow"],
            "otros": COLORS["blue"],
        },
    )
    fig.update_traces(
        textinfo="percent+label",
        textposition="inside",
        marker={"line": {"color": COLORS["panel"], "width": 2}},
    )
    fig.update_layout(title="Distribucion de eventos")
    return apply_chart_theme(fig, height=DONUT_CHART_HEIGHT)


def create_classification_chart(df):
    """Grafico de barras con la clasificacion real del CSV."""
    grouped = aggregate(df, "_classification")
    if grouped.empty:
        return empty_figure("Clasificacion real", height=BAR_CHART_HEIGHT)

    fig = px.bar(
        grouped,
        x="categoria",
        y="total",
        color="categoria",
        color_discrete_map=EVENT_COLORS,
        labels={"categoria": "Clasificacion", "total": "Eventos"},
    )
    fig.update_layout(title="Clasificacion real", showlegend=False)
    fig.update_traces(marker_line_color="rgba(255,255,255,0.18)", marker_line_width=1)
    return apply_chart_theme(fig, height=BAR_CHART_HEIGHT)


def create_location_chart(df):
    """Gráfico de ubicación final agrupado: entregado, rechazado, spam y validación técnica."""
    if df is None or df.empty:
        return empty_figure("Ubicación final", height=LARGE_CHART_HEIGHT)

    temp = df.copy()

    if "_final_location" not in temp.columns:
        temp["_final_location"] = ""

    candidate_cols = [
        "ubicacion_final",
        "final_location",
        "ubicacion",
        "accion",
        "disposition",
    ]

    current = temp["_final_location"].astype(str).fillna("").str.strip()

    for col in candidate_cols:
        if col in temp.columns:
            values = temp[col].astype(str).fillna("").str.strip()
            mask = (
                (current == "") |
                (current.str.lower() == "nan") |
                (current.str.lower() == "none") |
                (current.str.lower() == "sin_valor")
            )
            temp.loc[mask, "_final_location"] = values[mask]
            current = temp["_final_location"].astype(str).fillna("").str.strip()

    temp["_final_location"] = (
        temp["_final_location"]
        .astype(str)
        .fillna("")
        .str.strip()
        .replace({"": "sin_valor", "nan": "sin_valor", "None": "sin_valor"})
    )

    def canonical_location(value):
        value = normalize_text(value)

        if "spam" in value or "promoc" in value:
            return "spam"

        if (
            "rechaz" in value or
            "reject" in value or
            "blocked" in value or
            "bloque" in value
        ):
            return "rechazado"

        if (
            "inbox" in value or
            "enviado" in value or
            "sent" in value or
            "maildir" in value or
            "local" in value
        ):
            return "entregado"

        if (
            "tls" in value or
            "tls_ok" in value or
            "validacion" in value or
            "validación" in value
        ):
            return "validación técnica"

        return "otros"

    temp["_location_group"] = temp["_final_location"].apply(canonical_location)

    grouped = (
        temp["_location_group"]
        .value_counts(dropna=False)
        .reset_index()
    )

    grouped.columns = ["categoria", "total"]
    grouped["total"] = grouped["total"].astype(int)

    preferred_order = {
        "spam": 1,
        "rechazado": 2,
        "entregado": 3,
        "validación técnica": 4,
        "otros": 5,
    }

    grouped["orden"] = grouped["categoria"].map(preferred_order).fillna(99)
    grouped = grouped.sort_values(["orden", "total"], ascending=[False, True])

    if grouped.empty:
        return empty_figure("Ubicación final", height=LARGE_CHART_HEIGHT)

    def location_color(label):
        label = normalize_text(label)

        if label == "spam":
            return COLORS["orange"]

        if label == "rechazado":
            return COLORS["red"]

        if label == "entregado":
            return COLORS["green"]

        if "validacion" in label or "validación" in label:
            return COLORS["purple"]

        return COLORS["blue"]

    colors = [location_color(x) for x in grouped["categoria"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=grouped["total"],
                y=grouped["categoria"],
                orientation="h",
                marker=dict(
                    color=colors,
                    line=dict(color="rgba(236,246,255,0.20)", width=1),
                ),
                text=grouped["total"],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Eventos: %{x}<extra></extra>",
            )
        ]
    )

    max_value = int(grouped["total"].max()) if not grouped.empty else 1

    fig.update_layout(
        title="Ubicación final",
        xaxis_title="Eventos",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=112, r=42, t=56, b=48),
        bargap=0.30,
    )

    fig.update_xaxes(
        gridcolor="rgba(144,168,191,0.13)",
        zerolinecolor=COLORS["border"],
        range=[0, max_value * 1.15],
    )

    fig.update_yaxes(
        gridcolor="rgba(144,168,191,0.04)",
        zeroline=False,
    )

    return apply_chart_theme(fig, height=LARGE_CHART_HEIGHT)


def create_result_chart(df, column, title):
    """Grafico circular para resultados SPF, DKIM o DMARC."""
    if df.empty or not column or column not in df.columns:
        return empty_figure(title, height=DONUT_CHART_HEIGHT)

    temp = df.copy()
    temp["_auth_result"] = temp[column].apply(normalize_text)
    grouped = aggregate(temp, "_auth_result")
    if grouped.empty:
        return empty_figure(title, height=DONUT_CHART_HEIGHT)

    fig = px.pie(
        grouped,
        names="categoria",
        values="total",
        hole=0.58,
        color="categoria",
        color_discrete_map={
            "pass": COLORS["green"],
            "fail": COLORS["red"],
            "softfail": COLORS["yellow"],
            "neutral": COLORS["orange"],
            "none": COLORS["muted"],
            "temperror": COLORS["purple"],
            "permerror": COLORS["purple"],
        },
    )
    fig.update_traces(
        textinfo="percent+label",
        textposition="inside",
        marker={"line": {"color": COLORS["panel"], "width": 2}},
    )
    fig.update_layout(title=title)
    return apply_chart_theme(fig, height=DONUT_CHART_HEIGHT)



def ultra_normalize_donas(figure):
    """Normaliza y centra todas las donas/pies del dashboard."""
    if figure is None:
        return figure

    try:
        has_pie = False

        for trace in figure.data:
            if getattr(trace, "type", "") == "pie":
                has_pie = True
                trace.hole = 0.58
                trace.textinfo = "label+percent"
                trace.textposition = "inside"
                trace.hovertemplate = "%{label}<br>Eventos: %{value}<br>%{percent}<extra></extra>"
                trace.sort = False
                trace.automargin = False

                try:
                    trace.domain = dict(x=[0.15, 0.85], y=[0.12, 0.88])
                except Exception:
                    pass

                try:
                    trace.insidetextorientation = "radial"
                except Exception:
                    pass

                try:
                    trace.textfont = dict(size=11, color="#06111f")
                except Exception:
                    pass

                try:
                    colors = None
                    if trace.marker and hasattr(trace.marker, "colors"):
                        colors = trace.marker.colors

                    trace.marker = dict(
                        colors=colors,
                        line=dict(color="rgba(236,246,255,0.90)", width=1.3),
                    )
                except Exception:
                    pass

        if has_pie:
            figure.update_layout(
                title=dict(
                    x=0.5,
                    xanchor="center",
                    font=dict(size=17, color=COLORS["text"]),
                ),
                showlegend=False,
                margin=dict(l=6, r=6, t=54, b=24),
                hoverlabel=dict(
                    bgcolor="rgba(3,9,20,0.94)",
                    bordercolor="rgba(35,215,255,0.55)",
                    font=dict(color="#ecf6ff", size=13),
                ),
                uniformtext_minsize=9,
                uniformtext_mode="show",
                transition=dict(duration=260, easing="cubic-in-out"),
            )
        else:
            figure.update_layout(
                hoverlabel=dict(
                    bgcolor="rgba(3,9,20,0.94)",
                    bordercolor="rgba(35,215,255,0.55)",
                    font=dict(color="#ecf6ff", size=13),
                ),
                transition=dict(duration=260, easing="cubic-in-out"),
            )

    except Exception:
        return figure

    return figure



def center_global_distribution_donut(figure):
    """Centra únicamente la dona de Visión general sin romper hover/click."""
    if figure is None:
        return figure

    try:
        for trace in figure.data:
            if getattr(trace, "type", "") == "pie":
                # Centrado SOLO para la dona global.
                trace.domain = dict(
                    x=[0.08, 0.92],
                    y=[0.08, 0.92],
                )

                # IMPORTANTE:
                # No tocar trace.pull aquí.
                # El pull lo usa la interacción hover/click para resaltar sectores.
                trace.automargin = False

        figure.update_layout(
            title=dict(
                text="Distribución global de eventos",
                x=0.5,
                xanchor="center",
            ),
            margin=dict(l=0, r=0, t=52, b=10),
            showlegend=False,
            transition=dict(duration=260, easing="cubic-in-out"),
        )

    except Exception:
        return figure

    return figure


def create_graph(figure, height=DEFAULT_CHART_HEIGHT, graph_id=None, clear_on_unhover=False):
    """Envuelve dcc.Graph con altura fija y mejora visual de donas."""
    height_px = f"{height}px"
    figure = ultra_normalize_donas(figure)

    # Centrado específico SOLO para la dona de Visión general.
    if graph_id == "global-distribution-chart":
        figure = center_global_distribution_donut(figure)

    graph_kwargs = {
        "figure": figure,
        "config": GRAPH_CONFIG,
        "style": {"height": height_px, "width": "100%"},
        "responsive": True,
        "clear_on_unhover": clear_on_unhover,
    }

    if graph_id:
        graph_kwargs["id"] = graph_id

    return html.Div(
        dcc.Graph(**graph_kwargs),
        className="chart-frame donut-interactive-frame",
        style={
            "height": height_px,
            "overflow": "hidden",
            "width": "100%",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
        },
    )


def create_data_table(df):
    """Crea tabla interactiva optimizada, legible y con estilos SOC."""
    if df is None or df.empty:
        visible_df = pd.DataFrame()
    else:
        visible_df = df.drop(columns=[col for col in df.columns if str(col).startswith("_")], errors="ignore").copy()

    friendly_names = {
        "id_prueba": "ID",
        "id": "ID",
        "test_id": "ID",
        "tipo": "Tipo",
        "origen": "Origen",
        "destino": "Destino",
        "asunto": "Asunto",
        "resultado_esperado": "Esperado",
        "resultado_esper": "Esperado",
        "spf": "SPF",
        "spf_result": "SPF",
        "dkim": "DKIM",
        "dkim_result": "DKIM",
        "dmarc": "DMARC",
        "dmarc_result": "DMARC",
        "ubicacion_final": "Ubicación",
        "final_location": "Ubicación",
        "clasificacion_real": "Clasificación",
        "classification": "Clasificación",
        "clasificacion": "Clasificación",
        "observaciones": "Observaciones",
        "fuente": "Fuente",
    }

    preferred_order = [
        "id_prueba", "id", "test_id",
        "tipo",
        "origen",
        "destino",
        "asunto",
        "resultado_esperado", "resultado_esper",
        "spf", "spf_result",
        "dkim", "dkim_result",
        "dmarc", "dmarc_result",
        "ubicacion_final", "final_location",
        "clasificacion_real", "classification", "clasificacion",
        "fuente",
        "observaciones",
    ]

    if not visible_df.empty:
        ordered = []
        for col in preferred_order:
            if col in visible_df.columns and col not in ordered:
                ordered.append(col)

        for col in visible_df.columns:
            if col not in ordered:
                ordered.append(col)

        visible_df = visible_df[ordered]

    columns = [
        {
            "name": friendly_names.get(col, str(col).replace("_", " ").title()),
            "id": col,
            "deletable": False,
            "selectable": True,
        }
        for col in visible_df.columns
    ]
    # Estilos condicionales por valor, sin modificar datos.
    conditional_styles = []

    def add_contains(column_candidates, value, bg, fg="#ecf6ff", weight="700"):
        for col in column_candidates:
            if col in visible_df.columns:
                conditional_styles.append({
                    "if": {"filter_query": f"{{{col}}} contains '{value}'", "column_id": col},
                    "backgroundColor": bg,
                    "color": fg,
                    "fontWeight": weight,
                })

    def add_equals(column_candidates, value, bg, fg="#ecf6ff", weight="700"):
        for col in column_candidates:
            if col in visible_df.columns:
                conditional_styles.append({
                    "if": {"filter_query": f"{{{col}}} = '{value}'", "column_id": col},
                    "backgroundColor": bg,
                    "color": fg,
                    "fontWeight": weight,
                })

    auth_cols = ["spf", "spf_result", "dkim", "dkim_result", "dmarc", "dmarc_result"]
    class_cols = ["clasificacion_real", "classification", "clasificacion"]
    loc_cols = ["ubicacion_final", "final_location"]

    add_equals(auth_cols, "pass", "rgba(53,208,127,.20)", "#8ff0b9")
    add_equals(auth_cols, "fail", "rgba(255,77,103,.22)", "#ff9aad")
    add_equals(auth_cols, "none", "rgba(144,168,191,.16)", "#c7d4df")
    add_equals(auth_cols, "no_aplica", "rgba(144,168,191,.13)", "#b9c7d3")
    add_equals(auth_cols, "temperror", "rgba(155,140,255,.18)", "#c9c1ff")
    add_equals(auth_cols, "permerror", "rgba(155,140,255,.18)", "#c9c1ff")

    add_contains(class_cols, "legit", "rgba(53,208,127,.16)", "#8ff0b9")
    add_contains(class_cols, "spoof", "rgba(255,77,103,.20)", "#ff9aad")
    add_contains(class_cols, "reject", "rgba(255,77,103,.20)", "#ff9aad")
    add_contains(class_cols, "relay", "rgba(255,77,103,.18)", "#ff9aad")
    add_contains(class_cols, "lookalike", "rgba(255,159,67,.22)", "#ffc38a")
    add_contains(class_cols, "dkim", "rgba(255,209,102,.18)", "#ffe19a")
    add_contains(class_cols, "spf", "rgba(255,209,102,.18)", "#ffe19a")
    add_contains(class_cols, "sospech", "rgba(255,159,67,.22)", "#ffc38a")

    add_contains(loc_cols, "sent", "rgba(53,208,127,.16)", "#8ff0b9")
    add_contains(loc_cols, "enviado", "rgba(53,208,127,.16)", "#8ff0b9")
    add_contains(loc_cols, "inbox", "rgba(53,208,127,.16)", "#8ff0b9")
    add_contains(loc_cols, "maildir", "rgba(35,215,255,.15)", "#8eefff")
    add_contains(loc_cols, "spam", "rgba(255,159,67,.22)", "#ffc38a")
    add_contains(loc_cols, "rechaz", "rgba(255,77,103,.20)", "#ff9aad")
    add_contains(loc_cols, "reject", "rgba(255,77,103,.20)", "#ff9aad")

    # Estilo por filas completas para lectura rápida
    for col in class_cols:
        if col in visible_df.columns:
            conditional_styles.extend([
                {
                    "if": {"filter_query": f"{{{col}}} contains 'spoofing'"},
                    "backgroundColor": "rgba(255,77,103,.08)",
                },
                {
                    "if": {"filter_query": f"{{{col}}} contains 'legitimo'"},
                    "backgroundColor": "rgba(53,208,127,.055)",
                },
                {
                    "if": {"filter_query": f"{{{col}}} contains 'lookalike'"},
                    "backgroundColor": "rgba(255,159,67,.075)",
                },
            ])


    # FIX_ACTIVE_SELECTED_TABLE_STATE
    # Evita el fondo blanco/celeste que Dash aplica a celdas activas o seleccionadas.
    conditional_styles.extend([
        {
            "if": {"state": "active"},
            "backgroundColor": "#071426",
            "color": "#ecf6ff",
            "border": "1px solid rgba(35,215,255,0.28)",
        },
        {
            "if": {"state": "selected"},
            "backgroundColor": "#071426",
            "color": "#ecf6ff",
            "border": "1px solid rgba(35,215,255,0.28)",
        },
    ])


    # FIX_FINAL_NO_WHITE_ACTIVE_SELECTED
    conditional_styles.extend([
        {
            "if": {"state": "active"},
            "backgroundColor": "#071426",
            "color": "#ecf6ff",
            "border": "1px solid rgba(35,215,255,0.20)",
        },
        {
            "if": {"state": "selected"},
            "backgroundColor": "#071426",
            "color": "#ecf6ff",
            "border": "1px solid rgba(35,215,255,0.20)",
        },
    ])
    # FIX_COLORES_ESTADO_TABLA
    # Colores visuales para estados de autenticación, ubicación y clasificación.
    # No modifica datos; solo añade estilos condicionales a la tabla.
    try:
        def _add_state_style(cols, value, bg, fg="#ecf6ff", weight="800"):
            for _col in cols:
                if _col in visible_df.columns:
                    conditional_styles.append({
                        "if": {"filter_query": f"{{{_col}}} contains '{value}'", "column_id": _col},
                        "backgroundColor": bg,
                        "color": fg,
                        "fontWeight": weight,
                    })

        _auth_cols = [
            "spf", "spf_result",
            "dkim", "dkim_result",
            "dmarc", "dmarc_result",
            "resultado_spf", "resultado_dkim", "resultado_dmarc",
        ]

        _class_cols = [
            "clasificacion_real",
            "classification",
            "clasificacion",
            "resultado",
            "resultado_real",
        ]

        _loc_cols = [
            "ubicacion_final",
            "final_location",
            "ubicacion",
            "accion",
            "disposition",
        ]

        _type_cols = [
            "tipo",
            "tipo_evento",
            "fuente",
        ]

        # Autenticación
        _add_state_style(_auth_cols, "pass", "rgba(34,197,94,0.24)", "#bbf7d0", "900")
        _add_state_style(_auth_cols, "fail", "rgba(239,68,68,0.30)", "#fecaca", "900")
        _add_state_style(_auth_cols, "none", "rgba(148,163,184,0.20)", "#e2e8f0", "800")
        _add_state_style(_auth_cols, "no_aplica", "rgba(100,116,139,0.22)", "#cbd5e1", "800")
        _add_state_style(_auth_cols, "temperror", "rgba(168,85,247,0.24)", "#e9d5ff", "900")
        _add_state_style(_auth_cols, "permerror", "rgba(168,85,247,0.24)", "#e9d5ff", "900")

        # Ubicación / acción final
        _add_state_style(_loc_cols, "sent", "rgba(34,197,94,0.20)", "#bbf7d0", "850")
        _add_state_style(_loc_cols, "enviado", "rgba(34,197,94,0.20)", "#bbf7d0", "850")
        _add_state_style(_loc_cols, "inbox", "rgba(34,197,94,0.20)", "#bbf7d0", "850")
        _add_state_style(_loc_cols, "maildir", "rgba(56,189,248,0.20)", "#bae6fd", "850")
        _add_state_style(_loc_cols, "spam", "rgba(249,115,22,0.26)", "#fed7aa", "900")
        _add_state_style(_loc_cols, "rechaz", "rgba(239,68,68,0.28)", "#fecaca", "900")
        _add_state_style(_loc_cols, "reject", "rgba(239,68,68,0.28)", "#fecaca", "900")
        _add_state_style(_loc_cols, "blocked", "rgba(239,68,68,0.28)", "#fecaca", "900")

        # Clasificación
        _add_state_style(_class_cols, "legit", "rgba(34,197,94,0.18)", "#bbf7d0", "850")
        _add_state_style(_class_cols, "spoof", "rgba(239,68,68,0.26)", "#fecaca", "900")
        _add_state_style(_class_cols, "reject", "rgba(239,68,68,0.26)", "#fecaca", "900")
        _add_state_style(_class_cols, "relay", "rgba(239,68,68,0.24)", "#fecaca", "900")
        _add_state_style(_class_cols, "lookalike", "rgba(249,115,22,0.28)", "#fed7aa", "900")
        _add_state_style(_class_cols, "typo", "rgba(249,115,22,0.28)", "#fed7aa", "900")
        _add_state_style(_class_cols, "dkim", "rgba(250,204,21,0.24)", "#fef08a", "900")
        _add_state_style(_class_cols, "spf", "rgba(250,204,21,0.24)", "#fef08a", "900")
        _add_state_style(_class_cols, "auth", "rgba(250,204,21,0.22)", "#fef08a", "850")
        _add_state_style(_class_cols, "recipient", "rgba(249,115,22,0.24)", "#fed7aa", "850")

        # Tipo / fuente
        _add_state_style(_type_cols, "legit", "rgba(34,197,94,0.16)", "#bbf7d0", "850")
        _add_state_style(_type_cols, "spoof", "rgba(239,68,68,0.20)", "#fecaca", "900")
        _add_state_style(_type_cols, "soc", "rgba(168,85,247,0.22)", "#e9d5ff", "900")

        # Estados nativos de Dash DataTable para evitar blanco/celeste
        conditional_styles.extend([
            {
                "if": {"state": "active"},
                "backgroundColor": "#071426",
                "color": "#ecf6ff",
                "border": "1px solid rgba(35,215,255,0.22)",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "#071426",
                "color": "#ecf6ff",
                "border": "1px solid rgba(35,215,255,0.22)",
            },
        ])
    except Exception:
        pass



    return dash_table.DataTable(
        cell_selectable=False,
        css=[
            {
                "selector": ".dash-spreadsheet td.cell--selected",
                "rule": "background-color: #071426 !important; color: #ecf6ff !important; border-color: rgba(35,215,255,.22) !important;"
            },
            {
                "selector": ".dash-spreadsheet td.focused",
                "rule": "background-color: #071426 !important; color: #ecf6ff !important; border-color: rgba(35,215,255,.22) !important;"
            },
            {
                "selector": ".dash-spreadsheet td.dash-cell.cell--selected",
                "rule": "background-color: #071426 !important; color: #ecf6ff !important; box-shadow: inset 0 0 0 1px rgba(35,215,255,.28) !important;"
            },
            {
                "selector": ".dash-spreadsheet td.dash-cell.focused",
                "rule": "background-color: #071426 !important; color: #ecf6ff !important; box-shadow: inset 0 0 0 1px rgba(35,215,255,.28) !important;"
            },
            {
                "selector": ".dash-spreadsheet tr:hover td",
                "rule": "background-color: rgba(35,215,255,.06) !important; color: #ecf6ff !important;"
            },
            {
                "selector": ".dash-spreadsheet td:hover",
                "rule": "background-color: rgba(35,215,255,.08) !important; color: #ecf6ff !important; outline: none !important;"
            },
            {
                "selector": ".dash-table-tooltip",
                "rule": "display: none !important; visibility: hidden !important; opacity: 0 !important;"
            },
        ],
        data=visible_df.to_dict("records"),
        columns=columns,
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=18,
        export_format="csv",
        export_headers="display",
        fixed_rows={"headers": True, "data": 0},
        style_as_list_view=True,
        style_table={
            "overflowX": "auto",
            "overflowY": "auto",
            "maxHeight": "720px",
            "minWidth": "100%",
            "backgroundColor": "#06111f",
            "borderRadius": "16px",
        },
        style_header={
            "backgroundColor": "#102b47",
            "color": "#23d7ff",
            "fontWeight": "800",
            "border": "1px solid rgba(35,215,255,.18)",
            "textAlign": "center",
            "padding": "10px 8px",
            "whiteSpace": "normal",
        },
        style_filter={
            "backgroundColor": "#071426",
            "color": "#ecf6ff",
            "border": "1px solid rgba(35,215,255,.12)",
            "padding": "4px",
        },
        style_cell={
            "backgroundColor": "#071426",
            "color": "#ecf6ff",
            "border": "1px solid rgba(35,215,255,.10)",
            "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
            "fontSize": "13px",
            "padding": "9px 10px",
            "textAlign": "center",
            "whiteSpace": "nowrap",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
            "maxWidth": "260px",
            "minWidth": "90px",
        },
        style_cell_conditional=[
            {"if": {"column_id": "id_prueba"}, "minWidth": "78px", "maxWidth": "92px", "fontWeight": "800"},
            {"if": {"column_id": "id"}, "minWidth": "78px", "maxWidth": "92px", "fontWeight": "800"},
            {"if": {"column_id": "tipo"}, "minWidth": "120px", "maxWidth": "150px"},
            {"if": {"column_id": "origen"}, "textAlign": "left", "minWidth": "210px", "maxWidth": "260px"},
            {"if": {"column_id": "destino"}, "textAlign": "left", "minWidth": "210px", "maxWidth": "260px"},
            {"if": {"column_id": "asunto"}, "textAlign": "left", "minWidth": "180px", "maxWidth": "250px"},
            {"if": {"column_id": "observaciones"}, "textAlign": "left", "minWidth": "320px", "maxWidth": "520px"},
        ],
        style_data={
            "backgroundColor": "#071426",
            "color": "#ecf6ff",
        },
        style_data_conditional=conditional_styles,
    )
def status_alert(df, metadata, error, search_value=None):
    """Muestra solo avisos accionables para no desplazar el layout."""
    if error:
        return dbc.Alert(error, color="danger", className="status-alert")
    if df.empty and search_value:
        return dbc.Alert("La busqueda no ha devuelto resultados.", color="warning", className="status-alert")
    return None


def filter_dataframe(df, search_value):
    """Aplica busqueda global sobre todas las columnas visibles."""
    if df.empty or not search_value:
        return df

    needle = normalize_text(search_value)
    visible_df = df.drop(columns=[col for col in df.columns if col.startswith("_")], errors="ignore")
    mask = visible_df.astype(str).apply(
        lambda row: row.str.lower().str.contains(needle.replace("_", " "), regex=False).any()
        or row.str.lower().str.replace("-", "_", regex=False).str.contains(needle, regex=False).any(),
        axis=1,
    )
    return df.loc[mask]


def filter_spoofing_events(df):
    """Filtra registros relacionados con spoofing o suplantacion."""
    if df.empty:
        return df

    spoofing_terms = {"spoofing", "suplantacion", "malicioso"}
    buckets = df["_classification"].apply(classify_bucket)
    text_match = df["_classification"].apply(
        lambda value: any(term in normalize_text(value) for term in spoofing_terms)
    )
    return df.loc[(buckets == "spoofing") | text_match]


def auth_metric_cards(df, metadata):
    """Crea tarjetas con conteos pass/fail para SPF, DKIM y DMARC."""
    cards = []
    for label, key, accent in [
        ("SPF", "spf_result", COLORS["cyan"]),
        ("DKIM", "dkim_result", COLORS["purple"]),
        ("DMARC", "dmarc_result", COLORS["green"]),
    ]:
        column = metadata.get(key)
        if column and column in df.columns:
            normalized = df[column].apply(normalize_text)
            passed = int((normalized == "pass").sum())
            failed = int((normalized == "fail").sum())
            cards.append(create_metric_card(label, passed, f"{failed} fallos detectados", accent, "AUTH"))
    return cards


def calculate_report_metrics(df, metadata):
    """Calcula metricas de informe para evaluar la demo de deteccion."""
    if df.empty:
        return {
            "precision": 0,
            "recall": 0,
            "false_positives": 0,
            "false_negatives": 0,
            "deliverability": 0,
            "rejection_rate": 0,
            "total": 0,
        }

    expected_col = metadata.get("expected_classification")
    predicted_col = metadata.get("predicted_classification")

    if expected_col and predicted_col and expected_col in df.columns and predicted_col in df.columns:
        expected_spoof = df[expected_col].apply(lambda value: classify_bucket(value) == "spoofing")
        predicted_spoof = df[predicted_col].apply(lambda value: classify_bucket(value) == "spoofing")
    else:
        # Aproximacion para la demo cuando aun no hay columnas de verdad/prediccion.
        expected_spoof = df["_classification"].apply(lambda value: classify_bucket(value) == "spoofing")
        predicted_spoof = expected_spoof

    true_positive = int((expected_spoof & predicted_spoof).sum())
    false_positive = int((~expected_spoof & predicted_spoof).sum())
    false_negative = int((expected_spoof & ~predicted_spoof).sum())
    precision = true_positive / (true_positive + false_positive) if (true_positive + false_positive) else 0
    recall = true_positive / (true_positive + false_negative) if (true_positive + false_negative) else 0

    location = df["_final_location"].apply(normalize_text)
    delivered = location.str.contains("entrada|inbox|entregado|delivered|none", regex=True)
    rejected = location.str.contains("rechaz|reject|rejected", regex=True)

    return {
        "precision": precision,
        "recall": recall,
        "false_positives": false_positive,
        "false_negatives": false_negative,
        "deliverability": float(delivered.mean()) if len(df) else 0,
        "rejection_rate": float(rejected.mean()) if len(df) else 0,
        "total": int(len(df)),
    }


def page_heading(kicker, title, text):
    """Cabecera reutilizable para paginas internas."""
    return html.Div(
        [html.Div([html.Div(kicker, className="section-kicker"), html.H2(title)]), html.P(text)],
        className="section-heading",
    )



def load_soc_csv(csv_path=SOC_CSV_PATH):

    # Reaplicar extras SOC reales persistentes antes de leer el CSV.
    try:
        _merge_script = Path("/opt/tfm-dashboard/scripts/merge_soc_extras_reales.py")
        if _merge_script.exists():
            __import__("subprocess").run(
                ["python3", str(_merge_script)],
                stdout=__import__("subprocess").DEVNULL,
                stderr=__import__("subprocess").DEVNULL,
                timeout=10,
            )
    except Exception:
        pass
    """Carga el CSV de pruebas SOC separadas de la bateria principal."""
    if not csv_path.exists():
        return pd.DataFrame(), f"No se ha encontrado el CSV SOC en {csv_path}"

    try:
        df_soc = pd.read_csv(csv_path)
    except Exception as exc:
        return pd.DataFrame(), f"No se pudo leer el CSV SOC en {csv_path}: {exc}"

    return df_soc, None


def calculate_soc_kpis(df_soc):
    """Calcula KPIs simples para las pruebas SOC."""
    if df_soc is None or df_soc.empty:
        return {
            "total": 0,
            "bloqueados": 0,
            "rechazados": 0,
            "open_relay": 0,
            "tasa_bloqueo": 0,
        }

    tipo = df_soc.get("tipo", pd.Series(dtype=str)).astype(str).str.lower()
    esperado = df_soc.get("resultado_esperado", pd.Series(dtype=str)).astype(str).str.lower()
    ubicacion = df_soc.get("ubicacion_final", pd.Series(dtype=str)).astype(str).str.lower()
    clasificacion = df_soc.get("clasificacion_real", pd.Series(dtype=str)).astype(str).str.lower()

    total = len(df_soc)
    bloqueados = int(((esperado == "bloqueado") | (ubicacion == "rechazado") | (clasificacion == "relay_denied")).sum())
    rechazados = int((ubicacion == "rechazado").sum())
    open_relay = int((tipo == "open_relay_test").sum())
    tasa_bloqueo = bloqueados / total if total else 0

    return {
        "total": total,
        "bloqueados": bloqueados,
        "rechazados": rechazados,
        "open_relay": open_relay,
        "tasa_bloqueo": tasa_bloqueo,
    }



def create_distribution_chart_global(df, soc_df, highlight_label=None):
    """Dona global interactiva: resalta sectores al hacer hover/click."""
    kpis = calculate_kpis(df)
    soc_kpis = calculate_soc_kpis(soc_df)

    labels = ["legítimos", "spoofing"]
    values = [kpis["legitimos"], kpis["spoofing"]]
    colors = [COLORS["green"], COLORS["red"]]

    if soc_kpis["total"] > 0:
        labels.append("Pruebas SOC")
        values.append(soc_kpis["total"])
        colors.append(COLORS["purple"])

    total = sum(values) if sum(values) else 1

    text_values = []
    pulls = []
    line_widths = []

    for label, value in zip(labels, values):
        percent = value / total * 100

        if label == "Pruebas SOC":
            text_values.append(f"Pruebas<br>SOC<br>{percent:.1f}%")
        else:
            text_values.append(f"{label}<br>{percent:.1f}%")

        if highlight_label == label:
            pulls.append(0.085)
            line_widths.append(4)
        else:
            pulls.append(0.0)
            line_widths.append(1)

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(
                    colors=colors,
                    line=dict(color="#ecf6ff", width=line_widths),
                ),
                pull=pulls,
                text=text_values,
                textinfo="text",
                textposition="inside",
                insidetextorientation="radial",
                textfont=dict(size=10, color="#06111f"),
                hovertemplate="%{label}<br>Eventos: %{value}<br>%{percent}<extra></extra>",
                sort=False,
                direction="clockwise",
                rotation=0,
                domain=dict(
                    x=[0.08, 0.92],
                    y=[0.08, 0.92],
                ),
            )
        ]
    )

    fig.update_layout(
        title="Distribución global de eventos",
        title_x=0.5,
        title_xanchor="center",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"], size=13),
        showlegend=False,
        margin=dict(l=0, r=0, t=52, b=10),
        uniformtext_minsize=8,
        uniformtext_mode="show",
        transition=dict(duration=260, easing="cubic-in-out"),
    )


    # FIX_TOTAL_CENTRO_DONA_GLOBAL
    # Total en el centro SOLO de la dona de Visión general.
    try:
        fig.add_annotation(
            text=f"<b>{int(total)}</b><br><span style='font-size:12px'>eventos</span>",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            align="center",
            font=dict(
                size=28,
                color=COLORS["text"],
                family="Inter, Segoe UI, Arial, sans-serif",
            ),
            bgcolor="rgba(3,9,20,0.20)",
            bordercolor="rgba(35,215,255,0.0)",
        )
    except Exception:
        pass

    return fig


def create_classification_chart_global(df, soc_df):
    """Gráfica de clasificación global: legítimos, spoofing y Pruebas SOC."""
    kpis = calculate_kpis(df)
    soc_kpis = calculate_soc_kpis(soc_df)

    legitimos = int(kpis.get("legitimos", 0))
    spoofing = int(kpis.get("spoofing", 0))
    pruebas_soc = int(soc_kpis.get("total", 0))

    labels = ["legítimos", "spoofing", "Pruebas SOC"]
    values = [legitimos, spoofing, pruebas_soc]
    colors = [COLORS["green"], COLORS["red"], COLORS["purple"]]

    total = sum(values) if sum(values) else 1

    text_labels = [
        f"{value}<br>{(value / total * 100):.1f}%"
        for value in values
    ]

    max_value = max(values) if values else 1
    y_max = max(max_value * 1.25, 5)

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=text_labels,
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x}<br>Eventos: %{y}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title="Clasificación global",
        xaxis_title="Clasificación",
        yaxis_title="Eventos",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=40, r=20, t=70, b=60),
        showlegend=False,
    )

    fig.update_xaxes(
        gridcolor="rgba(255,255,255,0.08)",
        categoryorder="array",
        categoryarray=labels,
    )

    fig.update_yaxes(
        gridcolor="rgba(255,255,255,0.08)",
        range=[0, y_max],
        rangemode="tozero",
        zeroline=True,
        zerolinecolor="rgba(255,255,255,0.25)",
    )

    return fig



def normalize_location_for_global_chart(df):
    """Normaliza ubicación final para que la gráfica global incluya principal + SOC."""
    if df is None or df.empty:
        return pd.DataFrame()

    temp = df.copy()

    if "_final_location" not in temp.columns:
        temp["_final_location"] = ""

    # Rellenar _final_location desde columnas reales si faltan valores.
    candidate_cols = [
        "ubicacion_final",
        "final_location",
        "ubicacion",
        "accion",
        "disposition",
    ]

    current = temp["_final_location"].astype(str).fillna("").str.strip()

    for col in candidate_cols:
        if col in temp.columns:
            values = temp[col].astype(str).fillna("").str.strip()
            mask = (current == "") | (current.str.lower() == "nan") | (current.str.lower() == "none")
            temp.loc[mask, "_final_location"] = values[mask]
            current = temp["_final_location"].astype(str).fillna("").str.strip()

    temp["_final_location"] = (
        temp["_final_location"]
        .astype(str)
        .fillna("")
        .replace({"": "sin_valor", "nan": "sin_valor", "None": "sin_valor"})
    )

    return temp


def build_global_location_df(main_df, soc_df):
    """Construye dataframe dinámico para Ubicación final global."""
    parts = []

    main_norm = normalize_location_for_global_chart(main_df)
    if not main_norm.empty:
        parts.append(main_norm)

    soc_norm = normalize_location_for_global_chart(soc_df)
    if not soc_norm.empty:
        parts.append(soc_norm)

    if not parts:
        return pd.DataFrame()

    return pd.concat(parts, ignore_index=True, sort=False)


def pagina_soc(df, metadata, error, search_value=None):
    """Página portfolio diferenciada para pruebas SOC.

    Esta vista no replica Seguridad SMTP. En lugar de enfocarse en SMTP,
    presenta las pruebas como catálogo de controles defensivos, familias,
    severidad y evidencias.
    """
    soc_df, soc_error = load_soc_csv()

    if search_value and not soc_df.empty:
        mask = soc_df.astype(str).apply(
            lambda row: row.str.contains(search_value, case=False, na=False).any(),
            axis=1,
        )
        soc_df = soc_df[mask]

    raw_soc_df = soc_df.copy() if soc_df is not None and not soc_df.empty else pd.DataFrame()

    def _norm(value):
        return str(value).strip().lower()

    def _familia_control(row):
        tipo = _norm(row.get("tipo", ""))
        clasif = _norm(row.get("clasificacion_real", ""))

        if "open_relay" in tipo or "relay" in clasif:
            return "Relay / Perímetro SMTP"
        if "auth_fail" in tipo or "auth_fail" in clasif:
            return "Autenticación"
        if "recipient_unknown" in tipo or "recipient_unknown" in clasif:
            return "Validación de destinatarios"
        if "tls" in tipo or "tls_ok" in clasif:
            return "Transporte seguro"
        if "dkim" in tipo or "dkim" in clasif:
            return "DKIM / Integridad"
        if "spf" in tipo or "spf" in clasif:
            return "SPF / Origen autorizado"
        if "spoof" in tipo or "spoof" in clasif or "lookalike" in tipo or "lookalike" in clasif:
            return "Anti-spoofing"
        if "smtp_auth_success" in tipo or "smtp_auth_success" in clasif:
            return "Envío autenticado"
        return "Otros controles SOC"

    def _control_soc(row):
        tipo = _norm(row.get("tipo", ""))
        clasif = _norm(row.get("clasificacion_real", ""))

        if "open_relay" in tipo or "relay_denied" in clasif:
            return "Relay no autorizado denegado"
        if "auth_fail" in tipo or "auth_fail" in clasif:
            return "Intento de autenticación fallida"
        if "recipient_unknown" in tipo or "recipient_unknown" in clasif:
            return "Destinatario inexistente rechazado"
        if "tls" in tipo or "tls_ok" in clasif:
            return "Validación TLS correcta"
        if "smtp_auth_success" in tipo or "smtp_auth_success" in clasif:
            return "Envío autenticado permitido"
        if "dkim_rotation" in tipo or "dkim_rotation" in clasif:
            return "Rotación DKIM validada"
        if "dkim" in tipo or "dkim" in clasif:
            return "Control DKIM negativo"
        if "spf" in tipo or "spf" in clasif:
            return "Control SPF negativo"
        if "spoof" in tipo or "spoof" in clasif:
            return "Spoofing rechazado"
        if "lookalike" in tipo or "lookalike" in clasif:
            return "Dominio lookalike detectado"
        return "Control SOC registrado"

    def _severidad(row):
        clasif = _norm(row.get("clasificacion_real", ""))
        tipo = _norm(row.get("tipo", ""))
        esperado = _norm(row.get("resultado_esperado", ""))

        if any(token in clasif for token in ["relay_denied", "spoofing", "spf_fail", "dkim_fail", "dkim_absent", "lookalike"]):
            return "Alta"
        if "auth_fail" in clasif or "recipient_unknown" in clasif:
            return "Media"
        if "tls_ok" in clasif or "smtp_auth_success" in clasif or "dkim_rotation" in clasif:
            return "Informativa"
        if esperado == "bloqueado":
            return "Media"
        if "tls" in tipo:
            return "Informativa"
        return "Media"

    def _resultado_control(row):
        ubicacion = _norm(row.get("ubicacion_final", ""))
        esperado = _norm(row.get("resultado_esperado", ""))
        clasif = _norm(row.get("clasificacion_real", ""))

        if ubicacion in ["rechazado", "bloqueado", "reject", "rejected"]:
            return "Mitigado"
        if esperado == "seguro" or "tls_ok" in clasif or "dkim_rotation" in clasif:
            return "Validado"
        if esperado == "permitido" or "smtp_auth_success" in clasif:
            return "Permitido controlado"
        return "Revisar"

    soc_table_columns = [
        "id_prueba",
        "familia_control",
        "control_soc",
        "severidad",
        "resultado_control",
        "clasificacion_real",
        "origen",
        "destino",
        "evidencia",
    ]

    if raw_soc_df.empty:
        soc_table_df = pd.DataFrame(columns=soc_table_columns)
    else:
        soc_table_df = raw_soc_df.copy()

        soc_table_df["familia_control"] = soc_table_df.apply(_familia_control, axis=1)
        soc_table_df["control_soc"] = soc_table_df.apply(_control_soc, axis=1)
        soc_table_df["severidad"] = soc_table_df.apply(_severidad, axis=1)
        soc_table_df["resultado_control"] = soc_table_df.apply(_resultado_control, axis=1)

        if "observaciones" in soc_table_df.columns:
            evidencia = (
                soc_table_df["observaciones"]
                .fillna("")
                .astype(str)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
            soc_table_df["evidencia"] = evidencia.where(
                evidencia.str.len() <= 180,
                evidencia.str.slice(0, 180) + "...",
            )
        else:
            soc_table_df["evidencia"] = ""

        soc_table_df = soc_table_df[
            [col for col in soc_table_columns if col in soc_table_df.columns]
        ].copy()

    total_soc = int(len(soc_table_df))
    familias = int(soc_table_df["familia_control"].nunique()) if "familia_control" in soc_table_df.columns and not soc_table_df.empty else 0
    automatizadas = int(soc_table_df["id_prueba"].astype(str).str.startswith("AUTO-SOC").sum()) if "id_prueba" in soc_table_df.columns and not soc_table_df.empty else 0
    mitigadas = int((soc_table_df["resultado_control"] == "Mitigado").sum()) if "resultado_control" in soc_table_df.columns and not soc_table_df.empty else 0
    alta = int((soc_table_df["severidad"] == "Alta").sum()) if "severidad" in soc_table_df.columns and not soc_table_df.empty else 0
    evidencias_log = int(
        raw_soc_df.get("observaciones", pd.Series(dtype=str))
        .fillna("")
        .astype(str)
        .str.contains("syslog|queue_id|log=", case=False, regex=True)
        .sum()
    ) if not raw_soc_df.empty else 0
    cobertura = (mitigadas / total_soc * 100) if total_soc else 0

    cards = [
        create_metric_card("Familias SOC", familias, "Tipos de control", COLORS["cyan"], "FAM"),
        create_metric_card("Automatizadas", automatizadas, "Eventos detectados", COLORS["purple"], "AUTO"),
        create_metric_card("Mitigadas", mitigadas, f"{cobertura:.1f}% controladas", COLORS["green"], "OK"),
        create_metric_card("Severidad alta", alta, "Controles críticos", COLORS["red"], "HIGH"),
        create_metric_card("Evidencias log", evidencias_log, "Syslog/queue/log", "#facc15", "LOG"),
        create_metric_card("Total SOC", total_soc, "Pruebas documentadas", COLORS["blue"], "SOC"),
    ]

    family_counts = (
        soc_table_df["familia_control"].value_counts().to_dict()
        if "familia_control" in soc_table_df.columns and not soc_table_df.empty
        else {}
    )

    family_pills = [
        html.Span(f"{name}: {value}")
        for name, value in family_counts.items()
    ] or [html.Span("Sin datos SOC")]

    soc_table = dash_table.DataTable(
        id="soc-unique-table",
        columns=[
            {
                "name": {
                    "id_prueba": "ID",
                    "familia_control": "Familia",
                    "control_soc": "Control SOC",
                    "severidad": "Severidad",
                    "resultado_control": "Resultado",
                    "clasificacion_real": "Clasificación técnica",
                    "origen": "Origen",
                    "destino": "Destino",
                    "evidencia": "Evidencia",
                }.get(col, col),
                "id": col,
            }
            for col in soc_table_df.columns
        ],
        data=soc_table_df.to_dict("records"),
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_current=0,
        page_size=10,
        style_table={
            "overflowX": "auto",
            "overflowY": "visible",
            "width": "100%",
            "minWidth": "100%",
            "paddingBottom": "16px",
            "borderRadius": "18px",
            "border": "1px solid rgba(35,215,255,0.14)",
        },
        style_header={
            "backgroundColor": "rgba(8,30,54,0.98)",
            "color": "#9eeaff",
            "fontWeight": "900",
            "fontSize": "12px",
            "textTransform": "uppercase",
            "letterSpacing": "0.045em",
            "border": "1px solid rgba(35,215,255,0.18)",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_cell={
            "backgroundColor": "rgba(5,18,34,0.78)",
            "color": "#dcecff",
            "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
            "fontSize": "12px",
            "padding": "8px 10px",
            "border": "1px solid rgba(255,255,255,0.055)",
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "lineHeight": "1.25",
            "minWidth": "110px",
            "maxWidth": "300px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_cell_conditional=[
            {"if": {"column_id": "id_prueba"}, "width": "110px", "fontWeight": "900"},
            {"if": {"column_id": "familia_control"}, "minWidth": "210px", "fontWeight": "900"},
            {"if": {"column_id": "control_soc"}, "minWidth": "260px", "fontWeight": "850"},
            {"if": {"column_id": "severidad"}, "width": "120px", "fontWeight": "900"},
            {"if": {"column_id": "resultado_control"}, "minWidth": "155px", "fontWeight": "900"},
            {"if": {"column_id": "clasificacion_real"}, "minWidth": "210px"},
            {"if": {"column_id": "origen"}, "minWidth": "230px"},
            {"if": {"column_id": "destino"}, "minWidth": "250px"},
            {"if": {"column_id": "evidencia"}, "minWidth": "560px", "maxWidth": "760px"},
        ],
        style_data_conditional=[
            {"if": {"row_index": "odd"}, "backgroundColor": "rgba(8,26,47,0.78)"},
            {
                "if": {"filter_query": "{severidad} = 'Alta'"},
                "backgroundColor": "rgba(239,68,68,0.085)",
                "color": "#ffe1e1",
            },
            {
                "if": {"filter_query": "{severidad} = 'Media'"},
                "backgroundColor": "rgba(249,115,22,0.075)",
                "color": "#ffedd5",
            },
            {
                "if": {"filter_query": "{severidad} = 'Informativa'"},
                "backgroundColor": "rgba(56,189,248,0.070)",
                "color": "#d9fbff",
            },
            {
                "if": {"filter_query": "{resultado_control} = 'Mitigado'"},
                "borderLeft": "0px solid transparent",
            },
            {
                "if": {"filter_query": "{resultado_control} = 'Validado'"},
                "backgroundColor": "rgba(168,85,247,0.075)",
                "color": "#f1e4ff",
            },
            {
                "if": {"filter_query": "{resultado_control} = 'Permitido controlado'"},
                "backgroundColor": "rgba(34,211,238,0.075)",
                "color": "#d9fbff",
            },
            {
                "if": {"state": "active"},
                "backgroundColor": "rgba(35,215,255,0.16)",
                "border": "1px solid rgba(35,215,255,0.45)",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(35,215,255,0.12)",
                "border": "1px solid rgba(35,215,255,0.45)",
            },
        ],
    )

    content = [
        html.Section(cards, className="kpi-grid soc-unique-kpi-grid"),
        html.Div(
            [
                html.Div("SOC CONTROL CATALOG", className="soc-unique-eyebrow"),
                html.Div("Catálogo de pruebas defensivas", className="soc-unique-title"),
                html.Div(
                    "Vista diferenciada de Seguridad SMTP: agrupa las pruebas por familias de control, severidad y evidencias técnicas.",
                    className="soc-unique-subtitle",
                ),
                html.Div(family_pills, className="soc-unique-pills"),
            ],
            className="soc-unique-panel",
        ),
    ]

    if soc_error:
        content.append(dbc.Alert(soc_error, color="warning", className="status-alert"))
    else:
        content.append(
            html.Section(
                [
                    page_heading(
                        "Pruebas SOC",
                        "Catálogo de controles y evidencias",
                        "Vista portfolio de pruebas defensivas independientes: familias de control, severidad, resultado y trazabilidad técnica.",
                    ),
                    soc_table,
                ],
                className="table-shell soc-unique-table-shell",
            )
        )

    return content


def create_distribution_focus_panel(df, soc_df, selected_label=None):
    """Panel de foco para la dona global."""
    kpis = calculate_kpis(df)
    soc_kpis = calculate_soc_kpis(soc_df)

    items = {
        "legítimos": {
            "valor": kpis["legitimos"],
            "color": COLORS["green"],
            "descripcion": "Correos legítimos validados en la batería principal.",
            "badge": "OK",
        },
        "spoofing": {
            "valor": kpis["spoofing"],
            "color": COLORS["red"],
            "descripcion": "Intentos de suplantación registrados en la batería principal.",
            "badge": "SPF/DKIM/DMARC",
        },
        "Pruebas SOC": {
            "valor": soc_kpis["total"],
            "color": COLORS["purple"],
            "descripcion": "Eventos defensivos adicionales: open relay, autenticación fallida, TLS, destinatarios inexistentes y otros controles.",
            "badge": "SOC",
        },
    }

    total = sum(item["valor"] for item in items.values()) or 1

    if selected_label not in items:
        selected_label = "Pruebas SOC" if soc_kpis["total"] else "legítimos"

    item = items[selected_label]
    percent = item["valor"] / total * 100

    return html.Div(
        [
            html.Div(
                [
                    html.Div("Threat Focus", className="focus-kicker"),
                    html.H3(selected_label),
                    html.P(item["descripcion"]),
                ],
                className="focus-copy",
            ),
            html.Div(
                [
                    html.Div(item["badge"], className="focus-badge", style={"borderColor": item["color"], "color": item["color"]}),
                    html.Div(f"{item['valor']}", className="focus-value", style={"color": item["color"]}),
                    html.Div(f"{percent:.1f} % del total global", className="focus-percent"),
                ],
                className="focus-metric",
            ),
        ],
        className="focus-panel",
        style={"borderColor": item["color"]},
    )


def pagina_vision_general(df, metadata, error, search_value=None):
    """Pagina principal con vision global: bateria principal + pruebas SOC."""
    filtered_df = filter_dataframe(df, search_value)
    kpis = calculate_kpis(filtered_df)

    soc_df, _ = load_soc_csv()

    if search_value and not soc_df.empty:
        mask = soc_df.astype(str).apply(
            lambda row: row.str.contains(search_value, case=False, na=False).any(),
            axis=1,
        )
        soc_df = soc_df[mask]

    soc_kpis = calculate_soc_kpis(soc_df)
    total_global = kpis["total"] + soc_kpis["total"]

    cards = [
        create_metric_card(
            "Total de pruebas",
            total_global,
            f"Principales: {kpis['total']} | SOC: {soc_kpis['total']}",
            COLORS["cyan"],
            "01",
        ),
        create_metric_card("Legítimos", kpis["legitimos"], "Flujo autorizado", COLORS["green"], "OK"),
        create_metric_card("Spoofing", kpis["spoofing"], "Suplantación detectada", COLORS["red"], "!!"),
        create_metric_card("Pruebas SOC", soc_kpis["total"], f"Bloqueadas: {soc_kpis['bloqueados']}", COLORS["purple"], "SOC"),
        create_metric_card("Otros", kpis["otros"], "Sospechosos o no clasificados en batería principal", COLORS["orange"], "??"),
    ]

    # Tabla global: bateria principal + SOC
    principal_table_df = filtered_df.copy()
    principal_table_df["fuente"] = "principal"

    soc_table_df = soc_df.copy()
    if not soc_table_df.empty:
        soc_table_df["fuente"] = "soc"

    if not soc_table_df.empty:
        all_columns = list(dict.fromkeys(list(principal_table_df.columns) + list(soc_table_df.columns)))
        principal_table_df = principal_table_df.reindex(columns=all_columns)
        soc_table_df = soc_table_df.reindex(columns=all_columns)
        global_table_df = pd.concat([principal_table_df, soc_table_df], ignore_index=True)
    else:
        global_table_df = principal_table_df

    return [
        status_alert(filtered_df, metadata, error, search_value),
        html.Section(cards, className="kpi-grid"),
        dbc.Alert(
            "El total global y la tabla interactiva incluyen la batería principal y las pruebas SOC. Las gráficas de clasificación y ubicación representan la batería principal; el detalle SOC está disponible en la pestaña Pruebas SOC.",
            color="info",
            className="status-alert",
        ),
        html.Div(
            create_distribution_focus_panel(filtered_df, soc_df),
            id="global-focus-panel",
            className="focus-panel-shell",
        ),
        dbc.Row(
            [
                dbc.Col(
                    create_graph(
                        create_distribution_chart_global(filtered_df, soc_df),
                        DONUT_CHART_HEIGHT,
                        graph_id="global-distribution-chart",
                        clear_on_unhover=True,
                    ),
                    lg=5,
                ),
                dbc.Col(create_graph(create_classification_chart_global(filtered_df, soc_df), BAR_CHART_HEIGHT), lg=7),
            ],
            className="g-4 dashboard-row",
        ),
        dbc.Row(
            [dbc.Col(create_graph(create_location_chart(build_global_location_df(filtered_df, soc_df)), LARGE_CHART_HEIGHT), lg=12)],
            className="g-4 dashboard-row",
        ),
        html.Section(
            [
                page_heading(
                    "Event Explorer",
                    "Tabla interactiva global de pruebas",
                    "Incluye bateria principal y pruebas SOC. La columna fuente permite diferenciar el origen de cada registro.",
                ),
                create_data_table(global_table_df),
            ],
            className="table-shell",
        ),
    ]



def create_events_by_type_tabs(df):
    """Crea subpestañas en Eventos agrupando por tipo de evento."""
    if df is None or df.empty:
        return dbc.Alert(
            "No hay eventos disponibles con los filtros actuales.",
            color="warning",
            className="status-alert",
        )

    visible_df = df.copy()

    # Resolver columna de tipo de evento.
    type_column = None
    for candidate in ["tipo", "type", "tipo_evento", "fuente", "categoria"]:
        if candidate in visible_df.columns:
            type_column = candidate
            break

    if not type_column:
        return html.Section(
            [
                page_heading(
                    "Eventos",
                    "Tabla global de eventos",
                    "No se detectó una columna de tipo de evento; se muestra la tabla completa.",
                ),
                create_data_table(visible_df),
            ],
            className="table-shell",
        )

    # Normalizar valores vacíos.
    visible_df[type_column] = (
        visible_df[type_column]
        .astype(str)
        .fillna("sin_tipo")
        .replace({"": "sin_tipo", "nan": "sin_tipo", "None": "sin_tipo"})
    )

    counts = (
        visible_df[type_column]
        .value_counts(dropna=False)
        .reset_index()
    )

    counts.columns = ["tipo", "eventos"]

    # Orden: mayor número de eventos primero.
    counts = counts.sort_values("eventos", ascending=False)

    tabs = []

    # Pestaña Todos.
    tabs.append(
        dcc.Tab(
            label=f"Todos ({len(visible_df)})",
            value="todos",
            className="events-type-tab",
            selected_className="events-type-tab-selected",
            children=[
                html.Div(
                    [
                        html.Div(
                            [
                                html.Span("Todos los eventos", className="events-type-title"),
                                html.Span(f"{len(visible_df)} registros", className="events-type-count"),
                            ],
                            className="events-type-header",
                        ),
                        create_data_table(visible_df),
                    ],
                    className="events-type-panel",
                )
            ],
        )
    )

    # Una pestaña por tipo.
    for _, row in counts.iterrows():
        tipo = str(row["tipo"])
        total = int(row["eventos"])

        filtered_type_df = visible_df[visible_df[type_column].astype(str) == tipo].copy()

        safe_label = tipo.replace("_", " ")

        tabs.append(
            dcc.Tab(
                label=f"{safe_label} ({total})",
                value=f"tipo-{tipo}",
                className="events-type-tab",
                selected_className="events-type-tab-selected",
                children=[
                    html.Div(
                        [
                            html.Div(
                                [
                                    html.Span(safe_label, className="events-type-title"),
                                    html.Span(f"{total} registros", className="events-type-count"),
                                ],
                                className="events-type-header",
                            ),
                            create_data_table(filtered_type_df),
                        ],
                        className="events-type-panel",
                    )
                ],
            )
        )

    return html.Section(
        [
            page_heading(
                "Eventos",
                "Eventos agrupados por tipo",
                "Cada subpestaña muestra únicamente los eventos del tipo seleccionado. La pestaña Todos mantiene la vista completa.",
            ),
            dcc.Tabs(
                tabs,
                value="todos",
                className="events-type-tabs",
                parent_className="events-type-tabs-parent",
            ),
        ],
        className="table-shell events-type-shell",
    )


def pagina_eventos(df, metadata, error, search_value=None):
    """Página de eventos con subpestañas por tipo de evento."""
    filtered_df = filter_dataframe(df, search_value)

    # Añadir pruebas SOC a la vista de eventos si están disponibles.
    try:
        soc_df, soc_error = load_soc_csv()
    except Exception:
        soc_df, soc_error = pd.DataFrame(), None

    parts = []

    if filtered_df is not None and not filtered_df.empty:
        main_events = filtered_df.copy()
        if "fuente" not in main_events.columns:
            main_events["fuente"] = "principal"
        parts.append(main_events)

    if soc_df is not None and not soc_df.empty:
        soc_events = soc_df.copy()
        if search_value:
            soc_events = filter_dataframe(soc_events, search_value)
        if "fuente" not in soc_events.columns:
            soc_events["fuente"] = "soc"
        parts.append(soc_events)

    if parts:
        events_df = pd.concat(parts, ignore_index=True, sort=False)
    else:
        events_df = pd.DataFrame()

    content = [
        status_alert(events_df, metadata, error, search_value),
        create_events_by_type_tabs(events_df),
    ]

    if soc_error:
        content.insert(
            1,
            dbc.Alert(
                soc_error,
                color="warning",
                className="status-alert",
            ),
        )

    return content


def pagina_autenticacion(df, metadata, error, search_value=None):
    """Pagina SPF, DKIM y DMARC."""
    filtered_df = filter_dataframe(df, search_value)
    auth_columns = [metadata.get("spf_result"), metadata.get("dkim_result"), metadata.get("dmarc_result")]
    has_auth_data = any(column and column in filtered_df.columns for column in auth_columns)
    if not has_auth_data:
        return [
            status_alert(filtered_df, metadata, error, search_value),
            dbc.Alert("Pendiente de conectar con analizador DMARC.", color="warning", className="status-alert"),
        ]

    return [
        status_alert(filtered_df, metadata, error, search_value),
        html.Section(auth_metric_cards(filtered_df, metadata), className="kpi-grid"),
        dbc.Row(
            [
                dbc.Col(create_graph(create_result_chart(filtered_df, metadata.get("spf_result"), "SPF pass/fail"), DONUT_CHART_HEIGHT), lg=4),
                dbc.Col(create_graph(create_result_chart(filtered_df, metadata.get("dkim_result"), "DKIM pass/fail"), DONUT_CHART_HEIGHT), lg=4),
                dbc.Col(create_graph(create_result_chart(filtered_df, metadata.get("dmarc_result"), "DMARC pass/fail"), DONUT_CHART_HEIGHT), lg=4),
            ],
            className="g-4 dashboard-row",
        ),
    ]



def spoofing_explanation_panel():
    """Panel compacto exclusivo para la pestaña Spoofing, estilo portfolio."""
    return html.Section(
        [
            page_heading(
                "Análisis de suplantación",
                "Validación defensiva frente a intentos spoofing",
                "Resumen ejecutivo de controles aplicados y resultado esperado.",
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Resultado esperado", className="spoof-explain-title"),
                                    html.Div("Rechazo", className="spoof-explain-badge spoof-explain-red"),
                                    html.Div(
                                        "Los intentos spoofing deben terminar bloqueados o rechazados.",
                                        className="spoof-explain-text",
                                    ),
                                ]
                            ),
                            className="spoof-explain-card",
                        ),
                        lg=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Política aplicada", className="spoof-explain-title"),
                                    html.Div("DMARC p=reject", className="spoof-explain-badge spoof-explain-green"),
                                    html.Div(
                                        "La política final impide aceptar mensajes no alineados.",
                                        className="spoof-explain-text",
                                    ),
                                ]
                            ),
                            className="spoof-explain-card",
                        ),
                        lg=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Señal técnica", className="spoof-explain-title"),
                                    html.Div("SPF/DKIM fail", className="spoof-explain-badge spoof-explain-cyan"),
                                    html.Div(
                                        "Los fallos de autenticación identifican la suplantación.",
                                        className="spoof-explain-text",
                                    ),
                                ]
                            ),
                            className="spoof-explain-card",
                        ),
                        lg=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Valor portfolio", className="spoof-explain-title"),
                                    html.Div("Evidencia SOC", className="spoof-explain-badge spoof-explain-purple"),
                                    html.Div(
                                        "Demuestra detección y respuesta ante abuso de identidad.",
                                        className="spoof-explain-text",
                                    ),
                                ]
                            ),
                            className="spoof-explain-card",
                        ),
                        lg=3,
                    ),
                ],
                className="g-3",
            ),
        ],
        className="table-shell spoof-explain-shell",
    )



def _spoofing_location_series(df):
    """Devuelve serie normalizada de ubicación final para eventos spoofing."""
    if df is None or df.empty:
        return pd.Series([], dtype=str)

    if "ubicacion_final" in df.columns:
        return df["ubicacion_final"].astype(str).fillna("").str.lower()

    if "_final_location" in df.columns:
        return df["_final_location"].astype(str).fillna("").str.lower()

    return pd.Series([""] * len(df), dtype=str)


def _spoofing_outcome_counts(df):
    """Agrupa resultado final de eventos spoofing."""
    series = _spoofing_location_series(df)

    total = int(len(series))
    rechazado = int(series.str.contains("rechaz|reject|blocked|bloque", regex=True, na=False).sum())
    entregado = int(series.str.contains("inbox|enviado|sent|maildir|local", regex=True, na=False).sum())
    spam = int(series.str.contains("spam", regex=True, na=False).sum())

    otros = max(total - rechazado - entregado - spam, 0)

    return {
        "total": total,
        "rechazado": rechazado,
        "entregado": entregado,
        "spam": spam,
        "otros": otros,
    }


def create_spoofing_block_rate_chart(df):
    """Dona de efectividad anti-spoofing: rechazados vs no rechazados."""
    counts = _spoofing_outcome_counts(df)

    total = counts["total"]
    rechazado = counts["rechazado"]
    no_rechazado = max(total - rechazado, 0)

    if total == 0:
        return empty_figure("Efectividad anti-spoofing", height=DONUT_CHART_HEIGHT)

    values = [rechazado, no_rechazado]
    labels = ["rechazados", "no rechazados"]
    colors = [COLORS["red"], COLORS["orange"] if no_rechazado else COLORS["green"]]

    block_rate = rechazado / total * 100 if total else 0

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.62,
                marker=dict(
                    colors=colors,
                    line=dict(color="rgba(236,246,255,0.85)", width=1.2),
                ),
                textinfo="label+percent",
                textposition="inside",
                sort=False,
                hovertemplate="<b>%{label}</b><br>Eventos: %{value}<br>%{percent}<extra></extra>",
                domain=dict(x=[0.08, 0.92], y=[0.08, 0.92]),
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="Efectividad anti-spoofing",
            x=0.5,
            xanchor="center",
            font=dict(size=18, color=COLORS["text"]),
        ),
        showlegend=False,
        margin=dict(l=0, r=0, t=54, b=14),
        annotations=[
            dict(
                text=f"<b>{block_rate:.1f}%</b><br><span style='font-size:12px'>bloqueo</span>",
                x=0.5,
                y=0.5,
                xref="paper",
                yref="paper",
                showarrow=False,
                align="center",
                font=dict(
                    size=26,
                    color=COLORS["text"],
                    family="Inter, Segoe UI, Arial, sans-serif",
                ),
            )
        ],
    )

    return apply_chart_theme(fig, height=DONUT_CHART_HEIGHT)


def create_spoofing_outcome_chart(df):
    """Barra horizontal de resultado final spoofing."""
    counts = _spoofing_outcome_counts(df)

    labels = []
    values = []
    colors = []

    mapping = [
        ("rechazado", counts["rechazado"], COLORS["red"]),
        ("entregado", counts["entregado"], COLORS["green"]),
        ("spam", counts["spam"], COLORS["orange"]),
        ("otros", counts["otros"], COLORS["blue"]),
    ]

    for label, value, color in mapping:
        if value > 0:
            labels.append(label)
            values.append(value)
            colors.append(color)

    if not values:
        return empty_figure("Resultado final spoofing", height=LARGE_CHART_HEIGHT)

    plot_df = pd.DataFrame(
        {
            "categoria": labels,
            "total": values,
            "color": colors,
        }
    ).sort_values("total", ascending=True)

    max_value = int(plot_df["total"].max()) if not plot_df.empty else 1

    fig = go.Figure(
        data=[
            go.Bar(
                x=plot_df["total"],
                y=plot_df["categoria"],
                orientation="h",
                marker=dict(
                    color=plot_df["color"],
                    line=dict(color="rgba(236,246,255,0.22)", width=1),
                ),
                text=plot_df["total"],
                textposition="outside",
                cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>Eventos: %{x}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        title=dict(
            text="Resultado final spoofing",
            x=0.5,
            xanchor="center",
            font=dict(size=18, color=COLORS["text"]),
        ),
        xaxis_title="Eventos",
        yaxis_title="",
        showlegend=False,
        margin=dict(l=92, r=48, t=56, b=48),
        bargap=0.32,
    )

    fig.update_xaxes(
        gridcolor="rgba(144,168,191,0.13)",
        zerolinecolor=COLORS["border"],
        range=[0, max_value * 1.18],
    )

    fig.update_yaxes(
        gridcolor="rgba(144,168,191,0.04)",
        zeroline=False,
    )

    return apply_chart_theme(fig, height=LARGE_CHART_HEIGHT)



def spoofing_control_summary_panel(df):
    """Panel ejecutivo anti-spoofing para portfolio."""
    total = int(len(df)) if df is not None else 0

    rejected = 0
    delivered = 0
    spam = 0

    if df is not None and not df.empty:
        if "ubicacion_final" in df.columns:
            location_series = df["ubicacion_final"].astype(str).fillna("").str.lower()
        elif "_final_location" in df.columns:
            location_series = df["_final_location"].astype(str).fillna("").str.lower()
        else:
            location_series = pd.Series([""] * len(df))

        rejected = int(
            location_series.str.contains("rechaz|reject|blocked|bloque", regex=True, na=False).sum()
        )

        delivered = int(
            location_series.str.contains("inbox|enviado|sent|maildir|local", regex=True, na=False).sum()
        )

        spam = int(
            location_series.str.contains("spam", regex=True, na=False).sum()
        )

    not_rejected = max(total - rejected, 0)
    block_rate = (rejected / total * 100) if total else 0
    progress_width = f"{block_rate:.1f}%"

    if block_rate >= 95:
        status_label = "Control efectivo"
        status_class = "spoof-control-status-ok"
        interpretation = "La política defensiva bloqueó prácticamente todos los intentos de suplantación detectados."
    elif block_rate >= 70:
        status_label = "Control parcial"
        status_class = "spoof-control-status-warn"
        interpretation = "La defensa bloqueó la mayoría de intentos, pero existen eventos no rechazados que revisar."
    else:
        status_label = "Revisión requerida"
        status_class = "spoof-control-status-danger"
        interpretation = "La tasa de bloqueo es baja para un escenario anti-spoofing y requiere análisis."

    return html.Section(
        [
            page_heading(
                "Resultado anti-spoofing",
                "Resumen ejecutivo de la defensa aplicada",
                "Vista orientada a portfolio: detección, rechazo y efectividad del control.",
            ),

            html.Div(
                [
                    html.Div(
                        [
                            html.Div("Intentos detectados", className="spoof-control-label"),
                            html.Div(str(total), className="spoof-control-value spoof-control-red"),
                            html.Div("Eventos clasificados como spoofing", className="spoof-control-subtitle"),
                        ],
                        className="spoof-control-stat",
                    ),

                    html.Div(
                        [
                            html.Div("Rechazados", className="spoof-control-label"),
                            html.Div(str(rejected), className="spoof-control-value spoof-control-green"),
                            html.Div("Bloqueados por política defensiva", className="spoof-control-subtitle"),
                        ],
                        className="spoof-control-stat",
                    ),

                    html.Div(
                        [
                            html.Div("No rechazados", className="spoof-control-label"),
                            html.Div(str(not_rejected), className="spoof-control-value spoof-control-orange"),
                            html.Div("Entregados, spam u otros resultados", className="spoof-control-subtitle"),
                        ],
                        className="spoof-control-stat",
                    ),

                    html.Div(
                        [
                            html.Div("Efectividad", className="spoof-control-label"),
                            html.Div(f"{block_rate:.1f}%", className="spoof-control-value spoof-control-purple"),
                            html.Div("Tasa de bloqueo anti-spoofing", className="spoof-control-subtitle"),
                        ],
                        className="spoof-control-stat",
                    ),
                ],
                className="spoof-control-grid",
            ),

            html.Div(
                [
                    html.Div(
                        [
                            html.Span("Estado del control", className="spoof-control-progress-label"),
                            html.Span(status_label, className=f"spoof-control-status {status_class}"),
                        ],
                        className="spoof-control-progress-header",
                    ),

                    html.Div(
                        html.Div(
                            style={"width": progress_width},
                            className="spoof-control-progress-fill",
                        ),
                        className="spoof-control-progress-track",
                    ),

                    html.Div(
                        [
                            html.Span(f"{rejected} rechazados", className="spoof-control-mini-pill spoof-control-mini-green"),
                            html.Span(f"{not_rejected} no rechazados", className="spoof-control-mini-pill spoof-control-mini-orange"),
                            html.Span(f"{delivered} entregados", className="spoof-control-mini-pill spoof-control-mini-blue"),
                            html.Span(f"{spam} spam", className="spoof-control-mini-pill spoof-control-mini-amber"),
                        ],
                        className="spoof-control-mini-row",
                    ),

                    html.Div(
                        interpretation,
                        className="spoof-control-interpretation",
                    ),
                ],
                className="spoof-control-progress-panel",
            ),
        ],
        className="table-shell spoof-control-shell",
    )


def pagina_spoofing(df, metadata, error, search_value=None):
    """Página portfolio centrada en eventos de spoofing."""
    filtered_df = filter_spoofing_events(filter_dataframe(df, search_value))
    kpis = calculate_kpis(filtered_df)

    total_spoofing = int(len(filtered_df)) if filtered_df is not None else 0

    rejected_count = 0
    delivered_count = 0
    spam_count = 0

    if filtered_df is not None and not filtered_df.empty:
        if "ubicacion_final" in filtered_df.columns:
            location_series = filtered_df["ubicacion_final"].astype(str).fillna("").str.lower()
        elif "_final_location" in filtered_df.columns:
            location_series = filtered_df["_final_location"].astype(str).fillna("").str.lower()
        else:
            location_series = pd.Series([""] * len(filtered_df))

        rejected_count = int(
            location_series.str.contains("rechaz|reject|blocked|bloque", regex=True, na=False).sum()
        )

        delivered_count = int(
            location_series.str.contains("inbox|enviado|sent|maildir|local", regex=True, na=False).sum()
        )

        spam_count = int(
            location_series.str.contains("spam", regex=True, na=False).sum()
        )

    block_rate = (rejected_count / total_spoofing * 100) if total_spoofing else 0

    return [
        status_alert(filtered_df, metadata, error, search_value),

        spoofing_explanation_panel(),

        spoofing_control_summary_panel(filtered_df),

        html.Section(
            [
                page_heading(
                    "Spoofing",
                    "Evidencias de defensa anti-spoofing",
                    "Eventos filtrados por clasificación spoofing o términos equivalentes.",
                ),
                create_data_table(filtered_df),
            ],
            className="table-shell spoofing-table-shell",
        ),
    ]
def _safe_read_text_file(file_path, limit=2200):
    """Lee texto de forma segura para mostrarlo en el dashboard."""
    try:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            return ""
        content = p.read_text(errors="ignore")
        return content[:limit]
    except Exception:
        return ""


def _find_recent_files(base_paths, patterns=None, limit=8):
    """Busca ficheros recientes en rutas de evidencias."""
    if patterns is None:
        patterns = ["*"]

    found = []

    for base in base_paths:
        try:
            base_path = Path(base)
            if not base_path.exists():
                continue

            for pattern in patterns:
                for item in base_path.rglob(pattern):
                    if item.is_file():
                        try:
                            found.append((item.stat().st_mtime, item))
                        except Exception:
                            pass
        except Exception:
            pass

    found.sort(reverse=True, key=lambda x: x[0])
    return [item for _, item in found[:limit]]


def collect_external_reports_status():
    """Recopila SOLO informes reales DMARC Google y TLS-RPT."""
    
    # Rutas donde deben estar las evidencias reales DMARC.
    dmarc_paths = [
        "version_publica/dmarc_reportes_reales",
        "version_publica/dmarc",
        "version_publica/dmarc_reports",
        "version_publica/dmarc_analyzer_output",
    ]

    dmarc_allowed_ext = {".xml", ".zip", ".gz", ".csv", ".txt"}

    dmarc_exclude_terms = [
        "mta_sts",
        "mta-sts",
        "tls",
        "tlsrpt",
        "tls-rpt",
        "estado_servicios",
        "estado_final",
        "servicios",
        "backup",
        "dashboard",
    ]

    dmarc_files_all = []

    for base in dmarc_paths:
        try:
            base_path = Path(base)
            if not base_path.exists():
                continue

            for item in base_path.rglob("*"):
                if not item.is_file():
                    continue

                name = item.name.lower()
                full = str(item).lower()

                if item.suffix.lower() not in dmarc_allowed_ext:
                    continue

                if any(term in full for term in dmarc_exclude_terms):
                    continue

                # Debe parecer informe DMARC real o salida directa del analizador.
                looks_dmarc = (
                    "dmarc" in name
                    or "google" in name
                    or "rua" in name
                    or "aggregate" in name
                    or "resumen" in name
                    or "resultado" in name
                )

                if looks_dmarc:
                    try:
                        dmarc_files_all.append((item.stat().st_mtime, item))
                    except Exception:
                        pass
        except Exception:
            pass

    dmarc_files_all.sort(reverse=True, key=lambda x: x[0])
    dmarc_files = [item for _, item in dmarc_files_all[:10]]

    # Resumen DMARC: preferir resúmenes reales del analizador.
    dmarc_summary_candidates = [
        "version_publica/dmarc_analyzer_output/resumen.txt",
        "version_publica/dmarc_analyzer_output/resumen_dmarc.txt",
        "version_publica/dmarc_reportes_reales/resumen.txt",
        "version_publica/dmarc_reportes_reales/resumen_dmarc.txt",
    ]

    dmarc_summary = ""
    for candidate in dmarc_summary_candidates:
        dmarc_summary = _safe_read_text_file(candidate)
        if dmarc_summary:
            break

    if not dmarc_summary:
        if dmarc_files:
            dmarc_summary = (
                "Informes DMARC reales localizados:\\n"
                + "\\n".join(str(f) for f in dmarc_files[:6])
            )
        else:
            dmarc_summary = (
                "No se han incluido reportes agregados DMARC externos parseables en la versión pública sanitizada.\\n"
                "Versión pública revisada:\\n"
                + "\\n".join(dmarc_paths)
            )

    # TLS-RPT real: NO contar txt como reportes JSON.
    tls_base = Path("version_publica/tls_rpt")
    tls_summary_path = tls_base / "resumen_tls_rpt_real.txt"
    tls_summary = _safe_read_text_file(tls_summary_path)

    tls_json_files = []
    tls_evidence_files = []

    try:
        if tls_base.exists():
            for item in tls_base.rglob("*"):
                if not item.is_file():
                    continue

                name = item.name.lower()

                if item.suffix.lower() == ".json":
                    try:
                        tls_json_files.append((item.stat().st_mtime, item))
                    except Exception:
                        pass

                if item.suffix.lower() in {".txt", ".json", ".gz", ".zip", ".csv"}:
                    try:
                        tls_evidence_files.append((item.stat().st_mtime, item))
                    except Exception:
                        pass
    except Exception:
        pass

    tls_json_files.sort(reverse=True, key=lambda x: x[0])
    tls_evidence_files.sort(reverse=True, key=lambda x: x[0])

    tls_json_files = [item for _, item in tls_json_files]
    tls_evidence_files = [item for _, item in tls_evidence_files[:8]]

    if not tls_summary:
        tls_summary = (
            "TLS-RPT está publicado y revisado. "
            "Durante la ventana de observación no se localizaron reportes JSON parseables."
        )

    return {
        "dmarc_files": dmarc_files,
        "dmarc_summary": dmarc_summary,
        "tls_json_files": tls_json_files,
        "tls_evidence_files": tls_evidence_files,
        "tls_summary": tls_summary,
    }


def external_reports_panel():
    """Panel visual para pestaña Informes: Google DMARC y TLS-RPT reales."""
    status = collect_external_reports_status()

    dmarc_count = len(status["dmarc_files"])
    dmarc_last = str(status["dmarc_files"][0]) if status["dmarc_files"] else "Sin reportes DMARC externos parseables en la versión pública"

    dmarc_summary_display = status["dmarc_summary"] or ""

    # Aclarar que el resumen DMARC procede de reportes agregados RUA,
    # no de la batería total de pruebas del dashboard.
    dmarc_summary_display = dmarc_summary_display.replace(
        "Total de registros analizados:",
        "Registros RUA procesados:"
    )

    dmarc_summary_display = dmarc_summary_display.replace(
        "Total de mensajes analizados:",
        "Mensajes reportados en DMARC RUA:"
    )

    dmarc_summary_display = (
        dmarc_summary_display.rstrip()
        + "\n\nNota: estos valores proceden de reportes agregados DMARC externos "
        + "y no equivalen al número total de pruebas/eventos del dashboard."
    )

    tls_json_count = len(status["tls_json_files"])
    tls_last = str(status["tls_json_files"][0]) if status["tls_json_files"] else "Sin reportes TLS-RPT JSON parseables en la versión pública"

    return html.Section(
        [
            page_heading(
                "Informes externos",
                "Estado de reporting externo DMARC y TLS-RPT",
                "Este bloque resume el estado del reporting externo en la versión pública. No mezcla estos reportes con eventos SOC internos, pruebas DMARC ni evidencias de spoofing.",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Google DMARC", className="external-report-title"),
                                    html.Div(str(dmarc_count), className="external-report-number"),
                                    html.Div("reportes DMARC externos parseables en versión pública", className="external-report-subtitle"),
                                    html.Div("Última evidencia DMARC:", className="external-report-label"),
                                    html.Code(dmarc_last, className="external-report-code"),
                                    html.Pre(
                                        dmarc_summary_display,
                                        className="external-report-pre",
                                    ),
                                ]
                            ),
                            className="external-report-card external-report-card-google",
                        ),
                        lg=6,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("TLS-RPT", className="external-report-title"),
                                    html.Div(str(tls_json_count), className="external-report-number"),
                                    html.Div("reportes TLS-RPT JSON parseables en versión pública", className="external-report-subtitle"),
                                    html.Div("Último reporte JSON:", className="external-report-label"),
                                    html.Code(tls_last, className="external-report-code"),
                                    html.Pre(
                                        status["tls_summary"],
                                        className="external-report-pre",
                                    ),
                                ]
                            ),
                            className="external-report-card external-report-card-tls",
                        ),
                        lg=6,
                    ),
                ],
                className="g-4",
            ),
        ],
        className="table-shell external-reports-shell",
    )



def canonical_report_location(value):
    """Agrupa ubicaciones finales para informes: entregado, rechazado, spam, validación técnica."""
    value = normalize_text(value)

    if "spam" in value or "promoc" in value:
        return "spam"

    if (
        "rechaz" in value or
        "reject" in value or
        "blocked" in value or
        "bloque" in value
    ):
        return "rechazado"

    if (
        "inbox" in value or
        "enviado" in value or
        "sent" in value or
        "maildir" in value or
        "local" in value
    ):
        return "entregado"

    if (
        "tls" in value or
        "tls_ok" in value or
        "validacion" in value or
        "validación" in value
    ):
        return "validación técnica"

    return "otros"


def build_report_location_summary(main_df):
    """Construye resumen dinámico de ubicación final para la pestaña Informes."""
    parts = []

    if main_df is not None and not main_df.empty:
        parts.append(main_df.copy())

    try:
        soc_df, _ = load_soc_csv()
        if soc_df is not None and not soc_df.empty:
            parts.append(soc_df.copy())
    except Exception:
        pass

    if not parts:
        return pd.DataFrame(columns=["categoria", "eventos", "porcentaje"])

    combined = pd.concat(parts, ignore_index=True, sort=False)

    if "ubicacion_final" in combined.columns:
        location_series = combined["ubicacion_final"]
    elif "_final_location" in combined.columns:
        location_series = combined["_final_location"]
    else:
        location_series = pd.Series(["otros"] * len(combined))

    grouped = (
        location_series
        .astype(str)
        .fillna("")
        .apply(canonical_report_location)
        .value_counts()
        .reset_index()
    )

    grouped.columns = ["categoria", "eventos"]

    total = int(grouped["eventos"].sum()) if not grouped.empty else 0

    if total > 0:
        grouped["porcentaje"] = grouped["eventos"].apply(lambda x: f"{(x / total * 100):.1f}%")
    else:
        grouped["porcentaje"] = "0.0%"

    order = {
        "spam": 1,
        "rechazado": 2,
        "entregado": 3,
        "validación técnica": 4,
        "otros": 5,
    }

    grouped["orden"] = grouped["categoria"].map(order).fillna(99)
    grouped = grouped.sort_values("orden").drop(columns=["orden"])

    return grouped


def informes_location_summary_panel(main_df):
    """Panel de tabla para Informes con ubicación final agrupada."""
    summary_df = build_report_location_summary(main_df)

    total = int(summary_df["eventos"].sum()) if not summary_df.empty else 0

    rows = []

    for _, row in summary_df.iterrows():
        categoria = str(row["categoria"])
        eventos = int(row["eventos"])
        porcentaje = str(row["porcentaje"])

        class_map = {
            "spam": "loc-row-spam",
            "rechazado": "loc-row-rejected",
            "entregado": "loc-row-delivered",
            "validación técnica": "loc-row-technical",
            "otros": "loc-row-other",
        }

        rows.append(
            html.Tr(
                [
                    html.Td(categoria, className="loc-cell-category"),
                    html.Td(str(eventos), className="loc-cell-number"),
                    html.Td(porcentaje, className="loc-cell-percent"),
                ],
                className=class_map.get(categoria, "loc-row-other"),
            )
        )

    rows.append(
        html.Tr(
            [
                html.Td("Total", className="loc-cell-category loc-total"),
                html.Td(str(total), className="loc-cell-number loc-total"),
                html.Td("100.0%" if total else "0.0%", className="loc-cell-percent loc-total"),
            ],
            className="loc-row-total",
        )
    )

    return html.Section(
        [
            page_heading(
                "Resumen de ubicación final",
                "Agrupación global de eventos principales y pruebas SOC",
                "Los valores se calculan dinámicamente desde los CSV actuales del dashboard.",
            ),
            html.Div(
                html.Table(
                    [
                        html.Thead(
                            html.Tr(
                                [
                                    html.Th("Categoría"),
                                    html.Th("Eventos"),
                                    html.Th("%"),
                                ]
                            )
                        ),
                        html.Tbody(rows),
                    ],
                    className="location-summary-table",
                ),
                className="location-summary-wrapper",
            ),
        ],
        className="table-shell location-summary-shell",
    )




def load_email_threats_csv():
    """Carga las pruebas reales de amenazas de contenido de correo."""
    path = Path("data/bateria_pruebas_email_threats.csv")

    if not path.exists():
        return pd.DataFrame(), f"No existe {path}"

    try:
        threat_df = pd.read_csv(path)
        return threat_df, None
    except Exception as exc:
        return pd.DataFrame(), str(exc)


def create_email_threats_type_chart(threat_df):
    """Gráfico por tipo de amenaza email."""
    if threat_df is None or threat_df.empty or "tipo" not in threat_df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos de amenazas email",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="#eaf6ff"),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eaf6ff"),
            height=420,
        )
        return fig

    grouped = (
        threat_df["tipo"]
        .astype(str)
        .value_counts()
        .reset_index()
    )
    grouped.columns = ["tipo", "eventos"]

    colors = ["#38f8ff", "#a855f7", "#f97316", "#22c55e", "#facc15", "#ef4444"]

    fig = go.Figure(
        go.Bar(
            x=grouped["eventos"],
            y=grouped["tipo"],
            orientation="h",
            marker=dict(
                color=[colors[i % len(colors)] for i in range(len(grouped))],
                line=dict(color="rgba(234,246,255,0.35)", width=1),
            ),
            text=grouped["eventos"],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Pruebas: %{x}<extra></extra>",
        )
    )

    fig.update_layout(
        title=dict(
            text="Tipos de amenazas email simuladas",
            x=0.03,
            xanchor="left",
            font=dict(size=22, color="#eaf6ff"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,10,22,0.35)",
        font=dict(color="#eaf6ff"),
        height=420,
        margin=dict(l=190, r=60, t=66, b=40),
        showlegend=False,
        xaxis=dict(
            title="Pruebas reales",
            gridcolor="rgba(35,215,255,0.10)",
            zeroline=False,
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            gridcolor="rgba(35,215,255,0.04)",
        ),
    )

    return fig


def create_email_threats_mitre_chart(threat_df):
    """Gráfico por técnica MITRE."""
    if threat_df is None or threat_df.empty or "mitre" not in threat_df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos MITRE",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="#eaf6ff"),
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eaf6ff"),
            height=420,
        )
        return fig

    grouped = (
        threat_df["mitre"]
        .astype(str)
        .value_counts()
        .reset_index()
    )
    grouped.columns = ["mitre", "eventos"]

    fig = go.Figure(
        go.Pie(
            labels=grouped["mitre"],
            values=grouped["eventos"],
            hole=0.62,
            marker=dict(colors=["#38f8ff", "#a855f7", "#f97316", "#22c55e"]),
            textinfo="label+value",
            hovertemplate="<b>%{label}</b><br>Pruebas: %{value}<br>%{percent}<extra></extra>",
            sort=False,
        )
    )

    fig.update_layout(
        title=dict(
            text="Cobertura MITRE ATT&CK",
            x=0.03,
            xanchor="left",
            font=dict(size=22, color="#eaf6ff"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#eaf6ff"),
        height=420,
        margin=dict(l=30, r=30, t=66, b=40),
        legend=dict(
            orientation="h",
            y=-0.08,
            x=0.5,
            xanchor="center",
            font=dict(color="#dcecff"),
        ),
    )

    return fig


def email_threats_summary_panel(threat_df):
    """Panel explicativo para amenazas email."""
    return html.Div(
        [
            html.Div("EMAIL THREAT SIMULATION", className="email-threats-eyebrow"),
            html.Div("Amenazas de contenido de correo", className="email-threats-title"),
            html.Div(
                "Pruebas reales enviadas por SMTP local para validar transporte, trazabilidad y clasificación defensiva de contenido sospechoso benigno.",
                className="email-threats-subtitle",
            ),

            html.Div(
                [
                    html.Div(
                        [
                            html.Div("URLs sospechosas", className="email-threats-item-title"),
                            html.Div("Enlaces .invalid y patrones tipo login/acortador sin infraestructura externa.", className="email-threats-item-text"),
                        ],
                        className="email-threats-item email-threats-cyan",
                    ),
                    html.Div(
                        [
                            html.Div("Adjuntos benignos", className="email-threats-item-title"),
                            html.Div("EICAR y doble extensión como simulación defensiva controlada.", className="email-threats-item-text"),
                        ],
                        className="email-threats-item email-threats-orange",
                    ),
                    html.Div(
                        [
                            html.Div("Callback phishing simulado", className="email-threats-item-title"),
                            html.Div("Mensaje con llamada ficticia, sin capturar credenciales ni usar terceros.", className="email-threats-item-text"),
                        ],
                        className="email-threats-item email-threats-purple",
                    ),
                    html.Div(
                        [
                            html.Div("Evidencia real", className="email-threats-item-title"),
                            html.Div("Cada prueba conserva transcript SMTP real y queue id del servidor.", className="email-threats-item-text"),
                        ],
                        className="email-threats-item email-threats-green",
                    ),
                ],
                className="email-threats-list",
            ),
        ],
        className="email-threats-panel",
    )


def pagina_amenazas_email(df, metadata, error, search_value=None):
    """Página de amenazas de contenido de correo."""
    threat_df, threat_error = load_email_threats_csv()

    if search_value and not threat_df.empty:
        mask = pd.Series(False, index=threat_df.index)
        for col in threat_df.columns:
            mask = mask | threat_df[col].astype(str).str.contains(str(search_value), case=False, na=False)
        threat_df = threat_df[mask].copy()

    total = int(len(threat_df))
    tipos = int(threat_df["tipo"].nunique()) if not threat_df.empty and "tipo" in threat_df.columns else 0
    mitre = int(threat_df["mitre"].nunique()) if not threat_df.empty and "mitre" in threat_df.columns else 0
    validadas = int((threat_df["validada"].astype(str).str.lower() == "si").sum()) if not threat_df.empty and "validada" in threat_df.columns else 0
    adjuntos = int(threat_df["tipo"].astype(str).str.contains("adjunto|eicar|doble", case=False, na=False).sum()) if not threat_df.empty and "tipo" in threat_df.columns else 0
    urls = int(threat_df["tipo"].astype(str).str.contains("url", case=False, na=False).sum()) if not threat_df.empty and "tipo" in threat_df.columns else 0

    cards = [
        create_metric_card("Pruebas reales", total, "Aceptadas por SMTP", COLORS["cyan"], "MAIL"),
        create_metric_card("Tipos", tipos, "Familias de contenido", COLORS["purple"], "TYPE"),
        create_metric_card("MITRE", mitre, "Técnicas cubiertas", COLORS["orange"], "ATT&CK"),
        create_metric_card("Validadas", validadas, "Respuesta 250 tras DATA", COLORS["green"], "250"),
        create_metric_card("URLs", urls, "Links simulados", COLORS["cyan"], "URL"),
        create_metric_card("Adjuntos", adjuntos, "EICAR/doble extensión", COLORS["red"], "FILE"),
    ]

    # Tabla ejecutiva estilo SMTP: columnas útiles, compactas y no redundantes.
    # El CSV conserva todos los campos completos; la tabla muestra lo necesario para defensa.
    # Tabla ejecutiva: se crean columnas de visualización para no romper el layout.
    # El CSV original conserva resultado_smtp y evidencia completos.
    table_view = threat_df.copy()

    if not table_view.empty:
        if "resultado_smtp" in table_view.columns:
            resultado_raw = table_view["resultado_smtp"].fillna("").astype(str)
            queue_extraida = resultado_raw.str.extract(r"queued as\s+([A-Za-z0-9]+)", expand=False)
            table_view["queue_id"] = queue_extraida.fillna(resultado_raw)
        else:
            table_view["queue_id"] = ""

        if "evidencia" in table_view.columns:
            table_view["evidencia_file"] = (
                table_view["evidencia"]
                .fillna("")
                .astype(str)
                .str.replace("\\\\", "/", regex=False)
                .str.split("/")
                .str[-1]
            )
        else:
            table_view["evidencia_file"] = ""

        if "tipo" in table_view.columns:
            table_view["tipo_display"] = (
                table_view["tipo"]
                .fillna("")
                .astype(str)
                .str.replace("_", " ", regex=False)
            )
        else:
            table_view["tipo_display"] = ""

        if "id_prueba" in table_view.columns:
            table_view["id_display"] = table_view["id_prueba"].fillna("").astype(str)
        else:
            table_view["id_display"] = ""
    else:
        table_view["queue_id"] = ""
        table_view["evidencia_file"] = ""
        table_view["tipo_display"] = ""
        table_view["id_display"] = ""

    table_cols = [
        c for c in [
            "id_display",
            "tipo_display",
            "indicador",
            "queue_id",
            "mitre",
            "evidencia_file",
        ]
        if c in table_view.columns
    ]

    email_threats_table_labels = {
        "id_display": "ID",
        "tipo_display": "Tipo",
        "indicador": "Indicador",
        "queue_id": "Queue ID",
        "mitre": "MITRE",
        "evidencia_file": "Evidencia",
    }

    table_columns = [
        {"name": email_threats_table_labels.get(c, c), "id": c}
        for c in table_cols
    ]

    table_component = dash_table.DataTable(
        data=table_view[table_cols].to_dict("records") if not table_view.empty else [],
        columns=table_columns,
        page_size=8,
        sort_action="native",
        filter_action="none",
        style_cell_conditional=[
            {"if": {"column_id": "id_display"}, "width": "155px", "maxWidth": "155px", "textAlign": "right"},
            {"if": {"column_id": "tipo_display"}, "width": "190px", "maxWidth": "190px"},
            {"if": {"column_id": "indicador"}, "width": "280px", "maxWidth": "280px"},
            {"if": {"column_id": "queue_id"}, "width": "135px", "maxWidth": "135px", "textAlign": "center"},
            {"if": {"column_id": "mitre"}, "width": "95px", "maxWidth": "95px", "textAlign": "center"},
            {"if": {"column_id": "evidencia_file"}, "width": "230px", "maxWidth": "230px"},
        ],
        style_table={"overflowX": "auto", "maxHeight": "520px", "overflowY": "auto"},
        style_cell={
            "backgroundColor": "rgba(4,16,31,0.96)",
            "color": "#eaf6ff",
            "border": "1px solid rgba(35,215,255,0.12)",
            "fontFamily": "Inter, Segoe UI, Arial",
            "fontSize": "12px",
            "padding": "10px",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_header={
            "backgroundColor": "rgba(8,30,54,0.98)",
            "color": "#38f8ff",
            "fontWeight": "bold",
            "border": "1px solid rgba(35,215,255,0.25)",
        },
    )

    return [
        status_alert(threat_df, {"id": "id_prueba"}, threat_error, search_value),
        html.Section(cards, className="kpi-grid email-threats-kpi-grid"),

        dbc.Row(
            [
                dbc.Col(create_graph(create_email_threats_type_chart(threat_df), 430), lg=7),
                dbc.Col(email_threats_summary_panel(threat_df), lg=5),
            ],
            className="g-4 dashboard-row email-threats-row",
        ),

        dbc.Row(
            [
                dbc.Col(create_graph(create_email_threats_mitre_chart(threat_df), 430), lg=5),
                dbc.Col(
                    html.Div(
                        [
                            html.Div("Evidencias reales", className="email-threats-table-title"),
                            html.Div(
                                "Tabla de pruebas aceptadas por SMTP local. Cada fila apunta a un transcript real.",
                                className="email-threats-table-subtitle",
                            ),
                            table_component,
                        ],
                        className="table-shell email-threats-table-shell",
                    ),
                    lg=7,
                ),
            ],
            className="g-4 dashboard-row email-threats-bottom-row",
        ),
    ]


def pagina_informes(df, metadata, error, search_value=None):
    """Pagina de resumen estadistico y metricas de evaluacion."""
    filtered_df = filter_dataframe(df, search_value)

    try:
        soc_location_df, _ = load_soc_csv()
    except Exception:
        soc_location_df = pd.DataFrame()

    location_report_df = build_global_location_df(filtered_df, soc_location_df)
    metrics = calculate_report_metrics(filtered_df, metadata)
    cards = [
        create_metric_card("Precisión", f"{metrics['precision']:.1%}", "TP / (TP + FP)", COLORS["green"], "P"),
        create_metric_card("Recall", f"{metrics['recall']:.1%}", "TP / (TP + FN)", COLORS["cyan"], "R"),
        create_metric_card("Falsos positivos", metrics["false_positives"], "Legitimos marcados como spoofing", COLORS["orange"], "FP"),
        create_metric_card("Falsos negativos", metrics["false_negatives"], "Spoofing no detectado", COLORS["red"], "FN"),
        create_metric_card("Entregabilidad", f"{metrics['deliverability']:.1%}", "Eventos entregados", COLORS["green"], "IN"),
        create_metric_card("Tasa de rechazo", f"{metrics['rejection_rate']:.1%}", "Eventos rechazados", COLORS["red"], "RJ"),
    ]
    return [
        status_alert(filtered_df, metadata, error, search_value),
        html.Section(cards, className="kpi-grid report-grid"),
        external_reports_panel(),
        informes_location_summary_panel(filtered_df),
        dbc.Row(
            [
                dbc.Col(create_graph(create_distribution_chart(filtered_df), DONUT_CHART_HEIGHT), lg=5),
                dbc.Col(create_graph(create_location_chart(location_report_df), LARGE_CHART_HEIGHT), lg=7),
            ],
            className="g-4 dashboard-row",
        ),
    ]



def _find_column(df, candidates):
    """Devuelve la primera columna existente dentro de una lista de candidatos."""
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _count_value(df, column, value):
    if df is None or df.empty or not column or column not in df.columns:
        return 0
    return int((df[column].astype(str).str.lower() == value.lower()).sum())


def create_simple_donut(labels, values, colors, title):
    """Dona genérica interactiva."""
    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(colors=colors),
                textinfo="label+percent",
                textposition="inside",
                hovertemplate="%{label}<br>Eventos: %{value}<br>%{percent}<extra></extra>",
                sort=False,
            )
        ]
    )
    fig.update_layout(
        title=title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=20, r=20, t=60, b=35),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    )
    return fig


def create_simple_bar(labels, values, colors, title, x_title="Categoría", y_title="Eventos"):
    """Barras interactivas con porcentajes."""
    total = sum(values) or 1
    text_labels = [f"{v}<br>{(v / total * 100):.1f}%" for v in values]

    fig = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=text_labels,
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x}<br>Eventos: %{y}<extra></extra>",
            )
        ]
    )

    y_max = max(values) * 1.25 if values else 5
    y_max = max(y_max, 5)

    fig.update_layout(
        title=title,
        xaxis_title=x_title,
        yaxis_title=y_title,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=40, r=20, t=70, b=60),
        showlegend=False,
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", range=[0, y_max])
    return fig



def deliverability_spam_explanation_panel(inbox, spam, promociones, no_aparece, total):
    """Panel compacto de entregabilidad, estilo portfolio, sin texto redundante."""
    return html.Section(
        [
            page_heading(
                "Análisis de spam en Gmail",
                "Autenticación correcta no implica entrega directa a inbox",
                "Resumen ejecutivo de factores que explican la clasificación en spam.",
            ),

            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("SMTP aceptado", className="spam-explain-title"),
                                    html.Div("250 OK ≠ Inbox", className="spam-explain-badge spam-explain-blue"),
                                    html.Div(
                                        "El servidor receptor acepta el mensaje, pero Gmail decide la carpeta final después.",
                                        className="spam-explain-subtitle",
                                    ),
                                ]
                            ),
                            className="spam-explain-card",
                        ),
                        lg=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Autenticación", className="spam-explain-title"),
                                    html.Div("PASS ≠ Entrega", className="spam-explain-badge spam-explain-purple"),
                                    html.Div(
                                        "SPF, DKIM y DMARC validan identidad, pero no garantizan bandeja de entrada.",
                                        className="spam-explain-subtitle",
                                    ),
                                ]
                            ),
                            className="spam-explain-card",
                        ),
                        lg=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Factor principal", className="spam-explain-title"),
                                    html.Div("Reputación", className="spam-explain-badge spam-explain-orange"),
                                    html.Div(
                                        "Gmail pondera reputación del dominio/IP, historial, volumen y señales de usuario.",
                                        className="spam-explain-subtitle",
                                    ),
                                ]
                            ),
                            className="spam-explain-card",
                        ),
                        lg=3,
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    html.Div("Contexto portfolio", className="spam-explain-title"),
                                    html.Div("Laboratorio", className="spam-explain-badge spam-explain-green"),
                                    html.Div(
                                        "Pruebas repetitivas y bajo volumen pueden elevar la sospecha aunque la seguridad esté bien.",
                                        className="spam-explain-subtitle",
                                    ),
                                ]
                            ),
                            className="spam-explain-card",
                        ),
                        lg=3,
                    ),
                ],
                className="g-3",
            ),
        ],
        className="table-shell spam-explain-shell",
    )


def pagina_entregabilidad(df, metadata, error, search_value=None):
    """Página dedicada a entregabilidad Gmail: inbox, spam y aceptación SMTP."""
    filtered_df = filter_dataframe(df, search_value).copy()

    # Resolver columnas de forma robusta, sin depender solo de metadata.
    tipo_col = "tipo" if "tipo" in filtered_df.columns else metadata.get("type")
    destino_col = "destino" if "destino" in filtered_df.columns else None
    ubicacion_col = "ubicacion_final" if "ubicacion_final" in filtered_df.columns else metadata.get("location")
    id_col = "id_prueba" if "id_prueba" in filtered_df.columns else None

    if filtered_df.empty:
        return [
            status_alert(filtered_df, metadata, error, search_value),
            dbc.Alert("No hay datos cargados para calcular entregabilidad.", color="warning", className="status-alert"),
        ]

    # Selección robusta de correos legítimos hacia Gmail.
    legit_mask = pd.Series(False, index=filtered_df.index)

    if tipo_col and tipo_col in filtered_df.columns:
        legit_mask = legit_mask | filtered_df[tipo_col].astype(str).str.lower().str.contains("legit", na=False)

    if id_col and id_col in filtered_df.columns:
        legit_mask = legit_mask | filtered_df[id_col].astype(str).str.upper().str.startswith("L")

    if destino_col and destino_col in filtered_df.columns:
        gmail_mask = filtered_df[destino_col].astype(str).str.lower().str.contains("gmail.com", na=False)
        # Si hay destino Gmail, priorizamos legítimos Gmail.
        if gmail_mask.any():
            legit_mask = legit_mask & gmail_mask

    legit_df = filtered_df[legit_mask].copy()

    # Fallback: si por cualquier motivo no detecta legítimos, usar eventos con ubicación de entregabilidad.
    if legit_df.empty and ubicacion_col and ubicacion_col in filtered_df.columns:
        ubicaciones_entrega = ["inbox", "spam", "promociones", "no_aparece"]
        legit_df = filtered_df[
            filtered_df[ubicacion_col].astype(str).str.lower().isin(ubicaciones_entrega)
        ].copy()

    if ubicacion_col and ubicacion_col in legit_df.columns:
        ubicacion_series = legit_df[ubicacion_col].astype(str).str.lower()
    else:
        ubicacion_series = pd.Series([], dtype=str)

    total_legit = int(len(legit_df))
    inbox = int((ubicacion_series == "inbox").sum())
    spam = int((ubicacion_series == "spam").sum())
    promociones = int((ubicacion_series == "promociones").sum())
    no_aparece = int((ubicacion_series == "no_aparece").sum())

    smtp_aceptados = inbox + spam + promociones + no_aparece
    inbox_rate = inbox / total_legit if total_legit else 0
    spam_rate = spam / total_legit if total_legit else 0
    smtp_rate = smtp_aceptados / total_legit if total_legit else 0

    cards = [
        create_metric_card("Legítimos Gmail", total_legit, "Base analizada", COLORS["cyan"], "LG"),
        create_metric_card("SMTP aceptados", f"{smtp_rate:.1%}", f"{smtp_aceptados} mensajes", COLORS["green"], "250"),
        create_metric_card("Inbox", f"{inbox_rate:.1%}", f"{inbox} mensajes", COLORS["green"], "IN"),
        create_metric_card("Spam", f"{spam_rate:.1%}", f"{spam} mensajes", COLORS["orange"], "SP"),
        create_metric_card("No aparece", no_aparece, "No localizado", COLORS["red"], "NA"),
    ]

    labels = []
    values = []
    colors = []

    for label, value, color in [
        ("inbox", inbox, COLORS["green"]),
        ("spam", spam, COLORS["orange"]),
        ("promociones", promociones, COLORS["cyan"]),
        ("no_aparece", no_aparece, COLORS["red"]),
    ]:
        if value > 0:
            labels.append(label)
            values.append(value)
            colors.append(color)

    if not values:
        labels = ["sin datos"]
        values = [1]
        colors = [COLORS["orange"]]

    donut = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.58,
                marker=dict(colors=colors),
                textinfo="label+percent",
                textposition="inside",
                hovertemplate="%{label}<br>Mensajes: %{value}<br>%{percent}<extra></extra>",
                sort=False,
            )
        ]
    )

    donut.update_layout(
        title="Distribución inbox / spam",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=20, r=20, t=60, b=40),
        legend=dict(orientation="h", y=-0.18, x=0.5, xanchor="center"),
    )

    total_chart = sum(values) if sum(values) else 1
    bar_text = [
        f"{v}<br>{(v / total_chart * 100):.1f}%"
        for v in values
    ]

    bar = go.Figure(
        data=[
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=bar_text,
                textposition="outside",
                cliponaxis=False,
                hovertemplate="%{x}<br>Mensajes: %{y}<extra></extra>",
            )
        ]
    )

    y_max = max(values) * 1.25 if values else 5
    y_max = max(y_max, 5)

    bar.update_layout(
        title="Ubicación final de correos legítimos",
        xaxis_title="Ubicación final",
        yaxis_title="Mensajes",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=COLORS["text"]),
        margin=dict(l=40, r=20, t=70, b=60),
        showlegend=False,
    )

    bar.update_xaxes(gridcolor="rgba(255,255,255,0.08)")
    bar.update_yaxes(gridcolor="rgba(255,255,255,0.08)", range=[0, y_max])

    if legit_df.empty:
        tabla_df = filtered_df.head(0).copy()
        aviso = dbc.Alert(
            "No se han detectado correos legítimos Gmail con los criterios actuales. Revisa columnas tipo, destino e id_prueba.",
            color="warning",
            className="status-alert",
        )
    else:
        tabla_df = legit_df
        aviso = dbc.Alert(
            "Esta vista analiza la ubicación final de correos legítimos aceptados por Gmail. Distingue aceptación SMTP de llegada real a bandeja de entrada.",
            color="info",
            className="status-alert",
        )

    return [
        status_alert(filtered_df, metadata, error, search_value),
        aviso,
        html.Section(cards, className="kpi-grid"),
        deliverability_spam_explanation_panel(inbox, spam, promociones, no_aparece, total_chart),
        dbc.Row(
            [
                dbc.Col(create_graph(donut, DONUT_CHART_HEIGHT), lg=5),
                dbc.Col(create_graph(bar, BAR_CHART_HEIGHT), lg=7),
            ],
            className="g-4 dashboard-row",
        ),
        html.Section(
            [
                page_heading(
                    "Entregabilidad Gmail",
                    "Inbox, spam y aceptación SMTP",
                    "Tabla filtrable de correos legítimos usados para medir ubicación final y entregabilidad.",
                ),
                create_data_table(tabla_df),
            ],
            className="table-shell",
        ),
    ]


def create_soc_type_chart(df_soc):
    """Gráfico horizontal de tipos de pruebas SOC con nombres legibles."""
    if df_soc is None or df_soc.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos SOC",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="#eaf6ff"),
        )
        fig.update_layout(
            title=dict(
                text="Tipos de pruebas SOC",
                x=0.03,
                xanchor="left",
                font=dict(size=20, color="#eaf6ff"),
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(2,10,22,0.35)",
            font=dict(color="#eaf6ff"),
            margin=dict(l=160, r=70, t=54, b=42),
            height=420,
        )
        return fig

    if "tipo" in df_soc.columns:
        tipo_col = "tipo"
    elif "clasificacion_real" in df_soc.columns:
        tipo_col = "clasificacion_real"
    elif "resultado_real" in df_soc.columns:
        tipo_col = "resultado_real"
    else:
        tipo_col = df_soc.columns[0]

    grouped = (
        df_soc[tipo_col]
        .fillna("sin_tipo")
        .astype(str)
        .value_counts()
        .reset_index()
    )
    grouped.columns = ["tipo", "eventos"]

    smtp_type_labels = {
        "auth_fail": "Auth fail",
        "open_relay_test": "Open relay",
        "recipient_unknown": "Usuario inexistente",
        "tls_starttls_smtp": "STARTTLS SMTP",
        "tls_imaps": "TLS IMAPS",
        "smtp_auth_success": "SMTP AUTH OK",
        "spf_fail": "SPF fail",
        "dkim_broken": "DKIM roto",
        "dkim_absent": "DKIM ausente",
        "dkim_rotation": "Rotación DKIM",
        "spoofing_reject": "DMARC reject",
        "lookalike_domain": "Dominio lookalike",
        "relay_denied": "Relay denegado",
        "tls_ok": "TLS OK",
        "legitimo": "Legítimo",
        "sospechoso": "Sospechoso",
    }

    grouped["tipo_display"] = (
        grouped["tipo"]
        .astype(str)
        .map(smtp_type_labels)
        .fillna(
            grouped["tipo"]
            .astype(str)
            .str.replace("_", " ", regex=False)
            .str.replace("-", " ", regex=False)
            .str.title()
        )
    )

    colors = [
        "#38f8ff",
        "#a855f7",
        "#f97316",
        "#22c55e",
        "#facc15",
        "#ef4444",
        "#2f80ed",
        "#14b8a6",
        "#e879f9",
        "#fb7185",
        "#84cc16",
        "#60a5fa",
    ]

    fig = go.Figure(
        go.Bar(
            x=grouped["eventos"],
            y=grouped["tipo_display"],
            orientation="h",
            marker=dict(
                color=[colors[i % len(colors)] for i in range(len(grouped))],
                line=dict(color="rgba(234,246,255,0.35)", width=1),
            ),
            text=grouped["eventos"],
            textposition="outside",
            cliponaxis=False,
            customdata=grouped["tipo"],
            hovertemplate="<b>%{y}</b><br>Tipo técnico: %{customdata}<br>Eventos: %{x}<extra></extra>",
        )
    )

    max_x = int(grouped["eventos"].max()) if not grouped.empty else 1
    range_x = [0, max(2, max_x + 1)]

    fig.update_layout(
        title=dict(
            text="Tipos de pruebas SOC",
            x=0.03,
            xanchor="left",
            font=dict(size=20, color="#eaf6ff"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,10,22,0.35)",
        font=dict(color="#eaf6ff"),
        margin=dict(l=170, r=76, t=54, b=42),
        height=420,
        showlegend=False,
        bargap=0.28,
        xaxis=dict(
            title="Eventos reales",
            range=range_x,
            gridcolor="rgba(35,215,255,0.10)",
            zeroline=False,
            tickfont=dict(color="#eaf6ff", size=12),
            title_font=dict(color="#eaf6ff", size=14),
        ),
        yaxis=dict(
            title="",
            autorange="reversed",
            gridcolor="rgba(35,215,255,0.04)",
            tickfont=dict(color="#eaf6ff", size=12),
        ),
    )

    return fig


def create_soc_result_chart(df_soc):
    """Panel KPI para Resultado SOC.

    Sustituye la dona saturada por un panel ejecutivo:
    - Eventos SOC.
    - Mitigados.
    - Auth Fail.
    - TLS OK.
    Sin JS.
    """
    if df_soc is None or df_soc.empty:
        total = 0
        mitigados = 0
        open_relay = 0
        auth_fail = 0
        recipient_unknown = 0
        tls_ok = 0
    else:
        total = int(len(df_soc))

        tipo = df_soc.get("tipo", pd.Series(dtype=str)).astype(str).str.lower()
        ubicacion = df_soc.get("ubicacion_final", pd.Series(dtype=str)).astype(str).str.lower()
        clasif = df_soc.get("clasificacion_real", pd.Series(dtype=str)).astype(str).str.lower()
        esperado = df_soc.get("resultado_esperado", pd.Series(dtype=str)).astype(str).str.lower()

        open_relay = int((tipo == "open_relay_test").sum())
        auth_fail = int((clasif == "auth_fail").sum())
        recipient_unknown = int((clasif == "recipient_unknown").sum())
        tls_ok = int((clasif == "tls_ok").sum())

        mitigados = int(
            (
                ubicacion.isin(["rechazado", "bloqueado", "reject", "rejected"])
                | esperado.isin(["bloqueado", "seguro"])
                | clasif.isin(["relay_denied", "auth_fail", "recipient_unknown", "tls_ok"])
            ).sum()
        )

    rate = (mitigados / total * 100) if total else 0

    fig = go.Figure()

    items = [
        {
            "label": "Eventos SOC",
            "value": total,
            "sub": "controles registrados",
            "color": COLORS["cyan"],
            "domain": {"x": [0.00, 0.47], "y": [0.56, 1.00]},
        },
        {
            "label": "Mitigados",
            "value": mitigados,
            "sub": f"{rate:.1f}% del total",
            "color": COLORS["green"],
            "domain": {"x": [0.53, 1.00], "y": [0.56, 1.00]},
        },
        {
            "label": "Auth Fail",
            "value": auth_fail,
            "sub": "login inválido",
            "color": COLORS["red"],
            "domain": {"x": [0.00, 0.47], "y": [0.00, 0.44]},
        },
        {
            "label": "TLS OK",
            "value": tls_ok,
            "sub": "transporte seguro",
            "color": COLORS["purple"],
            "domain": {"x": [0.53, 1.00], "y": [0.00, 0.44]},
        },
    ]

    for item in items:
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=item["value"],
                number=dict(
                    font=dict(size=42, color=item["color"]),
                ),
                title=dict(
                    text=(
                        f'<span style="font-size:15px;color:#eaf6ff">{item["label"]}</span>'
                        f'<br>'
                        f'<span style="font-size:11px;color:#aebfd0">{item["sub"]}</span>'
                    )
                ),
                domain=item["domain"],
            )
        )

    fig.update_layout(
        title=dict(
            text="Resultado SOC",
            x=0.5,
            xanchor="center",
            font=dict(size=22, color="#eaf6ff"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=28, r=28, t=62, b=36),
        font=dict(color="#eaf6ff"),
        shapes=[
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0.00,
                y0=0.56,
                x1=0.47,
                y1=1.00,
                line=dict(color="rgba(35,215,255,0.22)", width=1),
                fillcolor="rgba(7,20,38,0.46)",
                layer="below",
            ),
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0.53,
                y0=0.56,
                x1=1.00,
                y1=1.00,
                line=dict(color="rgba(34,197,94,0.26)", width=1),
                fillcolor="rgba(7,20,38,0.46)",
                layer="below",
            ),
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0.00,
                y0=0.00,
                x1=0.47,
                y1=0.44,
                line=dict(color="rgba(239,68,68,0.26)", width=1),
                fillcolor="rgba(7,20,38,0.46)",
                layer="below",
            ),
            dict(
                type="rect",
                xref="paper",
                yref="paper",
                x0=0.53,
                y0=0.00,
                x1=1.00,
                y1=0.44,
                line=dict(color="rgba(168,85,247,0.24)", width=1),
                fillcolor="rgba(7,20,38,0.46)",
                layer="below",
            ),
        ],
        annotations=[
            dict(
                text=f"Open Relay: {open_relay} · Usuarios inexistentes: {recipient_unknown}",
                x=0.5,
                y=-0.13,
                xref="paper",
                yref="paper",
                showarrow=False,
                font=dict(size=11, color="#aebfd0"),
            )
        ],
    )

    return fig


def pagina_seguridad_smtp(df, metadata, error, search_value=None):
    """Página ejecutiva de seguridad SMTP/SOC."""
    filtered_df = filter_dataframe(df, search_value)
    soc_df, soc_error = load_soc_csv()

    if search_value and not soc_df.empty:
        mask = soc_df.astype(str).apply(
            lambda row: row.str.contains(search_value, case=False, na=False).any(),
            axis=1,
        )
        soc_df = soc_df[mask]

    soc_kpis = calculate_soc_kpis(soc_df)

    tipo = soc_df.get("tipo", pd.Series(dtype=str)).astype(str).str.lower() if not soc_df.empty else pd.Series(dtype=str)
    clasif = soc_df.get("clasificacion_real", pd.Series(dtype=str)).astype(str).str.lower() if not soc_df.empty else pd.Series(dtype=str)

    open_relay = int((tipo == "open_relay_test").sum()) if not soc_df.empty else 0
    auth_fail = int((clasif == "auth_fail").sum()) if not soc_df.empty else 0
    recipient_unknown = int((clasif == "recipient_unknown").sum()) if not soc_df.empty else 0
    tls_ok = int((clasif == "tls_ok").sum()) if not soc_df.empty else 0


    # KPIs SMTP coherentes:
    # Eventos SOC es el total. El resto son familias/dimensiones, no un desglose incompleto por tipo.
    esperado = soc_df.get("resultado_esperado", pd.Series(dtype=str)).astype(str).str.lower() if not soc_df.empty else pd.Series(dtype=str)
    ubicacion = soc_df.get("ubicacion_final", pd.Series(dtype=str)).astype(str).str.lower() if not soc_df.empty else pd.Series(dtype=str)

    abuso_smtp = int(
        (
            tipo.isin(["open_relay_test", "auth_fail", "recipient_unknown"])
            | clasif.isin(["relay_denied", "auth_fail", "recipient_unknown"])
        ).sum()
    ) if not soc_df.empty else 0

    identidad_correo = int(
        (
            tipo.str.contains("spf|dkim|dmarc|spoof|lookalike", regex=True, na=False)
            | clasif.str.contains("spf|dkim|dmarc|spoof|lookalike", regex=True, na=False)
        ).sum()
    ) if not soc_df.empty else 0

    tls_validado = int(
        (
            tipo.str.contains("tls", regex=False, na=False)
            | clasif.eq("tls_ok")
        ).sum()
    ) if not soc_df.empty else 0

    permitidas_controladas = int(
        (
            esperado.eq("permitido")
            | ubicacion.eq("enviado")
            | clasif.eq("smtp_auth_success")
        ).sum()
    ) if not soc_df.empty else 0


    # KPI coherente con el panel "Resultado SOC":
    # mitigadas incluye bloqueos/rechazos y validaciones seguras como TLS OK.
    esperado = soc_df.get("resultado_esperado", pd.Series(dtype=str)).astype(str).str.lower() if not soc_df.empty else pd.Series(dtype=str)
    ubicacion = soc_df.get("ubicacion_final", pd.Series(dtype=str)).astype(str).str.lower() if not soc_df.empty else pd.Series(dtype=str)

    mitigadas_smtp = int(
        (
            ubicacion.isin(["rechazado", "bloqueado", "reject", "rejected"])
            | esperado.isin(["bloqueado", "seguro"])
            | clasif.isin(["relay_denied", "auth_fail", "recipient_unknown", "tls_ok"])
        ).sum()
    ) if not soc_df.empty else 0

    cards = [
        create_metric_card("Eventos SOC", soc_kpis["total"], "Total de pruebas registradas", COLORS["cyan"], "SOC"),
        create_metric_card("Mitigadas", mitigadas_smtp, "Bloqueadas/seguras", COLORS["green"], "OK"),
        create_metric_card("Abuso SMTP", abuso_smtp, "Relay/auth/RCPT", COLORS["orange"], "SMTP"),
        create_metric_card("Identidad correo", identidad_correo, "SPF/DKIM/DMARC", COLORS["purple"], "ID"),
        create_metric_card("TLS OK", tls_validado, "Transporte validado", COLORS["cyan"], "TLS"),
        create_metric_card("Permitidas", permitidas_controladas, "Casos controlados", "#facc15", "OK"),
    ]

    # Tabla específica para Seguridad SMTP.
    # Bloque único y limpio:
    # - usa TODO soc_df;
    # - no filtra por TLS;
    # - humaniza etiquetas;
    # - muestra las filas más recientes del CSV arriba.
    smtp_table_columns = [
        "id_prueba",
        "tipo",
        "resultado_esperado",
        "ubicacion_final",
        "clasificacion_real",
        "origen",
        "destino",
        "evidencia",
    ]

    smtp_labels_clean = {
        "auth_fail": "Auth fail",
        "open_relay_test": "Open relay",
        "recipient_unknown": "Usuario inexistente",
        "tls_starttls_smtp": "STARTTLS SMTP",
        "tls_imaps": "TLS IMAPS",
        "smtp_auth_success": "SMTP AUTH OK",
        "spf_fail": "SPF fail",
        "dkim_broken": "DKIM roto",
        "dkim_absent": "DKIM ausente",
        "dkim_rotation": "Rotación DKIM",
        "spoofing_reject": "DMARC reject",
        "spoofing": "DMARC reject",
        "lookalike_domain": "Dominio lookalike",
        "relay_denied": "Relay denegado",
        "tls_ok": "TLS OK",
        "bloqueado": "Bloqueado",
        "seguro": "Seguro",
        "permitido": "Permitido",
        "rechazado": "Rechazado",
        "enviado": "Enviado",
        "validacion_tecnica": "Validación técnica",
        "fallo_dkim": "Fallo DKIM",
        "sospechoso": "Sospechoso",
    }

    if soc_df is None or soc_df.empty:
        smtp_table_df = pd.DataFrame(columns=smtp_table_columns)
    else:
        smtp_table_df = soc_df.copy()

        if "observaciones" in smtp_table_df.columns:
            evidencia_visual = (
                smtp_table_df["observaciones"]
                .fillna("")
                .astype(str)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
        elif "evidencia" in smtp_table_df.columns:
            evidencia_visual = (
                smtp_table_df["evidencia"]
                .fillna("")
                .astype(str)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
        else:
            evidencia_visual = pd.Series("", index=smtp_table_df.index)

        smtp_table_df["evidencia"] = evidencia_visual.where(
            evidencia_visual.str.len() <= 160,
            evidencia_visual.str.slice(0, 160) + "...",
        )

        for _col in ["tipo", "clasificacion_real", "resultado_esperado", "ubicacion_final"]:
            if _col in smtp_table_df.columns:
                original_values = smtp_table_df[_col].fillna("").astype(str)
                smtp_table_df[_col] = (
                    original_values
                    .map(smtp_labels_clean)
                    .fillna(
                        original_values
                        .str.replace("_", " ", regex=False)
                        .str.replace("-", " ", regex=False)
                        .str.title()
                    )
                )

        smtp_table_df = smtp_table_df[
            [col for col in smtp_table_columns if col in smtp_table_df.columns]
        ].copy()

        # Mostrar primero las últimas filas del CSV, sin filtrar nada.
        smtp_table_df = smtp_table_df.iloc[::-1].reset_index(drop=True)

    smtp_table = dash_table.DataTable(
        id="smtp-soc-table-v2",
        columns=[
            {
                "name": {
                    "id_prueba": "ID",
                    "tipo": "Tipo",
                    "resultado_esperado": "Esperado",
                    "ubicacion_final": "Ubicación",
                    "clasificacion_real": "Clasificación",
                    "origen": "Origen",
                    "destino": "Destino",
                    "evidencia": "Evidencia",
                }.get(col, col),
                "id": col,
            }
            for col in smtp_table_df.columns
        ],
        data=smtp_table_df.to_dict("records"),
        filter_action="native",
        sort_action="native",
        page_action="native",
        page_current=0,
        page_size=10,
        style_table={
            "overflowX": "auto",
            "overflowY": "visible",
            "width": "100%",
            "minWidth": "100%",
            "paddingBottom": "16px",
            "borderRadius": "18px",
            "border": "1px solid rgba(35,215,255,0.14)",
        },
        style_header={
            "backgroundColor": "rgba(8,30,54,0.98)",
            "color": "#9eeaff",
            "fontWeight": "900",
            "fontSize": "12px",
            "textTransform": "uppercase",
            "letterSpacing": "0.045em",
            "border": "1px solid rgba(35,215,255,0.18)",
            "whiteSpace": "normal",
            "height": "auto",
        },
        style_cell={
            "backgroundColor": "rgba(5,18,34,0.78)",
            "color": "#dcecff",
            "fontFamily": "Inter, Segoe UI, Arial, sans-serif",
            "fontSize": "12px",
            "padding": "8px 10px",
            "border": "1px solid rgba(255,255,255,0.055)",
            "textAlign": "left",
            "whiteSpace": "normal",
            "height": "auto",
            "lineHeight": "1.25",
            "minWidth": "105px",
            "maxWidth": "260px",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_cell_conditional=[
            {"if": {"column_id": "id_prueba"}, "width": "105px", "fontWeight": "800"},
            {"if": {"column_id": "tipo"}, "minWidth": "150px", "fontWeight": "800"},
            {"if": {"column_id": "resultado_esperado"}, "width": "120px"},
            {"if": {"column_id": "ubicacion_final"}, "width": "120px", "fontWeight": "800"},
            {"if": {"column_id": "clasificacion_real"}, "minWidth": "145px", "fontWeight": "800"},
            {"if": {"column_id": "origen"}, "minWidth": "180px"},
            {"if": {"column_id": "destino"}, "minWidth": "180px"},
            {"if": {"column_id": "evidencia"}, "minWidth": "420px", "maxWidth": "620px"},
        ],
        style_data_conditional=[
            {
                "if": {"row_index": "odd"},
                "backgroundColor": "rgba(8,26,47,0.78)",
            },

            # relay_denied: verde
            {
                "if": {"filter_query": "{clasificacion_real} contains 'relay_denied'"},
                "backgroundColor": "rgba(34,197,94,0.075)",
                "color": "#dfffea",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'relay_denied'", "column_id": "id_prueba"},
                "borderLeft": "1px solid rgba(35,215,255,0.09)",
            },

            # auth_fail: rojo
            {
                "if": {"filter_query": "{clasificacion_real} contains 'auth_fail'"},
                "backgroundColor": "rgba(239,68,68,0.080)",
                "color": "#ffe1e1",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'auth_fail'", "column_id": "id_prueba"},
                "borderLeft": "1px solid rgba(35,215,255,0.09)",
            },

            # recipient_unknown: amarillo
            {
                "if": {"filter_query": "{clasificacion_real} contains 'recipient_unknown'"},
                "backgroundColor": "rgba(250,204,21,0.085)",
                "color": "#fff7bf",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'recipient_unknown'", "column_id": "id_prueba"},
                "borderLeft": "1px solid rgba(35,215,255,0.09)",
            },

            # tls_ok: morado
            {
                "if": {"filter_query": "{clasificacion_real} contains 'tls_ok'"},
                "backgroundColor": "rgba(168,85,247,0.090)",
                "color": "#f1e4ff",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'tls_ok'", "column_id": "id_prueba"},
                "borderLeft": "1px solid rgba(35,215,255,0.09)",
            },

            # smtp_auth_success: cyan
            {
                "if": {"filter_query": "{clasificacion_real} contains 'smtp_auth_success'"},
                "backgroundColor": "rgba(34,211,238,0.080)",
                "color": "#d9fbff",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'smtp_auth_success'", "column_id": "id_prueba"},
                "borderLeft": "1px solid rgba(35,215,255,0.09)",
            },

            # lookalike/spoofing/dkim/spf: naranja/morado/rojo según riesgo
            {
                "if": {"filter_query": "{clasificacion_real} contains 'lookalike'"},
                "backgroundColor": "rgba(249,115,22,0.085)",
                "color": "#ffedd5",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'lookalike'", "column_id": "id_prueba"},
                "borderLeft": "1px solid rgba(35,215,255,0.09)",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'dkim'"},
                "backgroundColor": "rgba(168,85,247,0.075)",
                "color": "#f1e4ff",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'dkim'", "column_id": "id_prueba"},
                "borderLeft": "1px solid rgba(35,215,255,0.09)",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'spf'"},
                "backgroundColor": "rgba(249,115,22,0.075)",
                "color": "#ffedd5",
            },
            {
                "if": {"filter_query": "{clasificacion_real} contains 'spf'", "column_id": "id_prueba"},
                "borderLeft": "1px solid rgba(35,215,255,0.09)",
            },

            {
                "if": {"state": "active"},
                "backgroundColor": "rgba(35,215,255,0.16)",
                "border": "1px solid rgba(35,215,255,0.45)",
            },
            {
                "if": {"state": "selected"},
                "backgroundColor": "rgba(35,215,255,0.12)",
                "border": "1px solid rgba(35,215,255,0.45)",
            },
        ],
    )


    content = [
        status_alert(filtered_df, metadata, error, search_value),

        html.Div(
            [
                html.Div(
                    "SEGURIDAD SMTP",
                    style={
                        "color": "#38bdf8",
                        "fontSize": "12px",
                        "fontWeight": "900",
                        "letterSpacing": "0.18em",
                        "textTransform": "uppercase",
                        "marginBottom": "6px",
                    },
                ),
                html.Div(
                    "KPIs SOC de correo defensivo",
                    style={
                        "color": "#eaf6ff",
                        "fontSize": "22px",
                        "fontWeight": "900",
                        "lineHeight": "1.15",
                    },
                ),
                html.Div(
                    "Panel verificado en Python: eventos, bloqueos, open relay, autenticación fallida, usuarios inexistentes y TLS.",
                    style={
                        "color": "#aebfd0",
                        "fontSize": "14px",
                        "marginTop": "6px",
                    },
                ),
            ],
            className="smtp-visible-inline-banner",
            style={
                "maxWidth": "1240px",
                "margin": "22px auto 10px auto",
                "padding": "18px 22px",
                "borderRadius": "24px",
                "border": "1px solid rgba(35,215,255,0.35)",
                "background": "linear-gradient(135deg, rgba(6,22,42,0.98), rgba(10,38,64,0.94))",
                "boxShadow": "0 0 28px rgba(35,215,255,0.14), inset 0 1px 0 rgba(255,255,255,0.06)",
            },
        ),

        html.Section(cards, className="kpi-grid smtp-kpi-grid smtp-kpi-grid-confirmado smtp-visual-kpi-grid"),
    ]

    if soc_error:
        content.append(dbc.Alert(soc_error, color="warning", className="status-alert"))

    content.extend(
        [
            dbc.Row(
                [
                    dbc.Col(create_graph(create_soc_type_chart(soc_df), 520), lg=7),
                    dbc.Col(
                        html.Div(
                            [
                                html.Div("COBERTURA DEFENSIVA", className="smtp-coverage-eyebrow"),
                                html.Div("Cobertura defensiva SMTP", className="smtp-coverage-title"),
                                html.Div(
                                    "Lectura ejecutiva de las familias de control cubiertas por la batería SOC.",
                                    className="smtp-coverage-subtitle",
                                ),

                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div("Abuso SMTP", className="smtp-coverage-item-title"),
                                                html.Div("Open relay denegado, autenticación fallida y destinatarios inexistentes.", className="smtp-coverage-item-text"),
                                            ],
                                            className="smtp-coverage-item smtp-coverage-orange",
                                        ),
                                        html.Div(
                                            [
                                                html.Div("Identidad y anti-spoofing", className="smtp-coverage-item-title"),
                                                html.Div("SPF, DKIM, rotación DKIM, spoofing rechazado y dominio lookalike.", className="smtp-coverage-item-text"),
                                            ],
                                            className="smtp-coverage-item smtp-coverage-purple",
                                        ),
                                        html.Div(
                                            [
                                                html.Div("Transporte seguro", className="smtp-coverage-item-title"),
                                                html.Div("STARTTLS SMTP e IMAPS validados como controles de transporte.", className="smtp-coverage-item-text"),
                                            ],
                                            className="smtp-coverage-item smtp-coverage-cyan",
                                        ),
                                        html.Div(
                                            [
                                                html.Div("Trazabilidad SOC", className="smtp-coverage-item-title"),
                                                html.Div("Evidencias desde syslog, pruebas automatizadas y resultados reproducibles.", className="smtp-coverage-item-text"),
                                            ],
                                            className="smtp-coverage-item smtp-coverage-green",
                                        ),
                                    ],
                                    className="smtp-coverage-list",
                                ),

                                html.Div(
                                    [
                                        html.Span("Sin duplicar KPIs"),
                                        html.Span("Cobertura por familias"),
                                        html.Span("Evidencia defensiva"),
                                    ],
                                    className="smtp-coverage-pills",
                                ),
                            ],
                            className="smtp-coverage-panel",
                        ),
                        lg=5,
                    ),
                ],
                className="g-4 dashboard-row smtp-visual-chart-row",
            ),
            html.Section(
                [
                    page_heading(
                        "Seguridad SMTP",
                        "Eventos defensivos automatizados",
                        "Vista SOC de relay denegado, autenticación fallida, destinatarios inexistentes, TLS y otros controles.",
                    ),
                    smtp_table,
                ],
                className="table-shell smtp-table-shell smtp-visual-table-shell",
            ),
        ]
    )

    return content

def build_cronologia_dataset(search_value=None):
    """Construye dataset cronológico combinado: batería principal + pruebas SOC.

    Si no existe una fecha explícita por registro, se usa la fecha de modificación
    del CSV como fecha técnica de referencia. No se inventan fechas.
    """
    from datetime import datetime
    import re

    sources = [
        (CSV_PATH, "bateria_principal"),
        (SOC_CSV_PATH, "soc"),
    ]

    month_map = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    def extract_date_from_text(value):
        text_value = str(value or "")

        # ISO: 2026-07-01
        m = re.search(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b", text_value)
        if m:
            y, mo, d = map(int, m.groups())
            return pd.Timestamp(year=y, month=mo, day=d), "texto_iso"

        # DD/MM/YYYY
        m = re.search(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b", text_value)
        if m:
            d, mo, y = map(int, m.groups())
            return pd.Timestamp(year=y, month=mo, day=d), "texto_ddmmyyyy"

        # Syslog: Jun 28 15:05:03
        m = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})\s+\d{2}:\d{2}:\d{2}\b", text_value, flags=re.I)
        if m:
            month_name = m.group(1).lower()
            day = int(m.group(2))
            year = datetime.now().year
            return pd.Timestamp(year=year, month=month_map[month_name], day=day), "texto_syslog"

        return None, None

    frames = []

    for csv_path, fuente in sources:
        try:
            if not csv_path.exists():
                continue

            df_part = pd.read_csv(csv_path)
            df_part["fuente_cronologia"] = fuente
            df_part["_csv_path"] = str(csv_path)

            mtime_date = pd.Timestamp(datetime.fromtimestamp(csv_path.stat().st_mtime).date())

            fechas = []
            origenes = []

            for _, row in df_part.iterrows():
                detected_date = None
                detected_origin = None

                for col in ["observaciones", "asunto", "id_prueba", "tipo"]:
                    if col in df_part.columns:
                        detected_date, detected_origin = extract_date_from_text(row.get(col, ""))
                        if detected_date is not None:
                            break

                if detected_date is None:
                    detected_date = mtime_date
                    detected_origin = "mtime_csv"

                fechas.append(detected_date)
                origenes.append(detected_origin)

            df_part["fecha_evento"] = pd.to_datetime(fechas)
            df_part["origen_fecha"] = origenes

            frames.append(df_part)

        except Exception:
            continue

    if not frames:
        return pd.DataFrame()

    cron_df = pd.concat(frames, ignore_index=True, sort=False)

    if "tipo" not in cron_df.columns:
        cron_df["tipo"] = "sin_tipo"

    cron_df["tipo"] = cron_df["tipo"].fillna("sin_tipo").astype(str)
    cron_df["fecha_evento"] = pd.to_datetime(cron_df["fecha_evento"]).dt.normalize()

    if search_value:
        mask = cron_df.astype(str).apply(
            lambda row: row.str.contains(search_value, case=False, na=False).any(),
            axis=1,
        )
        cron_df = cron_df[mask]

    return cron_df


def create_cronologia_stock_chart(cron_df, tipo_label="General"):
    """Gráfica cronológica neón para el número de pruebas por día.

    Mantiene el estilo inicial:
    - Actividad diaria en barras.
    - Tendencia neón.
    - Media móvil 3D.
    - Range slider inferior.

    Fix:
    - Título, leyenda, botones y eje inferior no se solapan.
    """
    if cron_df is None or cron_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="Sin datos de cronología",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=18, color="#eaf6ff"),
        )
        fig.update_layout(
            title="Cronología de ataques / pruebas",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#eaf6ff"),
            height=520,
        )
        return fig

    grouped = (
        cron_df.groupby("fecha_evento")
        .size()
        .reset_index(name="eventos")
        .sort_values("fecha_evento")
    )

    min_day = grouped["fecha_evento"].min()
    max_day = grouped["fecha_evento"].max()

    if min_day == max_day:
        idx = pd.date_range(min_day - pd.Timedelta(days=1), max_day + pd.Timedelta(days=1), freq="D")
    else:
        idx = pd.date_range(min_day, max_day, freq="D")

    grouped = (
        grouped.set_index("fecha_evento")
        .reindex(idx, fill_value=0)
        .rename_axis("fecha_evento")
        .reset_index()
    )

    total = int(grouped["eventos"].sum())
    max_value = int(grouped["eventos"].max()) if not grouped.empty else 0

    fecha_origen = (
        cron_df["origen_fecha"].value_counts().index[0]
        if "origen_fecha" in cron_df.columns and not cron_df.empty
        else "desconocido"
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=grouped["fecha_evento"],
            y=grouped["eventos"],
            name="Volumen diario",
            marker=dict(
                color="rgba(35,215,255,0.22)",
                line=dict(color="rgba(35,215,255,0.36)", width=1),
            ),
            opacity=0.70,
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Pruebas: %{y}<extra></extra>",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=grouped["fecha_evento"],
            y=grouped["eventos"],
            name="Tendencia",
            mode="lines+markers",
            line=dict(color="#38f8ff", width=4, shape="spline"),
            marker=dict(
                size=10,
                color="#eaffff",
                line=dict(color="#38f8ff", width=2),
            ),
            fill="tozeroy",
            fillcolor="rgba(56,248,255,0.10)",
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Pruebas: %{y}<extra></extra>",
        )
    )

    if len(grouped) >= 3:
        grouped["media"] = grouped["eventos"].rolling(3, min_periods=1).mean()
        fig.add_trace(
            go.Scatter(
                x=grouped["fecha_evento"],
                y=grouped["media"],
                name="Media 3D",
                mode="lines",
                line=dict(color="#a855f7", width=2, dash="dot"),
                hovertemplate="<b>%{x|%Y-%m-%d}</b><br>Media: %{y:.2f}<extra></extra>",
            )
        )

    fig.update_layout(
        title=dict(
            text=f"Cronología · {tipo_label} · {total} pruebas",
            x=0.035,
            y=0.985,
            xanchor="left",
            yanchor="top",
            font=dict(size=24, color="#eaf6ff"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(2,10,22,0.35)",
        font=dict(color="#eaf6ff", size=12),
        height=520,
        margin=dict(l=54, r=42, t=122, b=104),
        hovermode="x unified",
        showlegend=True,
        legend=dict(
            orientation="h",
            x=0.29,
            y=1.105,
            xanchor="left",
            yanchor="bottom",
            bgcolor="rgba(0,0,0,0)",
            font=dict(color="#dcecff", size=11),
            itemwidth=92,
        ),
        xaxis=dict(
            title=dict(text="Fecha", standoff=34, font=dict(color="#eaf6ff", size=13)),
            gridcolor="rgba(35,215,255,0.08)",
            zeroline=False,
            tickfont=dict(color="#eaf6ff", size=12),
            rangeslider=dict(
                visible=True,
                thickness=0.055,
                bgcolor="rgba(3,12,24,0.72)",
                bordercolor="rgba(35,215,255,0.18)",
                borderwidth=1,
            ),
            rangeselector=dict(
                x=0.005,
                y=1.105,
                xanchor="left",
                yanchor="bottom",
                buttons=[
                    dict(count=7, label="7D", step="day", stepmode="backward"),
                    dict(count=30, label="30D", step="day", stepmode="backward"),
                    dict(step="all", label="ALL"),
                ],
                bgcolor="rgba(8,30,54,0.96)",
                activecolor="rgba(35,215,255,0.42)",
                bordercolor="rgba(35,215,255,0.22)",
                borderwidth=1,
                font=dict(color="#eaf6ff", size=11),
            ),
        ),
        yaxis=dict(
            title=dict(text="Pruebas / ataques", standoff=18, font=dict(color="#eaf6ff", size=13)),
            gridcolor="rgba(35,215,255,0.08)",
            zeroline=False,
            rangemode="tozero",
            tickfont=dict(color="#eaf6ff", size=12),
        ),
        annotations=[
            dict(
                text=f"Máximo diario: {max_value} · Fuente fecha dominante: {fecha_origen}",
                x=0.99,
                y=1.135,
                xref="paper",
                yref="paper",
                showarrow=False,
                xanchor="right",
                font=dict(size=11, color="#aebfd0"),
            )
        ],
    )

    return fig


def pagina_cronologia(df, metadata, error, search_value=None):
    """Página de cronología de pruebas/ataques con minipestañas por tipo."""
    cron_df = build_cronologia_dataset(search_value)

    total_pruebas = int(len(cron_df)) if cron_df is not None and not cron_df.empty else 0
    tipos = (
        cron_df["tipo"].astype(str).value_counts()
        if cron_df is not None and not cron_df.empty and "tipo" in cron_df.columns
        else pd.Series(dtype=int)
    )

    dias = int(cron_df["fecha_evento"].nunique()) if cron_df is not None and not cron_df.empty else 0
    tipos_total = int(tipos.shape[0]) if tipos is not None else 0

    origen_mtime = int((cron_df.get("origen_fecha", pd.Series(dtype=str)) == "mtime_csv").sum()) if cron_df is not None and not cron_df.empty else 0
    origen_texto = total_pruebas - origen_mtime

    tabs = [
        dcc.Tab(
            label=f"General ({total_pruebas})",
            value="general",
            className="cronologia-tab",
            selected_className="cronologia-tab-selected",
            children=[
                html.Div(
                    create_graph(create_cronologia_stock_chart(cron_df, "General"), 455),
                    className="cronologia-chart-shell",
                )
            ],
        )
    ]

    if cron_df is not None and not cron_df.empty:
        for tipo, count in tipos.items():
            tipo_df = cron_df[cron_df["tipo"].astype(str) == str(tipo)].copy()
            tabs.append(
                dcc.Tab(
                    label=f"{str(tipo)[:22]} ({int(count)})",
                    value=str(tipo),
                    className="cronologia-tab",
                    selected_className="cronologia-tab-selected",
                    children=[
                        html.Div(
                            create_graph(create_cronologia_stock_chart(tipo_df, str(tipo)), 455),
                            className="cronologia-chart-shell",
                        )
                    ],
                )
            )

    content = [
        status_alert(df, metadata, error, search_value),
        html.Div(
            [
                html.Div("CRONOLOGÍA DE PRUEBAS SOC", className="cronologia-eyebrow"),
                html.Div("Cronología de ataques y pruebas", className="cronologia-title"),
                html.Div(
                    "Serie temporal de pruebas, ataques simulados y controles SOC registrados cronológicamente.",
                    className="cronologia-subtitle",
                ),
                html.Div(
                    [
                        html.Span(f"{total_pruebas} pruebas totales"),
                        html.Span(f"{tipos_total} tipos"),
                        html.Span(f"{dias} días detectados"),
                        html.Span(f"{origen_texto} con fecha extraída"),
                        html.Span(f"{origen_mtime} con fecha técnica"),
                    ],
                    className="cronologia-pills",
                ),
            ],
            className="cronologia-hero",
        ),
        dcc.Tabs(
            id="cronologia-tabs",
            value="general",
            className="cronologia-tabs",
            parent_className="cronologia-tabs-parent",
            content_className="cronologia-tabs-content",
            children=tabs,
        ),
    ]

    return content


def build_sidebar():
    """Construye la barra lateral izquierda de navegación."""
    return html.Aside(
        [
            dbc.Nav(
                [
                    dbc.NavLink("Visión general", href="/", active="exact", className="nav-item"),
                    dbc.NavLink("Eventos", href="/eventos", active="exact", className="nav-item"),
                    dbc.NavLink("Entregabilidad", href="/entregabilidad", active="exact", className="nav-item"),
                    dbc.NavLink("Spoofing", href="/spoofing", active="exact", className="nav-item"),
                    dbc.NavLink("Seguridad SMTP", href="/seguridad-smtp", active="exact", className="nav-item"),
                    dbc.NavLink("Informes", href="/informes", active="exact", className="nav-item"),                    dbc.NavLink("Cronología", href="/cronologia", active="exact", className="nav-item"),
                ],
                className="side-nav",
                vertical=True,
                pills=True,
            ),
        ],
        className="sidebar",
    )


def fish_logo():
    """Logo superior: pez ciberseguridad con estilo neon para PhisDefense."""
    return html.Span(
        [
            html.Span(className="brand-logo-glow"),
            html.Span(
                [
                    html.Span(className="brand-logo-tail"),
                    html.Span(className="brand-logo-body"),
                    html.Span(className="brand-logo-eye"),
                    html.Span(className="brand-logo-mail-line"),
                    html.Span(className="brand-logo-fin"),
                ],
                className="brand-logo-mark",
            ),
        ],
        className="brand-logo",
        role="img",
        **{"aria-label": "Logotipo PhisDefense SOC"},
    )

def build_header():
    """Construye la cabecera superior con busqueda global."""
    return html.Header(
        [
            html.Div(
                [
                    fish_logo(),
                    html.H1("PhisDefense SOC Command Center"),
                ],
                className="header-title",
            ),
            html.Div(
                [
                    dcc.Input(
                        id="global-search",
                        type="search",
                        placeholder="Buscar en eventos...",
                        debounce=True,
                        className="global-search",
                    ),
                    html.Div("Render demo", className="endpoint-badge"),
                ],
                className="header-actions",
            ),
        ],
        className="topbar",
    )


def build_layout():
    """Compone la estructura principal de la aplicacion Dash."""
    return html.Div(
        [
            dcc.Location(id="url", refresh=False),
            dcc.Interval(id="refresh-interval", interval=60 * 1000, n_intervals=0),
            build_sidebar(),
            html.Main(
                [
                    build_header(),
                    dbc.Container(
                        [html.Div(id="page-content")],
                        fluid=True,
                        className="content-container",
                    ),
                ],
                className="main-panel",
            ),
        ],
        className="app-layout",
    )


external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, title="PhisDefense SOC", suppress_callback_exceptions=True)
server = app.server
app.layout = build_layout


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    Input("refresh-interval", "n_intervals"),
    Input("global-search", "value"),
)
def render_page(pathname, _, search_value):
    """Renderiza la pagina seleccionada sin reiniciar el servidor."""
    df, metadata, error = load_csv()
    routes = {
        "/": pagina_vision_general,
        "/eventos": pagina_eventos,
        "/entregabilidad": pagina_entregabilidad,
        "/spoofing": pagina_spoofing,
        "/seguridad-smtp": pagina_seguridad_smtp,        "/cronologia": pagina_cronologia,
        "/soc": pagina_seguridad_smtp,
        "/informes": pagina_informes,
    }
    page = routes.get(pathname, pagina_vision_general)
    return page(df, metadata, error, search_value)



@app.callback(
    Output("global-distribution-chart", "figure"),
    Output("global-focus-panel", "children"),
    Input("global-distribution-chart", "hoverData"),
    Input("global-distribution-chart", "clickData"),
    Input("global-search", "value"),
    prevent_initial_call=False,
)
def update_global_distribution_interaction(hover_data, click_data, search_value):
    """Actualiza dona y panel de foco con hover/click."""
    df, metadata, error = load_csv()
    filtered_df = filter_dataframe(df, search_value)

    soc_df, _ = load_soc_csv()
    if search_value and not soc_df.empty:
        mask = soc_df.astype(str).apply(
            lambda row: row.str.contains(search_value, case=False, na=False).any(),
            axis=1,
        )
        soc_df = soc_df[mask]

    selected_label = None

    if click_data and click_data.get("points"):
        selected_label = click_data["points"][0].get("label")

    if hover_data and hover_data.get("points"):
        selected_label = hover_data["points"][0].get("label")

    fig = create_distribution_chart_global(filtered_df, soc_df, highlight_label=selected_label)
    panel = create_distribution_focus_panel(filtered_df, soc_df, selected_label=selected_label)

    return fig, panel



app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            :root {
                --page: #06111f;
                --page-2: #08182b;
                --sidebar: #071426;
                --topbar: #0a1d33;
                --panel: #0d2238;
                --panel-2: #102b47;
                --border: #1e4b70;
                --text: #ecf6ff;
                --muted: #90a8bf;
                --blue: #2f8cff;
                --cyan: #23d7ff;
            }

            * {
                box-sizing: border-box;
            }

            body {
                margin: 0;
                background:
                    radial-gradient(circle at 22% 0%, rgba(35, 215, 255, 0.13), transparent 26%),
                    radial-gradient(circle at 88% 16%, rgba(47, 140, 255, 0.12), transparent 28%),
                    linear-gradient(135deg, var(--page), var(--page-2));
                color: var(--text);
                font-family: Inter, "Segoe UI", Arial, sans-serif;
            }

            .app-layout {
                display: grid;
                grid-template-columns: 270px minmax(0, 1fr);
                min-height: 100vh;
            }

            .sidebar {
                position: sticky;
                top: 0;
                height: 100vh;
                padding: 28px 18px;
                background:
                    linear-gradient(180deg, rgba(7, 20, 38, 0.98), rgba(6, 17, 31, 0.96)),
                    repeating-linear-gradient(0deg, rgba(35, 215, 255, 0.04) 0 1px, transparent 1px 72px);
                border-right: 1px solid rgba(30, 75, 112, 0.85);
            }

            .metric-subtitle,
            .section-heading p {
                color: var(--muted);
            }

            .side-nav {
                display: grid;
                gap: 8px;
                margin-top: 0;
            }

            .nav-item,
            .side-nav .nav-link {
                padding: 12px 12px;
                color: #bdd0e4;
                border: 1px solid transparent;
                border-radius: 8px;
                font-size: 14px;
                text-decoration: none;
            }

            .side-nav .nav-link:hover {
                color: white;
                background: rgba(47, 140, 255, 0.08);
            }

            .nav-item.active,
            .side-nav .nav-link.active {
                color: white;
                background: rgba(47, 140, 255, 0.14);
                border-color: rgba(35, 215, 255, 0.45);
                box-shadow: inset 3px 0 0 var(--cyan);
            }


            .main-panel {
                min-width: 0;
            }

            .topbar {
                min-height: 82px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 24px;
                padding: 18px 24px;
                background: rgba(10, 29, 51, 0.74);
                border-bottom: 1px solid rgba(30, 75, 112, 0.75);
                backdrop-filter: blur(12px);
            }

            .header-title {
                display: flex;
                align-items: center;
                gap: 18px;
                min-width: 0;
            }

            .top-fish-logo {
                position: relative;
                display: inline-block;
                width: 56px;
                height: 34px;
                flex: 0 0 56px;
            }

            .top-fish-logo .fish-body {
                position: absolute;
                right: 0;
                top: 7px;
                width: 42px;
                height: 20px;
                border: 3px solid var(--cyan);
                border-left-width: 2px;
                border-radius: 60% 48% 48% 60%;
                box-shadow: 0 0 16px rgba(35, 215, 255, 0.22);
            }

            .top-fish-logo .fish-tail {
                position: absolute;
                left: 0;
                top: 7px;
                width: 24px;
                height: 20px;
                border: 3px solid var(--cyan);
                clip-path: polygon(0 50%, 100% 0, 100% 100%);
                box-shadow: 0 0 14px rgba(35, 215, 255, 0.18);
            }

            .top-fish-logo .fish-eye {
                position: absolute;
                right: 9px;
                top: 15px;
                width: 4px;
                height: 4px;
                border-radius: 50%;
                background: var(--cyan);
                box-shadow: 0 0 8px rgba(35, 215, 255, 0.45);
            }

            .section-kicker,
            .metric-label {
                color: var(--cyan);
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 0;
                text-transform: uppercase;
            }

            h1 {
                margin: 0;
                font-size: 28px;
                line-height: 1.15;
                font-weight: 850;
            }

            .header-actions {
                display: flex;
                align-items: center;
                gap: 12px;
            }

            .global-search {
                width: 320px;
                max-width: 36vw;
                height: 42px;
                padding: 0 14px;
                color: var(--text);
                background: rgba(6, 17, 31, 0.9);
                border: 1px solid rgba(30, 75, 112, 0.9);
                border-radius: 8px;
                outline: none;
            }

            .global-search:focus {
                border-color: var(--cyan);
                box-shadow: 0 0 0 3px rgba(35, 215, 255, 0.12);
            }

            .endpoint-badge {
                padding: 10px 12px;
                color: #bcd4e8;
                background: rgba(13, 34, 56, 0.88);
                border: 1px solid rgba(30, 75, 112, 0.9);
                border-radius: 8px;
                font-size: 13px;
            }

            .content-container {
                padding: 24px;
            }

            .status-alert {
                border-radius: 8px;
                border-width: 1px;
                margin-bottom: 18px;
            }

            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 16px;
                margin-bottom: 16px;
            }

            .kpi-grid.two-columns {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }

            .kpi-grid.report-grid {
                grid-template-columns: repeat(3, minmax(0, 1fr));
            }

            .metric-card {
                height: 122px;
                min-height: 122px;
                border: 1px solid rgba(30, 75, 112, 0.9);
                border-radius: 8px;
                background:
                    linear-gradient(180deg, rgba(16, 43, 71, 0.98), rgba(13, 34, 56, 0.96));
                box-shadow: 0 18px 34px rgba(0, 0, 0, 0.28);
                overflow: hidden;
            }

            .metric-card::before {
                content: "";
                display: block;
                height: 3px;
                background: var(--accent);
            }

            .metric-label {
                display: flex;
                justify-content: space-between;
                gap: 10px;
            }

            .metric-number {
                margin-top: 13px;
                font-size: 36px;
                line-height: 1;
                font-weight: 900;
                color: white;
            }

            .metric-subtitle {
                margin-top: 10px;
                font-size: 13px;
            }

            .dashboard-row {
                margin-bottom: 16px;
            }

            .chart-frame {
                height: 360px;
                overflow: hidden;
                border: 1px solid rgba(30, 75, 112, 0.9);
                border-radius: 8px;
                background: var(--panel);
                box-shadow: 0 18px 34px rgba(0, 0, 0, 0.24);
            }

            .chart-frame .dash-graph,
            .chart-frame .js-plotly-plot,
            .chart-frame .plot-container,
            .chart-frame .svg-container {
                height: 100% !important;
                min-height: 0 !important;
                max-height: 100% !important;
            }

            .js-plotly-plot {
                border: 0;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: none;
            }

            .table-shell {
                padding: 20px;
                background: rgba(13, 34, 56, 0.96);
                border: 1px solid rgba(30, 75, 112, 0.9);
                border-radius: 8px;
                box-shadow: 0 18px 34px rgba(0, 0, 0, 0.24);
            }

            .section-heading {
                display: flex;
                align-items: end;
                justify-content: space-between;
                gap: 24px;
                margin-bottom: 16px;
            }

            .section-heading h2 {
                margin: 2px 0 0;
                font-size: 22px;
                font-weight: 850;
            }

            .section-heading p {
                margin: 0;
                font-size: 14px;
            }

            @media (max-width: 1100px) {
                .app-layout {
                    grid-template-columns: 1fr;
                }

                .sidebar {
                    position: static;
                    height: auto;
                }


                .kpi-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }
            }

            @media (max-width: 720px) {
                .topbar,
                .header-actions,
                .section-heading {
                    display: block;
                }

                .global-search {
                    width: 100%;
                    max-width: none;
                    margin-top: 14px;
                }

                .endpoint-badge {
                    display: inline-block;
                    margin-top: 10px;
                }

                .content-container {
                    padding: 18px 14px 30px;
                }

                .kpi-grid {
                    grid-template-columns: 1fr;
                }
            }
        
            /* ===== PHISDEFENSE PRO THEME V2 START ===== */

            body {
                background:
                    radial-gradient(circle at 15% 10%, rgba(35, 215, 255, 0.12), transparent 28%),
                    radial-gradient(circle at 85% 20%, rgba(157, 92, 255, 0.10), transparent 30%),
                    radial-gradient(circle at 45% 90%, rgba(53, 208, 127, 0.08), transparent 30%),
                    linear-gradient(135deg, #040b14 0%, #071426 45%, #07111f 100%) !important;
                color: #ecf6ff !important;
            }

            .app-layout {
                min-height: 100vh;
                background:
                    linear-gradient(90deg, rgba(35, 215, 255, 0.035) 1px, transparent 1px),
                    linear-gradient(180deg, rgba(35, 215, 255, 0.035) 1px, transparent 1px);
                background-size: 42px 42px;
            }

            .sidebar {
                background:
                    linear-gradient(180deg, rgba(7, 20, 38, 0.98), rgba(5, 13, 25, 0.98)),
                    radial-gradient(circle at 50% 0%, rgba(35, 215, 255, 0.20), transparent 42%) !important;
                border-right: 1px solid rgba(35, 215, 255, 0.18) !important;
                box-shadow: 12px 0 35px rgba(0, 0, 0, 0.38);
            }

            .side-nav {
                gap: 10px !important;
                padding: 18px 12px !important;
            }

            .nav-item {
                border-radius: 14px !important;
                padding: 12px 14px !important;
                color: #a9c4dc !important;
                border: 1px solid transparent !important;
                background: rgba(255, 255, 255, 0.025) !important;
                transition: all 180ms ease !important;
                font-weight: 600 !important;
                letter-spacing: 0.2px;
            }

            .nav-item:hover {
                color: #ecf6ff !important;
                border-color: rgba(35, 215, 255, 0.30) !important;
                background: rgba(35, 215, 255, 0.10) !important;
                transform: translateX(3px);
            }

            .nav-item.active {
                color: #06111f !important;
                background: linear-gradient(135deg, #23d7ff, #35d07f) !important;
                border-color: rgba(236, 246, 255, 0.35) !important;
                box-shadow:
                    0 0 18px rgba(35, 215, 255, 0.35),
                    inset 0 0 0 1px rgba(255, 255, 255, 0.25);
            }

            .topbar {
                background:
                    linear-gradient(90deg, rgba(13, 34, 56, 0.92), rgba(7, 20, 38, 0.72)) !important;
                border-bottom: 1px solid rgba(35, 215, 255, 0.16) !important;
                box-shadow: 0 12px 35px rgba(0, 0, 0, 0.28);
                backdrop-filter: blur(14px);
            }

            .header-title h1 {
                font-size: 1.45rem !important;
                font-weight: 800 !important;
                letter-spacing: 0.3px;
                background: linear-gradient(90deg, #ecf6ff, #23d7ff 55%, #35d07f);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                text-shadow: 0 0 25px rgba(35, 215, 255, 0.16);
            }

            .endpoint-badge {
                border: 1px solid rgba(35, 215, 255, 0.28) !important;
                background: rgba(35, 215, 255, 0.08) !important;
                color: #23d7ff !important;
                border-radius: 999px !important;
                padding: 8px 12px !important;
                box-shadow: inset 0 0 16px rgba(35, 215, 255, 0.08);
            }

            .global-search {
                border-radius: 999px !important;
                border: 1px solid rgba(35, 215, 255, 0.26) !important;
                background: rgba(4, 11, 20, 0.72) !important;
                color: #ecf6ff !important;
                box-shadow: inset 0 0 18px rgba(35, 215, 255, 0.05);
                transition: all 180ms ease;
            }

            .global-search:focus {
                outline: none !important;
                border-color: rgba(35, 215, 255, 0.70) !important;
                box-shadow:
                    0 0 0 3px rgba(35, 215, 255, 0.12),
                    inset 0 0 20px rgba(35, 215, 255, 0.08) !important;
            }

            .content-container {
                padding-top: 24px !important;
            }

            .status-alert {
                border-radius: 18px !important;
                border: 1px solid rgba(35, 215, 255, 0.18) !important;
                background:
                    linear-gradient(135deg, rgba(35, 215, 255, 0.08), rgba(255, 255, 255, 0.025)) !important;
                color: #d8ecff !important;
                box-shadow: 0 12px 30px rgba(0, 0, 0, 0.22);
            }

            .kpi-grid {
                gap: 18px !important;
                margin-bottom: 22px !important;
            }

            .metric-card,
            .kpi-card,
            .card {
                border-radius: 22px !important;
                border: 1px solid rgba(35, 215, 255, 0.18) !important;
                background:
                    linear-gradient(145deg, rgba(16, 43, 71, 0.92), rgba(8, 24, 43, 0.88)) !important;
                box-shadow:
                    0 18px 45px rgba(0, 0, 0, 0.30),
                    inset 0 0 0 1px rgba(255, 255, 255, 0.035);
                backdrop-filter: blur(12px);
                transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
            }

            .metric-card:hover,
            .kpi-card:hover,
            .card:hover {
                transform: translateY(-4px);
                border-color: rgba(35, 215, 255, 0.38) !important;
                box-shadow:
                    0 22px 55px rgba(0, 0, 0, 0.38),
                    0 0 26px rgba(35, 215, 255, 0.12),
                    inset 0 0 0 1px rgba(255, 255, 255, 0.06);
            }

            .chart-frame {
                border-radius: 24px !important;
                border: 1px solid rgba(35, 215, 255, 0.16) !important;
                background:
                    radial-gradient(circle at 20% 0%, rgba(35, 215, 255, 0.10), transparent 34%),
                    linear-gradient(145deg, rgba(13, 34, 56, 0.92), rgba(7, 20, 38, 0.88)) !important;
                box-shadow:
                    0 18px 46px rgba(0, 0, 0, 0.32),
                    inset 0 0 0 1px rgba(255, 255, 255, 0.035);
                overflow: hidden !important;
                transition: transform 180ms ease, border-color 180ms ease;
            }

            .chart-frame:hover {
                transform: translateY(-2px);
                border-color: rgba(35, 215, 255, 0.34) !important;
            }

            .table-shell {
                border-radius: 24px !important;
                border: 1px solid rgba(35, 215, 255, 0.16) !important;
                background:
                    linear-gradient(145deg, rgba(13, 34, 56, 0.95), rgba(7, 20, 38, 0.92)) !important;
                box-shadow:
                    0 18px 46px rgba(0, 0, 0, 0.32),
                    inset 0 0 0 1px rgba(255, 255, 255, 0.035);
                padding: 18px !important;
            }

            .section-heading {
                border-bottom: 1px solid rgba(35, 215, 255, 0.12);
                margin-bottom: 16px !important;
                padding-bottom: 12px !important;
            }

            .section-kicker {
                color: #23d7ff !important;
                text-transform: uppercase;
                letter-spacing: 1.8px;
                font-size: 0.72rem !important;
                font-weight: 800 !important;
            }

            .section-heading h2 {
                color: #ecf6ff !important;
                font-weight: 800 !important;
            }

            .section-heading p {
                color: #90a8bf !important;
            }

            .dash-table-container .dash-spreadsheet-container {
                border-radius: 16px !important;
                overflow: hidden !important;
                border: 1px solid rgba(35, 215, 255, 0.12) !important;
            }

            .dash-table-container .dash-spreadsheet-inner table {
                font-size: 13px !important;
            }

            .dash-table-container .dash-header {
                background: #102b47 !important;
                color: #23d7ff !important;
                font-weight: 800 !important;
            }

            .dash-table-container .dash-cell {
                background: rgba(6, 17, 31, 0.78) !important;
                color: #ecf6ff !important;
                border-color: rgba(35, 215, 255, 0.10) !important;
            }

            .dash-table-container .dash-cell:hover {
                background: rgba(35, 215, 255, 0.08) !important;
            }

            @keyframes subtlePulse {
                0% { box-shadow: 0 0 0 rgba(35, 215, 255, 0.0); }
                50% { box-shadow: 0 0 24px rgba(35, 215, 255, 0.12); }
                100% { box-shadow: 0 0 0 rgba(35, 215, 255, 0.0); }
            }

            .top-fish-logo,
            .brand-logo {
                filter: drop-shadow(0 0 10px rgba(35, 215, 255, 0.45));
                animation: subtlePulse 3.8s ease-in-out infinite;
            }

            /* ===== PHISDEFENSE PRO THEME V2 END ===== */

        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8052, debug=False)



