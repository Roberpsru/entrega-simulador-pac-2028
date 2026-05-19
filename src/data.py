"""Carga y caché de los datasets principales del Simulador PAC Euskadi."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

FICHERO_TABLA = "TABLA_GENERAL_PAGOS_DIRECTOS_2024_ANONIMIZADA.xlsx"
HOJA_TABLA    = "TABLA_GENERAL"


@st.cache_data
def cargar_datos() -> dict[str, pd.DataFrame]:
    """Carga todos los datasets con caché de Streamlit."""
    ruta_tabla = DATA_DIR / FICHERO_TABLA
    if not ruta_tabla.exists():
        raise FileNotFoundError(
            f"Fichero maestro no encontrado: {ruta_tabla}\n"
            "Asegúrate de que el archivo está en la carpeta 'data/' del proyecto."
        )

    df = pd.read_excel(ruta_tabla, sheet_name=HOJA_TABLA, engine="openpyxl")

    # SUP_MAX: superficie máxima incorporable por categoría y territorio
    # El fichero tiene filas ARABA, BIZKAIA, GIPUZKOA (sin fila EUSKADI).
    # El código del simulador calcula el total de Euskadi sumando las tres filas.
    ruta_sup = DATA_DIR / "SUP_MAX_SIGPAC.xlsx"
    if ruta_sup.exists():
        sup_max_df = pd.read_excel(ruta_sup, sheet_name="Superficie", engine="openpyxl")
    else:
        sup_max_df = pd.DataFrame()

    # CULTIVOS: mapa cultivo → categoría SIGPAC
    ruta_cultivos = DATA_DIR / "Tabla_Cultivos_PAC.xlsx"
    if ruta_cultivos.exists():
        cultivos_cat_df = pd.read_excel(
            ruta_cultivos, sheet_name="Sup", engine="openpyxl"
        )
    else:
        cultivos_cat_df = pd.DataFrame()

    return {
        "tabla_general":       df,
        "sup_max_sigpac":      sup_max_df,
        "cultivos_categorias": cultivos_cat_df,
    }
