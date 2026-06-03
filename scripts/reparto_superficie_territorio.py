"""Desglose por territorio de la superficie adicional incorporable (base >300).

Usa las MISMAS columnas que el Filtro B del simulador:
- Externas (viñedo y txakoli, frutales y frutos secos, hortícolas): máximo
  incorporable = potencial SIGPAC − superficie declarada (Tabla_Cultivos_PAC),
  repartido por territorio según la PROPORCIÓN del potencial SIGPAC de cada TH.
- ABRS sin derecho: Σ(SUP_Det_Ctr_ABRS − DERECHOS) recortado a ≥0, sobre la base
  activa (>300), atribuido REAL titular-a-titular por TH.

Salida: reparto_superficie_adicional_territorio.xlsx (una hoja). No toca la app.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src.derived import calcular_derivadas  # noqa: E402  (reutilizado)

OUT = RAIZ / "reparto_superficie_adicional_territorio.xlsx"
UMBRAL = 300
TERRS = ["Araba", "Gipuzkoa", "Bizkaia"]
CAT_SIGPAC = {
    "Viñedo y Txakoli": "VIÑEDO Y TXAKOLI",
    "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
    "Hortícolas": "HORTICOLA",
}
TH_SIGPAC = {"Araba": "ARABA", "Gipuzkoa": "GIPUZKOA", "Bizkaia": "BIZKAIA"}


def main():
    df = calcular_derivadas(
        pd.read_excel(RAIZ / "data" / "TABLA_GENERAL_PAGOS_DIRECTOS_2024_ANONIMIZADA.xlsx",
                      sheet_name="TABLA_GENERAL")
    )
    imp = [c for c in df.columns if c.startswith("IMP_AYUDA_") and c != "IMP_AYUDA_TOTAL"]
    df["IMP_AYUDA_TOTAL"] = df[imp].fillna(0).sum(axis=1)
    benef = df[df["IMP_AYUDA_TOTAL"] > 0].copy()
    activos = benef[benef["IMP_AYUDA_TOTAL"] >= UMBRAL].copy()

    sup_max = pd.read_excel(RAIZ / "data" / "SUP_MAX_SIGPAC.xlsx", sheet_name="Superficie")
    cult = pd.read_excel(RAIZ / "data" / "Tabla_Cultivos_PAC.xlsx", sheet_name="Sup")

    filas = []
    # ── Externas: máximo SIGPAC − declarado, repartido por proporción SIGPAC ──
    for tipo, col in CAT_SIGPAC.items():
        sig = float(sup_max[col].sum())
        cultivos = cult[cult[col] == "SI"]["Unnamed: 0"].tolist()
        cols_ok = [c for c in cultivos if c in benef.columns]
        decl = float(benef[cols_ok].sum().sum()) if cols_ok else 0.0
        maxha = max(0.0, sig - decl)
        fila = {"Categoría": tipo, "Método": "Proporción SIGPAC"}
        for terr, ts in TH_SIGPAC.items():
            f = sup_max[sup_max["SUPERFICIE DECLARADA SIGPAC"] == ts]
            prop = float(f[col].iloc[0]) / sig if sig > 0 else 0.0
            fila[terr] = round(maxha * prop, 2)
        fila["Euskadi"] = round(sum(fila[t] for t in TERRS), 2)
        filas.append(fila)

    # ── ABRS sin derecho: reparto REAL titular-a-titular por TH (base >300) ──
    exc = (activos["SUP_Det_Ctr_ABRS"].fillna(0) - activos["DERECHOS"].fillna(0)).clip(lower=0)
    g = activos.assign(_exc=exc).groupby("TH_DESC")["_exc"].sum()
    fila = {"Categoría": "Superficie ABRS sin derecho", "Método": "Real titular-a-TH"}
    for terr in TERRS:
        fila[terr] = round(float(g.get(terr, 0.0)), 2)
    fila["Euskadi"] = round(sum(fila[t] for t in TERRS), 2)
    filas.append(fila)

    tabla = pd.DataFrame(filas)[["Categoría", "Método", "Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]]

    # Subtotal externas (las que SÍ se suman al denominador del modelo)
    ext = tabla[tabla["Método"] == "Proporción SIGPAC"]
    subtotal = {
        "Categoría": "Subtotal externas (al denominador)", "Método": "—",
        "Araba": round(ext["Araba"].sum(), 2), "Gipuzkoa": round(ext["Gipuzkoa"].sum(), 2),
        "Bizkaia": round(ext["Bizkaia"].sum(), 2), "Euskadi": round(ext["Euskadi"].sum(), 2),
    }

    NOTA = ("Externas (viñedo, frutales, hortícolas): potencial SIGPAC − superficie declarada, "
            "repartido por proporción del potencial SIGPAC de cada territorio (agregado, no por "
            "titular). ABRS sin derecho: Σ(SUP_Det_Ctr_ABRS − DERECHOS)≥0 sobre la base >300, "
            "atribuida titular-a-titular por TH; ya está incluida en SUP_Det_Ctr_ABRS, por lo que "
            "NO se suma al denominador del modelo (es activación de superficie ya existente).")

    def _eu(v):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if isinstance(v, float) else str(v)

    disp = tabla.copy()
    for c in ["Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]:
        disp[c] = disp[c].map(_eu)
    print("REPARTO DE SUPERFICIE ADICIONAL POR CATEGORÍA Y TERRITORIO (base >300)\n")
    print(disp.to_string(index=False))
    print(f"\n{'Subtotal externas':<34}"
          f"Araba {_eu(subtotal['Araba'])} | Gipuzkoa {_eu(subtotal['Gipuzkoa'])} | "
          f"Bizkaia {_eu(subtotal['Bizkaia'])} | Euskadi {_eu(subtotal['Euskadi'])}")

    out = pd.concat([tabla, pd.DataFrame([subtotal])], ignore_index=True)
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        hoja = "Reparto_territorio"
        out.to_excel(xw, sheet_name=hoja, index=False)
        pd.DataFrame([[""], ["NOTA:"], [NOTA]]).to_excel(
            xw, sheet_name=hoja, startrow=len(out) + 2, startcol=0, index=False, header=False)
    print(f"\n[OK] Guardado: {OUT}")


if __name__ == "__main__":
    main()
