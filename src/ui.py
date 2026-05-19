"""Helpers de UI, formato, estilos y utilidades visuales.

Versión sin análisis IA: no requiere anthropic ni pdfplumber.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

# ─── Paleta de colores ─────────────────────────────────────────────────────

VERDE_OSCURO  = "#2d6a4f"
VERDE_MEDIO   = "#52b788"
VERDE_CLARO   = "#e9f5ee"
AZUL_SECUND   = "#1e6091"
AZUL_CLARO    = "#e8f4f8"
AZUL_OSCURO   = "#1a3a5c"
TEXTO         = "#1a1a2e"

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


# ─── Formateo de cifras (estilo europeo) ──────────────────────────────────

def _eu(v: float, decimales: int = 2) -> str:
    """Formatea un número en estilo europeo (. miles, , decimales)."""
    fmt = f"{v:,.{decimales}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_euros(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{_eu(float(v))} €"


def fmt_ha(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{_eu(float(v))} ha"


def fmt_int(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{int(round(float(v))):,}".replace(",", ".")


def fmt_num(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    f = float(v)
    if f == int(f):
        return fmt_int(int(f))
    return _eu(f)


def fmt_pct(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    return f"{_eu(float(v), 1)} %"


# ─── Estilos globales de página ────────────────────────────────────────────

def aplicar_estilos_pagina() -> None:
    st.markdown(
        """
        <style>
        /* Oculta el menú de hamburguesa y el footer de Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}

        /* Ajuste de márgenes del contenido principal */
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1200px;
        }

        /* Estilos para dataframes */
        .stDataFrame { border-radius: 6px; }

        /* Botones primarios en verde */
        .stButton > button[kind="primary"] {
            background-color: #2d6a4f;
            color: white;
            border: none;
        }
        .stButton > button[kind="primary"]:hover {
            background-color: #1b4332;
        }

        /* Scrollbar discreta en tablas */
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-thumb { background: #cccccc; border-radius: 3px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ─── Cabeceras de sección ──────────────────────────────────────────────────

def titulo_bloque(texto: str, bg: str = VERDE_OSCURO) -> None:
    """Cabecera de bloque temático con fondo de color."""
    st.markdown(
        f'<div style="background-color:{bg}; color:white; font-size:17px; '
        f'font-weight:700; padding:0.65rem 1rem; border-radius:6px; '
        f'margin:1.2rem 0 0.8rem 0;">{texto}</div>',
        unsafe_allow_html=True,
    )


def titulo_subapartado(texto: str) -> None:
    """Cabecera de subapartado (verde oscuro, sin fondo de relleno)."""
    st.markdown(
        f'<div style="font-size:15px; font-weight:700; color:{VERDE_OSCURO}; '
        f'border-bottom:2px solid {VERDE_OSCURO}; padding-bottom:0.2rem; '
        f'margin:1rem 0 0.6rem 0;">{texto}</div>',
        unsafe_allow_html=True,
    )


# ─── Tarjeta de métrica ────────────────────────────────────────────────────

def tarjeta(
    label: str,
    value: str,
    bg: str = VERDE_CLARO,
    border: str = VERDE_OSCURO,
    value_color: str = VERDE_OSCURO,
    value_size: str = "28px",
) -> str:
    """Devuelve HTML para una tarjeta de métrica estilizada."""
    return (
        f'<div style="background-color:{bg}; border-left:5px solid {border}; '
        f'border-radius:6px; padding:0.8rem 1rem; margin-bottom:0.5rem;">'
        f'<div style="font-size:12px; color:#555555; margin-bottom:0.3rem;">{label}</div>'
        f'<div style="font-size:{value_size}; font-weight:700; color:{value_color}; '
        f'line-height:1.2;">{value}</div>'
        f'</div>'
    )


# ─── Tabla estilizada ──────────────────────────────────────────────────────

def mostrar_tabla(df: pd.DataFrame, height: int | None = None) -> None:
    """Muestra un DataFrame con formato consistente."""
    kwargs: dict = {"use_container_width": True}
    if height:
        kwargs["height"] = height
    st.dataframe(df, **kwargs)


# ─── Helpers de gráficos Plotly ────────────────────────────────────────────

def estilo_v(fig, title: str = "", height: int = 420):
    """Aplica estilo corporativo a un gráfico de barras vertical."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXTO), x=0),
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=50, t=65, b=50),
        font=dict(color=TEXTO, size=12),
        xaxis=dict(
            showgrid=True, gridcolor="#eeeeee", gridwidth=1,
            zeroline=False,
        ),
        yaxis=dict(showgrid=False, zeroline=False),
        showlegend=True,
    )
    return fig


def estilo_h(fig, title: str = "", height: int = 420):
    """Aplica estilo corporativo a un gráfico de barras horizontal."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXTO), x=0),
        height=height,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=130, r=90, t=65, b=50),
        font=dict(color=TEXTO, size=12),
        xaxis=dict(
            showgrid=True, gridcolor="#eeeeee", gridwidth=1,
            zeroline=False,
        ),
        yaxis=dict(showgrid=False, zeroline=False, automargin=True),
        showlegend=True,
    )
    return fig


def estilo_pie(fig, title: str = ""):
    """Aplica estilo corporativo a un gráfico de donut/pie."""
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=TEXTO), x=0),
        height=380,
        margin=dict(l=20, r=20, t=65, b=20),
        font=dict(color=TEXTO, size=12),
    )
    return fig


def etiq_v(fig):
    """Añade etiquetas numéricas encima de cada barra vertical."""
    fig.update_traces(
        texttemplate="%{y}",
        textposition="outside",
        cliponaxis=False,
    )
    return fig


def etiq_h(fig):
    """Añade etiquetas numéricas a la derecha de cada barra horizontal."""
    fig.update_traces(
        texttemplate="%{x}",
        textposition="outside",
        cliponaxis=False,
    )
    return fig


# ─── Carga de datos auxiliares ─────────────────────────────────────────────

@st.cache_data
def cargar_vmr_derechos() -> pd.DataFrame:
    """Carga el valor medio por región agronómica desde el xlsx auxiliar."""
    ruta = DATA_DIR / "VALOR_MEDIO_REGIONES_ABRS.xlsx"
    if not ruta.exists():
        return pd.DataFrame()
    try:
        df = pd.read_excel(ruta, sheet_name="VMR_Derechos")
        return df
    except Exception:
        return pd.DataFrame()
