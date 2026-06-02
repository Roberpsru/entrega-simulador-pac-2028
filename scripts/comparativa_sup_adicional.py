"""ENTREGABLE — >300  vs  >300 + superficie adicional (Filtro B, 4 categorías).

Escenario A: umbral 300 (como la app).
Escenario B: umbral 300 + Filtro B "Incorporar superficie adicional" al máximo de
las 4 categorías (viñedo y txakoli, frutales y frutos secos, hortícolas y ABRS sin
derecho), con redistribución por hectárea (presupuesto constante).

Reutiliza el motor real src.simulation.simular_superficie y replica fielmente el
Filtro B de pages/2_Simulador.py (no existe función reutilizable: la lógica está
embebida en la página), con los mismos ficheros SUP_MAX_SIGPAC.xlsx y
Tabla_Cultivos_PAC.xlsx. src/kpis.py no existe.

Decisión de modelado (elegida por el usuario): los tres cuadros usan la población
EXISTENTES + NUEVAS EXPLOTACIONES estimadas, repartidas por territorio con la
proporción SIGPAC (igual que las hectáreas). El nº de explotaciones por territorio
es una estimación orientativa (la app no lo reparte por territorio).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

from entregables_300_500 import cargar, validar, mostrar   # noqa: E402
from comparativa_edad_65 import simular                    # noqa: E402
from src.simulation import simular_superficie              # noqa: E402

OUT = RAIZ / "comparativa_300_vs_300_superficie_adicional.xlsx"
UMBRAL = 300
ORDEN = ["Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]
TERRS = ["Araba", "Gipuzkoa", "Bizkaia"]
CAT_SIGPAC = {
    "Viñedo y Txakoli": "VIÑEDO Y TXAKOLI",
    "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
    "Hortícolas": "HORTICOLA",
}
TH_SIGPAC = {"Araba": "ARABA", "Bizkaia": "BIZKAIA", "Gipuzkoa": "GIPUZKOA"}


def main():
    df = cargar()
    benef = df[df["IMP_AYUDA_TOTAL"] > 0].copy()
    activos = benef[benef["IMP_AYUDA_TOTAL"] >= UMBRAL].copy()
    presupuesto = float(benef["IMP_AYUDA_TOTAL"].sum())

    sup_max = pd.read_excel(RAIZ / "data" / "SUP_MAX_SIGPAC.xlsx", sheet_name="Superficie")
    cult = pd.read_excel(RAIZ / "data" / "Tabla_Cultivos_PAC.xlsx", sheet_name="Sup")

    # ── Filtro B: max incorporable + nuevas explotaciones por categoría ──
    maxes, n_explot_cat, sup_media_cat = {}, {}, {}
    for tipo, col in CAT_SIGPAC.items():
        sigpac_max = float(sup_max[col].sum())
        cultivos = cult[cult[col] == "SI"]["Unnamed: 0"].tolist()
        cols_ok = [c for c in cultivos if c in benef.columns]
        sup_decl = float(benef[cols_ok].sum().sum()) if cols_ok else 0.0
        maxes[tipo] = max(0.0, sigpac_max - sup_decl)
        spt = benef[cols_ok].fillna(0).sum(axis=1) if cols_ok else pd.Series(dtype=float)
        n_act = int((spt > 0).sum()) if len(spt) else 0
        sup_media_cat[tipo] = (float(spt.sum()) / n_act) if n_act else 0.0
        n_explot_cat[tipo] = (maxes[tipo] / sup_media_cat[tipo]) if sup_media_cat[tipo] else 0.0

    exceso = (activos["SUP_Det_Ctr_ABRS"].fillna(0) - activos["DERECHOS"].fillna(0)).clip(lower=0)
    max_abrs = float(exceso.sum())
    total_externas = sum(maxes.values())

    print("\n  MÁXIMO INCORPORABLE por categoría (Filtro B):")
    for tipo in CAT_SIGPAC:
        print(f"    · {tipo:<26}{maxes[tipo]:>12,.2f} ha  (~{round(n_explot_cat[tipo])} nuevas explot.)")
    print(f"    · {'Superficie ABRS sin derecho':<26}{max_abrs:>12,.2f} ha  (ya en SUP_ABRS; no suma al denominador)")

    # ── Validación A ──
    sim_a = simular(df, lambda b: b["IMP_AYUDA_TOTAL"] < UMBRAL)
    if not validar(sim_a):
        print("\n*** PARADA: el motor no reproduce las cifras de la app. ***")
        sys.exit(1)

    # ── B: motor con superficie externa al denominador ──
    df_act, vh, _ = simular_superficie(activos, total_externas, presupuesto_total=presupuesto)

    # Reparto por territorio (SIGPAC) de ha externas y de nuevas explotaciones
    ha_terr = {t: 0.0 for t in TERRS}
    nexpl_terr = {t: 0.0 for t in TERRS}
    for tipo, col in CAT_SIGPAC.items():
        tot = float(sup_max[col].sum())
        if tot <= 0 or maxes[tipo] <= 0:
            continue
        for terr, terr_sig in TH_SIGPAC.items():
            fila = sup_max[sup_max["SUPERFICIE DECLARADA SIGPAC"] == terr_sig]
            if fila.empty:
                continue
            prop = float(fila[col].iloc[0]) / tot
            ha_terr[terr] += maxes[tipo] * prop
            nexpl_terr[terr] += n_explot_cat[tipo] * prop

    # ── Cuadros (OPCIÓN 1: solo beneficiarios EXISTENTES; NO se añaden nuevas) ──
    filas = {}
    sup_ex_terr = {}
    for terr in TERRS:
        d = df_act[df_act["TH_DESC"] == terr]
        act_t = d[d["IMP_SIMULADO"] > 0]
        benef_ex = int(len(act_t))
        sup_ex = float(act_t["SUP_Det_Ctr_ABRS"].fillna(0).sum())
        sup_ex_terr[terr] = sup_ex
        # A
        ra = sim_a.set_index("Territorio").loc[terr]
        benef_a = int(ra["Nº de beneficiarios"])
        sup_a = float(ra["Superficie activada (ha)"])
        medio_a = float(ra["Importe medio (€/explot.)"])
        # B: mismos beneficiarios existentes (no se añaden nuevas). La superficie
        # incluye las ha externas incorporadas; el importe medio del EXISTENTE baja
        # porque el valor/ha cae al ampliar el denominador.
        benef_b = benef_ex
        sup_b = sup_ex + ha_terr[terr]
        medio_b = float(act_t["IMP_SIMULADO"].mean()) if benef_ex else 0.0
        filas[terr] = dict(benef_a=benef_a, benef_b=benef_b,
                           sup_a=sup_a, sup_b=sup_b,
                           medio_a=medio_a, medio_b=medio_b)

    # Euskadi = suma de territorios (importe medio = total existente / nº existentes)
    eus = {}
    eus["benef_a"] = sum(filas[t]["benef_a"] for t in TERRS)
    eus["benef_b"] = sum(filas[t]["benef_b"] for t in TERRS)
    eus["sup_a"] = sum(filas[t]["sup_a"] for t in TERRS)
    eus["sup_b"] = sum(filas[t]["sup_b"] for t in TERRS)
    eus["medio_a"] = presupuesto / eus["benef_a"] if eus["benef_a"] else 0.0
    eus["medio_b"] = (sum(sup_ex_terr.values()) * vh) / eus["benef_b"] if eus["benef_b"] else 0.0
    filas["Euskadi"] = eus

    # Cifra para la nota: importe medio SI se incorporaran las nuevas explotaciones
    total_nuevas = sum(int(round(nexpl_terr[t])) for t in TERRS)
    medio_eus_con_nuevas = (eus["sup_b"] * vh) / (eus["benef_b"] + total_nuevas)

    def _eu_int(n):
        return f"{int(round(n)):,}".replace(",", ".")

    NOTA = (
        "NOTA: Este escenario refleja SOLO el efecto sobre las explotaciones existentes "
        "(no se añaden nuevas). La superficie adicional incorporada (viñedo, frutales, "
        "hortícolas) reduce ligeramente el importe medio del existente al ampliar el "
        "denominador. ADVERTENCIA: si se incorporaran las nuevas explotaciones que "
        f"generaría esa superficie (~{_eu_int(total_nuevas)} estimadas, sobre todo frutales "
        "y hortícolas de tamaño muy pequeño), el importe medio por explotación caería con "
        f"fuerza (en Euskadi, de ~{_eu_int(eus['medio_b'])} € a ~{_eu_int(medio_eus_con_nuevas)} €), "
        "NO por reducción del presupuesto (constante: 42.353.115,52 €) sino por repartirse "
        "entre muchas más explotaciones pequeñas."
    )

    def cuadro(a_key, b_key, etq_a, etq_b):
        return pd.DataFrame({
            "Territorio": ORDEN,
            etq_a: [round(filas[t][a_key], 2) for t in ORDEN],
            etq_b: [round(filas[t][b_key], 2) for t in ORDEN],
            "Diferencia (A − B)": [round(filas[t][a_key] - filas[t][b_key], 2) for t in ORDEN],
        })

    c1 = cuadro("benef_a", "benef_b", ">300", ">300 + sup. adicional")
    c2 = cuadro("sup_a", "sup_b", ">300", ">300 + sup. adicional")
    c3 = cuadro("medio_a", "medio_b", ">300", ">300 + sup. adicional")

    print(f"\n  Valor/ha: A = {presupuesto/float(activos['SUP_Det_Ctr_ABRS'].fillna(0).sum()):,.2f}  ->  "
          f"B (con +{total_externas:,.0f} ha) = {vh:,.2f}")
    print(f"  (Nuevas explotaciones estimadas, NO incluidas en los cuadros — solo para la nota): "
          f"~{total_nuevas:,}")
    mostrar("CUADRO 1 — Nº de beneficiarios (>300 vs >300 + sup. adicional)", c1)
    mostrar("CUADRO 2 — Superficie activada en ha (>300 vs >300 + sup. adicional)", c2)
    mostrar("CUADRO 3 — Importe medio por explotación € (>300 vs >300 + sup. adicional)", c3)
    print("\n" + NOTA)

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        hoja = "Comp_300_vs_sup_adicional"
        fila = 0
        for titulo, cdf in [
            ("CUADRO 1 — Nº de beneficiarios (solo beneficiarios existentes)", c1),
            ("CUADRO 2 — Superficie activada (ha)", c2),
            ("CUADRO 3 — Importe medio por explotación (€)", c3),
        ]:
            pd.DataFrame([[titulo]]).to_excel(xw, sheet_name=hoja, startrow=fila, startcol=0,
                                              index=False, header=False)
            fila += 1
            cdf.to_excel(xw, sheet_name=hoja, startrow=fila, index=False)
            fila += len(cdf) + 2
        # Nota de advertencia al pie de la hoja
        pd.DataFrame([[NOTA]]).to_excel(xw, sheet_name=hoja, startrow=fila, startcol=0,
                                        index=False, header=False)
    print(f"\n[OK] Guardado: {OUT}")


if __name__ == "__main__":
    main()
