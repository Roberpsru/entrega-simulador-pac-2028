"""Página de inicio del Simulador PAC Euskadi 2028-2032."""
import base64
from pathlib import Path

import streamlit as st

from src.ui import (
    VERDE_OSCURO,
    aplicar_estilos_pagina,
)

st.set_page_config(page_title="Inicio · PAC Euskadi", layout="wide")
aplicar_estilos_pagina()

DATA_DIR = Path(__file__).resolve().parent / "data"


# ─── Logos institucionales ─────────────────────────────────────────────────

def _img_base64(ruta: Path) -> str:
    with open(ruta, "rb") as f:
        return base64.b64encode(f.read()).decode()


logo_gv = _img_base64(DATA_DIR / "gova.jpg")
logo_hazi = _img_base64(DATA_DIR / "hazi.jpg")

st.markdown(
    f"""
    <div style="display:flex; align-items:center; justify-content:center; gap:60px;
    padding:1rem 0 1.5rem 0; border-bottom:2px solid #e0e0e0; margin-bottom:2rem;">
        <img src="data:image/jpeg;base64,{logo_gv}" style="height:110px; width:auto;">
        <img src="data:image/jpeg;base64,{logo_hazi}" style="height:60px; width:auto;">
    </div>
    """,
    unsafe_allow_html=True,
)


# ─── Título y presentación ─────────────────────────────────────────────────

st.markdown(
    f'<h1 style="color:{VERDE_OSCURO}; margin-top:1.5rem; margin-bottom:1rem;">'
    f'Simulador PAC Euskadi 2028-2032</h1>',
    unsafe_allow_html=True,
)

st.markdown(
    '<p style="font-size:16px; line-height:1.6; color:#222222; '
    'text-align:justify; margin-bottom:1.5rem;">'
    'Esta aplicación es una herramienta de apoyo a la toma de decisiones '
    'técnicas y políticas para el diseño de la Política Agraria Común (PAC) '
    'en Euskadi durante el período de programación <b>2028-2032</b>, '
    'desarrollada por <b>Hazi</b> para el <b>Departamento de Desarrollo '
    'Económico, Sostenibilidad y Medio Ambiente del Gobierno Vasco</b>. '
    'Trabaja sobre los datos reales de pagos directos de la campaña 2024: '
    '<b>7.283 titulares</b>, <b>42.353.115,52 €</b> de presupuesto y '
    '<b>257.360,88 ha</b> declaradas en Araba, Gipuzkoa y Bizkaia.'
    '</p>',
    unsafe_allow_html=True,
)


# ─── Tarjetas de navegación ────────────────────────────────────────────────

col_consulta, col_simulador = st.columns(2)

with col_consulta:
    st.markdown(
        """
        <div style="background-color:#e9f5ee; border-left:6px solid #2d6a4f;
        border-radius:8px; padding:1.2rem 1.5rem; height:100%;">
        <div style="font-size:17px; font-weight:700; color:#1b4332; margin-bottom:0.6rem;">Consulta</div>
        <div style="font-size:14px; color:#333333; line-height:1.6;">
        Explora la distribución actual de las ayudas directas. Filtra por
        territorio, género, edad, tipo de ayuda, cultivo y más para analizar
        cualquier subconjunto del padrón. Incluye análisis con IA para cada
        sección.
        </div></div>
        """,
        unsafe_allow_html=True,
    )

with col_simulador:
    st.markdown(
        """
        <div style="background-color:#e8f4f8; border-left:6px solid #1e6091;
        border-radius:8px; padding:1.2rem 1.5rem; height:100%;">
        <div style="font-size:17px; font-weight:700; color:#1a3a5c; margin-bottom:0.6rem;">Simulador</div>
        <div style="font-size:14px; color:#333333; line-height:1.6;">
        Simula reformas para la PAC 2028-2032 manteniendo el presupuesto
        constante. Modifica los parámetros, incorpora nueva superficie e
        compara el escenario simulado con la situación actual.
        </div></div>
        """,
        unsafe_allow_html=True,
    )


# ─── Pie de página ─────────────────────────────────────────────────────────

st.markdown(
    '<hr style="margin-top:2.5rem; margin-bottom:1rem; '
    'border:none; border-top:1px solid #cccccc;">',
    unsafe_allow_html=True,
)

st.markdown(
    '<p style="font-size:13px; color:#666666; text-align:center; '
    'font-style:italic;">'
    'Los resultados son simulaciones de apoyo a la decisión. La decisión '
    'final corresponde al órgano competente.'
    '</p>',
    unsafe_allow_html=True,
)
