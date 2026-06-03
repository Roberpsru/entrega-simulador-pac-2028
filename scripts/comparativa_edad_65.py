"""ENTREGABLE — comparativa simulada: >300 todas las edades vs >300 y <65.

Escenario A: exclusión por umbral 300 (como la app).
Escenario B: además excluye el grupo ≥65 redistribuyendo su importe por hectárea
entre el resto (acción "excluir grupo" encadenada sobre el umbral, NO un filtrado
descriptivo): el presupuesto se mantiene constante y los ≥65 ceden su importe.

Reutiliza el motor real src.simulation.simular_superficie y las funciones ya
validadas de entregables_300_500.py (cargar, validar, mostrar, territorios).
La edad se calcula con calcular_derivadas (EDAD = 2024 − año FNACIMIENTO); los
≥65 son EDAD >= 65; jurídicas / sin fecha (EDAD NaN) NO son ≥65 y se mantienen.

src/kpis.py no existe en el proyecto.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

from entregables_300_500 import cargar, validar, mostrar, territorios  # noqa: E402
from src.simulation import simular_superficie                          # noqa: E402

OUT = RAIZ / "comparativa_300_todas_vs_300_menor65.xlsx"
UMBRAL = 300
ORDEN = ["Araba", "Gipuzkoa", "Bizkaia", "Otro", "Euskadi"]


def simular(df: pd.DataFrame, excluir):
    """Flujo de la app: excluye el grupo indicado por `excluir(benef)` y
    redistribuye con presupuesto constante mediante el motor real. Agrega por
    territorio (mismo cálculo que pages/2_Simulador.py)."""
    benef = df[df["IMP_AYUDA_TOTAL"] > 0].copy()          # benef_global de la app
    presupuesto_constante = float(benef["IMP_AYUDA_TOTAL"].sum())

    mask_excl = excluir(benef)
    activos = benef[~mask_excl].copy()
    excl = benef[mask_excl].copy()
    excl["IMP_SIMULADO"] = 0.0

    df_act, _vh, _ = simular_superficie(                  # <-- motor reutilizado
        activos, 0.0, presupuesto_total=presupuesto_constante,
    )
    df_sim = pd.concat([df_act, excl], ignore_index=True) if len(excl) else df_act

    filas = []
    for terr in territorios(df):
        d = df_sim if terr == "Euskadi" else df_sim[df_sim["TH_DESC"] == terr]
        act_t = d[d["IMP_SIMULADO"] > 0]
        n_s = int(len(act_t))
        # Superficie activable simulada (SUP_ACTIVABLE = min(derechos, ABRS) +
        # sin derecho reactivada; aquí sin reactivación = min(derechos, ABRS)).
        sup_sim = float(act_t["SUP_ACTIVABLE"].fillna(0).sum())
        imp_med = float(act_t["IMP_SIMULADO"].mean()) if n_s else 0.0
        filas.append({
            "Territorio": terr,
            "Nº de beneficiarios": n_s,
            "Superficie activada (ha)": round(sup_sim, 2),
            "Importe medio (€/explot.)": round(imp_med, 2),
        })
    return pd.DataFrame(filas)


def cuadros(sim_a: pd.DataFrame, sim_b: pd.DataFrame):
    orden = [t for t in ORDEN if t in set(sim_a["Territorio"])]
    col_a, col_b = ">300 (todas las edades)", ">300 y <65"
    dif = "Diferencia (A − B)"

    def cuadro(col):
        a = sim_a.set_index("Territorio")[col]
        b = sim_b.set_index("Territorio")[col]
        return pd.DataFrame({
            "Territorio": orden,
            col_a: [round(float(a[t]), 2) for t in orden],
            col_b: [round(float(b[t]), 2) for t in orden],
            dif:   [round(float(a[t] - b[t]), 2) for t in orden],
        })

    return (
        cuadro("Nº de beneficiarios"),
        cuadro("Superficie activada (ha)"),
        cuadro("Importe medio (€/explot.)"),
    )


def main():
    df = cargar()

    # Escenario A — umbral 300, todas las edades
    sim_a = simular(df, lambda b: b["IMP_AYUDA_TOTAL"] < UMBRAL)
    if not validar(sim_a):
        print("\n*** PARADA: el motor no reproduce las cifras de la app. ***")
        sys.exit(1)

    # Escenario B — umbral 300 + exclusión del grupo ≥65 (con redistribución).
    # SOLO personas físicas: las jurídicas (aunque su FNACIMIENTO dé EDAD>=65)
    # y los titulares sin fecha NO se consideran ≥65 y se mantienen.
    def _excluir_b(b):
        es_fisica = b["ES_PERSONA_FISICA"].fillna(False) if "ES_PERSONA_FISICA" in b else True
        return (b["IMP_AYUDA_TOTAL"] < UMBRAL) | ((b["EDAD"] >= 65) & es_fisica)

    sim_b = simular(df, _excluir_b)

    # Recuento de exclusiones por edad (sobre la base >300 = activa en A)
    benef = df[df["IMP_AYUDA_TOTAL"] > 0]
    base_300 = benef[benef["IMP_AYUDA_TOTAL"] >= UMBRAL]
    es_fis = base_300["ES_PERSONA_FISICA"].fillna(False)
    n_65_excluidos = int(((base_300["EDAD"] >= 65) & es_fis).sum())
    n_juridicas_65_mantenidas = int(((base_300["EDAD"] >= 65) & ~es_fis).sum())
    n_sin_edad = int(base_300["EDAD"].isna().sum())
    print(f"\n  Titulares ≥65 (personas físicas) EXCLUIDOS por la acción de edad: {n_65_excluidos}")
    print(f"  Personas jurídicas con representante ≥65 MANTENIDAS: {n_juridicas_65_mantenidas}")
    print(f"  Titulares sin fecha de nacimiento MANTENIDOS: {n_sin_edad}")

    c1, c2, c3 = cuadros(sim_a, sim_b)
    mostrar("CUADRO 1 — Nº de beneficiarios (>300 todas vs >300 y <65)", c1)
    mostrar("CUADRO 2 — Superficie activada en ha (>300 todas vs >300 y <65)", c2)
    mostrar("CUADRO 3 — Importe medio por explotación € (>300 todas vs >300 y <65)", c3)

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        hoja = "Comparativa_300_vs_300_menor65"
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
            fila += len(cuadro_df) + 2
    print(f"\n[OK] Guardado: {OUT}")


if __name__ == "__main__":
    main()
