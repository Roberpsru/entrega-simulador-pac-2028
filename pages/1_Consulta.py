"""Consulta — versión interactiva del Dashboard con filtros."""
from __future__ import annotations

import locale
import re

import pandas as pd
import plotly.express as px
import streamlit as st

from src.data import cargar_datos
from src.derived import calcular_derivadas
from src.ui import (
    AZUL_CLARO, AZUL_OSCURO, AZUL_SECUND, TEXTO,
    VERDE_CLARO, VERDE_MEDIO, VERDE_OSCURO,
    aplicar_estilos_pagina, cargar_vmr_derechos,
    estilo_h, estilo_pie, estilo_v, etiq_h, etiq_v,
    fmt_euros, fmt_ha, fmt_int, fmt_num, fmt_pct,
    mostrar_tabla, tarjeta,
    titulo_bloque, titulo_subapartado,
)

st.set_page_config(page_title="Consulta · PAC Euskadi", layout="wide")

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

ORDEN_TRAMO8 = ["<1k", "1-5k", "5-15k", "15-25k", "25-50k", "50-75k", "75-100k", ">100k"]
MAPA_TRAMO8 = {
    "<1k": "<1k", "1-5k": "1-5k", "5-15k": "5-15k", "15-25k": "15-25k",
    "25-50k": "25-50k", "50-75k": "50-75k", "75-100k": "75-100k",
    "100-150k": ">100k", "150-200k": ">100k",
    "200-300k": ">100k", ">300k": ">100k",
}
benef_global["TRAMO_AYUDA_8"] = pd.Categorical(
    benef_global["TRAMO_AYUDA"].astype(str).map(MAPA_TRAMO8),
    categories=ORDEN_TRAMO8, ordered=True,
)


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


# ─── Título ────────────────────────────────────────────────────────────────

st.title("Consulta")
st.caption(
    "Aplica filtros sobre el padrón de la campaña 2024 para recalcular "
    "todos los indicadores, gráficos y tablas sobre el subconjunto seleccionado."
)


# ─── Panel de filtros ──────────────────────────────────────────────────────

FILTRO_KEYS = [
    "f_territorio", "f_genero", "f_edad", "f_ayuda", "f_superficie",
    "f_dedicacion", "f_activo", "f_ingresos15k", "f_condi_juridica",
]


def limpiar_filtros():
    for k in FILTRO_KEYS:
        st.session_state[k] = []
    for k in list(st.session_state.keys()):
        if k.startswith("ia_consulta_"):
            del st.session_state[k]


territorios_opts = ["Araba", "Gipuzkoa", "Bizkaia"]
genero_opts = (
    sorted(benef_global["GENERO"].dropna().unique().tolist())
    if "GENERO" in benef_global.columns else []
)
edad_opts = ["<40", "40-54", "55-64", "≥65"]
ayuda_opts = ORDEN_TRAMO8
superficie_opts = ["<5", "5-25", "25-100", ">100"]
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
condi_jur_opts = (
    sorted(benef_global["CONDI_JURIDICA"].dropna().unique().tolist())
    if "CONDI_JURIDICA" in benef_global.columns else []
)

_lineas = []
if st.session_state.get("f_territorio"): _lineas.append(f"Territorio: {', '.join(st.session_state['f_territorio'])}")
if st.session_state.get("f_genero"):     _lineas.append(f"Género: {', '.join(st.session_state['f_genero'])}")
if st.session_state.get("f_edad"):       _lineas.append(f"Edad: {', '.join(st.session_state['f_edad'])}")
if st.session_state.get("f_ayuda"):      _lineas.append(f"Tramo ayuda: {', '.join(st.session_state['f_ayuda'])}")
if st.session_state.get("f_superficie"): _lineas.append(f"Superficie: {', '.join(st.session_state['f_superficie'])}")
if st.session_state.get("f_dedicacion"): _lineas.append(f"Dedicación: {', '.join(st.session_state['f_dedicacion'])}")
if st.session_state.get("f_activo"):     _lineas.append(f"Activo: {', '.join(st.session_state['f_activo'])}")
if st.session_state.get("f_ingresos15k"):_lineas.append(f"Ingresos >15k: {', '.join(st.session_state['f_ingresos15k'])}")
if st.session_state.get("f_condi_juridica"): _lineas.append(f"Cond. jurídica: {', '.join(st.session_state['f_condi_juridica'])}")

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

st.sidebar.markdown("**Territorio**")
f_terr = st.sidebar.pills("t", territorios_opts, selection_mode="multi", key="f_territorio", label_visibility="collapsed")

st.sidebar.markdown("**Género**")
f_gen = st.sidebar.pills("g", genero_opts, selection_mode="multi", key="f_genero", label_visibility="collapsed")

st.sidebar.markdown("**Tramo de edad**")
f_edad = st.sidebar.pills("e", edad_opts, selection_mode="multi", key="f_edad", label_visibility="collapsed")

st.sidebar.markdown("**Tramo de ayuda**")
f_ayuda = st.sidebar.pills("a", ayuda_opts, selection_mode="multi", key="f_ayuda", label_visibility="collapsed")

st.sidebar.markdown("**Tramo de superficie**")
f_sup = st.sidebar.pills("s", superficie_opts, selection_mode="multi", key="f_superficie", label_visibility="collapsed")

if dedicacion_opts:
    st.sidebar.markdown("**Dedicación**")
    f_ded = st.sidebar.pills("d", dedicacion_opts, selection_mode="multi", key="f_dedicacion", label_visibility="collapsed")
else:
    f_ded = []

if activo_opts:
    st.sidebar.markdown("**Agricultor activo**")
    f_activo = st.sidebar.pills("ac", activo_opts, selection_mode="multi", key="f_activo", label_visibility="collapsed")
else:
    f_activo = []

if ingresos15k_opts:
    st.sidebar.markdown("**Ingresos agrarios > 15.000 €**")
    f_ingresos15k = st.sidebar.pills("i", ingresos15k_opts, selection_mode="multi", key="f_ingresos15k", label_visibility="collapsed")
else:
    f_ingresos15k = []

if condi_jur_opts:
    st.sidebar.markdown("**Condición jurídica**")
    f_condi_jur = st.sidebar.pills("cj", condi_jur_opts, selection_mode="multi", key="f_condi_juridica", label_visibility="collapsed")
else:
    f_condi_jur = []


# ─── Aplicar filtros ───────────────────────────────────────────────────────

benef = benef_global.copy()
if f_terr:
    benef = benef[benef["TH_DESC"].isin(f_terr)]
if f_gen and "GENERO" in benef.columns:
    benef = benef[benef["GENERO"].isin(f_gen)]
if f_edad:
    benef = benef[benef["TRAMO_EDAD"].astype(str).isin(f_edad)]
if f_ayuda:
    benef = benef[benef["TRAMO_AYUDA_8"].astype(str).isin(f_ayuda)]
if f_sup:
    benef = benef[benef["TRAMO_SUPERFICIE"].astype(str).isin(f_sup)]
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
if f_condi_jur and "CONDI_JURIDICA" in benef.columns:
    benef = benef[benef["CONDI_JURIDICA"].isin(f_condi_jur)]

if len(benef) == 0:
    st.warning("No hay beneficiarios que cumplan los filtros seleccionados.")
    st.stop()


total_filtrado = len(benef)
total_global = len(benef_global)
pct_filtrado = total_filtrado / total_global * 100
st.markdown(
    f'<div style="background-color:{VERDE_CLARO}; border-left:6px solid {VERDE_OSCURO}; '
    f'border-radius:6px; padding:0.7rem 1rem; margin: 0.5rem 0 1.2rem 0; color:#1b4332; '
    f'font-size:15px; font-weight:700;">'
    f'Mostrando {fmt_int(total_filtrado)} beneficiarios de {fmt_int(total_global)} totales '
    f'({fmt_pct(pct_filtrado)})</div>',
    unsafe_allow_html=True,
)

st.sidebar.markdown(
    f'<div style="font-size:11px; color:#666; margin-top:0.5rem; line-height:1.7;">'
    f'Registros cargados: <b>{fmt_int(total_global)}</b><br>'
    f'Registros filtrados: <b>{fmt_int(total_filtrado)}</b>'
    f'</div>',
    unsafe_allow_html=True,
)


# Métricas globales del subconjunto (para datos_dict de cada bloque)
total_beneficiarios = total_filtrado
importe_total = float(benef["IMP_AYUDA_TOTAL"].sum())


# ═══ RESUMEN GENERAL ══════════════════════════════════════════════════════

titulo_bloque("Resumen General")
vista = st.radio(
    "Vista del resumen",
    ["Derechos", "Superficie / Animales elegibles", "Importes"],
    horizontal=True,
    key="vista_resumen",
    label_visibility="collapsed",
)


def _pivot(df, cols_labels, fmt_func):
    filas = []
    for col, label in cols_labels:
        if col not in df.columns:
            continue
        fila = {"Concepto": label}
        for terr in ["Araba", "Bizkaia", "Gipuzkoa"]:
            fila[terr] = fmt_func(float(df[df["TH_DESC"] == terr][col].sum()))
        fila["Euskadi"] = fmt_func(float(df[col].sum()))
        filas.append(fila)
    return pd.DataFrame(filas) if filas else pd.DataFrame()


df_pivot = pd.DataFrame()

