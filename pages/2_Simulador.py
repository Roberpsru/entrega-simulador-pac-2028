"""Simulador — Reformas de la PAC 2028-2032 a presupuesto constante."""
from __future__ import annotations

import locale

import numpy as np
import pandas as pd
import plotly.express as px  # noqa: F401
import streamlit as st

from src.data import cargar_datos
from src.derived import calcular_derivadas
from src.simulation import simular_superficie
from src.ui import (
    AZUL_CLARO, AZUL_SECUND, TEXTO,
    VERDE_CLARO, VERDE_MEDIO, VERDE_OSCURO,
    aplicar_estilos_pagina,
    fmt_euros, fmt_ha, fmt_int, fmt_num, fmt_pct,
    mostrar_tabla, tarjeta, titulo_bloque, titulo_subapartado,
)

st.set_page_config(page_title="Simulador · PAC Euskadi", layout="wide")

try:
    locale.setlocale(locale.LC_ALL, "es_ES.UTF-8")
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, "Spanish_Spain.1252")
    except locale.Error:
        pass

aplicar_estilos_pagina()


# ─── Carga de datos ────────────────────────────────────────────────────────

try:
    datasets = cargar_datos()
except FileNotFoundError as e:
    st.error(str(e))
    st.stop()

df = calcular_derivadas(datasets["tabla_general"])
benef_global = df[df["IMP_AYUDA_TOTAL"] > 0].copy()


def _cat_motivo(v):
    if pd.isna(v) or str(v).strip() == "":
        return "Sin dato / Sin ayuda"
    v = str(v).strip()
    if v == "Bruto >5000":
        return "Sujetos al 25 %"
    if v == "Bruto <5000":
        return "Exentos (importe bajo)"
    if "Adquirido" in v:
        return "Exentos (adquisición)"
    if "Nuevo" in v:
        return "Nuevo agricultor/a"
    return "Sin dato / Sin ayuda"


if "MOTIVO_EXENTO" in benef_global.columns:
    benef_global["MOTIVO_EXENTO_CAT"] = benef_global["MOTIVO_EXENTO"].apply(_cat_motivo)


# ─── Título y metodología ──────────────────────────────────────────────────

st.title("Simulador")
st.caption("Define un escenario, aplica una acción y compara con la situación actual.")


with st.expander(
    "📋 Metodología y limitaciones — leer antes de interpretar", expanded=False,
):
    st.markdown("""
<div style="font-size:14px; line-height:1.6; color:#222;">
<p style="margin:0 0 0.6rem 0;"><b>¿Qué hace este simulador?</b><br>
Explora el efecto económico de hipótesis de reforma de la PAC 2028-2032 sobre las
explotaciones de Euskadi, partiendo de datos reales de la campaña 2024.
El presupuesto total se mantiene constante en todos los escenarios.</p>
<p style="margin:0 0 0.6rem 0;"><b>Modelo de cálculo: pago único por superficie ABRS</b><br>
La simulación sustituye el sistema actual (basado en derechos históricos con valores
diferenciados por región) por un modelo de pago uniforme por hectárea de superficie
ABRS declarada. El nuevo valor por hectárea = presupuesto total ÷ (superficie ABRS
total activa + nueva superficie externa incorporada).</p>
<p style="margin:0 0 0.6rem 0;"><b>Comparación actual vs simulado</b><br>
- <b>Situación actual</b>: el valor de referencia es el importe total ÷ número de derechos
activados (~298 €/derecho). Este es el denominador real del sistema vigente.<br>
- <b>Situación simulada</b>: el valor es el importe total ÷ superficie ABRS elegible total
(incluida la que actualmente carece de derechos asignados) + nueva superficie externa.<br>
- La diferencia entre ambos valores refleja el cambio estructural del modelo, no solo
el efecto de la superficie nueva.</p>
<p style="margin:0 0 0.6rem 0;"><b>Sobre las ayudas asociadas ganaderas</b><br>
Las ayudas asociadas ganaderas (vacuno de carne, ovino/caprino y vacuno de leche)
se integran en el valor por hectárea del modelo simulado. En la realidad estas ayudas
se devengan por animal elegible, no por superficie. El impacto sobre explotaciones
ganaderas debe interpretarse con cautela. Al final de los resultados se muestra la
situación actual detallada de estas ayudas.</p>
<p style="margin:0 0 0.6rem 0;"><b>Explotaciones sin superficie ABRS</b><br>
Algunas explotaciones perciben actualmente ayudas (complemento para jóvenes,
asociadas, ecorregímenes) sin tener superficie ABRS declarada. Estas explotaciones
no pueden incorporarse al modelo de pago por superficie y se identifican
explícitamente en los resultados, separadas de las exclusiones por criterio del usuario.</p>
<p style="margin:0 0 0.6rem 0;"><b>Superficie ABRS sin derecho</b><br>
La superficie ABRS declarada pero sin derecho asignado (SUP_Det_Ctr_ABRS > DERECHOS)
ya está incluida en el denominador del modelo simulado. Al seleccionar esta opción,
el análisis muestra explícitamente cuánta superficie adicional se activa por territorio.</p>
<p style="margin:0 0 0.6rem 0;"><b>Nueva superficie de viñedo, frutales u hortícolas</b><br>
Estas superficies añaden nuevas explotaciones al sistema (actualmente fuera del régimen
de pagos directos). Su número exacto es desconocido: la estimación se basa en la
superficie media actual por tipo de cultivo. Los importes son orientativos.</p>
<p style="margin:0;"><b>Este simulador es una herramienta de análisis, no normativa.</b>
Los escenarios generados apoyan la reflexión técnica y política, pero no prejuzgan
decisiones del Ministerio de Agricultura ni del Gobierno Vasco.</p>
</div>
""", unsafe_allow_html=True)


