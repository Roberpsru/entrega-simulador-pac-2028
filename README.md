# Simulador PAC Euskadi 2028-2032

> Aplicación interactiva para apoyar la toma de decisiones sobre el diseño de la Política Agraria Común en el País Vasco, a partir de los datos reales de pagos directos de la campaña 2024.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.57+-FF4B4B.svg)](https://streamlit.io)

---

## ⚠️ Aviso previo: fichero de datos necesario

Antes de ejecutar la aplicación, coloca en la carpeta `data/` el fichero maestro:

```
data/TABLA_GENERAL_PAGOS_DIRECTOS_2024_ANONIMIZADA.xlsx
```

Este archivo contiene el padrón de 7.283 titulares (versión anonimizada, sin NIF ni nombre del titular). También deben estar presentes:

| Fichero | Descripción |
|---|---|
| `data/TABLA_GENERAL_PAGOS_DIRECTOS_2024_ANONIMIZADA.xlsx` | Tabla maestra de pagos directos 2024 |
| `data/SIGPAC.xlsx` | Superficies admisibles PAC por uso y territorio |
| `data/VALOR_MEDIO_REGIONES_ABRS.xlsx` | Valor medio por región agronómica |

---

## ¿Qué es?

Una aplicación web Streamlit que permite **consultar** la distribución actual de las ayudas directas de la PAC en Euskadi y **simular reformas** para el período de programación 2028-2032, manteniendo el presupuesto global constante.

**Esta versión no incluye los botones de análisis con IA** ("Aspectos a tener en cuenta") y no requiere API key de Anthropic.

## Cifras clave (campaña 2024)

| Métrica | Valor |
|---|---|
| Titulares activos | 7.283 |
| Importe total de ayudas | 42.353.115,52 € |
| Superficie declarada | 257.360,88 ha |
| Territorios | Araba (1.634) · Gipuzkoa (3.025) · Bizkaia (2.624) |

## Módulos

- **Inicio** — página institucional
- **Consulta** — exploración del padrón 2024 con filtros multidimensionales
- **Simulador** — reformas a presupuesto constante (umbral mínimo + nueva superficie)
- **Guía metodológica** — contexto, decisiones de diseño y limitaciones

## Instalación local

Requisitos previos: Python 3.11+ y Git.

```bash
# Clonar o descomprimir el proyecto
cd entrega-simulador-pac-2028

# Crear y activar entorno virtual
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
```

La app se abre en `http://localhost:8501`.

## Despliegue en Streamlit Cloud

1. Sube el repositorio a tu cuenta de GitHub (asegúrate de incluir los ficheros `data/*.xlsx`).
2. Entra en [share.streamlit.io](https://share.streamlit.io), pulsa **Create app**.
3. Selecciona el repositorio, rama `main` y archivo `app.py`.
4. No es necesario configurar ningún secret (sin API key).

## Estructura

```
entrega-simulador-pac-2028/
├── app.py                    # Inicio (landing institucional)
├── pages/
│   ├── 1_Consulta.py         # Análisis con filtros multidimensionales
│   ├── 2_Simulador.py        # Simulador de reformas
│   └── 3_Guía.py             # Guía metodológica
├── src/
│   ├── data.py               # Carga y caché de los xlsx
│   ├── derived.py            # Variables derivadas
│   ├── simulation.py         # Algoritmo de redistribución
│   └── ui.py                 # Helpers de UI, formato y estilos
├── data/                     # Aquí van los xlsx (NO subir versión con NIF)
├── .streamlit/config.toml    # Tema verde
├── .python-version           # 3.12 (para Streamlit Cloud)
└── requirements.txt
```

## Metodología

Las simulaciones adoptan un **modelo de pago único por superficie ABRS**: el presupuesto total se divide entre la superficie ABRS elegible (incluida la que carece de derechos) más la nueva superficie externa incorporada. La lógica está en `src/simulation.py`.

La aplicación es un **apoyo a la decisión**, no una herramienta normativa.

---

Desarrollado por **Hazi** para el Departamento de Desarrollo Económico, Sostenibilidad y Medio Ambiente del Gobierno Vasco.
