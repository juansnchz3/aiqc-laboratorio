# ==============================================================
# AIQC – Panel de resumen (vista semáforo)
#   · construir_resumen()   : matriz analito × nivel con estado y datos
#   · render_overview_panel(): panel nativo (st.markdown, sin iframe)
#
# El panel se dibuja con st.markdown (unsafe_allow_html), NO con
# components.html: así hereda el tema claro de la app en vez de quedar
# aislado en un iframe que seguía el modo oscuro del sistema. Las clases
# CSS (.ov-*) viven en aiqc/styles.py. Sin dependencias de terceros salvo
# streamlit para pintar.
# ==============================================================
import html

import streamlit as st

from .knowledge_base import NIVELES

# Colores por estado (coherentes con styles.py / charts.py).
_COLOR_ESTADO = {
    "Verde": "#0D9E6E",
    "Ámbar": "#F59E0B",
    "Rojo": "#E53E3E",
}
_LED_ESTADO = {"Verde": "🟢", "Ámbar": "🟡", "Rojo": "🔴"}
_ORDEN_NIVEL = {"N": 0, "PB": 1, "PA": 2}


def construir_resumen(eval_completo, r4s_por_analito):
    """Construye la estructura de datos del semáforo a partir de los dicts ya
    evaluados y cacheados en app.py.

    - eval_completo: {(analito, nivel): df evaluado con Westgard}
    - r4s_por_analito: {analito: resultado R-4s (o None)}

    Devuelve una lista de dicts por analito, cada uno con sus niveles y el
    peor estado del analito (para ordenar/colorear la fila).
    """
    analitos = sorted({an for (an, _niv) in eval_completo})
    prioridad = {"Rojo": 2, "Ámbar": 1, "Verde": 0}
    resumen = []
    for an in analitos:
        niveles = []
        for niv in sorted(
            {n for (a, n) in eval_completo if a == an}, key=lambda n: _ORDEN_NIVEL.get(n, 9)
        ):
            df = eval_completo.get((an, niv))
            if df is None or df.empty:
                continue
            u = df.iloc[-1]
            niveles.append(
                {
                    "nivel": niv,
                    "nivel_label": NIVELES.get(niv, NIVELES["N"])["label"],
                    "estado": u["Estado"],
                    "valor": round(float(u["Valor"]), 3),
                    "z": round(float(u["Z_Score"]), 2),
                    "regla": u["Regla_Violada"],
                    "score": int(u["Score_Riesgo"]),
                }
            )
        if not niveles:
            continue
        peor = max((n["estado"] for n in niveles), key=lambda e: prioridad.get(e, 0))
        r4s = r4s_por_analito.get(an)
        resumen.append(
            {
                "analito": an,
                "niveles": niveles,
                "peor_estado": peor,
                "r4s": ({"label_a": r4s["label_a"], "label_b": r4s["label_b"]} if r4s else None),
            }
        )
    # Analitos con peor estado primero (Rojo arriba).
    resumen.sort(key=lambda a: prioridad.get(a["peor_estado"], 0), reverse=True)
    return resumen


def _cell_html(niv):
    color = _COLOR_ESTADO.get(niv["estado"], "#0D9E6E")
    led = _LED_ESTADO.get(niv["estado"], "⚪")
    regla = html.escape(str(niv["regla"]))
    return (
        f'<div class="ov-cell" style="border-left-color:{color}">'
        f'<div class="ov-cell-top"><span>{led}</span>'
        f'<span class="ov-cell-lbl">{html.escape(niv["nivel_label"])}</span></div>'
        f'<div class="ov-cell-val">{niv["valor"]}</div>'
        f'<div class="ov-cell-meta">Z {niv["z"]:+.2f} · {regla}</div>'
        f"</div>"
    )


def _card_html(a):
    color = _COLOR_ESTADO.get(a["peor_estado"], "#0D9E6E")
    cells = "".join(_cell_html(n) for n in a["niveles"])
    r4s_badge = ""
    if a["r4s"]:
        r4s_badge = (
            f'<span class="ov-r4s">⚡ R-4s '
            f'{html.escape(a["r4s"]["label_a"])} vs {html.escape(a["r4s"]["label_b"])}</span>'
        )
    return (
        f'<div class="ov-card" style="border-top-color:{color}">'
        f'<div class="ov-card-head"><span class="ov-name">{html.escape(a["analito"])}</span>'
        f"{r4s_badge}</div>"
        f'<div class="ov-cells">{cells}</div>'
        f"</div>"
    )


def render_overview_panel(resumen, height=None):
    """Dibuja el panel semáforo nativo. `resumen` viene de construir_resumen().

    Usa st.markdown (no iframe), así que sigue el tema claro de la app.
    `height` se acepta por compatibilidad con la firma anterior; se ignora.
    """
    n_rojo = sum(1 for a in resumen if a["peor_estado"] == "Rojo")
    n_ambar = sum(1 for a in resumen if a["peor_estado"] == "Ámbar")
    n_verde = sum(1 for a in resumen if a["peor_estado"] == "Verde")

    chips = (
        f'<span class="ov-chip ov-chip-rojo"{"" if n_rojo else " style=opacity:.4"}>🔴 {n_rojo} rojo</span>'
        f'<span class="ov-chip ov-chip-ambar"{"" if n_ambar else " style=opacity:.4"}>🟡 {n_ambar} ámbar</span>'
        f'<span class="ov-chip ov-chip-verde"{"" if n_verde else " style=opacity:.4"}>🟢 {n_verde} verde</span>'
    )

    if not resumen:
        cuerpo = '<div class="ov-empty">Sin datos para el rango seleccionado.</div>'
    else:
        cuerpo = f'<div class="ov-grid">{"".join(_card_html(a) for a in resumen)}</div>'

    st.markdown(
        f'<div class="ov-wrap">'
        f'<div class="ov-head"><span class="ov-title">🚦 Estado del laboratorio</span>'
        f'<div class="ov-chips">{chips}</div></div>'
        f"{cuerpo}</div>",
        unsafe_allow_html=True,
    )
