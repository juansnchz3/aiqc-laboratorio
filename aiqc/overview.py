# ==============================================================
# AIQC – Panel de resumen (vista semáforo)
#   · construir_resumen()  : matriz analito × nivel con estado y datos
#   · render_overview_panel(): panel HTML autocontenido (components.html)
#
# El panel se embebe con st.components.v1.html — HTML/CSS/JS autocontenido,
# SIN toolchain Node ni paso de build. Streamlit Cloud lo sirve tal cual.
# Flujo de datos Python → panel (solo lectura); los datos llegan como JSON.
# Sin dependencias de terceros salvo streamlit para el embed.
# ==============================================================
import html
import json

import streamlit.components.v1 as components

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


def _tarjeta_nivel_html(niv):
    color = _COLOR_ESTADO.get(niv["estado"], "#0D9E6E")
    led = _LED_ESTADO.get(niv["estado"], "⚪")
    regla = html.escape(str(niv["regla"]))
    return f"""
      <div class="nivel-cell" style="border-left:4px solid {color}">
        <div class="nivel-top">
          <span class="nivel-led">{led}</span>
          <span class="nivel-label">{html.escape(niv['nivel_label'])}</span>
        </div>
        <div class="nivel-valor">{niv['valor']}</div>
        <div class="nivel-meta">Z {niv['z']:+.2f} · {regla}</div>
      </div>"""


def _tarjeta_analito_html(a):
    color = _COLOR_ESTADO.get(a["peor_estado"], "#0D9E6E")
    niveles_html = "".join(_tarjeta_nivel_html(n) for n in a["niveles"])
    r4s_badge = ""
    if a["r4s"]:
        r4s_badge = (
            f'<span class="r4s-badge">⚡ R-4s '
            f'{html.escape(a["r4s"]["label_a"])} vs {html.escape(a["r4s"]["label_b"])}</span>'
        )
    return f"""
    <div class="analito-card" style="border-top:3px solid {color}">
      <div class="analito-head">
        <span class="analito-name">{html.escape(a['analito'])}</span>
        {r4s_badge}
      </div>
      <div class="niveles-grid">{niveles_html}</div>
    </div>"""


def render_overview_panel(resumen, height=None):
    """Embebe el panel semáforo. `resumen` viene de construir_resumen().

    Theme-aware (light/dark vía prefers-color-scheme). Autocontenido: todo el
    CSS/JS va inline, sin peticiones externas (compatible con Streamlit Cloud).
    """
    if not resumen:
        cuerpo = '<div class="vacio">Sin datos para el rango seleccionado.</div>'
    else:
        cuerpo = "".join(_tarjeta_analito_html(a) for a in resumen)

    # Conteo de estados para la cabecera.
    n_rojo = sum(1 for a in resumen if a["peor_estado"] == "Rojo")
    n_ambar = sum(1 for a in resumen if a["peor_estado"] == "Ámbar")
    n_verde = sum(1 for a in resumen if a["peor_estado"] == "Verde")

    # Altura estimada si no se fuerza: cabecera + filas. El grid mete ~2
    # tarjetas por fila en el ancho típico del dashboard; scrolling=True
    # cubre el caso de que quepan menos.
    if height is None:
        filas = -(-max(1, len(resumen)) // 2)  # ceil
        height = 70 + filas * 190

    datos_json = html.escape(json.dumps(resumen, ensure_ascii=False))

    doc = f"""
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  :root {{
    --bg: #FFFFFF; --card: #F8FAFC; --cell: #FFFFFF;
    --text: #1C2B3A; --muted: #64748B; --border: #E2E8F0;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #0E1117; --card: #1A2230; --cell: #131A24;
      --text: #E6EDF3; --muted: #94A3B8; --border: #2A3342;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font-family: "Inter", system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text);
  }}
  .resumen-head {{
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
    padding: 4px 2px 14px;
  }}
  .resumen-title {{ font-weight: 800; font-size: 1.05rem; }}
  .chips {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .chip {{
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 10px; border-radius: 999px; font-size: .8rem; font-weight: 700;
  }}
  .chip-rojo {{ background: rgba(229,62,62,.14); color: #E53E3E; }}
  .chip-ambar {{ background: rgba(245,158,11,.16); color: #B4740A; }}
  .chip-verde {{ background: rgba(13,158,110,.14); color: #0D9E6E; }}
  .grid {{
    display: grid; gap: 12px;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  }}
  .analito-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 12px 14px;
  }}
  .analito-head {{
    display: flex; align-items: center; justify-content: space-between;
    gap: 8px; margin-bottom: 10px; flex-wrap: wrap;
  }}
  .analito-name {{ font-weight: 700; font-size: .95rem; }}
  .r4s-badge {{
    font-size: .68rem; font-weight: 700; color: #E53E3E;
    background: rgba(229,62,62,.12); padding: 2px 7px; border-radius: 6px;
  }}
  .niveles-grid {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .nivel-cell {{
    flex: 1 1 78px; min-width: 78px; background: var(--cell);
    border: 1px solid var(--border); border-radius: 8px; padding: 7px 9px;
  }}
  /* min-height a 2 líneas: "Patológico Bajo" envuelve y sin esto los
     valores de celdas vecinas quedan a alturas distintas. */
  .nivel-top {{ display: flex; align-items: flex-start; gap: 5px; min-height: 27px; }}
  .nivel-led {{ font-size: .72rem; }}
  .nivel-label {{ font-size: .72rem; color: var(--muted); font-weight: 600; }}
  .nivel-valor {{ font-size: 1.15rem; font-weight: 800; margin-top: 2px; }}
  .nivel-meta {{ font-size: .68rem; color: var(--muted); margin-top: 1px; }}
  .vacio {{ color: var(--muted); padding: 24px; text-align: center; }}
</style>
</head>
<body>
  <div class="resumen-head">
    <span class="resumen-title">🚦 Estado del laboratorio</span>
    <div class="chips">
      <span class="chip chip-rojo"{' style="opacity:.4"' if not n_rojo else ""}>🔴 {n_rojo} rojo</span>
      <span class="chip chip-ambar"{' style="opacity:.4"' if not n_ambar else ""}>🟡 {n_ambar} ámbar</span>
      <span class="chip chip-verde"{' style="opacity:.4"' if not n_verde else ""}>🟢 {n_verde} verde</span>
    </div>
  </div>
  <div class="grid" id="grid">{cuerpo}</div>
  <script type="application/json" id="datos">{datos_json}</script>
</body>
</html>"""
    components.html(doc, height=height, scrolling=True)
