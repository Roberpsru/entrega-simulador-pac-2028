"""ENTREGABLE — >300 todas las edades  vs  >500 y <65.

Escenario A: exclusión por umbral 300 (como la app).
Escenario B: umbral 500 + exclusión del grupo ≥65 (solo personas físicas)
encadenados, con redistribución por hectárea (presupuesto constante). NO es un
filtrado descriptivo.

Reutiliza el motor real src.simulation.simular_superficie a través de la función
`simular` ya validada de comparativa_edad_65.py, y cargar/validar/mostrar/
territorios de entregables_300_500.py. src/kpis.py no existe.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

from entregables_300_500 import cargar, validar, mostrar  # noqa: E402
from comparativa_edad_65 import simular                   # noqa: E402 (reutiliza el motor)

OUT = RAIZ / "comparativa_300_todas_vs_500_menor65.xlsx"
ORDEN = ["Araba", "Gipuzkoa", "Bizkaia", "Otro", "Euskadi"]


def cuadros(sim_a: pd.DataFrame, sim_b: pd.DataFrame):
    orden = [t for t in ORDEN if t in set(sim_a["Territorio"])]
    col_a, col_b, dif = ">300 (todas las edades)", ">500 y <65", "Diferencia (A − B)"

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
    sim_a = simular(df, lambda b: b["IMP_AYUDA_TOTAL"] < 300)
    if not validar(sim_a):
        print("\n*** PARADA: el motor no reproduce las cifras de la app. ***")
        sys.exit(1)

    # Escenario B — umbral 500 + ≥65 (solo físicas), encadenados
    def _excluir_b(b):
        es_fis = b["ES_PERSONA_FISICA"].fillna(False) if "ES_PERSONA_FISICA" in b else True
        return (b["IMP_AYUDA_TOTAL"] < 500) | ((b["EDAD"] >= 65) & es_fis)

    sim_b = simular(df, _excluir_b)

    # Desglose de exclusiones de B (sobre benef_global = ayuda > 0)
    benef = df[df["IMP_AYUDA_TOTAL"] > 0]
    es_fis = benef["ES_PERSONA_FISICA"].fillna(False)
    m_imp = benef["IMP_AYUDA_TOTAL"] < 500
    m_edad = (benef["EDAD"] >= 65) & es_fis
    n_imp = int(m_imp.sum())
    n_edad = int(m_edad.sum())
    n_ambos = int((m_imp & m_edad).sum())
    n_total = int((m_imp | m_edad).sum())
    n_jur65 = int(((benef["EDAD"] >= 65) & ~es_fis).sum())
    print("\n  Exclusiones del Escenario B (sobre los titulares con ayuda > 0):")
    print(f"    · Por importe (< 500 €):                 {n_imp}")
    print(f"    · Por edad (≥65, personas físicas):      {n_edad}")
    print(f"      (de los cuales, también < 500 €:       {n_ambos})")
    print(f"    · TOTAL excluidos únicos en B:           {n_total}")
    print(f"    · Jurídicas con representante ≥65 MANTENIDAS: {n_jur65}")

    c1, c2, c3 = cuadros(sim_a, sim_b)
    mostrar("CUADRO 1 — Nº de beneficiarios (>300 todas vs >500 y <65)", c1)
    mostrar("CUADRO 2 — Superficie activada en ha (>300 todas vs >500 y <65)", c2)
    mostrar("CUADRO 3 — Importe medio por explotación € (>300 todas vs >500 y <65)", c3)

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        hoja = "Comp_300todas_vs_500menor65"
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
