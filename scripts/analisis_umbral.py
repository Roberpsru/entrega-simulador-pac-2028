"""Análisis por umbral de ayuda y territorio sobre la tabla maestra 2024.

Genera:
  - PASO 0: listado de columnas + comprobación de IMP_AYUDA_TOTAL y TH_DESC.
  - ANÁLISIS BASE (ayuda total > 300 €): nº beneficiarios, superficie total
    (después del CAP), número de derechos e importe medio por beneficiario.
  - COMPARATIVA >300 vs >500 € en tres cuadros (beneficiarios, superficie,
    importe medio), con columna de diferencia (>300 − >500).

Salida: tablas por consola + Excel 'analisis_umbral_2024.xlsx' (una hoja por cuadro).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
RUTA_XLSX = RAIZ / "data" / "TABLA_GENERAL_PAGOS_DIRECTOS_2024_ANONIMIZADA.xlsx"
HOJA = "TABLA_GENERAL"
SALIDA = RAIZ / "analisis_umbral_2024.xlsx"

ORDEN_TERR = ["Araba", "Gipuzkoa", "Bizkaia", "Otro"]
MAPA_TH = {1: "Araba", 20: "Gipuzkoa", 48: "Bizkaia"}


# ─── Carga ──────────────────────────────────────────────────────────────────

def cargar() -> pd.DataFrame:
    xls = pd.ExcelFile(RUTA_XLSX, engine="openpyxl")
    hoja = HOJA if HOJA in xls.sheet_names else xls.sheet_names[0]
    if hoja != HOJA:
        print(f"[aviso] Hoja '{HOJA}' no encontrada; uso la primera: '{hoja}'.")
    return pd.read_excel(xls, sheet_name=hoja)


# ─── PASO 0 ─────────────────────────────────────────────────────────────────

def paso0(df: pd.DataFrame) -> pd.DataFrame:
    print("=" * 70)
    print("PASO 0 — Columnas reales y variables derivadas")
    print("=" * 70)
    print(f"Total columnas: {len(df.columns)}")
    print(f"  ¿Existe IMP_AYUDA_TOTAL?  {'IMP_AYUDA_TOTAL' in df.columns}")
    print(f"  ¿Existe TH_DESC?          {'TH_DESC' in df.columns}")
    print(f"  ¿Existe TH?               {'TH' in df.columns}")

    # Ayuda total = suma de todas las columnas IMP_AYUDA_* (nulos = 0)
    cols_imp = [c for c in df.columns
                if c.startswith("IMP_AYUDA_") and c != "IMP_AYUDA_TOTAL"]
    if "IMP_AYUDA_TOTAL" not in df.columns:
        df["IMP_AYUDA_TOTAL"] = df[cols_imp].fillna(0).sum(axis=1)
        print(f"  -> IMP_AYUDA_TOTAL creada sumando {len(cols_imp)} columnas IMP_AYUDA_*.")

    # Territorio = TH mapeado (resto/nulo -> Otro)
    if "TH_DESC" not in df.columns:
        df["TH_DESC"] = df["TH"].map(MAPA_TH).fillna("Otro")
        print("  -> TH_DESC creada mapeando TH (1->Araba, 20->Gipuzkoa, 48->Bizkaia, resto->Otro).")

    # Superficie después del CAP (nulos = 0)
    if "SUPERFICIE_TOTAL_DESPUES_CAP" in df.columns:
        df["_SUP_CAP"] = df["SUPERFICIE_TOTAL_DESPUES_CAP"].fillna(0)
    else:
        df["_SUP_CAP"] = 0.0
        print("  [aviso] No existe SUPERFICIE_TOTAL_DESPUES_CAP; superficie = 0.")

    print(f"\n  Valores de TH presentes: {sorted(df['TH'].dropna().unique().tolist())}")
    print(f"  Reparto por territorio:  {df['TH_DESC'].value_counts().to_dict()}")
    return df


# ─── Agregación por territorio ──────────────────────────────────────────────

def agrupar(df_filtrado: pd.DataFrame, con_derechos: bool) -> pd.DataFrame:
    """Una fila por territorio (orden fijo) + fila Euskadi (todos, Otro incluido)."""
    filas = []
    for terr in ORDEN_TERR:
        g = df_filtrado[df_filtrado["TH_DESC"] == terr]
        filas.append(_fila(terr, g, con_derechos))
    filas.append(_fila("Euskadi", df_filtrado, con_derechos))  # total de TODOS
    return pd.DataFrame(filas)


def _fila(terr: str, g: pd.DataFrame, con_derechos: bool) -> dict:
    n = len(g)
    ayuda = float(g["IMP_AYUDA_TOTAL"].sum())
    fila = {
        "Territorio": terr,
        "Nº beneficiarios": n,
        "Superficie total (ha, post-CAP)": round(float(g["_SUP_CAP"].sum()), 2),
        "Importe medio (€/benef.)": round(ayuda / n, 2) if n > 0 else 0.0,
    }
    if con_derechos:
        fila["Nº de derechos"] = round(float(g["DERECHOS"].fillna(0).sum()), 2)
    # reordenar para que derechos quede antes del importe medio
    if con_derechos:
        fila = {
            "Territorio": fila["Territorio"],
            "Nº beneficiarios": fila["Nº beneficiarios"],
            "Superficie total (ha, post-CAP)": fila["Superficie total (ha, post-CAP)"],
            "Nº de derechos": fila["Nº de derechos"],
            "Importe medio (€/benef.)": fila["Importe medio (€/benef.)"],
        }
    return fila


# ─── Comparativa >300 vs >500 ───────────────────────────────────────────────

def cuadro(b300: pd.DataFrame, b500: pd.DataFrame, columna: str) -> pd.DataFrame:
    m = b300[["Territorio", columna]].merge(
        b500[["Territorio", columna]], on="Territorio", suffixes=(" >300", " >500"),
    )
    c300, c500 = f"{columna} >300", f"{columna} >500"
    m["Diferencia (>300 − >500)"] = (m[c300] - m[c500]).round(2)
    m = m.rename(columns={c300: ">300 €", c500: ">500 €"})
    return m


# ─── Impresión legible ──────────────────────────────────────────────────────

def _fmt(v) -> str:
    if isinstance(v, float):
        s = f"{v:,.2f}"
    elif isinstance(v, int):
        s = f"{v:,}"
    else:
        return str(v)
    return s.replace(",", "X").replace(".", ",").replace("X", ".")  # estilo europeo


def mostrar(titulo: str, tabla: pd.DataFrame) -> None:
    print("\n" + "-" * 70)
    print(titulo)
    print("-" * 70)
    disp = tabla.copy()
    for c in disp.columns:
        if c != "Territorio":
            disp[c] = disp[c].map(_fmt)
    print(disp.to_string(index=False))


# ─── Main ───────────────────────────────────────────────────────────────────

def main() -> None:
    df = cargar()
    df = paso0(df)

    base = agrupar(df[df["IMP_AYUDA_TOTAL"] > 300], con_derechos=True)
    b300 = agrupar(df[df["IMP_AYUDA_TOTAL"] > 300], con_derechos=False)
    b500 = agrupar(df[df["IMP_AYUDA_TOTAL"] > 500], con_derechos=False)

    cuadro1 = cuadro(b300, b500, "Nº beneficiarios")
    cuadro2 = cuadro(b300, b500, "Superficie total (ha, post-CAP)")
    cuadro3 = cuadro(b300, b500, "Importe medio (€/benef.)")

    mostrar("ANÁLISIS BASE — ayuda total > 300 €", base)
    mostrar("CUADRO 1 — Nº de beneficiarios (>300 vs >500)", cuadro1)
    mostrar("CUADRO 2 — Superficie total post-CAP en ha (>300 vs >500)", cuadro2)
    mostrar("CUADRO 3 — Importe medio por explotación € (>300 vs >500)", cuadro3)

    with pd.ExcelWriter(SALIDA, engine="openpyxl") as xw:
        base.to_excel(xw, sheet_name="Base_300", index=False)
        cuadro1.to_excel(xw, sheet_name="C1_beneficiarios", index=False)
        cuadro2.to_excel(xw, sheet_name="C2_superficie", index=False)
        cuadro3.to_excel(xw, sheet_name="C3_importe_medio", index=False)

    print(f"\n[OK] Excel guardado en: {SALIDA}")


if __name__ == "__main__":
    main()