# ─── Panel de filtros (sidebar) ────────────────────────────────────────────

SIM_FILTRO_KEYS = [
    "sim_f_edad", "sim_f_dedicacion",
    "sim_f_activo", "sim_f_ingresos15k",
]


def limpiar_filtros():
    for k in SIM_FILTRO_KEYS:
        st.session_state[k] = []
    st.session_state.pop("sim_df", None)
    st.session_state.pop("sim_params", None)


edad_opts = ["<40", "40-54", "55-64", "≥65"]
dedicacion_opts = (
    ["100%", "Entre 75 -<100%", "Entre 50 -<75%", "50%",
     "Entre 25 -<50%", "Entre 0 -<25%"]
    if "PORCENT_DEDICADO_AGRIC" in benef_global.columns else []
)
activo_opts = (
    ["Sujetos al 25 %", "Exentos (importe bajo)", "Exentos (adquisición)",
     "Nuevo agricultor/a", "Sin dato / Sin ayuda"]
    if "MOTIVO_EXENTO" in benef_global.columns else []
)
ingresos15k_opts = (
    ["SI", "NO", "Sin dato"]
    if "INGRESOS_AGRARIOS_>15000" in benef_global.columns else []
)

_lineas = []
if st.session_state.get("sim_f_edad"):       _lineas.append(f"Edad: {', '.join(st.session_state['sim_f_edad'])}")
if st.session_state.get("sim_f_dedicacion"): _lineas.append(f"Dedicación: {', '.join(st.session_state['sim_f_dedicacion'])}")
if st.session_state.get("sim_f_activo"):     _lineas.append(f"Activo: {', '.join(st.session_state['sim_f_activo'])}")
if st.session_state.get("sim_f_ingresos15k"):_lineas.append(f"Ingresos >15k: {', '.join(st.session_state['sim_f_ingresos15k'])}")

if _lineas:
    st.sidebar.markdown(
        f'<div style="background-color:{VERDE_CLARO}; border-left:4px solid {VERDE_OSCURO}; '
        f'border-radius:4px; padding:0.5rem 0.75rem; font-size:11px; color:#1b4332; '
        f'line-height:1.6; margin-bottom:0.5rem;">'
        f'<b>Filtros activos</b><br>' + '<br>'.join(_lineas) + '</div>',
        unsafe_allow_html=True,
    )

st.sidebar.divider()
st.sidebar.button("Limpiar filtros", on_click=limpiar_filtros)

st.sidebar.markdown("**Tramo de edad**")
f_edad = st.sidebar.pills("e", edad_opts, selection_mode="multi", key="sim_f_edad", label_visibility="collapsed")

if dedicacion_opts:
    st.sidebar.markdown("**Dedicación**")
    f_ded = st.sidebar.pills("d", dedicacion_opts, selection_mode="multi", key="sim_f_dedicacion", label_visibility="collapsed")
else:
    f_ded = []

if activo_opts:
    st.sidebar.markdown("**Agricultor activo**")
    f_activo = st.sidebar.pills("ac", activo_opts, selection_mode="multi", key="sim_f_activo", label_visibility="collapsed")
else:
    f_activo = []

if ingresos15k_opts:
    st.sidebar.markdown("**Ingresos agrarios > 15.000 €**")
    f_ingresos15k = st.sidebar.pills("i", ingresos15k_opts, selection_mode="multi", key="sim_f_ingresos15k", label_visibility="collapsed")
else:
    f_ingresos15k = []


# ─── Aplicar filtros ───────────────────────────────────────────────────────

benef = benef_global.copy()
if f_edad:
    benef = benef[benef["TRAMO_EDAD"].astype(str).isin(f_edad)]
if f_ded and "PORCENT_DEDICADO_AGRIC" in benef.columns:
    benef = benef[benef["PORCENT_DEDICADO_AGRIC"].isin(f_ded)]
if f_activo and "MOTIVO_EXENTO_CAT" in benef.columns:
    benef = benef[benef["MOTIVO_EXENTO_CAT"].isin(f_activo)]
if f_ingresos15k and "INGRESOS_AGRARIOS_>15000" in benef.columns:
    col_ing = benef["INGRESOS_AGRARIOS_>15000"]
    mask = pd.Series(False, index=benef.index)
    if "SI" in f_ingresos15k:
        mask = mask | (col_ing == "SI")
    if "NO" in f_ingresos15k:
        mask = mask | (col_ing == "NO")
    if "Sin dato" in f_ingresos15k:
        mask = mask | col_ing.isna()
    benef = benef[mask]

if len(benef) == 0:
    st.warning("No hay beneficiarios que cumplan los filtros seleccionados.")
    st.stop()

total_filtrado = len(benef)
total_global = len(benef_global)

st.sidebar.markdown(
    f'<div style="font-size:11px; color:#666; margin-top:0.5rem; line-height:1.7;">'
    f'Registros cargados: <b>{fmt_int(total_global)}</b><br>'
    f'Registros filtrados: <b>{fmt_int(total_filtrado)}</b>'
    f'</div>',
    unsafe_allow_html=True,
)


# ═══ Acción de simulación ══════════════════════════════════════════════════

titulo_bloque("Acción de simulación")

