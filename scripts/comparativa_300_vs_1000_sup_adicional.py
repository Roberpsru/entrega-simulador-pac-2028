"""ENTREGABLE — >300  vs  >1000 + superficie adicional (las CUATRO categorías).

Escenario A = ">300": umbral 300 sin Filtro B. Es el escenario base del motor nuevo
(superficie activable = min(derechos, ABRS)). Se VALIDA contra los anclajes de la app.

Escenario B = ">1000 + superficie adicional": primero se aplica el umbral 1000; sobre
los titulares SUPERVIVIENTES (>1000) se activan las cuatro palancas del Filtro B:
  · Cultivos externos (viñedo y txakoli, frutales y frutos secos, hortícolas): el
    máximo incorporable por categoría = potencial SIGPAC − superficie declarada se
    calcula sobre la BASE AMPLIA (ayuda > 0), igual que comparativa_sup_adicional.py
    (total ≈6.298,72 ha); el reparto territorial es real por titular pero usando solo
    la huella de cultivo de los supervivientes >1000 (proporciones del >1000, total fijo).
  · ABRS sin derecho REACTIVADA AL 100 %: ha_abrs_sin_derecho_reactivada = exceso
    completo Σ max(ABRS − DERECHOS, 0) calculado SOLO sobre los titulares >1000 (es
    exceso REAL de los titulares del escenario).

REUTILIZA el motor real src.simulation.simular_superficie (SUP_ACTIVABLE y el parámetro
ha_abrs_sin_derecho_reactivada) y las funciones validadas de entregables_300_500.py.

Uso:
  python scripts/comparativa_300_vs_1000_sup_adicional.py            -> CHECKPOINT (no escribe)
  python scripts/comparativa_300_vs_1000_sup_adicional.py --generar  -> genera el Excel
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

from entregables_300_500 import cargar, correr_simulador, validar, mostrar  # noqa: E402
from src.simulation import simular_superficie                              # noqa: E402

OUT = RAIZ / "comparativa_300_vs_1000_superficie_adicional.xlsx"
UMBRAL_A = 300
UMBRAL_B = 1000
TERRS = ["Araba", "Gipuzkoa", "Bizkaia"]
ORDEN = ["Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]
CAT_SIGPAC = {
    "Viñedo y Txakoli": "VIÑEDO Y TXAKOLI",
    "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
    "Hortícolas": "HORTICOLA",
}


def _eu(v):
    return (f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if isinstance(v, (int, float)) else str(v))


def escenario_b(df: pd.DataFrame) -> dict:
    """Umbral 1000 + Filtro B (4 palancas) sobre los supervivientes >1000."""
    benef = df[df["IMP_AYUDA_TOTAL"] > 0].copy()
    presupuesto = float(benef["IMP_AYUDA_TOTAL"].sum())           # constante (toda la base)
    survivors = benef[benef["IMP_AYUDA_TOTAL"] > UMBRAL_B].copy()  # umbral aplicado PRIMERO

    sup_max = pd.read_excel(RAIZ / "data" / "SUP_MAX_SIGPAC.xlsx", sheet_name="Superficie")
    cult = pd.read_excel(RAIZ / "data" / "Tabla_Cultivos_PAC.xlsx", sheet_name="Sup")

    # ── Externas (interpretación B): máximo incorporable por categoría sobre la BASE
    # AMPLIA (ayuda > 0), igual que comparativa_sup_adicional.py (total fijo ≈6.298,72);
    # reparto territorial = real por titular pero con la huella de cultivo de los
    # supervivientes >1000 (proporciones del >1000, total invariante). ──
    ha_cat_terr, maxes, n_explot_cat = {}, {}, {}
    for tipo, col in CAT_SIGPAC.items():
        sig = float(sup_max[col].sum())
        cols_ok = [c for c in cult[cult[col] == "SI"]["Unnamed: 0"].tolist()
                   if c in benef.columns]
        decl_full = float(benef[cols_ok].sum().sum()) if cols_ok else 0.0   # base amplia >0
        maxes[tipo] = max(0.0, sig - decl_full)
        decl_surv = float(survivors[cols_ok].sum().sum()) if cols_ok else 0.0  # huella >1000
        real_th = (survivors.assign(_s=survivors[cols_ok].fillna(0).sum(axis=1))
                   .groupby("TH_DESC")["_s"].sum()) if cols_ok else pd.Series(dtype=float)
        ha_cat_terr[tipo] = {
            t: (maxes[tipo] * float(real_th.get(t, 0.0)) / decl_surv if decl_surv > 0 else 0.0)
            for t in TERRS
        }
        # superficie media para estimar explotaciones teóricas nuevas: base amplia >0
        spt = benef[cols_ok].fillna(0).sum(axis=1) if cols_ok else pd.Series(dtype=float)
        n_act = int((spt > 0).sum()) if len(spt) else 0
        sup_media = (float(spt.sum()) / n_act) if n_act else 0.0
        n_explot_cat[tipo] = (maxes[tipo] / sup_media) if sup_media else 0.0

    ha_terr = {t: sum(ha_cat_terr[tipo][t] for tipo in CAT_SIGPAC) for t in TERRS}
    total_externas = sum(maxes.values())

    # ── ABRS sin derecho: exceso completo de los supervivientes >1000 (reactivación 100 %) ──
    exc_series = (survivors["SUP_Det_Ctr_ABRS"].fillna(0)
                  - survivors["DERECHOS"].fillna(0)).clip(lower=0)
    exceso_total = float(exc_series.sum())
    exc_g = survivors.assign(_e=exc_series).groupby("TH_DESC")["_e"].sum()
    exc_por_terr = {t: float(exc_g.get(t, 0.0)) for t in TERRS}

    # ── Motor: externas al denominador + reactivación total del exceso ──
    df_act, vh, _ = simular_superficie(
        survivors, total_externas, presupuesto_total=presupuesto,
        ha_abrs_sin_derecho_reactivada=exceso_total,
    )

    filas, sup_act_terr = {}, {}
    for terr in TERRS:
        act_t = df_act[(df_act["TH_DESC"] == terr) & (df_act["IMP_SIMULADO"] > 0)]
        n_b = int(len(act_t))
        sup_act = float(act_t["SUP_ACTIVABLE"].fillna(0).sum())
        sup_act_terr[terr] = sup_act
        filas[terr] = dict(
            benef_b=n_b,
            sup_b=sup_act + ha_terr[terr],
            medio_b=float(act_t["IMP_SIMULADO"].mean()) if n_b else 0.0,
        )
    act_eus = df_act[df_act["IMP_SIMULADO"] > 0]
    n_eus = int(len(act_eus))
    filas["Euskadi"] = dict(
        benef_b=sum(filas[t]["benef_b"] for t in TERRS),
        sup_b=sum(filas[t]["sup_b"] for t in TERRS),
        medio_b=float(act_eus["IMP_SIMULADO"].mean()) if n_eus else 0.0,
    )

    n_exact_umbral = int((benef["IMP_AYUDA_TOTAL"] == UMBRAL_B).sum())
    return dict(
        filas=filas, ha_cat_terr=ha_cat_terr, ha_terr=ha_terr, total_externas=total_externas,
        exc_por_terr=exc_por_terr, exceso_total=exceso_total, vh=vh,
        n_explot_cat=n_explot_cat, presupuesto=presupuesto,
        n_survivors=int(len(survivors)), n_exact_umbral=n_exact_umbral,
    )


def tabla_reparto(b: dict) -> pd.DataFrame:
    rep = []
    for tipo in CAT_SIGPAC:
        fila = {"Categoría": tipo, "Método": "Dato real por titular"}
        for t in TERRS:
            fila[t] = round(b["ha_cat_terr"][tipo][t], 2)
        fila["Euskadi"] = round(sum(b["ha_cat_terr"][tipo][t] for t in TERRS), 2)
        rep.append(fila)
    fila_abrs = {"Categoría": "Superficie ABRS sin derecho (reactivada)",
                 "Método": "Exceso titular a titular"}
    for t in TERRS:
        fila_abrs[t] = round(b["exc_por_terr"][t], 2)
    fila_abrs["Euskadi"] = round(sum(b["exc_por_terr"][t] for t in TERRS), 2)
    rep.append(fila_abrs)
    total = {"Categoría": "TOTAL superficie adicional", "Método": "—"}
    for t in TERRS:
        total[t] = round(b["ha_terr"][t] + b["exc_por_terr"][t], 2)
    total["Euskadi"] = round(sum(total[t] for t in TERRS), 2)
    rep.append(total)
    return pd.DataFrame(rep)[["Categoría", "Método", "Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]]


def checkpoint(b: dict):
    print("\n" + "=" * 72)
    print(f"CHECKPOINT B — titulares >1000 (supervivientes: {b['n_survivors']})")
    print("=" * 72)
    print(f"  Titulares con ayuda exactamente = {UMBRAL_B} €: {b['n_exact_umbral']} "
          f"(0 ⇒ '>1000' estricto equivale a la convención de la app)")

    # Externas por categoría y territorio
    rep_ext = []
    for tipo in CAT_SIGPAC:
        fila = {"Categoría": tipo}
        for t in TERRS:
            fila[t] = round(b["ha_cat_terr"][tipo][t], 2)
        fila["Euskadi"] = round(sum(b["ha_cat_terr"][tipo][t] for t in TERRS), 2)
        rep_ext.append(fila)
    rep_ext.append({"Categoría": "TOTAL externas",
                    **{t: round(b["ha_terr"][t], 2) for t in TERRS},
                    "Euskadi": round(b["total_externas"], 2)})
    mostrar("Externas (cultivos) a incorporar — dato real por titular, base >1000",
            pd.DataFrame(rep_ext)[["Categoría", "Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]])

    # ABRS sin derecho exceso por territorio
    abrs = [{"Concepto": "ABRS sin derecho (exceso, base >1000)",
             **{t: round(b["exc_por_terr"][t], 2) for t in TERRS},
             "Euskadi": round(b["exceso_total"], 2)}]
    mostrar("ABRS sin derecho a reactivar (100 %) — exceso titular a titular, base >1000",
            pd.DataFrame(abrs)[["Concepto", "Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]])

    # Total superficie adicional por territorio
    tot = [{"Concepto": "TOTAL superficie adicional en B",
            **{t: round(b["ha_terr"][t] + b["exc_por_terr"][t], 2) for t in TERRS},
            "Euskadi": round(b["total_externas"] + b["exceso_total"], 2)}]
    mostrar("Total de superficie adicional incorporada en B por territorio",
            pd.DataFrame(tot)[["Concepto", "Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]])
    print("\n  >>> CHECKPOINT: revisa estas cifras. Ejecuta con --generar para crear el Excel.")


def cuadro(sim_a: pd.DataFrame, b: dict, col_a: str, key_b: str) -> pd.DataFrame:
    a = sim_a.set_index("Territorio")[col_a]
    return pd.DataFrame({
        "Territorio": ORDEN,
        ">300": [round(float(a[t]), 2) for t in ORDEN],
        ">1000 + sup. adicional": [round(float(b["filas"][t][key_b]), 2) for t in ORDEN],
        "Diferencia (A − B)": [round(float(a[t]) - float(b["filas"][t][key_b]), 2) for t in ORDEN],
    })


def main():
    generar = "--generar" in sys.argv
    df = cargar()

    # ── Escenario A (>300) + validación obligatoria ──
    sim_a = correr_simulador(df, UMBRAL_A)
    if not validar(sim_a):
        print("\n*** PARADA: A no coincide con los anclajes del motor nuevo. ***")
        sys.exit(1)

    # ── Escenario B (>1000 + Filtro B) ──
    b = escenario_b(df)

    checkpoint(b)
    if not generar:
        print("\n[CHECKPOINT] No se ha escrito ningún Excel. Esperando visto bueno.")
        return

    # ── Cuadros ──
    c1 = cuadro(sim_a, b, "Nº de beneficiarios", "benef_b")
    c2 = cuadro(sim_a, b, "Superficie activada (ha)", "sup_b")
    c3 = cuadro(sim_a, b, "Importe medio (€/explot.)", "medio_b")
    reparto = tabla_reparto(b)

    # ── NOTA: explotaciones teóricas nuevas (solo de los cultivos externos) ──
    total_nuevas = sum(int(round(b["n_explot_cat"][t])) for t in CAT_SIGPAC)
    total_nuevas_str = f"{total_nuevas:,}".replace(",", ".")
    eus = b["filas"]["Euskadi"]
    medio_con_nuevas = (eus["sup_b"] * b["vh"]) / (eus["benef_b"] + total_nuevas) if (eus["benef_b"] + total_nuevas) else 0.0
    NOTA = (
        "NOTA 1 — En B se activan las CUATRO palancas del Filtro B sobre los supervivientes "
        f">1000: cultivos externos ({_eu(b['total_externas'])} ha, dato real por titular) y "
        f"reactivación del 100 % de la ABRS sin derecho ({_eu(b['exceso_total'])} ha, exceso "
        "titular a titular). El umbral 1000 se aplica PRIMERO; las superficies adicionales son "
        "solo las de los supervivientes, no las de los excluidos <1000.  "
        "NOTA 2 — Los cuadros mantienen las explotaciones EXISTENTES. La superficie de cultivos "
        f"externos generaría ~{total_nuevas_str} explotaciones teóricas nuevas (sobre todo "
        "frutales y hortícolas de tamaño muy pequeño); si se contaran, el importe medio en "
        f"Euskadi pasaría de ~{_eu(eus['medio_b'])} € a ~{_eu(medio_con_nuevas)} €, por repartir "
        f"el mismo presupuesto ({_eu(b['presupuesto'])} €) entre más explotaciones. La "
        "reactivación de la ABRS sin derecho no crea explotaciones nuevas (es superficie de "
        "titulares ya existentes)."
    )

    # ── Mostrar ──
    print(f"\n  Valor/ha simulado en B = {b['vh']:,.2f}")
    mostrar("CUADRO 1 — Nº de beneficiarios (existentes)", c1)
    mostrar("CUADRO 2 — Superficie activada (ha)", c2)
    mostrar("CUADRO 3 — Importe medio por explotación (€)", c3)
    mostrar("REPARTO de la superficie incorporada en B por categoría y territorio", reparto)
    print("\n" + NOTA)

    # ── Excel: TODO en una sola hoja, apilado ──
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        hoja = "Comp_300_vs_1000_sup_adic"
        fila = 0
        bloques = [
            ("CUADRO 1 — Nº de beneficiarios (existentes)", c1),
            ("CUADRO 2 — Superficie activada (ha)", c2),
            ("CUADRO 3 — Importe medio por explotación (€)", c3),
            ("REPARTO de la superficie incorporada en B por categoría y territorio", reparto),
        ]
        for titulo, cdf in bloques:
            pd.DataFrame([[titulo]]).to_excel(
                xw, sheet_name=hoja, startrow=fila, startcol=0, index=False, header=False)
            fila += 1
            cdf.to_excel(xw, sheet_name=hoja, startrow=fila, index=False)
            fila += len(cdf) + 2
        pd.DataFrame([["NOTA:"], [NOTA]]).to_excel(
            xw, sheet_name=hoja, startrow=fila, startcol=0, index=False, header=False)
    print(f"\n[OK] Guardado (sobrescrito): {OUT}")


if __name__ == "__main__":
    main()
