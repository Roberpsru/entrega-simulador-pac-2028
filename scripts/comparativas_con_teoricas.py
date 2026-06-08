"""ENTREGABLES (NUEVOS) — comparativas de superficie adicional CON explotaciones teoricas.

Cuatro escenarios. En el escenario B el numero de explotaciones pasa a ser:
    existentes (supervivientes del escenario) + teoricas nuevas de los cultivos externos.
La superficie NO cambia (Cuadro 2 identico al Excel actual). Cambian el numero de
explotaciones (Cuadro 1) y el importe medio (Cuadro 3). La columna A (>300, foto de hoy)
se mantiene igual que en los Excel actuales (6.333 explot., 139.068,13 ha, 6.687,69 EUR),
sin teoricas.

Las teoricas salen SOLO de los cultivos externos (viñedo, frutales, horticolas):
    teoricas_categoria = (potencial SIGPAC - declarado base amplia) / superficie media
La reactivacion de ABRS sin derecho NO crea explotaciones (titulares ya existentes).
El total Euskadi de teoricas es ~6.124 en los cuatro (maxes y sup_media son invariantes
al escenario). El reparto por territorio sigue la huella de cultivo de cada escenario.

REUTILIZA el motor real src.simulation.simular_superficie y las funciones validadas de
entregables_300_500.py. Reproduce la logica de externas/teoricas de:
  comparativa_sup_adicional.py (E5), comparativa_300_vs_500_sup_adicional.py (E6),
  comparativa_300_vs_1000_sup_adicional.py (E7), comparativa_300_vs_500_sup_adicional_menor65.py (E8).

Uso:
  python scripts/comparativas_con_teoricas.py            -> CHECKPOINT (no escribe Excel)
  python scripts/comparativas_con_teoricas.py --generar  -> genera los cuatro Excel
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

PRESUPUESTO_REF = 42353115.52
TERRS = ["Araba", "Gipuzkoa", "Bizkaia"]
ORDEN = ["Araba", "Gipuzkoa", "Bizkaia", "Euskadi"]
CAT_SIGPAC = {
    "Viñedo y Txakoli": "VIÑEDO Y TXAKOLI",
    "Frutales y frutos secos": "FRUTALES Y FRUTOS SECOS",
    "Hortícolas": "HORTICOLA",
}

# Escenarios: clave, etiqueta de columna B, umbral, modo activos, base de reparto
# territorial de externas ("benef" = base amplia >0 ; "act" = supervivientes),
# filtro de edad <65, nombre de Excel y hoja.
ESCENARIOS = [
    dict(key="E5", etq=">300 + sup. adicional", umbral=300, incluir_igual=True,
         reparto="benef", edad65=False,
         out="comparativa_300_vs_300_superficie_adicional_con_teoricas.xlsx",
         hoja="Comp_300_vs_300_con_teoricas"),
    dict(key="E6", etq=">500 + sup. adicional", umbral=500, incluir_igual=False,
         reparto="act", edad65=False,
         out="comparativa_300_vs_500_superficie_adicional_con_teoricas.xlsx",
         hoja="Comp_300_vs_500_con_teoricas"),
    dict(key="E7", etq=">1000 + sup. adicional", umbral=1000, incluir_igual=False,
         reparto="act", edad65=False,
         out="comparativa_300_vs_1000_superficie_adicional_con_teoricas.xlsx",
         hoja="Comp_300_vs_1000_con_teoricas"),
    dict(key="E8", etq=">500 + sup. adicional + <65", umbral=500, incluir_igual=False,
         reparto="act", edad65=True,
         out="comparativa_300_vs_500_sup_adicional_menor65_con_teoricas.xlsx",
         hoja="Comp_300_vs_500_supadic_m65_con_teoricas"),
]

# Anclajes de validacion (Euskadi) que pasa el usuario.
ANCLAS = {
    "E5": dict(total_con_teor=12457, medio_con_teor=3399.95, sup=159302.93),
    "E6": dict(total_con_teor=11843, medio_con_teor=3576.22, sup=157914.73),
    "E7": dict(total_con_teor=10549, medio_con_teor=4014.89, sup=153049.83),
    "E8": dict(total_con_teor=10041, medio_con_teor=4218.02, sup=136369.16),
}
EDAD_CORTE = 65


def _eu(v):
    return (f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if isinstance(v, (int, float)) else str(v))


def _mi(v):  # entero con separador de miles europeo
    return f"{int(round(v)):,}".replace(",", ".")


def reparto_entero(floats: dict, total_int: int) -> dict:
    """Reparte `total_int` unidades enteras entre las claves de `floats` por el
    metodo del resto mayor, de modo que la suma de enteros = total_int exacto."""
    res = {t: int(floats[t]) for t in floats}          # parte entera (floor para no negativos)
    rem = total_int - sum(res.values())
    orden = sorted(floats, key=lambda t: floats[t] - int(floats[t]), reverse=True)
    i = 0
    while rem > 0 and orden:
        res[orden[i % len(orden)]] += 1
        rem -= 1
        i += 1
    while rem < 0:
        for t in sorted(floats, key=lambda t: floats[t] - int(floats[t])):
            if res[t] > 0:
                res[t] -= 1
                rem += 1
                break
    return res


# ─── Escenario B generico (reproduce la logica de los originales) ─────────────

def escenario_b(df: pd.DataFrame, esc: dict) -> dict:
    benef = df[df["IMP_AYUDA_TOTAL"] > 0].copy()
    presupuesto = float(benef["IMP_AYUDA_TOTAL"].sum())
    umbral = esc["umbral"]

    # Conjunto activo de B (supervivientes del escenario)
    if esc["incluir_igual"]:
        act = benef[benef["IMP_AYUDA_TOTAL"] >= umbral].copy()
    else:
        act = benef[benef["IMP_AYUDA_TOTAL"] > umbral].copy()
    if esc["edad65"]:
        es_fis = (act["ES_PERSONA_FISICA"].fillna(False)
                  if "ES_PERSONA_FISICA" in act else pd.Series(True, index=act.index))
        mask_65 = (act["EDAD"] >= EDAD_CORTE) & es_fis
        act = act[~mask_65].copy()

    sup_max = pd.read_excel(RAIZ / "data" / "SUP_MAX_SIGPAC.xlsx", sheet_name="Superficie")
    cult = pd.read_excel(RAIZ / "data" / "Tabla_Cultivos_PAC.xlsx", sheet_name="Sup")

    base_split = benef if esc["reparto"] == "benef" else act

    ha_cat_terr, maxes, sup_media, n_explot_cat = {}, {}, {}, {}
    n_teor_cat_terr = {}
    for tipo, col in CAT_SIGPAC.items():
        sig = float(sup_max[col].sum())
        cols_ok = [c for c in cult[cult[col] == "SI"]["Unnamed: 0"].tolist()
                   if c in benef.columns]
        decl_full = float(benef[cols_ok].sum().sum()) if cols_ok else 0.0   # base amplia >0
        maxes[tipo] = max(0.0, sig - decl_full)

        decl_split = float(base_split[cols_ok].sum().sum()) if cols_ok else 0.0
        real_th = (base_split.assign(_s=base_split[cols_ok].fillna(0).sum(axis=1))
                   .groupby("TH_DESC")["_s"].sum()) if cols_ok else pd.Series(dtype=float)
        ha_cat_terr[tipo] = {
            t: (maxes[tipo] * float(real_th.get(t, 0.0)) / decl_split if decl_split > 0 else 0.0)
            for t in TERRS
        }

        # superficie media (base amplia >0) -> explotaciones teoricas
        spt = benef[cols_ok].fillna(0).sum(axis=1) if cols_ok else pd.Series(dtype=float)
        n_act = int((spt > 0).sum()) if len(spt) else 0
        sup_media[tipo] = (float(spt.sum()) / n_act) if n_act else 0.0
        n_explot_cat[tipo] = (maxes[tipo] / sup_media[tipo]) if sup_media[tipo] else 0.0
        n_teor_cat_terr[tipo] = {
            t: (ha_cat_terr[tipo][t] / sup_media[tipo]) if sup_media[tipo] else 0.0
            for t in TERRS
        }

    ha_terr = {t: sum(ha_cat_terr[tipo][t] for tipo in CAT_SIGPAC) for t in TERRS}
    total_externas = sum(maxes.values())

    # ABRS sin derecho: exceso completo del conjunto activo (reactivacion 100 %)
    exc_series = (act["SUP_Det_Ctr_ABRS"].fillna(0) - act["DERECHOS"].fillna(0)).clip(lower=0)
    exceso_total = float(exc_series.sum())

    df_act, vh, _ = simular_superficie(
        act, total_externas, presupuesto_total=presupuesto,
        ha_abrs_sin_derecho_reactivada=exceso_total,
    )

    # Existentes (supervivientes activos) y superficie activada por territorio
    existentes, sup_b = {}, {}
    for terr in TERRS:
        act_t = df_act[(df_act["TH_DESC"] == terr) & (df_act["IMP_SIMULADO"] > 0)]
        existentes[terr] = int(len(act_t))
        sup_b[terr] = float(act_t["SUP_ACTIVABLE"].fillna(0).sum()) + ha_terr[terr]
    existentes["Euskadi"] = sum(existentes[t] for t in TERRS)
    sup_b["Euskadi"] = sum(sup_b[t] for t in TERRS)

    # Teoricas enteras por categoria y territorio, TOTALMENTE ADITIVAS:
    #   - total Euskadi de cada categoria = round(n_explot_cat[tipo])  (invariante al
    #     escenario; es el valor de los anclajes: 103 + 4.674 + 1.347 = 6.124)
    #   - reparto territorial por resto mayor para que sume ese entero exacto
    teor_cat_int = {tipo: int(round(n_explot_cat[tipo])) for tipo in CAT_SIGPAC}
    cell = {tipo: reparto_entero({t: n_teor_cat_terr[tipo][t] for t in TERRS},
                                 teor_cat_int[tipo]) for tipo in CAT_SIGPAC}
    teor = {t: sum(cell[tipo][t] for tipo in CAT_SIGPAC) for t in TERRS}
    teor["Euskadi"] = sum(teor_cat_int[tipo] for tipo in CAT_SIGPAC)

    return dict(
        existentes=existentes, sup_b=sup_b, teor=teor, vh=vh,
        presupuesto=presupuesto, total_externas=total_externas, exceso_total=exceso_total,
        n_teor_cat_terr=n_teor_cat_terr, n_explot_cat=n_explot_cat, sup_media=sup_media,
        teor_cat_int=teor_cat_int, cell=cell, n_act=int(len(act)),
    )


# ─── Cuadros con teoricas ─────────────────────────────────────────────────────

def cuadro1(sim_a, b, etq):
    a = sim_a.set_index("Territorio")["Nº de beneficiarios"]
    fa = [int(a[t]) for t in ORDEN]
    fb = [b["existentes"][t] + b["teor"][t] for t in ORDEN]
    return pd.DataFrame({
        "Territorio": ORDEN,
        ">300": fa,
        etq: fb,
        "Diferencia (A - B)": [fa[i] - fb[i] for i in range(len(ORDEN))],
    })


def cuadro2(sim_a, b, etq):
    a = sim_a.set_index("Territorio")["Superficie activada (ha)"]
    fa = [round(float(a[t]), 2) for t in ORDEN]
    fb = [round(float(b["sup_b"][t]), 2) for t in ORDEN]
    return pd.DataFrame({
        "Territorio": ORDEN,
        ">300": fa,
        etq: fb,
        "Diferencia (A - B)": [round(fa[i] - fb[i], 2) for i in range(len(ORDEN))],
    })


def importe_medio_b(b):
    """Importe medio por territorio (con teoricas) segun la mecanica del simulador."""
    med = {}
    for t in TERRS:
        den = b["existentes"][t] + b["teor"][t]
        med[t] = (b["vh"] * b["sup_b"][t] / den) if den else 0.0
    den_eus = b["existentes"]["Euskadi"] + b["teor"]["Euskadi"]
    med["Euskadi"] = (b["presupuesto"] / den_eus) if den_eus else 0.0
    return med


def cuadro3(sim_a, b, etq):
    a = sim_a.set_index("Territorio")["Importe medio (€/explot.)"]
    med = importe_medio_b(b)
    fa = [round(float(a[t]), 2) for t in ORDEN]
    fb = [round(float(med[t]), 2) for t in ORDEN]
    return pd.DataFrame({
        "Territorio": ORDEN,
        ">300": fa,
        etq: fb,
        "Diferencia (A - B)": [round(fa[i] - fb[i], 2) for i in range(len(ORDEN))],
    })


def tabla_teoricas(b):
    rep = []
    for t in TERRS:
        fila = {"Territorio": t}
        for tipo in CAT_SIGPAC:
            fila[tipo] = b["cell"][tipo][t]
        fila["TOTAL"] = b["teor"][t]
        rep.append(fila)
    eus = {"Territorio": "Euskadi"}
    for tipo in CAT_SIGPAC:
        eus[tipo] = b["teor_cat_int"][tipo]
    eus["TOTAL"] = b["teor"]["Euskadi"]
    rep.append(eus)
    cols = ["Territorio"] + list(CAT_SIGPAC) + ["TOTAL"]
    return pd.DataFrame(rep)[cols]


def nota(esc, b):
    etq = esc["etq"]
    teor_eus = b["teor"]["Euskadi"]
    med = importe_medio_b(b)
    existentes_eus = b["existentes"]["Euskadi"]
    return (
        f"NOTA — En el escenario B ({etq}) el numero de explotaciones pasa a ser "
        f"EXISTENTES + TEORICAS NUEVAS. Las teoricas ({_mi(teor_eus)} en Euskadi) proceden "
        "SOLO de los cultivos externos (viñedo y txakoli, frutales y frutos secos, "
        "horticolas): teoricas = (potencial SIGPAC - superficie ya declarada) / superficie "
        "media por explotacion de cada categoria, sin aplicar umbral (se cuentan todas). La "
        "reactivacion de la ABRS sin derecho NO crea explotaciones nuevas (es superficie de "
        "titulares ya existentes). La superficie activada (Cuadro 2) es identica al Excel sin "
        f"teoricas; solo cambian el numero de explotaciones (Cuadro 1) y el importe medio "
        f"(Cuadro 3). Importe medio Euskadi con teoricas = presupuesto ({_eu(b['presupuesto'])} "
        f"EUR) / ({_mi(existentes_eus)} existentes + {_mi(teor_eus)} teoricas) = "
        f"{_eu(med['Euskadi'])} EUR. La columna >300 (A) es la foto actual, sin teoricas."
    )


# ─── Validacion ───────────────────────────────────────────────────────────────

def validar_con_teoricas(esc, b):
    anc = ANCLAS[esc["key"]]
    med = importe_medio_b(b)
    teor_eus = b["teor"]["Euskadi"]
    total = b["existentes"]["Euskadi"] + teor_eus
    sup_eus = b["sup_b"]["Euskadi"]
    print(f"\n  VALIDACION {esc['key']} (Euskadi):")
    print(f"    Teoricas               : {teor_eus:>8}      (esp ~6.124)")
    print(f"    Total con teoricas     : {total:>8}      (esp ~{anc['total_con_teor']})  "
          f"[existentes {b['existentes']['Euskadi']} + teoricas {teor_eus}]")
    print(f"    Importe medio con teor : {med['Euskadi']:>11,.2f} (esp ~{anc['medio_con_teor']:,.2f})")
    print(f"    Superficie activada    : {sup_eus:>14,.2f} (esp {anc['sup']:,.2f})")
    ok_teor = abs(teor_eus - 6124) <= 5
    ok_total = abs(total - anc["total_con_teor"]) <= 5
    ok_med = abs(med["Euskadi"] - anc["medio_con_teor"]) <= 1.0
    ok_sup = abs(sup_eus - anc["sup"]) <= 0.05
    estado = all([ok_teor, ok_total, ok_med, ok_sup])
    print(f"    -> {'OK' if estado else 'DISCREPANCIA'}  "
          f"(teor {ok_teor}, total {ok_total}, medio {ok_med}, sup {ok_sup})")
    return estado


# ─── Escritura de Excel (solo con --generar tras el OK) ──────────────────────

def escribir_excel(esc, c1, c2, c3, tteor, NOTA):
    out = RAIZ / esc["out"]
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        hoja = esc["hoja"]
        fila = 0
        bloques = [
            ("CUADRO 1 - Nº de explotaciones (existentes + teóricas nuevas)", c1),
            ("CUADRO 2 - Superficie activada (ha) (idéntico al Excel sin teóricas)", c2),
            ("CUADRO 3 - Importe medio por explotación (€) (con teóricas)", c3),
            ("Explotaciones teóricas nuevas por territorio", tteor),
        ]
        for titulo, cdf in bloques:
            pd.DataFrame([[titulo]]).to_excel(
                xw, sheet_name=hoja, startrow=fila, startcol=0, index=False, header=False)
            fila += 1
            cdf.to_excel(xw, sheet_name=hoja, startrow=fila, index=False)
            fila += len(cdf) + 2
        pd.DataFrame([["NOTA:"], [NOTA]]).to_excel(
            xw, sheet_name=hoja, startrow=fila, startcol=0, index=False, header=False)
    print(f"  [OK] Guardado: {out}")


def main():
    generar = "--generar" in sys.argv
    df = cargar()

    sim_a = correr_simulador(df, 300)
    if not validar(sim_a):
        print("\n*** PARADA: A (>300) no coincide con los anclajes del motor. ***")
        sys.exit(1)

    todo_ok = True
    resultados = []
    for esc in ESCENARIOS:
        b = escenario_b(df, esc)
        c1 = cuadro1(sim_a, b, esc["etq"])
        c2 = cuadro2(sim_a, b, esc["etq"])
        c3 = cuadro3(sim_a, b, esc["etq"])
        tteor = tabla_teoricas(b)
        NOTA = nota(esc, b)

        print("\n" + "=" * 72)
        print(f"ESCENARIO {esc['key']} — A=>300  vs  B={esc['etq']}  (con teoricas)")
        print(f"  supervivientes activos en B: {b['n_act']}   valor/ha (tasa) = {b['vh']:,.2f}")
        print("=" * 72)
        mostrar("CUADRO 1 - Nº de explotaciones (existentes + teoricas nuevas)", c1)
        mostrar("CUADRO 2 - Superficie activada (ha) (identico al Excel sin teoricas)", c2)
        mostrar("CUADRO 3 - Importe medio por explotacion (EUR) (con teoricas)", c3)
        mostrar("Explotaciones teoricas nuevas por territorio (y categoria)", tteor)
        print("\n  " + NOTA)
        ok = validar_con_teoricas(esc, b)
        todo_ok = todo_ok and ok
        resultados.append((esc, c1, c2, c3, tteor, NOTA))

    print("\n" + "=" * 72)
    print(f"RESUMEN VALIDACION: {'TODO COINCIDE CON LOS ANCLAJES' if todo_ok else 'HAY DISCREPANCIAS'}")
    print("=" * 72)

    if not generar:
        print("\n[CHECKPOINT] No se ha escrito ningun Excel. Esperando el OK explicito.")
        return
    if not todo_ok:
        print("\n*** PARADA: hay discrepancias con los anclajes. No se escribe nada. ***")
        sys.exit(1)
    print("\nGenerando los cuatro Excel nuevos (con sufijo _con_teoricas)...")
    for esc, c1, c2, c3, tteor, NOTA in resultados:
        escribir_excel(esc, c1, c2, c3, tteor, NOTA)


if __name__ == "__main__":
    main()