if vista == "Derechos":
    cols_dr = sorted(
        [c for c in benef.columns if c.startswith("D_R_") and c[4:].isdigit()],
        key=lambda c: int(c[4:]),
    )
    cols = [(c, f"Región {int(c[4:]):02d}") for c in cols_dr]
    if "DERECHOS" in benef.columns:
        cols.append(("DERECHOS", "Total Derechos"))
    df_pivot = _pivot(benef, cols, fmt_num)
    mostrar_tabla(df_pivot)

elif vista == "Superficie / Animales elegibles":
    titulo_subapartado("Superficie (ha)")
    cols_sup = [c for c in benef.columns if c.startswith("SUP_Det_Ctr_")]
    cols_sup_lbl = [(c, c.replace("SUP_Det_Ctr_", "").replace("_", " ")) for c in cols_sup]
    df_pivot_sup = _pivot(benef, cols_sup_lbl, fmt_ha)
    mostrar_tabla(df_pivot_sup)

    titulo_subapartado("Animales elegibles (nº)")
    cols_aps = [c for c in benef.columns if c.startswith("Número_APS_")]
    cols_aps_lbl = [(c, c.replace("Número_APS_", "").replace("_", " ")) for c in cols_aps]
    df_pivot_aps = _pivot(benef, cols_aps_lbl, fmt_int)
    mostrar_tabla(df_pivot_aps)

    partes = []
    if not df_pivot_sup.empty:
        partes.append(df_pivot_sup.assign(Sección="Superficie"))
    if not df_pivot_aps.empty:
        partes.append(df_pivot_aps.assign(Sección="Animales elegibles"))
    df_pivot = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()

elif vista == "Importes":
    cols_imp_resumen = [
        c for c in benef.columns
        if c.startswith("IMP_AYUDA_") and c != "IMP_AYUDA_TOTAL"
    ]
    cols_imp_lbl = [(c, c.replace("IMP_AYUDA_", "")) for c in cols_imp_resumen]
    if "IMP_AYUDA_TOTAL" in benef.columns:
        cols_imp_lbl.append(("IMP_AYUDA_TOTAL", "TOTAL"))
    df_pivot = _pivot(benef, cols_imp_lbl, fmt_euros)
    mostrar_tabla(df_pivot)



# ═══ 0. CONDICIÓN DE AGRICULTOR ACTIVO Y ELEGIBILIDAD ══════════════════════

titulo_bloque("0. Condición de agricultor activo y elegibilidad")