st.info(
    "Las dos acciones son acumulativas. Primero se aplica el umbral mínimo "
    "(define quién participa). Después se incorpora la nueva superficie "
    "(redistribuye el presupuesto entre las explotaciones activas más la nueva "
    "superficie). Puedes usar una sola o ambas combinadas."
)

# ── A. Umbral mínimo de ayuda ────────────────────────────────────────────
titulo_subapartado("A. Umbral mínimo de ayuda")
umbral = st.slider(
    "Excluir explotaciones que reciben menos de (€) — pon 0 para desactivar",
    0, 5000, 0, step=50, key="sim_umbral",
)
n_excl_prev = int((benef["IMP_AYUDA_TOTAL"] < umbral).sum()) if umbral > 0 else 0
st.caption(
    f"{fmt_int(n_excl_prev)} explotaciones quedarían excluidas." if umbral > 0
    else "Umbral desactivado. Todas las explotaciones del subconjunto participan."
)

# ── B. Incorporar superficie adicional ───────────────────────────────────
titulo_subapartado("B. Incorporar superficie adicional")
st.markdown("**Tipos de superficie a incorporar** (selecciona uno o varios)")
tipos_sel = st.pills(
    "tipos_sup",
    ["Viñedo y Txakoli", "Frutales y frutos secos", "Hortícolas", "Superficie ABRS sin derecho"],
    selection_mode="multi", key="sim_tipos_sup", label_visibility="collapsed",
)

nuevas_ha_por_tipo: dict[str, float] = {}
total_nuevas_ha = 0.0

if tipos_sel:
    sup_max_df = datasets["sup_max_sigpac"]
    cultivos_cat_df = datasets["cultivos_categorias"]

    CAT_SIGPAC = {
        "Viñedo y Txakoli":        "VIÑEDO Y TXAKOLI",
        "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
        "Hortícolas":              "HORTICOLA",
    }

    def _max_incorporable(tipo: str) -> float:
        if tipo == "Superficie ABRS sin derecho":
            exceso = (
                benef_global["SUP_Det_Ctr_ABRS"].fillna(0)
                - benef_global["DERECHOS"].fillna(0)
            ).clip(lower=0)
            return float(exceso.sum())
        col_sig = CAT_SIGPAC[tipo]
        sigpac_max = float(sup_max_df[col_sig].sum())
        cultivos = cultivos_cat_df[
            cultivos_cat_df[col_sig] == "SI"
        ]["Unnamed: 0"].tolist()
        cols_ok = [c for c in cultivos if c in benef_global.columns]
        sup_declarada = float(benef_global[cols_ok].sum().sum()) if cols_ok else 0.0
        return max(0.0, sigpac_max - sup_declarada)

    for tipo in tipos_sel:
        max_ha = _max_incorporable(tipo)
        if max_ha > 0:
            ha = st.slider(
                f"Ha a incorporar — {tipo}",
                0.0, float(max_ha), 0.0, step=10.0,
                key=f"sim_ha_{tipo}",
            )
            st.caption(f"Máximo incorporable: {fmt_ha(max_ha)}")
        else:
            ha = 0.0
            st.warning(f"No hay superficie incorporable de tipo «{tipo}» en este subconjunto.")
        nuevas_ha_por_tipo[tipo] = ha

    total_nuevas_ha = sum(nuevas_ha_por_tipo.values())


# ── Detección de cambios respecto a la última simulación ────────────────
params_actuales = {
    "umbral": int(umbral),
    "nuevas_ha_por_tipo": dict(nuevas_ha_por_tipo),
    "filtros": {k: st.session_state.get(k, []) for k in SIM_FILTRO_KEYS},
}
if "sim_params" in st.session_state:
    ultimo = st.session_state["sim_params"]
    cambiado = (
        params_actuales["umbral"] != ultimo.get("umbral", 0)
        or params_actuales["nuevas_ha_por_tipo"] != ultimo.get("nuevas_ha_por_tipo", {})
        or params_actuales["filtros"] != ultimo.get("filtros", {})
    )
    if cambiado and "sim_df" in st.session_state:
        st.warning(
            "⚠ Los parámetros han cambiado desde la última simulación. "
            "Pulsa **Simular** para actualizar los resultados."
        )

accion_activa = umbral > 0 or total_nuevas_ha > 0
simular = st.button("Simular", type="primary") if accion_activa else False
if not accion_activa:
    st.caption("Configura al menos una acción para activar el botón Simular.")


# ═══ Lógica de simulación combinada ════════════════════════════════════════

