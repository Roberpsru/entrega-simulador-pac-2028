"""Reparto de las externas por territorio según DATO REAL por titular.

Para cada categoría externa (viñedo y txakoli, frutales y frutos secos, hortícolas):
- Máximo incorporable = potencial SIGPAC − superficie declarada (igual que el Filtro B).
- Reparto por territorio = máximo × (superficie de cultivo REAL declarada en el TH /
  total declarado), sumando las columnas de cultivo de la categoría agrupadas por TH.

Población para el dato real: beneficiarios con ayuda > 0. Salida: Excel. No toca la app.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from src.derived import calcular_derivadas  # noqa: E402

OUT = RAIZ / "reparto_externas_real_por_titular.xlsx"
TERRS = ["Araba", "Gipuzkoa", "Bizkaia"]
CAT_SIGPAC = {
    "Viñedo y Txakoli": "VIÑEDO Y TXAKOLI",
    "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
    "Hortícolas": "HORTICOLA",
}


def _eu(v):
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if isinstance(v, float) else str(v)


def main():
    df = calcular_derivadas(
        pd.read_excel(RAIZ / "data" / "TABLA_GENERAL_PAGOS_DIRECTOS_2024_ANONIMIZADA.xlsx",
                      sheet_name="TABLA_GENERAL")
    )
    imp = [c for c in df.columns if c.startswith("IMP_AYUDA_") and c != "IMP_AYUDA_TOTAL"]
    df["IMP_AYUDA_TOTAL"] = df[imp].fillna(0).sum(axis=1)
    benef = df[df["IMP_AYUDA_TOTAL"] > 0].copy()
    sup_max = pd.read_excel(RAIZ / "data" / "SUP_MAX_SIGPAC.xlsx", sheet_name="Superficie")
    cult = pd.read_excel(RAIZ / "data" / "Tabla_Cultivos_PAC.xlsx", sheet_name="Sup")

    filas = []
    for tipo, col in CAT_SIGPAC.items():
        sig_total = float(sup_max[col].sum())
        cultivos = cult[cult[col] == "SI"]["Unnamed: 0"].tolist()
        cols_ok = [c for c in cultivos if c in benef.columns]
        decl_total = float(benef[cols_ok].sum().sum()) if cols_ok else 0.0
        maxha = max(0.0, sig_total - decl_total)

        # Superficie real declarada por TH (suma de columnas de cultivo agrupada por TH)
        real_th = (benef.assign(_s=benef[cols_ok].fillna(0).sum(axis=1))
                   .groupby("TH_DESC")["_s"].sum()) if cols_ok else pd.Series(dtype=float)

        fila = {"Categoría": tipo}
        for terr in TERRS:
            prop_real = float(real_th.get(terr, 0.0)) / decl_total if decl_total > 0 else 0.0
            fila[terr] = round(maxha * prop_real, 2)
        fila["Euskadi"] = round(sum(fila[t] for t in TERRS), 2)
        filas.append(fila)

    tabla = pd.DataFrame(filas)[["Categoría", "Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]]

    # Fila total externas
    total = {"Categoría": "TOTAL externas"}
    for c in ["Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]:
        total[c] = round(tabla[c].sum(), 2)
    out = pd.concat([tabla, pd.DataFrame([total])], ignore_index=True)

    disp = out.copy()
    for c in ["Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]:
        disp[c] = disp[c].map(_eu)
    print("REPARTO DE EXTERNAS POR TERRITORIO — DATO REAL POR TITULAR (ha)\n")
    print(disp.to_string(index=False))

    NOTA = ("Reparto por la superficie de cultivo REAL declarada en cada territorio "
            "(suma de las columnas de cultivo de cada categoría agrupada por TH, sobre los "
            "beneficiarios con ayuda > 0). El máximo incorporable por categoría es el del "
            "Filtro B (potencial SIGPAC − superficie declarada).")
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        out.to_excel(xw, sheet_name="Externas_real_por_titular", index=False)
        pd.DataFrame([[""], ["NOTA:"], [NOTA]]).to_excel(
            xw, sheet_name="Externas_real_por_titular", startrow=len(out) + 2, index=False, header=False)
    print(f"\n[OK] Guardado: {OUT}")


if __name__ == "__main__":
    main()
