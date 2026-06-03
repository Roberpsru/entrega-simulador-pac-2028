"""Entregables 1 y 2 — situación actual (>300) y comparativa simulada 300 vs 500.

PASO 0: lista columnas y confirma que IMP_AYUDA_TOTAL y TH_DESC son derivadas.

ENTREGABLE 1 — situacion_actual_300.xlsx (foto REAL, no simulador): beneficiarios
con ayuda total actual > 300 €, por territorio.

ENTREGABLE 2 — comparativa_300_vs_500.xlsx (motor del SIMULADOR): reutiliza el
motor real src.simulation.simular_superficie (la "lógica de simulación"). La
agregación por territorio NO está en un módulo (vive en pages/2_Simulador.py), así
que se replica fielmente y se VALIDA contra las cifras de la app antes de seguir.

Nota: src/kpis.py no existe en el proyecto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from src.derived import calcular_derivadas          # noqa: E402  (reutilizado)
from src.simulation import simular_superficie       # noqa: E402  (motor reutilizado)

RUTA_XLSX = RAIZ / "data" / "TABLA_GENERAL_PAGOS_DIRECTOS_2024_ANONIMIZADA.xlsx"
HOJA = "TABLA_GENERAL"
OUT1 = RAIZ / "situacion_actual_300.xlsx"
OUT2 = RAIZ / "comparativa_300_vs_500.xlsx"

ORDEN = ["Araba", "Gipuzkoa", "Bizkaia", "Otro"]

# Validación obligatoria (cifras de la app) para umbral 300: benef, sup activada, € medio.
# Superficie activada simulada = min(derechos, ABRS) por titular (la que hoy genera pago);
# la ABRS sin derecho ya NO entra en el denominador salvo reactivación por Filtro B.
VALID_300 = {
    "Araba":    (1518,  87830.18, 17620.97),
    "Bizkaia":  (2181,  23919.95,  3340.12),
    "Gipuzkoa": (2634,  27318.00,  3158.57),
    "Euskadi":  (6333, 139068.13,  6687.69),
}


# ─── Carga + derivadas (reutilizando calcular_derivadas) ─────────────────────

def cargar() -> pd.DataFrame:
    xls = pd.ExcelFile(RUTA_XLSX, engine="openpyxl")
    hoja = HOJA if HOJA in xls.sheet_names else xls.sheet_names[0]
    raw = pd.read_excel(xls, sheet_name=hoja)
    print("=" * 72)
    print("PASO 0 — Columnas reales y derivadas")
    print("=" * 72)
    print(f"Total columnas en el Excel: {len(raw.columns)}")
    print(f"  IMP_AYUDA_TOTAL en el Excel: {'IMP_AYUDA_TOTAL' in raw.columns}  (derivada)")
    print(f"  TH_DESC en el Excel        : {'TH_DESC' in raw.columns}  (derivada)")
    df = calcular_derivadas(raw)   # crea IMP_AYUDA_TOTAL y TH_DESC como en la app
    print("  -> calcular_derivadas() aplicada: IMP_AYUDA_TOTAL y TH_DESC creadas.")
    df["_SUP_CAP"] = df.get("SUPERFICIE_TOTAL_DESPUES_CAP", 0)
    df["_SUP_CAP"] = df["_SUP_CAP"].fillna(0)
    hay_otro = (df["TH_DESC"] == "Otro").any()
    print(f"  Territorios presentes: {df['TH_DESC'].value_counts().to_dict()}")
    print(f"  ¿Hay titulares 'Otro' (sin TH)? {hay_otro}")
    return df


def territorios(df: pd.DataFrame) -> list[str]:
    base = [t for t in ORDEN if t != "Otro" or (df["TH_DESC"] == "Otro").any()]
    return base + ["Euskadi"]


# ─── ENTREGABLE 1 — foto actual real (>300) ──────────────────────────────────

def situacion_actual(df: pd.DataFrame, umbral: float = 300) -> pd.DataFrame:
    g_all = df[df["IMP_AYUDA_TOTAL"] > umbral].copy()
    filas = []
    for terr in territorios(df):
        g = g_all if terr == "Euskadi" else g_all[g_all["TH_DESC"] == terr]
        n = len(g)
        imp_total = float(g["IMP_AYUDA_TOTAL"].sum())
        # Superficie activada = la que de verdad genera pago hoy = min(derechos, ABRS).
        # NO se usa SUPERFICIE_TOTAL_DESPUES_CAP.
        sup_act = float(
            g[["DERECHOS", "SUP_Det_Ctr_ABRS"]].fillna(0).min(axis=1).sum()
        )
        derechos = float(g["DERECHOS"].fillna(0).sum())
        filas.append({
            "Territorio": terr,
            "Nº de beneficiarios": n,
            "Superficie activada (ha)": round(sup_act, 2),
            "Importe total (€)": round(imp_total, 2),
            "Nº de derechos": round(derechos, 2),
            "Importe medio (€/benef.)": round(imp_total / n, 2) if n else 0.0,
        })
    return pd.DataFrame(filas)


# ─── ENTREGABLE 2 — motor del simulador (reutiliza simular_superficie) ────────

def correr_simulador(df: pd.DataFrame, umbral: float) -> pd.DataFrame:
    """Reproduce EXACTAMENTE el flujo de pages/2_Simulador.py (sin filtros de
    sidebar): excluye < umbral, redistribuye con presupuesto constante mediante
    el motor real, y agrega por territorio."""
    benef = df[df["IMP_AYUDA_TOTAL"] > 0].copy()           # benef_global de la app
    presupuesto_constante = float(benef["IMP_AYUDA_TOTAL"].sum())

    mask_excl = benef["IMP_AYUDA_TOTAL"] < umbral           # app: < umbral excluido
    activos = benef[~mask_excl].copy()
    excl = benef[mask_excl].copy()
    excl["IMP_SIMULADO"] = 0.0

    df_act, _vh, _ = simular_superficie(                    # <-- motor reutilizado
        activos, 0.0, presupuesto_total=presupuesto_constante,
    )
    df_sim = pd.concat([df_act, excl], ignore_index=True) if len(excl) else df_act

    filas = []
    for terr in territorios(df):
        d = df_sim if terr == "Euskadi" else df_sim[df_sim["TH_DESC"] == terr]
        activos_t = d[d["IMP_SIMULADO"] > 0]
        n_s = int(len(activos_t))
        sup_sim = float(activos_t["SUP_ACTIVABLE"].fillna(0).sum())   # activada simulada = min(der, ABRS)
        imp_med = float(activos_t["IMP_SIMULADO"].mean()) if n_s else 0.0
        filas.append({
            "Territorio": terr,
            "Nº de beneficiarios": n_s,
            "Superficie activada (ha)": round(sup_sim, 2),
            "Importe medio (€/explot.)": round(imp_med, 2),
        })
    return pd.DataFrame(filas)


def validar(sim300: pd.DataFrame) -> bool:
    print("\n" + "=" * 72)
    print("VALIDACIÓN obligatoria — umbral 300 debe coincidir con la app")
    print("=" * 72)
    ok = True
    for _, r in sim300.iterrows():
        terr = r["Territorio"]
        if terr not in VALID_300:
            continue
        n_ok, sup_ok, med_ok = VALID_300[terr]
        dn = int(r["Nº de beneficiarios"]) == n_ok
        ds = abs(r["Superficie activada (ha)"] - sup_ok) <= 0.01
        dm = abs(r["Importe medio (€/explot.)"] - med_ok) <= 0.01
        estado = "OK" if (dn and ds and dm) else "DISCREPANCIA"
        if not (dn and ds and dm):
            ok = False
        print(f"  {terr:<9} benef {int(r['Nº de beneficiarios']):>5} (esp {n_ok}) | "
              f"sup {r['Superficie activada (ha)']:>11,.2f} (esp {sup_ok:,.2f}) | "
              f"medio {r['Importe medio (€/explot.)']:>10,.2f} (esp {med_ok:,.2f})  -> {estado}")
    print(f"\n  RESULTADO VALIDACIÓN: {'TODO COINCIDE' if ok else 'NO COINCIDE -> PARAR'}")
    return ok


def comparativa(sim300: pd.DataFrame, sim500: pd.DataFrame):
    orden = [t for t in ["Araba", "Gipuzkoa", "Bizkaia", "Otro", "Euskadi"]
             if t in set(sim300["Territorio"])]

    def cuadro(col, etiqueta):
        a = sim300.set_index("Territorio")[col]
        b = sim500.set_index("Territorio")[col]
        return pd.DataFrame({
            "Territorio": orden,
            ">300 €": [round(float(a[t]), 2) for t in orden],
            ">500 €": [round(float(b[t]), 2) for t in orden],
            "Diferencia (>300 − >500)": [round(float(a[t] - b[t]), 2) for t in orden],
        })

    return (
        cuadro("Nº de beneficiarios", "benef"),
        cuadro("Superficie activada (ha)", "sup"),
        cuadro("Importe medio (€/explot.)", "medio"),
    )


# ─── Presentación europea + impresión ────────────────────────────────────────

def _fmt(v):
    if isinstance(v, (int, float)):
        s = f"{v:,.2f}" if isinstance(v, float) else f"{v:,}"
        return s.replace(",", "X").replace(".", ",").replace("X", ".")
    return str(v)


def mostrar(titulo, tabla):
    print("\n" + "-" * 72)
    print(titulo)
    print("-" * 72)
    disp = tabla.copy()
    for c in disp.columns:
        if c != "Territorio":
            disp[c] = disp[c].map(_fmt)
    print(disp.to_string(index=False))


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    df = cargar()

    # ENTREGABLE 1
    actual = situacion_actual(df, 300)
    mostrar("ENTREGABLE 1 — Situación ACTUAL real (ayuda total > 300 €)", actual)
    with pd.ExcelWriter(OUT1, engine="openpyxl") as xw:
        actual.to_excel(xw, sheet_name="Situacion_actual_300", index=False)
    print(f"\n[OK] Guardado: {OUT1}")

    # ENTREGABLE 2 — motor del simulador + validación
    sim300 = correr_simulador(df, 300)
    if not validar(sim300):
        print("\n*** PARADA: el motor no reproduce las cifras de la app. "
              "No se generan cuadros con cifras no validadas. ***")
        sys.exit(1)

    sim500 = correr_simulador(df, 500)
    c1, c2, c3 = comparativa(sim300, sim500)

    mostrar("CUADRO 1 — Nº de beneficiarios (simulado >300 vs >500)", c1)
    mostrar("CUADRO 2 — Superficie activada en ha (simulado >300 vs >500)", c2)
    mostrar("CUADRO 3 — Importe medio por explotación € (simulado >300 vs >500)", c3)

    # Tres cuadros apilados en UNA sola hoja, con título y fila en blanco
    with pd.ExcelWriter(OUT2, engine="openpyxl") as xw:
        hoja = "Comparativa_300_vs_500"
        fila = 0
        bloques = [
            ("CUADRO 1 — Nº de beneficiarios (simulado)", c1),
            ("CUADRO 2 — Superficie activada (ha) (simulado)", c2),
            ("CUADRO 3 — Importe medio por explotación (€) (simulado)", c3),
        ]
        for titulo, cuadro_df in bloques:
            pd.DataFrame([[titulo]]).to_excel(
                xw, sheet_name=hoja, startrow=fila, startcol=0, index=False, header=False,
            )
            fila += 1
            cuadro_df.to_excel(xw, sheet_name=hoja, startrow=fila, index=False)
            fila += len(cuadro_df) + 2   # tabla + cabecera + fila en blanco
    print(f"\n[OK] Guardado: {OUT2}")


if __name__ == "__main__":
    main()
