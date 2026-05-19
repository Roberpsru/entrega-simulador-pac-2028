"""Guía metodológica del Simulador PAC Euskadi 2028-2032."""
import streamlit as st
from src.ui import (
    AZUL_CLARO, AZUL_SECUND, VERDE_CLARO, VERDE_OSCURO,
    aplicar_estilos_pagina, titulo_bloque, titulo_subapartado,
)

st.set_page_config(page_title="Guia · PAC Euskadi", layout="wide")
aplicar_estilos_pagina()

st.title("Guía metodológica")
st.caption(
    "Contexto, criterios de diseño, contenido de cada módulo y "
    "limitaciones conocidas de la herramienta."
)


titulo_bloque("Sobre los datos de la campaña 2024", bg="#4a4a4a")

st.markdown("""
<div style="font-size:15px; line-height:1.6; color:#222; text-align:justify;">
<p style="margin:0 0 0.6rem 0;">
La aplicación trabaja con los datos reales de los pagos directos de la PAC en Euskadi
correspondientes a la campaña 2024. La información de partida procede del padrón de
titulares relacionados con la PAC en el ejercicio 2024, que contiene <b>7.692 registros</b>.
De ese conjunto, el análisis se realiza sobre <b>7.283 titulares (94,7 %)</b>, que son
aquellos que efectivamente percibieron alguna ayuda en la campaña y cuentan con los datos
completos para el análisis.
</p>
<p style="margin:0 0 0.6rem 0;">
Se han excluido <b>409 registros (5,3 %)</b> que figuran en el padrón pero no aportan
valor económico al análisis de la campaña 2024:
</p>
<ul style="margin:0 0 0.6rem 1.2rem; padding:0;">
<li style="margin-bottom:0.3rem;">362 titulares que constaban con derechos asignados pero no percibieron ayudas
en 2024 por diferentes causas.</li>
<li style="margin-bottom:0.3rem;">47 titulares que figuran en el padrón sin derechos asignados y sin percepción
de ningún tipo de ayuda (ni directa, ni asociada agrícola, ni asociada ganadera).</li>
</ul>
<p style="margin:0;">
En ambos casos, el importe cobrado en 2024 es 0 € y no aportan superficie declarada,
animales ni cultivos al análisis. El importe global analizado (<b>42.353.115,52 €</b>)
y la superficie declarada (<b>257.360,88 ha</b>) corresponden íntegramente a los
<b>7.283 titulares activos</b>.
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══ 1. CONTEXTO E IMPULSORES ══════════════════════════════════════════════

titulo_bloque("1. Contexto e impulsores")

st.markdown("""
<div style="font-size:15px; line-height:1.6; color:#222; text-align:justify;">
<p style="margin:0 0 0.6rem 0;">Los pagos directos de la PAC representan el principal instrumento de apoyo a la
renta de las explotaciones agrarias en Euskadi. Con un presupuesto anual de
<b>42,35 millones de euros</b> y <b>7.283 explotaciones beneficiarias</b> en la
campaña 2024, su diseño tiene implicaciones directas sobre la viabilidad económica
de miles de familias agricultoras y ganaderas en Araba, Bizkaia y Gipuzkoa.</p>
<p style="margin:0 0 0.6rem 0;">El horizonte de programación <b>2028-2032</b> abre un proceso de negociación en el
que el Gobierno Vasco —a través del Departamento de Desarrollo Económico,
Sostenibilidad y Medio Ambiente— necesita analizar con rigor las implicaciones de
distintas hipótesis de reforma antes de trasladar sus posiciones al Ministerio de
Agricultura.</p>
<p style="margin:0;">Esta herramienta nace con ese objetivo: <b>apoyar la toma de decisiones técnicas y
políticas a partir de datos reales</b>, con transparencia sobre lo que se puede
calcular y sobre lo que permanece incierto.</p>
</div>
""", unsafe_allow_html=True)


# ═══ 2. POR QUÉ SE HA DISEÑADO ASÍ ════════════════════════════════════════

titulo_bloque("2. Por qué se ha diseñado así")

st.markdown("""
<div style="font-size:15px; line-height:1.6; color:#222; text-align:justify;">
<p style="margin:0 0 0.6rem 0;">El diseño de la herramienta refleja una tensión fundamental: la necesidad de explorar
escenarios de reforma cuando las reglas del juego futuras son en gran medida
<b>desconocidas</b>.</p>
<p style="margin:0 0 0.6rem 0;">No se sabe si la PAC 2028-2032 mantendrá el sistema de derechos históricos, cuántas
regiones agronómicas ABRS existirán, cómo evolucionarán los ecorregímenes, si se
ampliarán las ayudas asociadas o cómo se redistribuirá el complemento para jóvenes.
Esta incertidumbre es genuina y condiciona cualquier ejercicio de simulación.
Además, el Gobierno Vasco no diseña la PAC en exclusiva: la normativa depende de la
negociación europea y de las competencias compartidas con el Ministerio de Agricultura.</p>
<p style="margin:0;">Ante ello se han adoptado las siguientes decisiones metodológicas:</p>
</div>
""", unsafe_allow_html=True)

decisiones = [
    (
        "Presupuesto constante",
        "El total de 42.353.115,52 € se mantiene fijo en todos los escenarios. "
        "Cualquier reforma simulada redistribuye este importe sin crearlo ni destruirlo. "
        "Es la única hipótesis neutral que permite comparar escenarios sin predeterminar "
        "el nivel de financiación futura.",
    ),
    (
        "Modelo de pago único por superficie ABRS",
        "La simulación adopta un valor uniforme por hectárea de superficie ABRS elegible "
        "que integra todos los complementos actuales (básico, redistributivo, jóvenes, "
        "ecorregímenes y asociadas). Se ha elegido este modelo porque permite explorar "
        "escenarios sin predeterminar la estructura futura de líneas de apoyo, que es "
        "completamente desconocida.",
    ),
    (
        "Integración de las ayudas asociadas ganaderas",
        "Las ayudas por animal (vacuno de carne, ovino/caprino y vacuno de leche) "
        "se integran en el valor por hectárea del modelo simulado. En la realidad "
        "se devengan por cabeza de ganado. Esta simplificación introduce una "
        "distorsión que se recoge en una tabla informativa al final del simulador, "
        "donde se muestra la situación actual de estas ayudas por tipo y territorio.",
    ),
    (
        "Diferencias territoriales como estructura, no como privilegio",
        "Las diferencias en el importe medio percibido entre Araba, Bizkaia y Gipuzkoa no reflejan "
        "ningún trato preferente, sino estructuras productivas distintas respaldadas por diferentes "
        "herramientas del Plan Estratégico de la PAC (PEPAC). Araba concentra explotaciones de cereal "
        "y rumiantes con un peso histórico mayor en la Ayuda Básica a la Renta por superficie. "
        "Por el contrario, Bizkaia y Gipuzkoa cuentan con una mayor implantación de la viticultura, "
        "la fruticultura y la horticultura. Estos sectores se canalizan financieramente a través de "
        "las Intervenciones Sectoriales del Primer Pilar (FEAGA) —como los Programas Operativos— "
        "y de las medidas de desarrollo rural del Segundo Pilar (FEADER), en lugar de los pagos "
        "directos tradicionales a la renta.",
    ),
]

for titulo_d, texto_d in decisiones:
    st.markdown(
        f'<div style="background-color:{VERDE_CLARO}; border-left:5px solid {VERDE_OSCURO}; '
        f'border-radius:6px; padding:0.9rem 1.2rem; margin-bottom:0.75rem;">'
        f'<div style="font-size:15px; font-weight:700; color:#1b4332; margin-bottom:0.4rem;">'
        f'{titulo_d}</div>'
        f'<div style="font-size:14px; color:#333; line-height:1.7;">{texto_d}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══ 3. CONTENIDO DE CADA MÓDULO ═══════════════════════════════════════════

titulo_bloque("3. Contenido de cada módulo")

titulo_subapartado("Consulta")

st.markdown("""
<div style="font-size:15px; line-height:1.6; color:#222; text-align:justify;">
<p style="margin:0 0 0.6rem 0;">Permite explorar la distribución actual de los pagos directos aplicando cualquier
combinación de filtros sobre el padrón de la campaña 2024. Los resultados —gráficos,
tablas e indicadores— se recalculan automáticamente sobre el subconjunto seleccionado.</p>
<p style="margin:0 0 0.6rem 0;"><b>Filtros disponibles:</b> territorio, género, tramo de edad, tramo de superficie,
dedicación a la agricultura, condición de agricultor activo, ingresos agrarios
superiores a 15.000 € y condición jurídica.</p>
<p style="margin:0 0 0.6rem 0;"><b>Bloques de análisis:</b> resumen general (derechos, superficie y importes por tipo
y territorio), condición de agricultor activo y elegibilidad, distribución por
territorio y tramos de ayuda, derechos ABRS, tipos de ayuda, perfil de los
beneficiarios (edad, género, formación, dedicación) y distribución por superficie
y cultivos.</p>
<p style="margin:0;">Cada bloque incluye un botón de <b>análisis con inteligencia artificial</b> que
genera un comentario técnico orientado a la toma de decisiones, fundamentado en
la normativa PAC vigente y en los datos del subconjunto seleccionado.</p>
</div>
""", unsafe_allow_html=True)

titulo_subapartado("Simulador")

st.markdown("""
<div style="font-size:15px; line-height:1.6; color:#222; text-align:justify;">
<p style="margin:0 0 0.6rem 0;">Permite explorar el efecto económico de hipótesis de reforma manteniendo el
presupuesto total constante. Los filtros del sidebar definen el colectivo que
participa en el nuevo sistema; las acciones de simulación definen qué cambia.</p>
<p style="margin:0 0 0.6rem 0;"><b>Acción A — Umbral mínimo de ayuda:</b> las explotaciones que reciben menos de
X euros dejan de participar. Su presupuesto se redistribuye proporcionalmente
entre las que permanecen. Permite explorar el efecto de concentrar el apoyo en
explotaciones más profesionales o más dependientes de la PAC.</p>
<p style="margin:0 0 0.6rem 0;"><b>Acción B — Incorporación de superficie adicional:</b> se incorporan nuevas
hectáreas al sistema (viñedo y Txakoli, frutales y frutos secos, hortícolas,
o superficie ABRS sin derecho asignado). El presupuesto total se redistribuye
entre una base mayor de superficie, lo que reduce el valor por hectárea pero
amplía el número de beneficiarios potenciales.</p>
<p style="margin:0;">Ambas acciones pueden combinarse. Los resultados muestran la comparación entre
la situación actual y el escenario simulado a nivel de Euskadi y por territorio
histórico.</p>
</div>
""", unsafe_allow_html=True)


# ═══ 4. LIMITACIONES CONOCIDAS ═════════════════════════════════════════════

titulo_bloque("4. Limitaciones conocidas")

limitaciones = [
    (
        "Incertidumbre normativa",
        "Los escenarios simulados asumen redistribución proporcional en la estructura "
        "de ayudas actual. La redistribución real dependerá de decisiones del "
        "Ministerio de Agricultura que están fuera del alcance del Gobierno Vasco: "
        "no se sabe si se mantendrá el sistema de derechos, cuántas regiones ABRS "
        "existirán, ni cómo se estructurarán los complementos en el nuevo período.",
    ),
    (
        "Nuevas explotaciones por incorporación de superficie",
        "Incorporar viñedo, frutales u hortícolas implica la entrada de explotaciones "
        "actualmente fuera del sistema de pagos directos. Su número real es desconocido "
        "al no existir un directorio actualizado de explotaciones por cultivo. Las "
        "estimaciones de la herramienta se basan en la superficie media actual por tipo "
        "de cultivo y deben interpretarse como orientativas.",
    ),
    (
        "Explotaciones sin superficie ABRS",
        "Algunas explotaciones perciben actualmente ayudas (complemento para jóvenes, "
        "asociadas, ecorregímenes) sin tener superficie ABRS declarada. El modelo de "
        "pago por superficie no puede incorporarlas y las excluye del análisis simulado. "
        "Se identifican explícitamente en los resultados, separadas de las exclusiones "
        "por criterio del usuario.",
    ),
    (
        "Cobertura de datos fiscales",
        "Al 23 % del padrón se cruza sus datos fiscales con las Haciendas Forales. "
        "Los datos de ingresos agrarios y la relación renta agraria / "
        "total deben interpretarse con esta limitación de cobertura.",
    ),
    (
        "Horizonte temporal de los datos",
        "La herramienta trabaja sobre los datos de la campaña 2024. No incluye series "
        "temporales ni permite analizar tendencias interanuales. Los datos son "
        "representativos de la estructura del sector en el período 2023-2027.",
    ),
    (
        "Alcance del simulador",
        "El simulador analiza exclusivamente el efecto sobre el reparto del presupuesto de los pagos "
        "directos desacoplados y acoplados a la renta. No mide el impacto en la renta total de las "
        "explotaciones, ya que la renta agraria final depende de factores ajenos a esta herramienta, "
        "tales como los precios de mercado, los costes de producción, las ayudas al desarrollo rural "
        "del FEADER (Segundo Pilar) y las intervenciones sectoriales del FEAGA (especialmente "
        "relevantes para la viticultura, la fruticultura y la horticultura).",
    ),
]

for titulo_l, texto_l in limitaciones:
    st.markdown(
        f'<div style="background-color:#fef9ec; border-left:5px solid #e07b39; '
        f'border-radius:6px; padding:0.9rem 1.2rem; margin-bottom:0.75rem;">'
        f'<div style="font-size:15px; font-weight:700; color:#8b4513; margin-bottom:0.4rem;">'
        f'{titulo_l}</div>'
        f'<div style="font-size:14px; color:#333; line-height:1.7;">{texto_l}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══ NOTA FINAL ════════════════════════════════════════════════════════════

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    f'<div style="background-color:{AZUL_CLARO}; border-left:6px solid {AZUL_SECUND}; '
    f'border-radius:8px; padding:1.2rem 1.5rem; font-size:14px; '
    f'line-height:1.8; color:#1a1a2e;">'
    f'<b>Nota final.</b> Esta herramienta es un apoyo a la reflexión técnica y '
    f'política. Sus resultados son escenarios hipotéticos que ayudan a anticipar '
    f'efectos, no predicciones normativas ni propuestas oficiales del Gobierno Vasco. '
    f'La decisión final sobre el diseño de la PAC 2028-2032 corresponde al órgano '
    f'competente, en el marco de la normativa europea y de las competencias del '
    f'Gobierno Vasco en materia agraria.'
    f'</div>',
    unsafe_allow_html=True,
)
