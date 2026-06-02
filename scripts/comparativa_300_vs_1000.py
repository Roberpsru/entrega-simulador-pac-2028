"""ENTREGABLE — comparativa SIMULADA 300 vs 1000 en una sola hoja.

Reutiliza el motor real y las funciones del script de entregables anterior
(cargar, correr_simulador -> usa src.simulation.simular_superficie, validar,
mostrar). Solo cambian el umbral alto (1000), las etiquetas y el fichero de salida.

PASO 0 y validación obligatoria (umbral 300) los realiza cargar()/validar().
src/kpis.py no existe; la "lógica de simulación" reutilizada es src/simulation.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

# Reutilización de las funciones ya escritas y validadas
from entregables_300_500 import (   # noqa: E402
    cargar, correr_simulador, validar, mostrar,
)

OUT = RAIZ / "comparativa_300_vs_1000.xlsx"
UMBRAL_BAJO, UMBRAL_ALTO = 300, 1000
ORDEN = ["Araba", "Gipuzkoa", "Bizkaia", "Otro", "Euskadi"]


def cuadros(sim_bajo: pd.DataFrame, sim_alto: pd.DataFrame):
    orden = [t for t in ORDEN if t in set(sim_bajo["Territorio"])]
    col_b, col_a = f">{UMBRAL_BAJO} €", f">{UMBRAL_ALTO} €"
    dif = f"Diferencia (>{UMBRAL_BAJO} − >{UMBRAL_ALTO})"

    def cuadro(col):
        a = sim_bajo.set_index("Territorio")[col]
        b = sim_alto.set_index("Territorio")[col]
        return pd.DataFrame({
            "Territorio": orden,
            col_b: [round(float(a[t]), 2) for t in orden],
            col_a: [round(float(b[t]), 2) for t in orden],
            dif:   [round(float(a[t] - b[t]), 2) for t in orden],
        })

    return (
        cuadro("Nº de beneficiarios"),
        cuadro("Superficie activada (ha)"),
        cuadro("Importe medio (€/explot.)"),
    )


def main():
    df = cargar()

    sim_bajo = correr_simulador(df, UMBRAL_BAJO)
    if not validar(sim_bajo):
        print("\n*** PARADA: el motor no reproduce las cifras de la app. "
              "No se generan cuadros con cifras no validadas. ***")
        sys.exit(1)

    sim_alto = correr_simulador(df, UMBRAL_ALTO)
    c1, c2, c3 = cuadros(sim_bajo, sim_alto)

    mostrar(f"CUADRO 1 — Nº de beneficiarios (simulado >{UMBRAL_BAJO} vs >{UMBRAL_ALTO})", c1)
    mostrar(f"CUADRO 2 — Superficie activada en ha (simulado >{UMBRAL_BAJO} vs >{UMBRAL_ALTO})", c2)
    mostrar(f"CUADRO 3 — Importe medio por explotación € (simulado >{UMBRAL_BAJO} vs >{UMBRAL_ALTO})", c3)

    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        hoja = f"Comparativa_{UMBRAL_BAJO}_vs_{UMBRAL_ALTO}"
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
