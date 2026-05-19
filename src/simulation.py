"""Algoritmos de simulación de redistribución presupuestaria.

Modelo de pago único por superficie ABRS:
    nuevo_valor_ha = presupuesto_activos / (sup_ABRS_activos + nuevas_ha_externas)
    IMP_SIMULADO_i = SUP_Det_Ctr_ABRS_i × nuevo_valor_ha   (explotaciones activas)
    IMP_SIMULADO_i = 0                                       (explotaciones excluidas)
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def simular_superficie(
    df: pd.DataFrame,
    nuevas_ha_externas: float = 0.0,
) -> tuple[pd.DataFrame, float, float]:
    """Redistribuye el presupuesto entre los beneficiarios activos del DataFrame.

    Parámetros
    ----------
    df : DataFrame de explotaciones activas (IMP_AYUDA_TOTAL > 0).
         Debe contener las columnas ``IMP_AYUDA_TOTAL`` y ``SUP_Det_Ctr_ABRS``.
    nuevas_ha_externas : Hectáreas externas (viñedo, frutales, hortícolas)
         a añadir al denominador.  Las ha ABRS sin derecho ya están en
         ``SUP_Det_Ctr_ABRS`` y no se suman aquí.

    Retorna
    -------
    df_simulado : copia de ``df`` con la columna ``IMP_SIMULADO`` añadida.
    nuevo_valor_ha : nuevo valor €/ha ABRS resultante.
    coste_nueva_sup : presupuesto asignado a la nueva superficie externa.
    """
    df = df.copy()

    presupuesto_total = float(df["IMP_AYUDA_TOTAL"].sum())

    if "SUP_Det_Ctr_ABRS" in df.columns:
        sup_abrs = df["SUP_Det_Ctr_ABRS"].fillna(0)
    else:
        sup_abrs = pd.Series(0.0, index=df.index)

    sup_total_denominador = float(sup_abrs.sum()) + float(nuevas_ha_externas)

    if sup_total_denominador <= 0:
        df["IMP_SIMULADO"] = df["IMP_AYUDA_TOTAL"].copy()
        return df, 0.0, 0.0

    nuevo_valor_ha = presupuesto_total / sup_total_denominador

    df["IMP_SIMULADO"] = sup_abrs * nuevo_valor_ha

    # Las explotaciones sin superficie ABRS no reciben ayuda simulada
    df.loc[sup_abrs == 0, "IMP_SIMULADO"] = 0.0

    coste_nueva_sup = float(nuevas_ha_externas) * nuevo_valor_ha

    return df, nuevo_valor_ha, coste_nueva_sup