if simular:
    # Solo viñedo, frutales, hortícolas son verdaderamente "nuevas".
    # "Superficie ABRS sin derecho" ya está en SUP_Det_Ctr_ABRS y se activa
    # automáticamente al usar el modelo de pago único por superficie.
    TIPOS_EXTERNOS = {"Viñedo y Txakoli", "Frutales y frutos secos", "Hortícolas"}
    total_nuevas_ha_externas = sum(
        ha for tipo, ha in nuevas_ha_por_tipo.items()
        if tipo in TIPOS_EXTERNOS
    )
    ha_abrs_sin_derecho = nuevas_ha_por_tipo.get("Superficie ABRS sin derecho", 0.0)

    # PASO 1: umbral
    if umbral > 0:
        mask_excl = benef["IMP_AYUDA_TOTAL"] < umbral
        benef_activos = benef[~mask_excl].copy()
        excluidos_df = benef[mask_excl].copy()
        excluidos_df["IMP_SIMULADO"] = 0.0
    else:
        benef_activos = benef.copy()
        excluidos_df = pd.DataFrame()

    # PASO 2: superficie sobre los activos (solo nuevas externas al denominador)
    if total_nuevas_ha_externas > 0 or umbral > 0:
        df_activos_sim, nuevo_valor_ha, coste_nueva_sup = simular_superficie(
            benef_activos, total_nuevas_ha_externas,
        )
    else:
        df_activos_sim = benef_activos.copy()
        df_activos_sim["IMP_SIMULADO"] = df_activos_sim["IMP_AYUDA_TOTAL"].copy()
        nuevo_valor_ha = 0.0
        coste_nueva_sup = 0.0

    # Distribución de las nuevas ha externas por territorio usando SIGPAC
    sup_max_df = datasets["sup_max_sigpac"]
    CAT_SIGPAC_TERR = {
        "Viñedo y Txakoli":        "VIÑEDO Y TXAKOLI",
        "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
        "Hortícolas":              "HORTICOLA",
    }
    TH_SIGPAC = {"Araba": "ARABA", "Bizkaia": "BIZKAIA", "Gipuzkoa": "GIPUZKOA"}

    ha_externas_por_terr = {"Araba": 0.0, "Bizkaia": 0.0, "Gipuzkoa": 0.0}
    for tipo, ha in nuevas_ha_por_tipo.items():
        if tipo not in TIPOS_EXTERNOS or ha <= 0:
            continue
        col_sig = CAT_SIGPAC_TERR[tipo]
        total_sig = float(sup_max_df[col_sig].sum())
        if total_sig <= 0:
            continue
        for terr, terr_sig in TH_SIGPAC.items():
            fila = sup_max_df[sup_max_df["SUPERFICIE DECLARADA SIGPAC"] == terr_sig]
            if fila.empty:
                continue
            proporcion = float(fila[col_sig].iloc[0]) / total_sig
            ha_externas_por_terr[terr] += ha * proporcion
    ha_externas_por_terr["Euskadi"] = sum(ha_externas_por_terr.values())

    # PASO 3: reunir activos + excluidos
    if len(excluidos_df) > 0:
        df_sim = pd.concat([df_activos_sim, excluidos_df], ignore_index=True)
    else:
        df_sim = df_activos_sim.copy()

    # Estimación de nuevas explotaciones por tipo
    cultivos_cat_df = datasets["cultivos_categorias"]
    cat_sig_map_est = {
        "Viñedo y Txakoli":        "VIÑEDO Y TXAKOLI",
        "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
        "Hortícolas":              "HORTICOLA",
    }
    nuevas_explot_por_tipo: dict[str, int] = {}
    for t in tipos_sel:
        ha = nuevas_ha_por_tipo.get(t, 0.0)
        if t == "Superficie ABRS sin derecho" or ha <= 0:
            nuevas_explot_por_tipo[t] = 0
            continue
        col_sig = cat_sig_map_est[t]
        cultivos = cultivos_cat_df[
            cultivos_cat_df[col_sig] == "SI"
        ]["Unnamed: 0"].tolist()
        cols_ok = [c for c in cultivos if c in benef_global.columns]
        if not cols_ok:
            nuevas_explot_por_tipo[t] = 0
            continue
        suma_por_titular = benef_global[cols_ok].fillna(0).sum(axis=1)
        n_actuales_t = int((suma_por_titular > 0).sum())
        sup_actual_t = float(suma_por_titular.sum())
        sup_media_t = sup_actual_t / n_actuales_t if n_actuales_t > 0 else 0.0
        nuevas_explot_por_tipo[t] = (
            int(round(ha / sup_media_t)) if sup_media_t > 0 else 0
        )

    incluye_sup_nuevos = any(
        t in {"Viñedo y Txakoli", "Frutales y frutos secos", "Hortícolas"}
        for t in tipos_sel
    )

    st.session_state["sim_df"] = df_sim
    st.session_state["sim_params"] = {
        "umbral": int(umbral),
        "n_excl_umbral": int(len(excluidos_df)),
        "tipos_sel": list(tipos_sel),
        "nuevas_ha_por_tipo": dict(nuevas_ha_por_tipo),
        "total_nuevas_ha": float(total_nuevas_ha),
        "total_nuevas_ha_externas": float(total_nuevas_ha_externas),
        "ha_abrs_sin_derecho": float(ha_abrs_sin_derecho),
        "ha_externas_por_terr": {k: float(v) for k, v in ha_externas_por_terr.items()},
        "nuevo_valor_ha": float(nuevo_valor_ha),
        "coste_nueva_sup": float(coste_nueva_sup),
        "incluye_sup_nuevos": incluye_sup_nuevos,
        "nuevas_explot_por_tipo": nuevas_explot_por_tipo,
        "total_nuevas_explot": int(sum(nuevas_explot_por_tipo.values())),
        "filtros": params_actuales["filtros"],
    }


# ═══ Bloques de resultados ═════════════════════════════════════════════════

