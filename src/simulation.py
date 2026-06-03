"""Algoritmos de simulación de redistribución presupuestaria.

Modelo de pago único por superficie ABRS, limitado por los derechos:

    sup_activable_i = min(DERECHOS_i, SUP_Det_Ctr_ABRS_i)      (base: solo lo que
                                                                hoy genera pago)
              + exceso_i × fraccion_reactivada                  (superficie ABRS
                                                                sin derecho que el
                                                                usuario decide
                                                                reactivar, Filtro B)

    nuevo_valor_ha = presupuesto / (Σ sup_activable_i + nuevas_ha_externas)
    IMP_SIMULADO_i = sup_activable_i × nuevo_valor_ha          (explotaciones activas)
    IMP_SIMULADO_i = 0                                          (sin superficie activable
                                                                o explotaciones excluidas)

La superficie ABRS declarada por encima de los derechos (``exceso``) NO entra en
el denominador por defecto: hoy no genera pago.  Solo se incorpora si el usuario
la reactiva mediante el Filtro B "Superficie ABRS sin derecho"; en ese caso se
reparte titular a titular en proporción al exceso de cada uno.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def simular_superficie(
    df: pd.DataFrame,
    nuevas_ha_externas: float = 0.0,
    presupuesto_total: float | None = None,
    ha_abrs_sin_derecho_reactivada: float = 0.0,
) -> tuple[pd.DataFrame, float, float]:
    """Redistribuye el presupuesto entre los beneficiarios activos del DataFrame.

    Parámetros
    ----------
    df : DataFrame de explotaciones activas (IMP_AYUDA_TOTAL > 0).
         Debe contener ``IMP_AYUDA_TOTAL``, ``SUP_Det_Ctr_ABRS`` y ``DERECHOS``.
         La superficie activable de cada titular es ``min(DERECHOS,
         SUP_Det_Ctr_ABRS)``: la que realmente genera pago hoy.  Si falta la
         columna ``DERECHOS`` se usa la superficie ABRS completa (comportamiento
         de compatibilidad).
    nuevas_ha_externas : Hectáreas externas (viñedo, frutales, hortícolas)
         a añadir al denominador.  Son superficie nueva, fuera del padrón actual.
    presupuesto_total : Presupuesto constante a repartir.  Si se indica
         (p. ej. el total del subconjunto ANTES de excluir explotaciones por
         umbral), el importe de las excluidas se redistribuye entre las que
         permanecen.  Si es ``None``, se deriva del propio ``df``.
    ha_abrs_sin_derecho_reactivada : Hectáreas de superficie ABRS declarada pero
         sin derecho (``SUP_Det_Ctr_ABRS`` − ``DERECHOS`` > 0) que el usuario
         decide reactivar (Filtro B).  Se reparten entre los titulares que tienen
         exceso, en proporción a su exceso individual, y se suman al denominador.
         Se recorta automáticamente al exceso total disponible.

    Retorna
    -------
    df_simulado : copia de ``df`` con las columnas ``SUP_ACTIVABLE`` (superficie
         activable por titular usada en el reparto) e ``IMP_SIMULADO`` añadidas.
    nuevo_valor_ha : nuevo valor €/ha resultante.
    coste_nueva_sup : presupuesto asignado a la nueva superficie externa.
    """
    df = df.copy()

    if presupuesto_total is None:
        presupuesto_total = float(df["IMP_AYUDA_TOTAL"].sum())
    else:
        presupuesto_total = float(presupuesto_total)

    if "SUP_Det_Ctr_ABRS" in df.columns:
        sup_abrs = df["SUP_Det_Ctr_ABRS"].fillna(0)
    else:
        sup_abrs = pd.Series(0.0, index=df.index)

    if "DERECHOS" in df.columns:
        derechos = df["DERECHOS"].fillna(0)
    else:
        # Sin columna de derechos no podemos limitar: usamos la ABRS completa.
        derechos = sup_abrs

    # Superficie que hoy genera pago: min(derechos, ABRS) titular a titular.
    sup_con_derecho = np.minimum(derechos, sup_abrs)

    # Superficie ABRS declarada por encima de los derechos (sin derecho asignado).
    exceso = (sup_abrs - derechos).clip(lower=0)
    exceso_total = float(exceso.sum())

    # Filtro B: el usuario reactiva una parte (o el total) del exceso, repartida
    # titular a titular en proporción a su exceso individual.
    ha_reactivada = float(ha_abrs_sin_derecho_reactivada)
    ha_reactivada = max(0.0, min(ha_reactivada, exceso_total))
    fraccion = ha_reactivada / exceso_total if exceso_total > 0 else 0.0

    sup_activable = sup_con_derecho + exceso * fraccion
    df["SUP_ACTIVABLE"] = sup_activable

    sup_total_denominador = float(sup_activable.sum()) + float(nuevas_ha_externas)

    if sup_total_denominador <= 0:
        df["IMP_SIMULADO"] = df["IMP_AYUDA_TOTAL"].copy()
        return df, 0.0, 0.0

    nuevo_valor_ha = presupuesto_total / sup_total_denominador

    df["IMP_SIMULADO"] = sup_activable * nuevo_valor_ha

    # Las explotaciones sin superficie activable no reciben ayuda simulada.
    df.loc[sup_activable == 0, "IMP_SIMULADO"] = 0.0

    coste_nueva_sup = float(nuevas_ha_externas) * nuevo_valor_ha

    return df, nuevo_valor_ha, coste_nueva_sup