if "MOTIVO_EXENTO" in benef.columns:
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

    benef["MOTIVO_EXENTO_CAT"] = benef["MOTIVO_EXENTO"].apply(_cat_motivo)

    ORDEN_CAT = [
        "Sujetos al 25 %", "Exentos (importe bajo)", "Exentos (adquisición)",
        "Nuevo agricultor/a", "Sin dato / Sin ayuda",
    ]
    COLORES_CAT = {
        "Sujetos al 25 %": "#1e6091",
        "Exentos (importe bajo)": "#2d6a4f",
        "Exentos (adquisición)": "#52b788",
        "Nuevo agricultor/a": "#e07b39",
        "Sin dato / Sin ayuda": "#aaaaaa",
    }

    n_25 = 0
    imp_25 = 0.0
    pct_25_imp = 0.0
    n_debajo = 0
    n_encima = 0
    n_nuevos = 0
    cjoven_nuevos = 0
    n_latente_con_derechos = 0
    n_latente_sin_derechos = 0
    pesos_por_tramo_ayuda = pd.DataFrame()
    pesos_por_tramo_edad = pd.DataFrame()


    titulo_subapartado("A. Mapa general del padrón por condición de elegibilidad")

    cat_stats = (
        benef.groupby("MOTIVO_EXENTO_CAT")
        .agg(
            beneficiarios=("MOTIVO_EXENTO_CAT", "size"),
            importe_total=("IMP_AYUDA_TOTAL", "sum"),
            importe_medio=("IMP_AYUDA_TOTAL", "mean"),
            importe_mediano=("IMP_AYUDA_TOTAL", "median"),
        )
        .reset_index()
    )
    cat_stats["pct"] = cat_stats["beneficiarios"] / cat_stats["beneficiarios"].sum() * 100
    cat_stats["MOTIVO_EXENTO_CAT"] = pd.Categorical(
        cat_stats["MOTIVO_EXENTO_CAT"], categories=ORDEN_CAT, ordered=True,
    )
    cat_stats = cat_stats.sort_values("MOTIVO_EXENTO_CAT")

    fig = px.bar(
        cat_stats.sort_values("beneficiarios"),
        x="beneficiarios", y="MOTIVO_EXENTO_CAT", orientation="h",
        color="MOTIVO_EXENTO_CAT", color_discrete_map=COLORES_CAT,
        category_orders={"MOTIVO_EXENTO_CAT": ORDEN_CAT},
    )
    etiq_h(fig)
    fig.update_layout(showlegend=False)
    st.plotly_chart(estilo_h(fig, title="Beneficiarios por condición de elegibilidad"),
                    width="stretch")

    total_n = int(len(benef))
    total_imp_cat = float(benef["IMP_AYUDA_TOTAL"].sum())
    total_row = pd.DataFrame([{
        "MOTIVO_EXENTO_CAT": "Total",
        "beneficiarios": total_n,
        "importe_total": total_imp_cat,
        "importe_medio": total_imp_cat / total_n if total_n else 0.0,
        "importe_mediano": float(benef["IMP_AYUDA_TOTAL"].median()),
        "pct": 100.0,
    }])
    cat_stats_ext = pd.concat(
        [cat_stats.assign(MOTIVO_EXENTO_CAT=cat_stats["MOTIVO_EXENTO_CAT"].astype(str)),
         total_row],
        ignore_index=True,
    )
    mostrar_tabla(pd.DataFrame({
        "Categoría": cat_stats_ext["MOTIVO_EXENTO_CAT"].astype(str),
        "Beneficiarios": cat_stats_ext["beneficiarios"].apply(fmt_int),
        "% sobre total": cat_stats_ext["pct"].apply(fmt_pct),
        "Importe total": cat_stats_ext["importe_total"].apply(fmt_euros),
        "Importe medio": cat_stats_ext["importe_medio"].apply(fmt_euros),
        "Importe mediano": cat_stats_ext["importe_mediano"].apply(fmt_euros),
    }))


    titulo_subapartado("B. El grupo crítico: sujetos al 25 % de la renta agraria")

    grupo_25 = benef[benef["MOTIVO_EXENTO_CAT"] == "Sujetos al 25 %"]
    n_25 = len(grupo_25)
    imp_25 = float(grupo_25["IMP_AYUDA_TOTAL"].sum())
    pct_25_imp = imp_25 / importe_total * 100 if importe_total else 0.0

    k1, k2, k3 = st.columns(3)
    k1.markdown(tarjeta("Beneficiarios sujetos al 25 %", fmt_int(n_25),
                        bg=AZUL_CLARO, border=AZUL_OSCURO, value_color=AZUL_OSCURO),
                unsafe_allow_html=True)
    k2.markdown(tarjeta("Importe que concentran", fmt_euros(imp_25),
                        bg=AZUL_CLARO, border=AZUL_OSCURO, value_color=AZUL_OSCURO),
                unsafe_allow_html=True)
    k3.markdown(tarjeta("% sobre presupuesto del subconjunto", fmt_pct(pct_25_imp),
                        bg=AZUL_CLARO, border=AZUL_OSCURO, value_color=AZUL_OSCURO),
                unsafe_allow_html=True)

    if "RELACION_INGRESOS_AGRARIOS_TOTAL" in grupo_25.columns and n_25 > 0:
        con_dato = grupo_25.dropna(subset=["RELACION_INGRESOS_AGRARIOS_TOTAL"]).copy()
        n_con_dato = len(con_dato)
        st.info(
            f"De los {fmt_int(n_25)} sujetos al 25 %, **{fmt_int(n_con_dato)}** "
            f"({fmt_pct(n_con_dato / n_25 * 100 if n_25 else 0)}) tienen la "
            f"relación de ingresos agrarios declarada."
        )

        if n_con_dato:
            BINS_REL = [-float("inf"), 25, 50, 75, 100, float("inf")]
            LABELS_REL = ["<25 %", "25-50 %", "50-75 %", "75-100 %", ">100 %"]
            con_dato["TRAMO_REL"] = pd.cut(
                con_dato["RELACION_INGRESOS_AGRARIOS_TOTAL"],
                bins=BINS_REL, labels=LABELS_REL, right=False,
            )
            tramo_rel = (
                con_dato.dropna(subset=["TRAMO_REL"])
                .groupby("TRAMO_REL", observed=True).size()
                .reset_index(name="beneficiarios")
            )
            fig = px.bar(
                tramo_rel, x="TRAMO_REL", y="beneficiarios",
                color="TRAMO_REL",
                color_discrete_map={
                    "<25 %": "#c0392b", "25-50 %": VERDE_OSCURO,
                    "50-75 %": VERDE_OSCURO, "75-100 %": VERDE_OSCURO,
                    ">100 %": VERDE_OSCURO,
                },
                category_orders={"TRAMO_REL": LABELS_REL},
            )
            etiq_v(fig)
            fig.update_layout(showlegend=False)
            st.plotly_chart(
                estilo_v(fig, title="Sujetos al 25 % por tramo de relación de ingresos"),
                width="stretch",
            )

            n_debajo = int((con_dato["RELACION_INGRESOS_AGRARIOS_TOTAL"] < 25).sum())
            n_encima = int((con_dato["RELACION_INGRESOS_AGRARIOS_TOTAL"] >= 25).sum())
            st.markdown(
                f'<div style="background-color:#fde8e8; border-left:6px solid #c0392b; '
                f'border-radius:8px; padding:1.25rem 1.5rem; margin-bottom:0.75rem;">'
                f'<div style="font-size:16px; font-weight:700; color:#262730; margin-bottom:0.9rem;">'
                f'Posible riesgo de no elegibilidad (umbral 25 %)</div>'
                f'<div style="display:flex; gap:2rem; flex-wrap:wrap;">'
                f'<div style="flex:1; min-width:220px;">'
                f'<div style="font-size:32px; font-weight:700; color:#c0392b; line-height:1.1;">'
                f'{fmt_int(n_debajo)}</div>'
                f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
                f'titulares por debajo del 25 %</div></div>'
                f'<div style="flex:1; min-width:220px;">'
                f'<div style="font-size:32px; font-weight:700; color:{VERDE_OSCURO}; line-height:1.1;">'
                f'{fmt_int(n_encima)}</div>'
                f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
                f'titulares que cumplen el umbral</div></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

            if "TRAMO_AYUDA_8" in con_dato.columns:
                con_dato["CUMPLE_25"] = (
                    con_dato["RELACION_INGRESOS_AGRARIOS_TOTAL"] >= 25
                ).map({True: "Sí (≥ 25 %)", False: "No (< 25 %)"})
                cruce25 = pd.crosstab(
                    con_dato["TRAMO_AYUDA_8"], con_dato["CUMPLE_25"],
                    margins=True, margins_name="Total",
                )
                cruce25_disp = cruce25.copy().astype("float").map(fmt_int)
                cruce25_disp.insert(0, "Tramo de ayuda", cruce25_disp.index.astype(str))
                mostrar_tabla(cruce25_disp.reset_index(drop=True))
    else:
        st.caption("Columna RELACION_INGRESOS_AGRARIOS_TOTAL no disponible o sin sujetos al 25 %.")


    titulo_subapartado("C. Perfil comparado de los grupos exentos")

    GRUPOS_EXENTOS = ["Exentos (importe bajo)", "Exentos (adquisición)", "Nuevo agricultor/a"]
    DEDIC_ALTA = {"100%", "Entre 75 -<100%", "Entre 50 -<75%"}

    filas_exentos = []
    for grupo in GRUPOS_EXENTOS:
        sub = benef[benef["MOTIVO_EXENTO_CAT"] == grupo]
        if len(sub) == 0:
            continue
        n = len(sub)
        imp_medio = float(sub["IMP_AYUDA_TOTAL"].mean())
        tramo_edad_top = "—"
        if "TRAMO_EDAD" in sub.columns:
            modo = sub["TRAMO_EDAD"].mode()
            if not modo.empty:
                tramo_edad_top = str(modo.iloc[0])
        territorio_top = "—"
        if "TH_DESC" in sub.columns:
            modo = sub["TH_DESC"].mode()
            if not modo.empty:
                territorio_top = str(modo.iloc[0])
        pct_ded_alta = 0.0
        if "PORCENT_DEDICADO_AGRIC" in sub.columns:
            n_alta = int(sub["PORCENT_DEDICADO_AGRIC"].isin(DEDIC_ALTA).sum())
            pct_ded_alta = n_alta / n * 100 if n else 0.0
        filas_exentos.append({
            "Grupo": grupo,
            "Beneficiarios": n,
            "Importe medio": imp_medio,
            "Tramo edad más frecuente": tramo_edad_top,
            "Territorio más frecuente": territorio_top,
            "% dedicación > 50 %": pct_ded_alta,
        })

    if filas_exentos:
        exentos_df = pd.DataFrame(filas_exentos)

        sub_total = benef[benef["MOTIVO_EXENTO_CAT"].isin(GRUPOS_EXENTOS)]
        n_total_exe = len(sub_total)
        imp_medio_total = float(sub_total["IMP_AYUDA_TOTAL"].mean()) if n_total_exe else 0.0
        edad_top_total = "—"
        if "TRAMO_EDAD" in sub_total.columns and not sub_total["TRAMO_EDAD"].mode().empty:
            edad_top_total = str(sub_total["TRAMO_EDAD"].mode().iloc[0])
        terr_top_total = "—"
        if "TH_DESC" in sub_total.columns and not sub_total["TH_DESC"].mode().empty:
            terr_top_total = str(sub_total["TH_DESC"].mode().iloc[0])
        pct_ded_total = 0.0
        if "PORCENT_DEDICADO_AGRIC" in sub_total.columns and n_total_exe:
            n_alta_total = int(sub_total["PORCENT_DEDICADO_AGRIC"].isin(DEDIC_ALTA).sum())
            pct_ded_total = n_alta_total / n_total_exe * 100
        exentos_df_ext = pd.concat([exentos_df, pd.DataFrame([{
            "Grupo": "Total",
            "Beneficiarios": n_total_exe,
            "Importe medio": imp_medio_total,
            "Tramo edad más frecuente": edad_top_total,
            "Territorio más frecuente": terr_top_total,
            "% dedicación > 50 %": pct_ded_total,
        }])], ignore_index=True)

        mostrar_tabla(pd.DataFrame({
            "Grupo": exentos_df_ext["Grupo"],
            "Beneficiarios": exentos_df_ext["Beneficiarios"].apply(fmt_int),
            "Importe medio": exentos_df_ext["Importe medio"].apply(fmt_euros),
            "Tramo edad más frecuente": exentos_df_ext["Tramo edad más frecuente"],
            "Territorio más frecuente": exentos_df_ext["Territorio más frecuente"],
            "% dedicación > 50 %": exentos_df_ext["% dedicación > 50 %"].apply(fmt_pct),
        }))

        if "TH_DESC" in benef.columns:
            terr_exentos = (
                benef[benef["MOTIVO_EXENTO_CAT"].isin(GRUPOS_EXENTOS)]
                .dropna(subset=["TH_DESC"])
                .groupby(["TH_DESC", "MOTIVO_EXENTO_CAT"], observed=True).size()
                .reset_index(name="beneficiarios")
            )
            if not terr_exentos.empty:
                fig = px.bar(
                    terr_exentos, x="TH_DESC", y="beneficiarios",
                    color="MOTIVO_EXENTO_CAT", barmode="group",
                    color_discrete_map=COLORES_CAT,
                    category_orders={"MOTIVO_EXENTO_CAT": GRUPOS_EXENTOS},
                )
                etiq_v(fig)
                st.plotly_chart(
                    estilo_v(fig, title="Distribución territorial de los grupos exentos"),
                    width="stretch",
                )

        nuevos = benef[benef["MOTIVO_EXENTO_CAT"] == "Nuevo agricultor/a"]
        n_nuevos = len(nuevos)
        if n_nuevos > 0:
            titulo_subapartado("Nuevo agricultor/a — detalle")

            if "TRAMO_EDAD" in nuevos.columns:
                edad_nuevos = (
                    nuevos.dropna(subset=["TRAMO_EDAD"])
                    .groupby("TRAMO_EDAD", observed=True).size()
                    .reset_index(name="beneficiarios")
                )
                if not edad_nuevos.empty:
                    fig = px.bar(
                        edad_nuevos, x="TRAMO_EDAD", y="beneficiarios",
                        color_discrete_sequence=["#e07b39"],
                    )
                    etiq_v(fig)
                    st.plotly_chart(
                        estilo_v(fig, title="Nuevos agricultores por tramo de edad"),
                        width="stretch",
                    )

            cjoven_nuevos = (
                int(nuevos["IMP_AYUDA_CJOVEN"].notna().sum())
                if "IMP_AYUDA_CJOVEN" in nuevos.columns else 0
            )
            st.metric("Nuevos agricultores que también cobran CJOVEN", fmt_int(cjoven_nuevos))
    else:
        st.caption("No hay beneficiarios en los grupos exentos.")


    titulo_subapartado("D. Sin dato / Sin ayuda: el padrón latente")

    sin_ayuda = benef[benef["MOTIVO_EXENTO_CAT"] == "Sin dato / Sin ayuda"]
    if "DERECHOS" in sin_ayuda.columns and not sin_ayuda.empty:
        con_derechos = sin_ayuda[(sin_ayuda["DERECHOS"].notna()) & (sin_ayuda["DERECHOS"] > 0)]
        sin_derechos = sin_ayuda[sin_ayuda["DERECHOS"].isna() | (sin_ayuda["DERECHOS"] == 0)]
        n_latente_con_derechos = len(con_derechos)
        n_latente_sin_derechos = len(sin_derechos)

        st.markdown(
            f'<div style="background-color:#fef3e2; border-left:6px solid #e07b39; '
            f'border-radius:8px; padding:1.25rem 1.5rem; margin-bottom:0.75rem;">'
            f'<div style="font-size:16px; font-weight:700; color:#262730; margin-bottom:0.4rem;">'
            f'Padrón latente</div>'
            f'<div style="font-size:32px; font-weight:700; color:#e07b39; line-height:1.1;">'
            f'{fmt_int(n_latente_con_derechos)}</div>'
            f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
            f'titulares con derechos declarados que no percibieron ayudas '
            f'(de un total de {fmt_int(len(sin_ayuda))} sin ayuda en el subconjunto)</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.caption(
            f"{fmt_int(n_latente_sin_derechos)} titulares sin ayuda y sin derechos "
            f"activables registrados."
        )

    if "TH_DESC" in sin_ayuda.columns and not sin_ayuda.empty:
        terr_sin = (
            sin_ayuda.dropna(subset=["TH_DESC"])
            .groupby("TH_DESC", observed=True).size()
            .reset_index(name="beneficiarios")
        )
        if not terr_sin.empty:
            fig = px.bar(
                terr_sin, x="TH_DESC", y="beneficiarios",
                color_discrete_sequence=["#aaaaaa"],
            )
            etiq_v(fig)
            st.plotly_chart(
                estilo_v(fig, title="Distribución territorial del padrón sin ayuda"),
                width="stretch",
            )

    st.warning(
        "Estos titulares figuran en el padrón pero no percibieron pagos directos, "
        "bien por no cumplir la condición de agricultor activo, bien por no "
        "disponer de derechos activables."
    )


    titulo_subapartado("E. Estructura de ingresos agrarios sobre el total")

    if "RELACION_INGRESOS_AGRARIOS_TOTAL" in benef.columns:
        rel_full = benef.dropna(subset=["RELACION_INGRESOS_AGRARIOS_TOTAL"]).copy()
        if not rel_full.empty:
            BINS_REL_E = [-float("inf"), 25, 50, 75, 100, float("inf")]
            LABELS_REL_E = ["<25 %", "25-50 %", "50-75 %", "75-100 %", ">100 %"]
            rel_full["TRAMO_REL_E"] = pd.cut(
                rel_full["RELACION_INGRESOS_AGRARIOS_TOTAL"],
                bins=BINS_REL_E, labels=LABELS_REL_E, right=False,
            )
            tramo_rel_e = (
                rel_full.dropna(subset=["TRAMO_REL_E"])
                .groupby("TRAMO_REL_E", observed=True).size()
                .reset_index(name="beneficiarios")
            )
            fig = px.bar(
                tramo_rel_e, x="TRAMO_REL_E", y="beneficiarios",
                color="TRAMO_REL_E",
                color_discrete_map={
                    "<25 %": "#c0392b", "25-50 %": VERDE_OSCURO,
                    "50-75 %": VERDE_OSCURO, "75-100 %": VERDE_OSCURO,
                    ">100 %": VERDE_OSCURO,
                },
                category_orders={"TRAMO_REL_E": LABELS_REL_E},
            )
            etiq_v(fig)
            fig.update_layout(showlegend=False)
            st.plotly_chart(
                estilo_v(fig, title="Beneficiarios por tramo de relación ingresos agrarios / total"),
                width="stretch",
            )

            col_a, col_b = st.columns(2)
            with col_a:
                if "TRAMO_AYUDA_8" in rel_full.columns:
                    pesos_por_tramo_ayuda = (
                        rel_full.groupby("TRAMO_AYUDA_8", observed=True)
                        ["RELACION_INGRESOS_AGRARIOS_TOTAL"].mean()
                        .reset_index()
                    )
                    fig = px.bar(
                        pesos_por_tramo_ayuda, x="TRAMO_AYUDA_8",
                        y="RELACION_INGRESOS_AGRARIOS_TOTAL",
                        color_discrete_sequence=[AZUL_SECUND],
                    )
                    etiq_v(fig)
                    st.plotly_chart(
                        estilo_v(fig, title="Relación media por tramo de ayuda (%)"),
                        width="stretch",
                    )
            with col_b:
                if "TRAMO_EDAD" in rel_full.columns:
                    pesos_por_tramo_edad = (
                        rel_full.dropna(subset=["TRAMO_EDAD"])
                        .groupby("TRAMO_EDAD", observed=True)
                        ["RELACION_INGRESOS_AGRARIOS_TOTAL"].mean()
                        .reset_index()
                    )
                    fig = px.bar(
                        pesos_por_tramo_edad, x="TRAMO_EDAD",
                        y="RELACION_INGRESOS_AGRARIOS_TOTAL",
                        color_discrete_sequence=[VERDE_OSCURO],
                    )
                    etiq_v(fig)
                    st.plotly_chart(
                        estilo_v(fig, title="Relación media por tramo de edad (%)"),
                        width="stretch",
                    )

            st.caption(
                "Dato disponible solo para los titulares que autorizaron el cruce "
                "con la Agencia Tributaria o Haciendas Forales (aproximadamente el "
                "23 % del padrón). Los valores reflejan la dependencia estructural "
                "de la renta agraria en el sector."
            )


else:
    st.caption("Columna MOTIVO_EXENTO no disponible.")


st.divider()


# ═══ 1. DISTRIBUCIÓN POR TERRITORIO ════════════════════════════════════════

titulo_bloque("1. Distribución por territorio")

terr_stats = (
    benef.dropna(subset=["TH_DESC"])
    .groupby("TH_DESC", observed=True)
    .agg(
        beneficiarios=("IMP_AYUDA_TOTAL", "size"),
        importe_total=("IMP_AYUDA_TOTAL", "sum"),
        superficie_total=("SUPERFICIE_TOTAL_DESPUES_CAP", "sum"),
    )
    .reset_index()
)

if not terr_stats.empty:
    terr_stats["importe_medio"] = terr_stats["importe_total"] / terr_stats["beneficiarios"]

    fig = px.bar(
        terr_stats.sort_values("beneficiarios"),
        x="beneficiarios", y="TH_DESC", orientation="h",
        color_discrete_sequence=[VERDE_OSCURO],
    )
    etiq_h(fig)
    st.plotly_chart(estilo_h(fig, title="Beneficiarios por territorio"),
                    width="stretch")

    fig = px.bar(
        terr_stats.sort_values("importe_total"),
        x="importe_total", y="TH_DESC", orientation="h",
        color_discrete_sequence=[AZUL_SECUND],
    )
    etiq_h(fig)
    st.plotly_chart(estilo_h(fig, title="Importe total por territorio (€)"),
                    width="stretch")

    tabla_terr = terr_stats.sort_values("importe_total", ascending=False)
    total_row = tabla_terr.agg({
        "beneficiarios": "sum",
        "importe_total": "sum",
        "superficie_total": "sum",
    }).to_frame().T
    total_row["TH_DESC"] = "Total"
    total_row["importe_medio"] = total_row["importe_total"] / total_row["beneficiarios"]
    tabla_terr_ext = pd.concat([tabla_terr, total_row], ignore_index=True)
    mostrar_tabla(pd.DataFrame({
        "Territorio": tabla_terr_ext["TH_DESC"],
        "Beneficiarios": tabla_terr_ext["beneficiarios"].apply(fmt_int),
        "Importe total": tabla_terr_ext["importe_total"].apply(fmt_euros),
        "Importe medio": tabla_terr_ext["importe_medio"].apply(fmt_euros),
        "Superficie total": tabla_terr_ext["superficie_total"].apply(fmt_ha),
    }))

else:
    st.caption("Ninguno de los beneficiarios filtrados tiene territorio asignado.")


# ═══ 2. DISTRIBUCIÓN POR TRAMOS DE AYUDA ═══════════════════════════════════

titulo_bloque("2. Distribución por tramos de ayuda")

tramo_stats = (
    benef.dropna(subset=["TRAMO_AYUDA_8"])
    .groupby("TRAMO_AYUDA_8", observed=True)
    .agg(
        beneficiarios=("IMP_AYUDA_TOTAL", "size"),
        importe_total=("IMP_AYUDA_TOTAL", "sum"),
    )
    .reset_index()
)

g1, g2 = st.columns(2)
with g1:
    fig = px.bar(
        tramo_stats, x="TRAMO_AYUDA_8", y="beneficiarios",
        color_discrete_sequence=[VERDE_OSCURO],
    )
    etiq_v(fig)
    st.plotly_chart(estilo_v(fig, title="Beneficiarios por tramo de ayuda"),
                    width="stretch")
with g2:
    fig = px.bar(
        tramo_stats, x="TRAMO_AYUDA_8", y="importe_total",
        color_discrete_sequence=[AZUL_SECUND],
    )
    etiq_v(fig)
    st.plotly_chart(estilo_v(fig, title="Importe acumulado por tramo (€)"),
                    width="stretch")

imps_ord = benef["IMP_AYUDA_TOTAL"].sort_values(ascending=False).reset_index(drop=True)
total_imp = imps_ord.sum()
n_50 = int((imps_ord.cumsum() < total_imp * 0.5).sum()) + 1 if len(imps_ord) else 0
pct_50 = n_50 / len(imps_ord) * 100 if len(imps_ord) else 0.0

st.markdown(
    tarjeta(
        "Concentración del presupuesto (subconjunto)",
        f"El <b>{fmt_pct(pct_50)}</b> de los beneficiarios filtrados "
        f"({fmt_int(n_50)} titulares) concentra el 50 % del presupuesto del subconjunto.",
        value_size="18px",
    ),
    unsafe_allow_html=True,
)



# ═══ 3. DERECHOS DE AYUDA ABRS ═════════════════════════════════════════════

titulo_bloque("3. Derechos de ayuda ABRS")

try:
    vmr_df = cargar_vmr_derechos()
except Exception:
    vmr_df = pd.DataFrame()

# Defaults
total_derechos = 0.0
media_der = 0.0
mediana_der = 0.0
total_sup_abrs = 0.0
media_sup_abrs = 0.0
total_exceso_ha = 0.0
n_afectados = 0
pct_afectados = 0.0
vm_medio = None
vm_min = None
vm_max = None
regiones_df = pd.DataFrame()


# ── A. Distribución del nº de derechos por beneficiario ──────────────────
titulo_subapartado("A. Distribución del nº de derechos por beneficiario")

if "DERECHOS" in benef.columns:
    der_no_null = benef["DERECHOS"].dropna()
    con_der = der_no_null[der_no_null > 0]
    total_derechos = float(der_no_null.sum())
    media_der = float(con_der.mean()) if len(con_der) else 0.0
    mediana_der = float(con_der.median()) if len(con_der) else 0.0

    k1, k2, k3 = st.columns(3)
    k1.markdown(tarjeta("Total de derechos", fmt_num(total_derechos)),
                unsafe_allow_html=True)
    k2.markdown(tarjeta("Media de derechos por beneficiario", fmt_num(media_der)),
                unsafe_allow_html=True)
    k3.markdown(tarjeta("Mediana de derechos por beneficiario", fmt_num(mediana_der)),
                unsafe_allow_html=True)

    BINS_DER = [0, 5, 15, 30, 50, 100, float("inf")]
    LABELS_DER = ["<5", "5-15", "15-30", "30-50", "50-100", "≥100"]
    benef["TRAMO_DERECHOS"] = pd.cut(
        benef["DERECHOS"], bins=BINS_DER, labels=LABELS_DER, right=False,
    )
    der_tramo = (
        benef.dropna(subset=["TRAMO_DERECHOS"])
        .groupby("TRAMO_DERECHOS", observed=True)
        .agg(beneficiarios=("DERECHOS", "size"), total_tramo=("DERECHOS", "sum"))
        .reset_index()
    )
    if not der_tramo.empty:
        total_n_der = int(der_tramo["beneficiarios"].sum())
        der_tramo["pct"] = der_tramo["beneficiarios"] / total_n_der * 100 if total_n_der else 0.0
        der_tramo["media_tramo"] = der_tramo["total_tramo"] / der_tramo["beneficiarios"]

        fig = px.bar(
            der_tramo, x="TRAMO_DERECHOS", y="beneficiarios",
            color_discrete_sequence=[VERDE_OSCURO],
        )
        etiq_v(fig)
        st.plotly_chart(estilo_v(fig, title="Beneficiarios por tramo de derechos"),
                        width="stretch")

        suma_b = int(der_tramo["beneficiarios"].sum())
        suma_t = float(der_tramo["total_tramo"].sum())
        der_tramo_ext = pd.concat([
            der_tramo.assign(TRAMO_DERECHOS=der_tramo["TRAMO_DERECHOS"].astype(str)),
            pd.DataFrame([{
                "TRAMO_DERECHOS": "Total",
                "beneficiarios": suma_b,
                "total_tramo": suma_t,
                "pct": 100.0,
                "media_tramo": suma_t / suma_b if suma_b else 0.0,
            }]),
        ], ignore_index=True)
        mostrar_tabla(pd.DataFrame({
            "Tramo de derechos": der_tramo_ext["TRAMO_DERECHOS"].astype(str),
            "Beneficiarios": der_tramo_ext["beneficiarios"].apply(fmt_int),
            "% sobre total": der_tramo_ext["pct"].apply(fmt_pct),
            "Total derechos del tramo": der_tramo_ext["total_tramo"].apply(fmt_num),
            "Derechos medios": der_tramo_ext["media_tramo"].apply(fmt_num),
        }))
else:
    st.caption("Columna DERECHOS no disponible.")


# ── B. Derechos por región agronómica ────────────────────────────────────
titulo_subapartado("B. Derechos por región agronómica")

cols_d_r = sorted(
    [c for c in df.columns if c.startswith("D_R_") and c[4:].isdigit()],
    key=lambda c: int(c[4:]),
)

if cols_d_r:
    mapa_regiones: dict[int, dict] = {}
    if not vmr_df.empty:
        for _, fila in vmr_df.iterrows():
            txt = str(fila.get("Región", ""))
            m = re.search(r"\d+", txt)
            if not m:
                continue
            num = int(m.group())
            try:
                valor = float(fila["2024"]) if pd.notna(fila["2024"]) else None
            except (KeyError, ValueError, TypeError):
                valor = None
            mapa_regiones[num] = {
                "orientacion": str(fila.get("Orientación Productiva", "")).strip() or None,
                "valor_2024": valor,
            }

    regiones_data = []
    for col in cols_d_r:
        region_num = int(col[4:])
        # En Consulta el cruce se hace contra el subconjunto filtrado
        serie = benef[col].fillna(0) if col in benef.columns else pd.Series(dtype=float)
        total = float(serie.sum())
        n_b = int((serie > 0).sum())
        if total == 0 and n_b == 0:
            continue
        info_reg = mapa_regiones.get(region_num, {})
        valor_2024 = info_reg.get("valor_2024")
        orientacion = info_reg.get("orientacion")
        valor_total = total * valor_2024 if valor_2024 is not None else None
        regiones_data.append({
            "Región": f"R{region_num:02d}",
            "Orientación Productiva": orientacion or "—",
            "Total Derechos": total,
            "Beneficiarios con derechos": n_b,
            "Valor medio 2024 (€/derecho)": valor_2024,
            "Valor total estimado (€)": valor_total,
        })
    regiones_df = pd.DataFrame(regiones_data).sort_values("Total Derechos", ascending=False)

    if not regiones_df.empty:
        COLORES_ORIENT = {
            "Secano": VERDE_OSCURO,
            "Regadío": AZUL_SECUND,
            "Cultivos Permanentes": "#a05627",
            "Pastos Permanentes": VERDE_MEDIO,
        }
        fig = px.bar(
            regiones_df.sort_values("Total Derechos"),
            x="Total Derechos", y="Región", orientation="h",
            color="Orientación Productiva",
            color_discrete_map=COLORES_ORIENT,
        )
        etiq_h(fig)
        st.plotly_chart(
            estilo_h(fig, title="Total de derechos por región agronómica",
                     height=max(380, 32 * len(regiones_df))),
            width="stretch",
        )

        suma_der = float(regiones_df["Total Derechos"].sum())
        suma_ben = int(regiones_df["Beneficiarios con derechos"].sum())
        suma_val_total = float(regiones_df["Valor total estimado (€)"].sum(skipna=True))
        der_con_valor = float(
            regiones_df.loc[
                regiones_df["Valor medio 2024 (€/derecho)"].notna(), "Total Derechos"
            ].sum()
        )
        vm_ponderado = (
            suma_val_total / der_con_valor if der_con_valor > 0 else None
        )
        regiones_df_ext = pd.concat([regiones_df, pd.DataFrame([{
            "Región": "Total",
            "Orientación Productiva": "—",
            "Total Derechos": suma_der,
            "Beneficiarios con derechos": suma_ben,
            "Valor medio 2024 (€/derecho)": vm_ponderado,
            "Valor total estimado (€)": suma_val_total if suma_val_total else None,
        }])], ignore_index=True)
        mostrar_tabla(pd.DataFrame({
            "Región": regiones_df_ext["Región"],
            "Orientación Productiva": regiones_df_ext["Orientación Productiva"],
            "Total Derechos": regiones_df_ext["Total Derechos"].apply(fmt_int),
            "Beneficiarios con derechos": regiones_df_ext["Beneficiarios con derechos"].apply(fmt_int),
            "Valor medio 2024 (€/derecho)": regiones_df_ext["Valor medio 2024 (€/derecho)"].apply(fmt_euros),
            "Valor total estimado (€)": regiones_df_ext["Valor total estimado (€)"].apply(fmt_euros),
        }))
    else:
        st.caption("Ningún beneficiario filtrado tiene derechos en estas regiones.")
else:
    st.caption("No se han encontrado columnas D_R_XX.")


# ── C. Superficie con derecho ABRS ───────────────────────────────────────
titulo_subapartado("C. Superficie con derecho ABRS")

if "SUP_Det_Ctr_ABRS" in benef.columns:
    sup_no_null = benef["SUP_Det_Ctr_ABRS"].dropna()
    sup_pos = sup_no_null[sup_no_null > 0]
    total_sup_abrs = float(sup_no_null.sum())
    media_sup_abrs = float(sup_pos.mean()) if len(sup_pos) else 0.0

    k1, k2 = st.columns(2)
    k1.markdown(tarjeta("Superficie total con derecho ABRS", fmt_ha(total_sup_abrs)),
                unsafe_allow_html=True)
    k2.markdown(tarjeta("Superficie media por beneficiario", fmt_ha(media_sup_abrs)),
                unsafe_allow_html=True)

    BINS_SUP_ABRS = [0, 5, 25, 100, float("inf")]
    LABELS_SUP_ABRS = ["<5 ha", "5-25 ha", "25-100 ha", ">100 ha"]
    benef["TRAMO_SUP_ABRS"] = pd.cut(
        benef["SUP_Det_Ctr_ABRS"], bins=BINS_SUP_ABRS,
        labels=LABELS_SUP_ABRS, right=False,
    )
    sup_abrs_tramo = (
        benef.dropna(subset=["TRAMO_SUP_ABRS"])
        .groupby("TRAMO_SUP_ABRS", observed=True)
        .agg(
            beneficiarios=("SUP_Det_Ctr_ABRS", "size"),
            total_tramo=("SUP_Det_Ctr_ABRS", "sum"),
        )
        .reset_index()
    )
    if not sup_abrs_tramo.empty:
        sup_abrs_tramo["media_tramo"] = (
            sup_abrs_tramo["total_tramo"] / sup_abrs_tramo["beneficiarios"]
        )
        fig = px.bar(
            sup_abrs_tramo, x="TRAMO_SUP_ABRS", y="beneficiarios",
            color_discrete_sequence=[VERDE_OSCURO],
        )
        etiq_v(fig)
        st.plotly_chart(
            estilo_v(fig, title="Beneficiarios por tramo de superficie ABRS"),
            width="stretch",
        )

        suma_b_abrs = int(sup_abrs_tramo["beneficiarios"].sum())
        suma_t_abrs = float(sup_abrs_tramo["total_tramo"].sum())
        sup_abrs_tramo_ext = pd.concat([
            sup_abrs_tramo.assign(TRAMO_SUP_ABRS=sup_abrs_tramo["TRAMO_SUP_ABRS"].astype(str)),
            pd.DataFrame([{
                "TRAMO_SUP_ABRS": "Total",
                "beneficiarios": suma_b_abrs,
                "total_tramo": suma_t_abrs,
                "media_tramo": suma_t_abrs / suma_b_abrs if suma_b_abrs else 0.0,
            }]),
        ], ignore_index=True)
        mostrar_tabla(pd.DataFrame({
            "Tramo de superficie": sup_abrs_tramo_ext["TRAMO_SUP_ABRS"].astype(str),
            "Beneficiarios": sup_abrs_tramo_ext["beneficiarios"].apply(fmt_int),
            "Superficie total": sup_abrs_tramo_ext["total_tramo"].apply(fmt_ha),
            "Superficie media": sup_abrs_tramo_ext["media_tramo"].apply(fmt_ha),
        }))
else:
    st.caption("Columna SUP_Det_Ctr_ABRS no disponible.")


# ── D. Contraste DERECHOS vs SUP_Det_Ctr_ABRS ────────────────────────────
titulo_subapartado("D. Contraste DERECHOS vs Superficie ABRS — superficie sin derecho")

if {"DERECHOS", "SUP_Det_Ctr_ABRS"}.issubset(benef.columns):
    contraste = benef.dropna(subset=["DERECHOS", "SUP_Det_Ctr_ABRS"]).copy()
    contraste["exceso_ha"] = contraste["SUP_Det_Ctr_ABRS"] - contraste["DERECHOS"]
    contraste["exceso_positivo"] = contraste["exceso_ha"].clip(lower=0)

    total_exceso_ha = float(contraste["exceso_positivo"].sum())
    n_afectados = int((contraste["exceso_ha"] > 0).sum())
    pct_afectados = (
        n_afectados / total_beneficiarios * 100 if total_beneficiarios else 0.0
    )

    st.markdown(
        f'<div style="background-color:#fde8e8; border-left:6px solid #c0392b; '
        f'border-radius:8px; padding:1.25rem 1.5rem; margin-bottom:0.75rem;">'
        f'<div style="font-size:16px; font-weight:700; color:#262730; margin-bottom:0.9rem;">'
        f'Superficie declarada SIN derecho ABRS activable</div>'
        f'<div style="display:flex; gap:2rem; flex-wrap:wrap;">'
        f'<div style="flex:1; min-width:220px;">'
        f'<div style="font-size:32px; font-weight:700; color:#c0392b; line-height:1.1;">'
        f'{fmt_ha(total_exceso_ha)}</div>'
        f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
        f'superficie total sin derecho activable</div></div>'
        f'<div style="flex:1; min-width:220px;">'
        f'<div style="font-size:32px; font-weight:700; color:#c0392b; line-height:1.1;">'
        f'{fmt_int(n_afectados)}</div>'
        f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
        f'beneficiarios afectados (en el subconjunto)</div></div>'
        f'<div style="flex:1; min-width:220px;">'
        f'<div style="font-size:32px; font-weight:700; color:#c0392b; line-height:1.1;">'
        f'{fmt_pct(pct_afectados)}</div>'
        f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
        f'sobre el total de beneficiarios filtrados</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    BINS_EXC = [-float("inf"), 0, 5, 25, 100, float("inf")]
    LABELS_EXC = ["0 ha", "0-5 ha", "5-25 ha", "25-100 ha", ">100 ha"]
    contraste["TRAMO_EXCESO"] = pd.cut(
        contraste["exceso_ha"], bins=BINS_EXC, labels=LABELS_EXC, right=True,
    )
    exc_tramo = (
        contraste.dropna(subset=["TRAMO_EXCESO"])
        .groupby("TRAMO_EXCESO", observed=True)
        .agg(
            beneficiarios=("exceso_ha", "size"),
            ha_sin_derecho=("exceso_positivo", "sum"),
        )
        .reset_index()
    )
    if not exc_tramo.empty:
        exc_tramo["pct_ha"] = (
            exc_tramo["ha_sin_derecho"] / total_exceso_ha * 100
            if total_exceso_ha > 0 else 0.0
        )

        fig = px.bar(
            exc_tramo, x="TRAMO_EXCESO", y="beneficiarios",
            color_discrete_sequence=["#c0392b"],
        )
        etiq_v(fig)
        st.plotly_chart(
            estilo_v(fig, title="Beneficiarios por tramo de exceso (ha sin derecho)"),
            width="stretch",
        )

        suma_b_exc = int(exc_tramo["beneficiarios"].sum())
        suma_ha_exc = float(exc_tramo["ha_sin_derecho"].sum())
        exc_tramo_ext = pd.concat([
            exc_tramo.assign(TRAMO_EXCESO=exc_tramo["TRAMO_EXCESO"].astype(str)),
            pd.DataFrame([{
                "TRAMO_EXCESO": "Total",
                "beneficiarios": suma_b_exc,
                "ha_sin_derecho": suma_ha_exc,
                "pct_ha": 100.0 if suma_ha_exc > 0 else 0.0,
            }]),
        ], ignore_index=True)
        mostrar_tabla(pd.DataFrame({
            "Tramo de exceso": exc_tramo_ext["TRAMO_EXCESO"].astype(str),
            "Beneficiarios": exc_tramo_ext["beneficiarios"].apply(fmt_int),
            "Ha totales sin derecho": exc_tramo_ext["ha_sin_derecho"].apply(fmt_ha),
            "% sobre total ha sin derecho": exc_tramo_ext["pct_ha"].apply(fmt_pct),
        }))

    st.warning(
        "La superficie en exceso (declarada por encima del nº de derechos del "
        "titular) **no activa ningún derecho de pago básico (ABRS)** y, por "
        "tanto, no genera cobro bajo ese régimen."
    )
else:
    st.caption("Faltan columnas DERECHOS o SUP_Det_Ctr_ABRS.")


# ── E. Valor medio de los derechos por beneficiario ──────────────────────
titulo_subapartado("E. Valor medio de los derechos por beneficiario")

if {"IMP_AYUDA_ABRS", "DERECHOS"}.issubset(benef.columns):
    mask_vm = (benef["IMP_AYUDA_ABRS"] > 0) & (benef["DERECHOS"] > 0)
    con_valor = benef[mask_vm].copy()
    if len(con_valor):
        con_valor["valor_medio_derecho"] = (
            con_valor["IMP_AYUDA_ABRS"] / con_valor["DERECHOS"]
        )
        vm_medio = float(con_valor["valor_medio_derecho"].mean())
        vm_min = float(con_valor["valor_medio_derecho"].min())
        vm_max = float(con_valor["valor_medio_derecho"].max())

        k1, k2, k3 = st.columns(3)
        k1.markdown(tarjeta("Valor medio del derecho", fmt_euros(vm_medio)),
                    unsafe_allow_html=True)
        k2.markdown(tarjeta("Valor mínimo observado", fmt_euros(vm_min)),
                    unsafe_allow_html=True)
        k3.markdown(tarjeta("Valor máximo observado", fmt_euros(vm_max)),
                    unsafe_allow_html=True)

        BINS_VM = [-float("inf"), 50, 100, 200, 400, float("inf")]
        LABELS_VM = ["<50 €", "50-100 €", "100-200 €", "200-400 €", ">400 €"]
        con_valor["TRAMO_VM"] = pd.cut(
            con_valor["valor_medio_derecho"],
            bins=BINS_VM, labels=LABELS_VM, right=False,
        )
        vm_tramo = (
            con_valor.dropna(subset=["TRAMO_VM"])
            .groupby("TRAMO_VM", observed=True).size()
            .reset_index(name="beneficiarios")
        )
        fig = px.bar(
            vm_tramo, x="TRAMO_VM", y="beneficiarios",
            color_discrete_sequence=[VERDE_OSCURO],
        )
        etiq_v(fig)
        st.plotly_chart(
            estilo_v(fig, title="Beneficiarios por tramo de valor medio del derecho"),
            width="stretch",
        )

        if not vmr_df.empty and "2024" in vmr_df.columns:
            st.markdown("**Valor medio 2024 por región agronómica (referencia)**")
            vmr_ref = vmr_df.sort_values("2024", ascending=False).copy()
            mostrar_tabla(pd.DataFrame({
                "Región": vmr_ref["Región"].astype(str),
                "Orientación Productiva": vmr_ref["Orientación Productiva"].astype(str),
                "Valor medio 2024 (€/derecho)": vmr_ref["2024"].apply(fmt_euros),
            }))
    else:
        st.caption("Ningún beneficiario del subconjunto tiene IMP_AYUDA_ABRS y DERECHOS > 0 simultáneamente.")
else:
    st.caption("Faltan columnas IMP_AYUDA_ABRS o DERECHOS.")




# ═══ 4. TIPOS DE AYUDA ═════════════════════════════════════════════════════

titulo_bloque("4. Tipos de ayuda")

cols_imp = [c for c in df.columns if c.startswith("IMP_AYUDA_") and c != "IMP_AYUDA_TOTAL"]
filas_ay = []
for col in cols_imp:
    if col not in benef.columns:
        continue
    serie = benef[col]
    n = int(serie.notna().sum())
    if n == 0:
        continue
    filas_ay.append({
        "Tipo de ayuda": col.replace("IMP_AYUDA_", ""),
        "Beneficiarios": n,
        "Importe total": float(serie.sum()),
        "Importe medio": float(serie.mean()),
    })
ayudas_df = pd.DataFrame(filas_ay).sort_values("Importe total", ascending=False)


def _grupo_ayuda(tipo: str) -> str:
    if tipo == "ABRS":
        return "ABRS"
    if tipo == "REDISTR":
        return "Redistributiva"
    if tipo == "CJOVEN":
        return "Complemento Jóvenes"
    if tipo.startswith("EERR"):
        return "Ecorregímenes"
    if tipo.startswith("ASOC"):
        return "Asociadas"
    return "Otros"


if not ayudas_df.empty:
    ORDEN_GRUPOS_AYUDA = [
        "ABRS", "Redistributiva", "Complemento Jóvenes",
        "Ecorregímenes", "Asociadas", "Otros",
    ]
    ayudas_grupos = (
        ayudas_df.assign(Grupo=ayudas_df["Tipo de ayuda"].map(_grupo_ayuda))
        .groupby("Grupo", as_index=False)["Importe total"].sum()
    )
    ayudas_grupos["Grupo"] = pd.Categorical(
        ayudas_grupos["Grupo"], categories=ORDEN_GRUPOS_AYUDA, ordered=True
    )
    ayudas_grupos = ayudas_grupos.sort_values("Importe total")

    fig = px.bar(
        ayudas_grupos, x="Importe total", y="Grupo", orientation="h",
        color_discrete_sequence=[VERDE_OSCURO],
    )
    etiq_h(fig)
    st.plotly_chart(
        estilo_h(fig, title="Importe total por grupo de ayuda (€)"),
        width="stretch",
    )

    suma_b_ay = int(ayudas_df["Beneficiarios"].sum())
    suma_imp_ay = float(ayudas_df["Importe total"].sum())
    ayudas_df_ext = pd.concat([ayudas_df, pd.DataFrame([{
        "Tipo de ayuda": "Total",
        "Beneficiarios": suma_b_ay,
        "Importe total": suma_imp_ay,
        "Importe medio": suma_imp_ay / suma_b_ay if suma_b_ay else 0.0,
    }])], ignore_index=True)
    mostrar_tabla(pd.DataFrame({
        "Tipo de ayuda": ayudas_df_ext["Tipo de ayuda"],
        "Beneficiarios": ayudas_df_ext["Beneficiarios"].apply(fmt_int),
        "Importe total": ayudas_df_ext["Importe total"].apply(fmt_euros),
        "Importe medio": ayudas_df_ext["Importe medio"].apply(fmt_euros),
    }), height=min(640, 38 * (len(ayudas_df_ext) + 1)))
else:
    st.caption("No hay registros de ayudas en el subconjunto filtrado.")



# ═══ 5. PERFIL DE LOS BENEFICIARIOS ════════════════════════════════════════

titulo_bloque("5. Perfil de los beneficiarios")

# Fila 1: edad + género
c_a, c_c = st.columns(2)
with c_a:
    edad_stats = (
        benef.dropna(subset=["TRAMO_EDAD"])
        .groupby("TRAMO_EDAD", observed=True).size()
        .reset_index(name="beneficiarios")
    )
    if not edad_stats.empty:
        fig = px.bar(
            edad_stats, x="TRAMO_EDAD", y="beneficiarios",
            color_discrete_sequence=[VERDE_OSCURO],
        )
        etiq_v(fig)
        st.plotly_chart(estilo_v(fig, title="Por tramo de edad"),
                        width="stretch")
with c_c:
    if "GENERO" in benef.columns:
        gen_stats = (
            benef.dropna(subset=["GENERO"])
            .groupby("GENERO").size().reset_index(name="beneficiarios")
        )
        if not gen_stats.empty:
            fig = px.bar(
                gen_stats, x="GENERO", y="beneficiarios",
                color_discrete_sequence=[VERDE_OSCURO],
            )
            etiq_v(fig)
            st.plotly_chart(estilo_v(fig, title="Por género"),
                            width="stretch")
    else:
        st.caption("Columna GENERO no disponible.")

# Fila 2: tabla cruzada
titulo_subapartado("Distribución cruzada: género × tramo de edad")
if {"GENERO", "TRAMO_EDAD"}.issubset(benef.columns):
    cruce = pd.crosstab(
        benef["GENERO"], benef["TRAMO_EDAD"], dropna=True, margins=True,
        margins_name="Total",
    )
    if not cruce.empty:
        cruce_disp = cruce.copy().astype("float").map(fmt_int)
        cruce_disp.insert(0, "Género", cruce_disp.index)
        mostrar_tabla(cruce_disp.reset_index(drop=True))
else:
    st.caption("Faltan columnas GENERO o TRAMO_EDAD.")

# Fila 3: formación + donut condición jurídica
c_f, c_b = st.columns(2)
with c_f:
    if "FORMACION_AGRARIA" in benef.columns:
        form_stats = (
            benef.dropna(subset=["FORMACION_AGRARIA"])
            .groupby("FORMACION_AGRARIA").size()
            .reset_index(name="beneficiarios")
            .sort_values("beneficiarios", ascending=True)
        )
        if not form_stats.empty:
            fig = px.bar(
                form_stats, x="beneficiarios", y="FORMACION_AGRARIA",
                orientation="h", color_discrete_sequence=[VERDE_OSCURO],
            )
            etiq_h(fig)
            st.plotly_chart(estilo_h(fig, title="Formación agraria"),
                            width="stretch")
    else:
        st.caption("Columna FORMACION_AGRARIA no disponible.")
with c_b:
    cond = (
        benef.assign(
            etiqueta=lambda d: d["ES_PERSONA_FISICA"].map(
                {True: "Persona física", False: "Entidad jurídica"}
            )
        )
        .groupby("etiqueta").size().reset_index(name="beneficiarios")
    )
    if not cond.empty:
        fig = px.pie(
            cond, values="beneficiarios", names="etiqueta",
            color_discrete_sequence=[VERDE_OSCURO, AZUL_SECUND], hole=0.55,
        )
        fig.update_traces(textinfo="percent+label",
                          textfont=dict(size=14, color=TEXTO))
        st.plotly_chart(estilo_pie(fig, title="Condición jurídica"),
                        width="stretch")

# Fila 4: dedicación
if "PORCENT_DEDICADO_AGRIC" in benef.columns:
    ORDEN_DED = [
        "100%", "Entre 75 -<100%", "Entre 50 -<75%", "50%",
        "Entre 25 -<50%", "Entre 0 -<25%",
    ]
    ded_stats = (
        benef.dropna(subset=["PORCENT_DEDICADO_AGRIC"])
        .groupby("PORCENT_DEDICADO_AGRIC").size()
        .reset_index(name="beneficiarios")
    )
    if not ded_stats.empty:
        ded_stats["PORCENT_DEDICADO_AGRIC"] = pd.Categorical(
            ded_stats["PORCENT_DEDICADO_AGRIC"], categories=ORDEN_DED, ordered=True,
        )
        ded_stats = ded_stats.sort_values("PORCENT_DEDICADO_AGRIC")
        fig = px.bar(
            ded_stats, x="PORCENT_DEDICADO_AGRIC", y="beneficiarios",
            color_discrete_sequence=[VERDE_OSCURO],
        )
        etiq_v(fig)
        st.plotly_chart(estilo_v(fig, title="Dedicación a la actividad agraria"),
                        width="stretch")

# Fila 5: peso ingresos agrarios
col_rel = "RELACION_INGRESOS_AGRARIOS_TOTAL"
if col_rel in benef.columns:
    peso_por_tramo = (
        benef.dropna(subset=[col_rel, "TRAMO_AYUDA_8"])
        .groupby("TRAMO_AYUDA_8", observed=True)[col_rel]
        .mean()
        .reset_index()
    )
    if not peso_por_tramo.empty:
        fig = px.bar(
            peso_por_tramo, x="TRAMO_AYUDA_8", y=col_rel,
            color_discrete_sequence=[AZUL_SECUND],
        )
        etiq_v(fig)
        st.plotly_chart(
            estilo_v(fig,
                     title="Peso medio de los ingresos agrarios sobre el total, por tramo (%)"),
            width="stretch",
        )

# Fila 6: tarjeta ingresos > 15k
col_15k = "INGRESOS_AGRARIOS_>15000"
n_si = 0
pct_si_total = 0.0
pct_si_marcados = 0.0
marcados = 0
if col_15k in benef.columns:
    marcados = int(benef[col_15k].notna().sum())
    n_si = int((benef[col_15k] == "SI").sum())
    pct_si_total = n_si / total_beneficiarios * 100 if total_beneficiarios else 0.0
    pct_si_marcados = n_si / marcados * 100 if marcados else 0.0
    st.markdown(
        f'<div style="background-color:{VERDE_CLARO}; border-left:6px solid {VERDE_OSCURO}; '
        f'border-radius:8px; padding:1.25rem 1.5rem; margin-bottom:0.75rem;">'
        f'<div style="font-size:16px; font-weight:700; color:#262730; margin-bottom:0.9rem;">'
        f'Ingresos agrarios superiores a 15.000 €</div>'
        f'<div style="display:flex; gap:2rem; flex-wrap:wrap;">'
        f'<div style="flex:1; min-width:220px;">'
        f'<div style="font-size:32px; font-weight:700; color:{VERDE_OSCURO}; line-height:1.1;">'
        f'{fmt_int(n_si)}</div>'
        f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
        f'titulares con ingresos > 15.000 €</div></div>'
        f'<div style="flex:1; min-width:220px;">'
        f'<div style="font-size:32px; font-weight:700; color:{VERDE_OSCURO}; line-height:1.1;">'
        f'{fmt_pct(pct_si_total)}</div>'
        f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
        f'sobre el total de beneficiarios filtrados ({fmt_int(total_beneficiarios)})</div></div>'
        f'<div style="flex:1; min-width:220px;">'
        f'<div style="font-size:32px; font-weight:700; color:{VERDE_OSCURO}; line-height:1.1;">'
        f'{fmt_pct(pct_si_marcados)}</div>'
        f'<div style="font-size:13px; color:#555; margin-top:0.3rem;">'
        f'sobre los {fmt_int(marcados)} con el dato declarado</div></div>'
        f'</div></div>',
        unsafe_allow_html=True,
    )



# ═══ 6. DISTRIBUCIÓN POR SUPERFICIE Y CULTIVOS ═════════════════════════════

titulo_bloque("6. Distribución por superficie y cultivos")

sup_stats = (
    benef.dropna(subset=["TRAMO_SUPERFICIE"])
    .groupby("TRAMO_SUPERFICIE", observed=True)
    .agg(
        beneficiarios=("IMP_AYUDA_TOTAL", "size"),
        sup_media=("SUPERFICIE_TOTAL_DESPUES_CAP", "mean"),
        imp_medio=("IMP_AYUDA_TOTAL", "mean"),
    )
    .reset_index()
)

g_a, g_b = st.columns(2)
with g_a:
    if not sup_stats.empty:
        fig = px.bar(
            sup_stats, x="TRAMO_SUPERFICIE", y="beneficiarios",
            color_discrete_sequence=[VERDE_OSCURO],
        )
        etiq_v(fig)
        st.plotly_chart(estilo_v(fig, title="Beneficiarios por tramo de superficie"),
                        width="stretch")
with g_b:
    if not sup_stats.empty:
        fig = px.scatter(
            sup_stats, x="sup_media", y="imp_medio",
            size="beneficiarios", color="TRAMO_SUPERFICIE",
            color_discrete_sequence=[VERDE_OSCURO, VERDE_MEDIO, AZUL_SECUND, "#1b4332"],
            size_max=55,
        )
        estilo_v(fig, title="Superficie media vs importe medio por tramo")
        fig.update_layout(
            margin=dict(l=60, r=120, t=80, b=60),
            xaxis_title="Superficie media (ha)",
            yaxis_title="Importe medio (€)",
            legend_title_text="Tramo",
        )
        st.plotly_chart(fig, width="stretch")


# Top 15 cultivos del subconjunto
COLS_NO_CULTIVO = {
    "CAMPAÑA", "TH", "EXPEDIENTE", "CIFNIFSOL", "TITULAR", "INTEGRIDAD_REGISTRO",
    "FNACIMIENTO", "GENERO", "PORCENT_DEDICADO_AGRIC", "FORMACION_AGRARIA",
    "AÑO_EMPIEZA_GERENTE", "CONDI_JURIDICA", "MOTIVO_EXENTO",
    "RELACION_INGRESOS_AGRARIOS_TOTAL", "INGRESOS_AGRARIOS_>15000",
    "DERECHOS", "SUPERFICIE_TOTAL_DESPUES_CAP",
    "EDAD", "TRAMO_EDAD", "TH_DESC", "IMP_AYUDA_TOTAL", "TRAMO_AYUDA",
    "TRAMO_AYUDA_8", "TRAMO_SUPERFICIE", "TRAMO_DERECHOS", "TRAMO_SUP_ABRS",
    "N_AYUDAS_DISTINTAS", "RECIBE_CJOVEN", "ES_PERSONA_FISICA",
}
PREFIJOS_NO_CULTIVO = ("D_R_", "SUP_Det_Ctr_", "Número_APS_", "IMP_AYUDA_")

cols_cultivo = [
    c for c in df.columns
    if c not in COLS_NO_CULTIVO
    and not any(c.startswith(p) for p in PREFIJOS_NO_CULTIVO)
    and pd.api.types.is_numeric_dtype(df[c])
]

cultivos = []
for col in cols_cultivo:
    if col not in benef.columns:
        continue
    serie = benef[col]
    superficie = float(serie.sum())
    n = int(serie.notna().sum())
    if n == 0:
        continue
    cultivos.append({
        "Cultivo": col.replace("_", " "),
        "Superficie total": superficie,
        "Beneficiarios": n,
        "Superficie media": superficie / n if n else 0.0,
    })
cultivos_df = pd.DataFrame(cultivos).sort_values("Superficie total", ascending=False)
top15 = cultivos_df.head(15)

if not top15.empty:
    titulo_subapartado("Top 15 cultivos por superficie declarada")

    fig = px.bar(
        top15.sort_values("Superficie total"),
        x="Superficie total", y="Cultivo", orientation="h",
        color_discrete_sequence=[VERDE_OSCURO],
    )
    etiq_h(fig)
    st.plotly_chart(estilo_h(fig, title="Superficie total por cultivo (ha)",
                             height=560),
                    width="stretch")

    fig = px.bar(
        top15.sort_values("Beneficiarios"),
        x="Beneficiarios", y="Cultivo", orientation="h",
        color_discrete_sequence=[AZUL_SECUND],
    )
    etiq_h(fig)
    st.plotly_chart(estilo_h(fig, title="Nº de beneficiarios por cultivo",
                             height=560),
                    width="stretch")

    titulo_subapartado(f"Tabla completa de cultivos ({len(cultivos_df)})")
    suma_sup_cult = float(cultivos_df["Superficie total"].sum())
    suma_b_cult = int(cultivos_df["Beneficiarios"].sum())
    cultivos_df_ext = pd.concat([cultivos_df, pd.DataFrame([{
        "Cultivo": "Total",
        "Superficie total": suma_sup_cult,
        "Beneficiarios": suma_b_cult,
        "Superficie media": suma_sup_cult / suma_b_cult if suma_b_cult else 0.0,
    }])], ignore_index=True)
    mostrar_tabla(pd.DataFrame({
        "Cultivo": cultivos_df_ext["Cultivo"],
        "Superficie total": cultivos_df_ext["Superficie total"].apply(fmt_ha),
        "Beneficiarios": cultivos_df_ext["Beneficiarios"].apply(fmt_int),
        "Superficie media por beneficiario": cultivos_df_ext["Superficie media"].apply(fmt_ha),
    }), height=400)



# ─── Tabla detalle anonimizada + exportación ──────────────────────────────

st.divider()
titulo_bloque("Tabla detalle del subconjunto filtrado")

cols_detalle_origen = [
    "CIFNIFSOL", "TH_DESC", "TRAMO_EDAD", "GENERO", "CONDI_JURIDICA",
    "TRAMO_AYUDA_8", "IMP_AYUDA_TOTAL", "SUPERFICIE_TOTAL_DESPUES_CAP", "DERECHOS",
]
cols_detalle_origen = [c for c in cols_detalle_origen if c in benef.columns]

detalle = benef[cols_detalle_origen].copy().reset_index(drop=True)
ids = []
for i, nif in enumerate(detalle.get("CIFNIFSOL", pd.Series(["XXXX"] * len(detalle)))):
    prefijo = (
        str(nif)[:4].upper() if pd.notna(nif) and str(nif).strip() not in {"", "nan"}
        else "XXXX"
    )
    ids.append(f"{prefijo}-{i + 1:04d}")

detalle["ID"] = ids
if "CIFNIFSOL" in detalle.columns:
    detalle = detalle.drop(columns=["CIFNIFSOL"])

orden_cols = ["ID"] + [c for c in cols_detalle_origen if c != "CIFNIFSOL"]
detalle = detalle[orden_cols]
detalle.columns = ["ID", "Territorio", "Tramo edad", "Género", "Condición jurídica",
                   "Tramo de ayuda", "Importe total", "Superficie", "Derechos"][: len(orden_cols)]

st.caption(
    f"Tabla detalle del subconjunto filtrado: {fmt_int(len(detalle))} filas totales "
    f"(mostrando hasta 500)."
)

# Formato para la vista en pantalla
detalle_vista = detalle.head(500).copy()
for col in detalle_vista.columns:
    if col == "Importe total":
        detalle_vista[col] = detalle_vista[col].apply(fmt_euros)
    elif col == "Superficie":
        detalle_vista[col] = detalle_vista[col].apply(fmt_ha)
    elif col == "Derechos":
        detalle_vista[col] = detalle_vista[col].apply(fmt_num)
    else:
        detalle_vista[col] = detalle_vista[col].astype(str)

mostrar_tabla(detalle_vista, height=400)

csv_bytes = detalle.to_csv(index=False, sep=";", decimal=",").encode("utf-8-sig")
st.download_button(
    "Exportar a CSV",
    data=csv_bytes,
    file_name=f"consulta_pac_{total_filtrado}_beneficiarios.csv",
    mime="text/csv",
    type="primary",
)


st.divider()
st.markdown(
    "Aplica nuevos filtros o pulsa **Limpiar filtros** para volver a la "
    "vista completa del padrón."
)