if "sim_df" in st.session_state and "sim_params" in st.session_state:
    df_sim = st.session_state["sim_df"]
    p = st.session_state["sim_params"]

    # Métricas globales reutilizadas en Bloques A, B y C
    n_sin_abrs = int((benef_global["SUP_Det_Ctr_ABRS"].fillna(0) == 0).sum())
    DERECHOS_GLOBAL_TOP = float(benef_global["DERECHOS"].fillna(0).sum())
    val_actual_por_derecho = (
        float(benef_global["IMP_AYUDA_TOTAL"].sum()) / DERECHOS_GLOBAL_TOP
        if DERECHOS_GLOBAL_TOP > 0 else 0.0
    )

    # ── Bloque A — Banner del escenario ──────────────────────────────────
    titulo_bloque("Escenario simulado", bg=AZUL_SECUND)

    acciones_texto = []
    if p["umbral"] > 0:
        acciones_texto.append(
            f"umbral mínimo de <b>{fmt_euros(p['umbral'])}</b> "
            f"(excluye {fmt_int(p['n_excl_umbral'])} explotaciones)"
        )
    if p["total_nuevas_ha"] > 0:
        tipos_str = ", ".join(
            f"{t}: {fmt_ha(ha)}"
            for t, ha in p["nuevas_ha_por_tipo"].items() if ha > 0
        )
        acciones_texto.append(
            f"incorporación de <b>{fmt_ha(p['total_nuevas_ha'])}</b> ha adicionales "
            f"({tipos_str})"
        )

    acciones_html = (
        " + ".join(acciones_texto) if acciones_texto else "ninguna acción configurada"
    )

    n_total = len(benef_global)
    n_sim = int((df_sim["IMP_SIMULADO"] > 0).sum())
    n_excl_total = n_total - n_sim

    linea_nuevas = ""
    if p["incluye_sup_nuevos"] and p["total_nuevas_explot"] > 0:
        detalle = ", ".join(
            f"{t}: ~{fmt_int(n)}"
            for t, n in p["nuevas_explot_por_tipo"].items() if n > 0
        )
        linea_nuevas = (
            f"<b>Estimación de nuevas explotaciones incorporadas:</b> "
            f"~{fmt_int(p['total_nuevas_explot'])} ({detalle}). "
            f"Calculadas a partir de la superficie media actual por tipo de cultivo.<br>"
        )

    linea_valor_ha = ""
    if p["nuevo_valor_ha"] > 0:
        sup_total_actual = float(benef_global["SUP_Det_Ctr_ABRS"].fillna(0).sum())
        val_actual_banner = (
            float(benef_global["IMP_AYUDA_TOTAL"].sum()) / sup_total_actual
            if sup_total_actual > 0 else 0.0
        )
        linea_valor_ha = (
            f"<b>Valor medio por hectárea:</b> actual {fmt_euros(val_actual_banner)} → "
            f"simulado {fmt_euros(p['nuevo_valor_ha'])} "
            f"({fmt_pct((p['nuevo_valor_ha'] / val_actual_banner - 1) * 100) if val_actual_banner > 0 else '—'}).<br>"
        )

    n_excl_criterios = max(0, n_excl_total - n_sin_abrs)
    linea_excluidos = (
        f"<b>Explotaciones excluidas por los criterios aplicados (sidebar + umbral):</b> "
        f"{fmt_int(n_excl_criterios)} "
        f"({fmt_pct(n_excl_criterios / n_total * 100) if n_total > 0 else '—'} del padrón).<br>"
        f"<b>Explotaciones sin superficie ABRS declarada:</b> {fmt_int(n_sin_abrs)} — "
        f"no se incorporan al análisis simulado por carecer de base de superficie en este modelo. "
        f"Sus pagos actuales (complemento para jóvenes, asociadas, etc.) no tienen equivalente "
        f"en el modelo de pago único por superficie.<br>"
    )

    st.markdown(f"""
<div style="background-color:#f0f7ff; border-left:6px solid {AZUL_SECUND};
border-radius:8px; padding:1.2rem 1.5rem; font-size:14px; line-height:1.9; color:#222;">
<b>Acciones aplicadas:</b> {acciones_html}.<br>
<b>Hipótesis de partida:</b> presupuesto total constante
({fmt_euros(float(benef_global["IMP_AYUDA_TOTAL"].sum()))}).<br>
{linea_excluidos}<b>Explotaciones que permanecen:</b> {fmt_int(n_sim)}.<br>
{linea_nuevas}{linea_valor_ha}<b>Nota metodológica:</b> los resultados asumen redistribución
proporcional en la estructura actual. La redistribución real depende de decisiones
del Ministerio de Agricultura.
</div>
""", unsafe_allow_html=True)

    if p["incluye_sup_nuevos"]:
        st.warning(
            "⚠ La incorporación de viñedo, frutales u hortícolas implica la creación de "
            "nuevos derechos ABRS y la entrada de explotaciones actualmente fuera del sistema. "
            "El número real de nuevas explotaciones es desconocido. Los importes son orientativos."
        )

    if p["nuevo_valor_ha"] > 0:
        st.info(
            "ℹ Las ayudas asociadas ganaderas (vacuno de carne, ovino/caprino y vacuno de leche) "
            "se han incluido en el cálculo del valor por hectárea ABRS, ya que la simulación "
            "adopta un modelo de pago único por superficie. En la realidad estas ayudas se "
            "devengan por animal elegible, no por hectárea. El impacto sobre explotaciones "
            "ganaderas debe interpretarse con cautela."
        )

    st.markdown(
        f'<div style="background-color:#f8f9fa; border-left:4px solid #999; '
        f'border-radius:4px; padding:0.6rem 1rem; font-size:12px; color:#555; '
        f'margin-bottom:1rem;">'
        f'<b>Criterio de comparación:</b> la situación actual se valora en €/derecho '
        f'({fmt_euros(val_actual_por_derecho)}); la simulada en €/ha de superficie ABRS '
        f'({fmt_euros(p["nuevo_valor_ha"]) if p["nuevo_valor_ha"] > 0 else "—"}). '
        f'Las explotaciones sin superficie ABRS ({fmt_int(n_sin_abrs)}) no se incluyen '
        f'en el análisis simulado y se muestran separadamente.'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Bloque B — Explotaciones y superficie por territorio ─────────────
    titulo_subapartado("Explotaciones y superficie por territorio")

    TIPOS_EXTERNOS_B = {"Viñedo y Txakoli", "Frutales y frutos secos", "Hortícolas"}

    def _sup_activada_actual(df_in):
        """Superficie actualmente activada = min(DERECHOS, SUP_ABRS) por explotación."""
        if "DERECHOS" not in df_in.columns or "SUP_Det_Ctr_ABRS" not in df_in.columns:
            return float(df_in["SUP_Det_Ctr_ABRS"].fillna(0).sum())
        return float(
            df_in[["DERECHOS", "SUP_Det_Ctr_ABRS"]]
            .fillna(0)
            .min(axis=1)
            .sum()
        )

    def _sup_simulada(df_in, ha_externas_terr: float):
        """SUP_Det_Ctr_ABRS de activos (incluye ABRS sin derecho) + nuevas externas."""
        base = float(
            df_in[df_in["IMP_SIMULADO"] > 0]["SUP_Det_Ctr_ABRS"].fillna(0).sum()
        )
        return base + ha_externas_terr

    ha_externas_por_terr = p.get("ha_externas_por_terr", {})
    total_nuevas_ha_externas = p.get("total_nuevas_ha_externas", 0.0)

    filas_terr = []
    for terr in ["Araba", "Bizkaia", "Gipuzkoa", "Euskadi"]:
        df_a = (
            benef_global if terr == "Euskadi"
            else benef_global[benef_global["TH_DESC"] == terr]
        )
        df_s = df_sim if terr == "Euskadi" else df_sim[df_sim["TH_DESC"] == terr]
        n_a = int((df_a["IMP_AYUDA_TOTAL"] > 0).sum())
        n_s = int((df_s["IMP_SIMULADO"] > 0).sum())
        sup_act = _sup_activada_actual(df_a[df_a["IMP_AYUDA_TOTAL"] > 0])
        sup_sim = _sup_simulada(df_s, ha_externas_por_terr.get(terr, 0.0))
        imp_med_a = (
            float(df_a[df_a["IMP_AYUDA_TOTAL"] > 0]["IMP_AYUDA_TOTAL"].mean())
            if n_a > 0 else 0.0
        )
        imp_med_s = (
            float(df_s[df_s["IMP_SIMULADO"] > 0]["IMP_SIMULADO"].mean())
            if n_s > 0 else 0.0
        )
        filas_terr.append({
            "Territorio":             terr,
            "Benef. actual":          fmt_int(n_a),
            "Benef. simulado":        fmt_int(n_s),
            "Δ Benef.":               fmt_int(n_s - n_a),
            "Sup. activada actual":   fmt_ha(sup_act),
            "Sup. activada simulada": fmt_ha(sup_sim),
            "Δ Superficie":           fmt_ha(sup_sim - sup_act),
            "Imp. medio actual":      fmt_euros(imp_med_a),
            "Imp. medio simulado":    fmt_euros(imp_med_s),
            "Δ Imp. medio": (
                fmt_pct((imp_med_s / imp_med_a - 1) * 100) if imp_med_a > 0 else "—"
            ),
        })

    # Fila nuevas explotaciones (estimación) — superficie media ponderada
    _sup_media_nuevas = 0.0
    if any(p["nuevas_ha_por_tipo"].get(t, 0) > 0 for t in TIPOS_EXTERNOS_B):
        cultivos_cat_df_b = datasets["cultivos_categorias"]
        cat_sig_map_b = {
            "Viñedo y Txakoli":        "VIÑEDO Y TXAKOLI",
            "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
            "Hortícolas":              "HORTICOLA",
        }
        sup_medias_list = []
        for t, n_nv in p["nuevas_explot_por_tipo"].items():
            if n_nv <= 0 or t not in cat_sig_map_b:
                continue
            col_sig = cat_sig_map_b[t]
            cultivos = cultivos_cat_df_b[
                cultivos_cat_df_b[col_sig] == "SI"
            ]["Unnamed: 0"].tolist()
            cols_ok = [c for c in cultivos if c in benef_global.columns]
            if not cols_ok:
                continue
            sup_por_tit = benef_global[cols_ok].fillna(0).sum(axis=1)
            n_act_t = int((sup_por_tit > 0).sum())
            if n_act_t > 0:
                sup_medias_list.append(float(sup_por_tit.sum()) / n_act_t)
        _sup_media_nuevas = float(np.mean(sup_medias_list)) if sup_medias_list else 0.0

        filas_terr.append({
            "Territorio":             "Nuevas explot. (est.)",
            "Benef. actual":          "0",
            "Benef. simulado":        f"~{fmt_int(p['total_nuevas_explot'])}",
            "Δ Benef.":               f"+~{fmt_int(p['total_nuevas_explot'])}",
            "Sup. activada actual":   "—",
            "Sup. activada simulada": fmt_ha(total_nuevas_ha_externas),
            "Δ Superficie":           fmt_ha(total_nuevas_ha_externas),
            "Imp. medio actual":      "—",
            "Imp. medio simulado":    f"~{fmt_euros(p['nuevo_valor_ha'] * _sup_media_nuevas)}",
            "Δ Imp. medio":           "—",
        })

    mostrar_tabla(pd.DataFrame({
        "Territorio":             [f["Territorio"] for f in filas_terr],
        "Benef. actual":          [f["Benef. actual"] for f in filas_terr],
        "Benef. simulado":        [f["Benef. simulado"] for f in filas_terr],
        "Δ Benef.":               [f["Δ Benef."] for f in filas_terr],
        "Sup. activada actual":   [f["Sup. activada actual"] for f in filas_terr],
        "Sup. activada simulada": [f["Sup. activada simulada"] for f in filas_terr],
        "Δ Superficie":           [f["Δ Superficie"] for f in filas_terr],
    }))

    st.markdown("<br>", unsafe_allow_html=True)

    mostrar_tabla(pd.DataFrame({
        "Territorio":          [f["Territorio"] for f in filas_terr],
        "Imp. medio actual":   [f["Imp. medio actual"] for f in filas_terr],
        "Imp. medio simulado": [f["Imp. medio simulado"] for f in filas_terr],
        "Δ Imp. medio":        [f["Δ Imp. medio"] for f in filas_terr],
    }))

    # Texto interpretativo
    n_s_eus = int((df_sim["IMP_SIMULADO"] > 0).sum())
    n_a_eus = int((benef_global["IMP_AYUDA_TOTAL"] > 0).sum())
    im_a_eus = (
        float(benef_global[benef_global["IMP_AYUDA_TOTAL"] > 0]["IMP_AYUDA_TOTAL"].mean())
        if n_a_eus > 0 else 0.0
    )
    im_s_eus = (
        float(df_sim[df_sim["IMP_SIMULADO"] > 0]["IMP_SIMULADO"].mean())
        if n_s_eus > 0 else 0.0
    )

    st.info(
        f"En el escenario simulado participan {fmt_int(n_s_eus)} explotaciones "
        f"({fmt_int(n_a_eus - n_s_eus)} menos que en la situación actual). "
        f"El importe medio por explotación "
        f"{'sube' if im_s_eus >= im_a_eus else 'baja'} "
        f"de {fmt_euros(im_a_eus)} a {fmt_euros(im_s_eus)} "
        f"({fmt_pct(abs((im_s_eus / im_a_eus - 1) * 100) if im_a_eus > 0 else 0)})."
    )

    # ── Bloque C — Valor del derecho a nivel Euskadi ─────────────────────
    titulo_subapartado("Valor del derecho — Euskadi")

    nuevo_vh = p["nuevo_valor_ha"]
    abrs_activos = float(
        df_sim[df_sim["IMP_SIMULADO"] > 0]["SUP_Det_Ctr_ABRS"].fillna(0).sum()
    )
    derechos_sim_aprox = abrs_activos + p.get("total_nuevas_ha_externas", 0.0)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        tarjeta(
            "Derechos / ha totales actuales",
            fmt_int(DERECHOS_GLOBAL_TOP),
        ),
        unsafe_allow_html=True,
    )
    c2.markdown(
        tarjeta(
            "Derechos / ha simulados (aprox.)",
            fmt_int(derechos_sim_aprox),
            bg=AZUL_CLARO, border=AZUL_SECUND, value_color=AZUL_SECUND,
        ),
        unsafe_allow_html=True,
    )
    c3.markdown(
        tarjeta(
            "Valor actual por derecho",
            fmt_euros(val_actual_por_derecho),
        ),
        unsafe_allow_html=True,
    )
    c4.markdown(
        tarjeta(
            "Valor simulado por ha",
            fmt_euros(nuevo_vh) if nuevo_vh > 0 else fmt_euros(val_actual_por_derecho),
            bg=AZUL_CLARO, border=AZUL_SECUND, value_color=AZUL_SECUND,
        ),
        unsafe_allow_html=True,
    )

    st.caption(
        "El valor actual se calcula sobre derechos activados (modelo vigente basado en "
        "derechos históricos). El valor simulado se calcula sobre superficie elegible "
        "total (modelo de pago por superficie). La diferencia refleja el cambio "
        "estructural del modelo, no solo el efecto de la nueva superficie incorporada."
    )

    delta = (
        (nuevo_vh / val_actual_por_derecho - 1) * 100
        if val_actual_por_derecho > 0 and nuevo_vh > 0 else 0
    )
    st.info(
        f"El modelo simulado aplica {fmt_euros(nuevo_vh)} por hectárea de superficie ABRS, "
        f"frente a {fmt_euros(val_actual_por_derecho)} por derecho en el sistema actual. "
        f"Esto supone una {'reducción' if delta < 0 else 'subida'} del {fmt_pct(abs(delta))} "
        f"en el valor unitario. La diferencia refleja tanto el cambio de denominador (de derechos "
        f"a superficie) como el efecto de la nueva superficie incorporada."
    )

    # ── Bloque D — Concentración del presupuesto (Euskadi) ───────────────
    titulo_subapartado("Concentración del presupuesto — Euskadi")

    def _concentracion(serie):
        s = serie[serie > 0].sort_values(ascending=False).reset_index(drop=True)
        if len(s) == 0:
            return 0, 0.0
        cum = s.cumsum()
        n50 = int((cum < s.sum() * 0.5).sum()) + 1
        return n50, n50 / len(s) * 100

    n50_a, pct50_a = _concentracion(benef_global["IMP_AYUDA_TOTAL"])
    n50_s, pct50_s = _concentracion(df_sim["IMP_SIMULADO"])

    c1, c2 = st.columns(2)
    c1.markdown(
        tarjeta(
            "Actual: explotaciones que concentran el 50 % del presupuesto",
            f"{fmt_int(n50_a)} ({fmt_pct(pct50_a)})",
        ),
        unsafe_allow_html=True,
    )
    c2.markdown(
        tarjeta(
            "Simulado: explotaciones que concentran el 50 % del presupuesto",
            f"{fmt_int(n50_s)} ({fmt_pct(pct50_s)})",
            bg=AZUL_CLARO, border=AZUL_SECUND, value_color=AZUL_SECUND,
        ),
        unsafe_allow_html=True,
    )

    mas_menos = "más concentrado" if pct50_s < pct50_a else "más distribuido"
    st.info(
        f"El presupuesto simulado es **{mas_menos}** que el actual: "
        f"el 50 % lo concentran {fmt_int(n50_s)} explotaciones ({fmt_pct(pct50_s)}), "
        f"frente a {fmt_int(n50_a)} ({fmt_pct(pct50_a)}) actualmente. "
        + (
            "Mayor concentración indica que las explotaciones de mayor tamaño ganan peso relativo. "
            if pct50_s < pct50_a else
            "Menor concentración indica un reparto más equitativo entre explotaciones. "
        )
    )

    # Cálculo silencioso de ganadores/perdedores para el payload IA (Bloque G)
    _delta_serie = df_sim["IMP_SIMULADO"] - df_sim["IMP_AYUDA_TOTAL"]
    n_gana = int((_delta_serie > 1).sum())
    n_pierde = int((_delta_serie < -1).sum())
    delta_med_global = float(_delta_serie.median())

    # ── Bloque F — Asociadas ganaderas (situación actual, por territorio) ─
    titulo_subapartado("Ayudas asociadas ganaderas — situación actual")

    st.caption(
        "Solo se muestran los tres grupos ganaderos (vacuno de carne, ovino/caprino "
        "y vacuno de leche). Las asociadas de base vegetal (proteicas, remolacha, olivar) "
        "no se incluyen aquí. En el escenario simulado estos pagos quedan integrados "
        "en el valor por hectárea (ver nota metodológica)."
    )

    GRUPOS_GANADEROS = {
        "Vacuno de carne": {
            "imp": ["IMP_AYUDA_ASOC_VACUNO_CARNE", "IMP_AYUDA_ASOC_CEBO_LARGO", "IMP_AYUDA_ASOC_CEBO_CORTO"],
            "aps": ["Número_APS_ASOC_VACUNO_CARNE", "Número_APS_ASOC_CEBO_LARGO", "Número_APS_ASOC_CEBO_CORTO"],
        },
        "Ovino/Caprino": {
            "imp": ["IMP_AYUDA_ASOC_OVICAP_CARNE", "IMP_AYUDA_ASOC_OVICAP_LECHE", "IMP_AYUDA_ASOC_OVICAP_PASTO"],
            "aps": ["Número_APS_ASOC_OVICAP_CARNE", "Número_APS_ASOC_OVICAP_LECHE", "Número_APS_ASOC_OVICAP_PASTO"],
        },
        "Vacuno de leche": {
            "imp": ["IMP_AYUDA_ASOC_VACLECHE_PENIN", "IMP_AYUDA_ASOC_VACLECHE_MON"],
            "aps": ["Número_APS_ASOC_VACLECHE_PENIN", "Número_APS_ASOC_VACLECHE_MON"],
        },
    }

    filas_gan = []
    resumen_gan = []
    for grupo, cols in GRUPOS_GANADEROS.items():
        cols_imp = [c for c in cols["imp"] if c in benef_global.columns]
        cols_aps = [c for c in cols["aps"] if c in benef_global.columns]
        if not cols_imp:
            continue
        imp_serie = benef_global[cols_imp].fillna(0).sum(axis=1)
        aps_serie = (
            benef_global[cols_aps].fillna(0).sum(axis=1)
            if cols_aps else pd.Series(0, index=benef_global.index)
        )
        mask = imp_serie > 0
        for terr in ["Araba", "Bizkaia", "Gipuzkoa", "Euskadi"]:
            m = mask if terr == "Euskadi" else mask & (benef_global["TH_DESC"] == terr)
            n = int(m.sum())
            if n == 0:
                continue
            imp_t = float(imp_serie[m].sum())
            aps_t = float(aps_serie[m].sum())
            filas_gan.append({
                "Tipo":               grupo,
                "Territorio":         terr,
                "Beneficiarios":      fmt_int(n),
                "Importe total":      fmt_euros(imp_t),
                "Importe medio":      fmt_euros(imp_t / n),
                "Animales elegibles": fmt_int(aps_t),
                "€ / animal":         fmt_euros(imp_t / aps_t if aps_t > 0 else 0),
            })
        n_eus = int(mask.sum())
        imp_eus = float(imp_serie[mask].sum())
        pct_eus = imp_eus / float(benef_global["IMP_AYUDA_TOTAL"].sum()) * 100
        resumen_gan.append(
            f"**{grupo}**: {fmt_int(n_eus)} explotaciones, "
            f"{fmt_euros(imp_eus)} ({fmt_pct(pct_eus)} del presupuesto PAC)"
        )

    if filas_gan:
        mostrar_tabla(pd.DataFrame(filas_gan))
        st.info(" · ".join(resumen_gan))
    else:
        st.caption("No se han encontrado columnas de ayudas asociadas ganaderas.")

    # ── Bloque G — Análisis IA ───────────────────────────────────────────
