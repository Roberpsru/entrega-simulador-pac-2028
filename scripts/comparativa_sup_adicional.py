"""ENTREGABLE — >300  vs  >300 + superficie adicional (REPARTO REAL POR TITULAR).

Escenario A: umbral 300 (como la app).
Escenario B: umbral 300 + incorporación de superficie de viñedo/txakoli, frutales/
frutos secos y hortícolas al máximo del Filtro B, REPARTIDA ENTRE TERRITORIOS SEGÚN
LA SUPERFICIE DE CULTIVO REALMENTE DECLARADA POR TITULAR EN CADA TH (no por proporción
SIGPAC). La ABRS sin derecho NO se vuelve a sumar (ya está en la superficie activada de A).

Reutiliza el motor real src.simulation.simular_superficie, calcular_derivadas, y las
funciones cargar/validar/mostrar de entregables_300_500.py. La distribución real por
titular replica la lógica de scripts/reparto_externas_real.py. src/kpis.py no existe.

Decisión de modelado: los cuadros mantienen el nº de explotaciones EXISTENTES (no se
añaden nuevas). La NOTA estima las nuevas teóricas y su efecto en el importe medio.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ))

from entregables_300_500 import cargar, validar, mostrar   # noqa: E402
from src.simulation import simular_superficie              # noqa: E402
from comparativa_edad_65 import simular                     # noqa: E402

OUT = RAIZ / "comparativa_300_vs_300_superficie_adicional.xlsx"
UMBRAL = 300
TERRS = ["Araba", "Gipuzkoa", "Bizkaia"]
ORDEN = ["Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]
CAT_SIGPAC = {
    "Viñedo y Txakoli": "VIÑEDO Y TXAKOLI",
    "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
    "Hortícolas": "HORTICOLA",
}
# Validación B: superficie activada esperada por territorio
VALID_B = {"Araba": 97141.50, "Gipuzkoa": 33399.21, "Bizkaia": 28762.22, "Euskadi": 159302.93}


def main():
    df = cargar()
    benef = df[df["IMP_AYUDA_TOTAL"] > 0].copy()
    activos = benef[benef["IMP_AYUDA_TOTAL"] >= UMBRAL].copy()
    presupuesto = float(benef["IMP_AYUDA_TOTAL"].sum())
    sup_max = pd.read_excel(RAIZ / "data" / "SUP_MAX_SIGPAC.xlsx", sheet_name="Superficie")
    cult = pd.read_excel(RAIZ / "data" / "Tabla_Cultivos_PAC.xlsx", sheet_name="Sup")

    # ── Filtro B: máximo por categoría + reparto REAL POR TITULAR por TH ──
    ha_cat_terr, maxes, n_explot_cat = {}, {}, {}
    for tipo, col in CAT_SIGPAC.items():
        sig = float(sup_max[col].sum())
        cols_ok = [c for c in cult[cult[col] == "SI"]["Unnamed: 0"].tolist() if c in benef.columns]
        decl = float(benef[cols_ok].sum().sum()) if cols_ok else 0.0
        maxes[tipo] = max(0.0, sig - decl)
        # superficie real declarada por TH (suma de columnas de cultivo agrupada por TH)
        real_th = (benef.assign(_s=benef[cols_ok].fillna(0).sum(axis=1))
                   .groupby("TH_DESC")["_s"].sum()) if cols_ok else pd.Series(dtype=float)
        ha_cat_terr[tipo] = {
            t: (maxes[tipo] * float(real_th.get(t, 0.0)) / decl if decl > 0 else 0.0) for t in TERRS
        }
        spt = benef[cols_ok].fillna(0).sum(axis=1) if cols_ok else pd.Series(dtype=float)
        n_act = int((spt > 0).sum()) if len(spt) else 0
        sup_media = (float(spt.sum()) / n_act) if n_act else 0.0
        n_explot_cat[tipo] = (maxes[tipo] / sup_media) if sup_media else 0.0

    ha_terr = {t: sum(ha_cat_terr[tipo][t] for tipo in CAT_SIGPAC) for t in TERRS}
    total_externas = sum(maxes.values())
    max_abrs = float((activos["SUP_Det_Ctr_ABRS"].fillna(0) - activos["DERECHOS"].fillna(0)).clip(lower=0).sum())

    # ── Validación A ──
    sim_a = simular(df, lambda b: b["IMP_AYUDA_TOTAL"] < UMBRAL)
    if not validar(sim_a):
        print("\n*** PARADA: A no coincide con la app. ***"); sys.exit(1)

    # ── B: motor con superficie externa al denominador (escalar total) ──
    df_act, vh, _ = simular_superficie(activos, total_externas, presupuesto_total=presupuesto)

    filas, sup_ex_terr = {}, {}
    for terr in TERRS:
        act_t = df_act[(df_act["TH_DESC"] == terr) & (df_act["IMP_SIMULADO"] > 0)]
        benef_ex = int(len(act_t))
        sup_ex = float(act_t["SUP_Det_Ctr_ABRS"].fillna(0).sum())
        sup_ex_terr[terr] = sup_ex
        ra = sim_a.set_index("Territorio").loc[terr]
        filas[terr] = dict(
            benef_a=int(ra["Nº de beneficiarios"]), benef_b=benef_ex,
            sup_a=float(ra["Superficie activada (ha)"]), sup_b=sup_ex + ha_terr[terr],
            medio_a=float(ra["Importe medio (€/explot.)"]),
            medio_b=float(act_t["IMP_SIMULADO"].mean()) if benef_ex else 0.0,
        )
    eus = dict(
        benef_a=sum(filas[t]["benef_a"] for t in TERRS), benef_b=sum(filas[t]["benef_b"] for t in TERRS),
        sup_a=sum(filas[t]["sup_a"] for t in TERRS), sup_b=sum(filas[t]["sup_b"] for t in TERRS),
        medio_a=presupuesto / sum(filas[t]["benef_a"] for t in TERRS),
        medio_b=(sum(sup_ex_terr.values()) * vh) / sum(filas[t]["benef_b"] for t in TERRS),
    )
    filas["Euskadi"] = eus

    # ── Validación B (superficie activada por territorio, reparto real) ──
    print("\n" + "=" * 72 + "\nVALIDACIÓN B — superficie activada (reparto real por titular)\n" + "=" * 72)
    okB = True
    for terr in ORDEN:
        got = round(filas[terr]["sup_b"], 2); exp = VALID_B[terr]
        estado = "OK" if abs(got - exp) <= 0.02 else "DISCREPANCIA"  # tol. redondeo 2 decimales
        if estado != "OK":
            okB = False
        print(f"  {terr:<9} activada {got:>12,.2f} (esp {exp:>12,.2f}) -> {estado}")
    if not okB:
        print("\n*** PARADA: B no coincide. ***"); sys.exit(1)
    print("  RESULTADO: TODO COINCIDE")

    # ── Cuadros ──
    def cuadro(ka, kb):
        return pd.DataFrame({
            "Territorio": ORDEN,
            ">300": [round(filas[t][ka], 2) for t in ORDEN],
            ">300 + sup. adicional": [round(filas[t][kb], 2) for t in ORDEN],
            "Diferencia (A − B)": [round(filas[t][ka] - filas[t][kb], 2) for t in ORDEN],
        })
    c1, c2, c3 = cuadro("benef_a", "benef_b"), cuadro("sup_a", "sup_b"), cuadro("medio_a", "medio_b")

    # ── Tabla de reparto por categoría (dato real por titular) ──
    rep = []
    for tipo in CAT_SIGPAC:
        fila = {"Categoría": tipo, "Método": "Dato real por titular"}
        for t in TERRS:
            fila[t] = round(ha_cat_terr[tipo][t], 2)
        fila["Euskadi"] = round(sum(ha_cat_terr[tipo][t] for t in TERRS), 2)
        rep.append(fila)
    rep.append({"Categoría": "TOTAL externas", "Método": "—",
                **{t: round(sum(ha_cat_terr[tipo][t] for tipo in CAT_SIGPAC), 2) for t in TERRS},
                "Euskadi": round(total_externas, 2)})
    reparto = pd.DataFrame(rep)[["Categoría", "Método", "Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]]

    # ── NOTA ──
    total_nuevas = sum(int(round(n_explot_cat[t])) for t in CAT_SIGPAC)
    medio_con_nuevas = (eus["sup_b"] * vh) / (eus["benef_b"] + total_nuevas)

    def _i(n):
        return f"{int(round(n)):,}".replace(",", ".")

    def _e(v):
        return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    NOTA = (
        "NOTA 1 — La superficie ABRS sin derecho NO se suma en B: ya está incluida en la "
        f"superficie activada del Escenario A ({_e(eus['sup_a'])} ha). En la base >300 asciende "
        f"a {_e(max_abrs)} ha. En B solo se incorporan los cultivos externos ({_e(total_externas)} ha).  "
        "NOTA 2 — Las externas se reparten por territorio según el DATO REAL POR TITULAR "
        "(superficie de cultivo declarada en cada TH), no por proporción SIGPAC.  "
        "NOTA 3 — Los cuadros mantienen las explotaciones EXISTENTES. Esa superficie generaría "
        f"~{_i(total_nuevas)} explotaciones teóricas nuevas (sobre todo frutales y hortícolas de "
        f"tamaño muy pequeño); si se contaran, el importe medio en Euskadi caería de "
        f"~{_e(eus['medio_b'])} € a ~{_e(medio_con_nuevas)} €, por repartir el mismo presupuesto "
        "(42.353.115,52 €) entre muchas más explotaciones."
    )

    # ── Mostrar ──
    print(f"\n  Valor/ha: A = {presupuesto/float(activos['SUP_Det_Ctr_ABRS'].fillna(0).sum()):,.2f}  ->  B = {vh:,.2f}")
    mostrar("CUADRO 1 — Nº de beneficiarios (existentes)", c1)
    mostrar("CUADRO 2 — Superficie activada (ha)", c2)
    mostrar("CUADRO 3 — Importe medio por explotación (€)", c3)
    mostrar("REPARTO de la superficie incorporada por categoría y territorio (dato real)", reparto)
    print("\n" + NOTA)

    # ── Excel: TODO en una sola hoja, apilado ──
    with pd.ExcelWriter(OUT, engine="openpyxl") as xw:
        hoja = "Comp_300_vs_sup_adicional"
        fila = 0
        bloques = [
            ("CUADRO 1 — Nº de beneficiarios (existentes)", c1),
            ("CUADRO 2 — Superficie activada (ha)", c2),
            ("CUADRO 3 — Importe medio por explotación (€)", c3),
            ("REPARTO de la superficie incorporada por categoría y territorio (dato real por titular)", reparto),
        ]
        for titulo, cdf in bloques:
            pd.DataFrame([[titulo]]).to_excel(xw, sheet_name=hoja, startrow=fila, startcol=0, index=False, header=False)
            fila += 1
            cdf.to_excel(xw, sheet_name=hoja, startrow=fila, index=False)
            fila += len(cdf) + 2
        pd.DataFrame([["NOTA:"], [NOTA]]).to_excel(xw, sheet_name=hoja, startrow=fila, startcol=0, index=False, header=False)
    print(f"\n[OK] Guardado (sobrescrito): {OUT}")


if __name__ == "__main__":
    main()
