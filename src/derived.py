"""Cálculo de variables derivadas sobre el DataFrame maestro."""
from __future__ import annotations

import datetime

import numpy as np
import pandas as pd

# ─── Tramos canónicos ──────────────────────────────────────────────────────

ORDEN_TRAMO_AYUDA = [
    "<1k", "1-5k", "5-15k", "15-25k", "25-50k", "50-75k",
    "75-100k", "100-150k", "150-200k", "200-300k", ">300k",
]

ORDEN_TRAMO_SUPERFICIE = ["<5", "5-25", "25-100", ">100"]

ORDEN_TRAMO_EDAD = ["<40", "40-54", "55-64", "≥65"]

# Mapa código TH → nombre
_MAPA_TH = {1: "Araba", 20: "Gipuzkoa", 48: "Bizkaia"}


def calcular_derivadas(df: pd.DataFrame) -> pd.DataFrame:
    """Añade columnas derivadas al DataFrame maestro y lo devuelve."""
    df = df.copy()

    # ── TH_DESC ───────────────────────────────────────────────────────────
    if "TH" in df.columns:
        df["TH_DESC"] = df["TH"].map(_MAPA_TH).fillna("Otro")

    # ── EDAD y TRAMO_EDAD ─────────────────────────────────────────────────
    if "FNACIMIENTO" in df.columns:
        año_ref = 2024
        df["EDAD"] = año_ref - pd.to_numeric(
            df["FNACIMIENTO"].astype(str).str[:4], errors="coerce"
        )
        bins  = [-np.inf, 39, 54, 64, np.inf]
        labels = ORDEN_TRAMO_EDAD
        df["TRAMO_EDAD"] = pd.cut(
            df["EDAD"], bins=bins, labels=labels, right=True,
        )

    # ── IMP_AYUDA_TOTAL ───────────────────────────────────────────────────
    cols_imp = [c for c in df.columns if c.startswith("IMP_AYUDA_") and c != "IMP_AYUDA_TOTAL"]
    if cols_imp:
        df["IMP_AYUDA_TOTAL"] = df[cols_imp].sum(axis=1, min_count=1)
    elif "IMP_AYUDA_TOTAL" not in df.columns:
        df["IMP_AYUDA_TOTAL"] = np.nan

    # ── TRAMO_AYUDA (11 tramos) ───────────────────────────────────────────
    bins_ay = [
        -np.inf, 1000, 5000, 15000, 25000, 50000,
        75000, 100000, 150000, 200000, 300000, np.inf,
    ]
    labels_ay = ORDEN_TRAMO_AYUDA
    df["TRAMO_AYUDA"] = pd.cut(
        df["IMP_AYUDA_TOTAL"], bins=bins_ay, labels=labels_ay, right=True,
    )

    # ── TRAMO_SUPERFICIE ──────────────────────────────────────────────────
    col_sup = "SUPERFICIE_TOTAL_DESPUES_CAP"
    if col_sup in df.columns:
        bins_sup  = [-np.inf, 5, 25, 100, np.inf]
        labels_sup = ORDEN_TRAMO_SUPERFICIE
        df["TRAMO_SUPERFICIE"] = pd.cut(
            df[col_sup], bins=bins_sup, labels=labels_sup, right=True,
        )

    # ── N_AYUDAS_DISTINTAS ────────────────────────────────────────────────
    cols_imp_all = [c for c in df.columns if c.startswith("IMP_AYUDA_") and c != "IMP_AYUDA_TOTAL"]
    if cols_imp_all:
        df["N_AYUDAS_DISTINTAS"] = (df[cols_imp_all].fillna(0) > 0).sum(axis=1)

    # ── RECIBE_CJOVEN ─────────────────────────────────────────────────────
    if "IMP_AYUDA_CJOVEN" in df.columns:
        df["RECIBE_CJOVEN"] = df["IMP_AYUDA_CJOVEN"].notna() & (df["IMP_AYUDA_CJOVEN"] > 0)

    # ── ES_PERSONA_FISICA ─────────────────────────────────────────────────
    if "CONDI_JURIDICA" in df.columns and "ES_PERSONA_FISICA" not in df.columns:
        df["ES_PERSONA_FISICA"] = df["CONDI_JURIDICA"].str.upper().isin(
            {"PERSONA FISICA", "PERSONA FÍSICA", "FISICA", "FÍSICA"}
        )

    return df
