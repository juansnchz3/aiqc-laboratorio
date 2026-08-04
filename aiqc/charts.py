# ==============================================================
# AIQC – Gráficos Plotly y paneles de UI
#   · build_lj_figure()    : Levey-Jennings
#   · build_ewma_figure()  : EWMA
#   · build_cusum_figure() : CUSUM
#   · render_kb_panel()    : ficha Bio-Rad
#   · render_r4s_alert()   : tarjeta de alarma R-4s
#   · estado_badge()       : badge de estado
# ==============================================================
import plotly.graph_objects as go
import streamlit as st

from .knowledge_base import NIVELES, buscar_kb


# ==============================================================
# BADGES
# ==============================================================
def estado_badge(e):
    cfg = {"Verde": ("badge-green", "●"), "Ámbar": ("badge-amber", "▲"), "Rojo": ("badge-red", "■")}
    cls, ico = cfg.get(e, ("badge-green", "●"))
    return f'<span class="badge {cls}">{ico} {e}</span>'


# ==============================================================
# PANEL BIO-RAD KB
# ==============================================================
def _lista(items):
    """Lista <ul> a partir de un iterable de textos."""
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>"


def render_kb_panel(analito, estado, regla, nivel):
    kb = buscar_kb(analito, estado)
    nivel_label = NIVELES.get(nivel, NIVELES["N"])["label"]
    card_class = (
        "biorad-card-red"
        if estado == "Rojo"
        else "biorad-card-amber" if estado == "Ámbar" else "biorad-card"
    )
    if kb is None:
        st.markdown(
            f'<div class="{card_class}"><b>Bio-Rad KB:</b> No hay ficha para <b>{analito}</b>. '
            f'Consulta en <a href="https://myeinserts-app.qcnet.com/home" target="_blank">myeInserts QCNet</a>.</div>',
            unsafe_allow_html=True,
        )
        return
    ico = "🔴" if estado == "Rojo" else "🟡" if estado == "Ámbar" else "🟢"

    # Toda la ficha va en UN solo st.markdown. Repartir el <div> contenedor
    # entre varias llamadas no envuelve nada: Streamlit aísla cada bloque y
    # cierra las etiquetas sueltas, dejando una tarjeta vacía y el contenido
    # fuera de ella.
    col_causas = (
        f'<div><div class="kb-lbl">Causas más probables</div>{_lista(kb["causas_comunes"])}'
    )
    if estado == "Ámbar" and any(r in regla for r in ["10_x", "4_1s", "2_2s"]):
        deriva = kb.get("causas_deriva", [])
        if deriva:
            col_causas += f'<div class="kb-lbl">Causas de deriva</div>{_lista(deriva)}'
    col_causas += "</div>"

    acciones = kb["acciones_1_3s"] if estado == "Rojo" else kb["acciones_warn"]
    col_acciones = f'<div><div class="kb-lbl">Acciones correctivas</div>{_lista(acciones)}</div>'

    st.markdown(
        f'<div class="{card_class}">'
        f'<div class="kb-head">{ico} Guía Bio-Rad — {analito} · {nivel_label} '
        f"· Regla <code>{regla}</code></div>"
        f'<div class="kb-meta">Producto: {kb["producto"]} · Grupo: {kb["grupo"]}</div>'
        f'<div class="kb-cols">{col_causas}{col_acciones}</div>'
        f'<div class="kb-foot"><b>Interferencias:</b> {kb["interferencias"]}<br>'
        f'<b>Estabilidad:</b> {kb["estabilidad_biorad"]}<br>'
        f'<b>Referencia:</b> {kb["referencia"]}<br>'
        f'<a href="https://myeinserts-app.qcnet.com/home" target="_blank">'
        f"myeInserts QCNet Bio-Rad</a></div>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ==============================================================
# ALERTA R-4s
# ==============================================================
def render_r4s_alert(r4s):
    st.markdown(
        f"""<div style="background:#FFFAFA;border:1.5px solid #FECACA;border-left:5px solid #E53E3E;
border-radius:12px;padding:18px 20px;margin-bottom:14px;box-shadow:0 2px 12px rgba(229,62,62,.08);">
<div style="font-size:15px;font-weight:700;color:#991B1B;margin-bottom:8px">⚡ Regla R-4s — Error aleatorio entre niveles</div>
<div style="font-size:13px;color:#7F1D1D;line-height:1.7">
<b>{r4s['analito']}</b>: nivel <b>{r4s['label_a']}</b> Z=<b>{r4s['z_a']:+.2f}σ</b>
vs nivel <b>{r4s['label_b']}</b> Z=<b>{r4s['z_b']:+.2f}σ</b><br>
Diferencia: <b>{r4s['diferencia']:.2f}σ</b> — indica <b>error aleatorio</b>.
</div></div>""",
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:14px 16px;">
<div style="font-size:12px;font-weight:700;color:#991B1B;text-transform:uppercase;margin-bottom:8px">{r4s['label_a']}</div>
<div style="font-size:22px;font-weight:700;color:#E53E3E">{r4s['valor_a']}</div>
<div style="font-size:12px;color:#7F1D1D;margin-top:4px">Media:{r4s['media_a']} SD:{r4s['sd_a']} Z=<b>{r4s['z_a']:+.2f}σ</b></div>
</div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:14px 16px;">
<div style="font-size:12px;font-weight:700;color:#1D4ED8;text-transform:uppercase;margin-bottom:8px">{r4s['label_b']}</div>
<div style="font-size:22px;font-weight:700;color:#1A6FC4">{r4s['valor_b']}</div>
<div style="font-size:12px;color:#1E40AF;margin-top:4px">Media:{r4s['media_b']} SD:{r4s['sd_b']} Z=<b>{r4s['z_b']:+.2f}σ</b></div>
</div>""",
            unsafe_allow_html=True,
        )
    st.markdown(
        "**Acción:** Repetir **ambos niveles** con viales nuevos · **No recalibrar** como primer paso · Documentar"
    )


# ==============================================================
# EWMA
# ==============================================================
def build_ewma_figure(fechas, z_scores, ewma_r, analito, nivel):
    nivel_label = NIVELES.get(nivel, NIVELES["N"])["label"]
    lim_w = ewma_r["lim_warn"]
    lim_a = ewma_r["lim_act"]
    fig = go.Figure()
    for y0, y1, col in [
        (lim_a, lim_a * 2, "rgba(229,62,62,.08)"),
        (-lim_a * 2, -lim_a, "rgba(229,62,62,.08)"),
        (lim_w, lim_a, "rgba(245,158,11,.07)"),
        (-lim_a, -lim_w, "rgba(245,158,11,.07)"),
        (-lim_w, lim_w, "rgba(13,158,110,.05)"),
    ]:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=col, line_width=0)
    for y, col, dash, name in [
        (lim_a, "#E53E3E", "dot", f"+3σ ({lim_a:.3f})"),
        (-lim_a, "#E53E3E", "dot", "-3σ"),
        (lim_w, "#F59E0B", "dash", f"+2σ ({lim_w:.3f})"),
        (-lim_w, "#F59E0B", "dash", "-2σ"),
        (0, "#0D9E6E", "solid", "Media"),
    ]:
        fig.add_hline(
            y=y,
            line_color=col,
            line_width=1.5,
            line_dash=dash,
            annotation_text=name,
            annotation_position="right",
            annotation_font=dict(color=col, size=10),
        )
    fig.add_trace(
        go.Scatter(
            x=fechas,
            y=z_scores,
            mode="lines",
            name="Z-Score",
            line=dict(color="#CBD5E1", width=1),
            opacity=0.6,
        )
    )
    color_map = {"Verde": "#0D9E6E", "Ámbar": "#F59E0B", "Rojo": "#E53E3E"}
    for estado in ["Verde", "Ámbar", "Rojo"]:
        idx = [i for i, e in enumerate(ewma_r["estados"]) if e == estado]
        if not idx:
            continue
        fig.add_trace(
            go.Scatter(
                x=[fechas[i] for i in idx],
                y=[ewma_r["ewma"][i] for i in idx],
                mode="markers+lines",
                name=f"EWMA {estado}",
                marker=dict(size=7, color=color_map[estado], line=dict(color="#FFF", width=1)),
                line=dict(color=color_map[estado], width=2),
            )
        )
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"EWMA — {analito} · {nivel_label}",
            font=dict(size=13, color="#1C2B3A", family="Inter"),
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFBFC",
        font=dict(color="#475569", family="Inter"),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", tickformat="%d %b", title="Fecha"),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="EWMA (σ)"),
        height=360,
        margin=dict(l=10, r=140, t=50, b=40),
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
    )
    return fig


# ==============================================================
# CUSUM
# ==============================================================
def build_cusum_figure(fechas, cusum_r, analito, nivel):
    nivel_label = NIVELES.get(nivel, NIVELES["N"])["label"]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=fechas,
            y=cusum_r["cusum_pos"],
            name="C+ (↑)",
            marker_color=["#E53E3E" if a else "#93C5FD" for a in cusum_r["alarma_any"]],
            opacity=0.85,
        )
    )
    fig.add_trace(
        go.Bar(
            x=fechas,
            y=[-v for v in cusum_r["cusum_neg"]],
            name="C− (↓)",
            marker_color=["#F59E0B" if a else "#6EE7B7" for a in cusum_r["alarma_any"]],
            opacity=0.85,
        )
    )
    h_val = max(max(cusum_r["cusum_pos"] + [0]), 5)
    fig.add_hline(
        y=h_val,
        line_color="#E53E3E",
        line_width=1.5,
        line_dash="dash",
        annotation_text=f"h={h_val}",
        annotation_position="right",
        annotation_font=dict(color="#E53E3E", size=10),
    )
    fig.add_hline(
        y=-h_val,
        line_color="#F59E0B",
        line_width=1.5,
        line_dash="dash",
        annotation_text=f"-h={h_val}",
        annotation_position="right",
        annotation_font=dict(color="#F59E0B", size=10),
    )
    fig.update_layout(
        template="plotly_white",
        barmode="overlay",
        title=dict(
            text=f"CUSUM — {analito} · {nivel_label}",
            font=dict(size=13, color="#1C2B3A", family="Inter"),
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFBFC",
        font=dict(color="#475569", family="Inter"),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", tickformat="%d %b", title="Fecha"),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="CUSUM (σ)"),
        height=320,
        margin=dict(l=10, r=140, t=50, b=40),
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
    )
    return fig


# ==============================================================
# LEVEY-JENNINGS
# ==============================================================
def build_lj_figure(df_series, analito, nivel):
    u = df_series.iloc[-1]
    m = u["Media_Objetivo"]
    sd = u["SD_Objetivo"]
    nivel_label = NIVELES.get(nivel, NIVELES["N"])["label"]
    fig = go.Figure()
    for y0, y1, col in [
        (m + 2 * sd, m + 3 * sd, "rgba(229,62,62,.10)"),
        (m - 3 * sd, m - 2 * sd, "rgba(229,62,62,.10)"),
        (m + sd, m + 2 * sd, "rgba(245,158,11,.08)"),
        (m - 2 * sd, m - sd, "rgba(245,158,11,.08)"),
        (m - sd, m + sd, "rgba(13,158,110,.06)"),
    ]:
        fig.add_hrect(y0=y0, y1=y1, fillcolor=col, line_width=0)
    for y_v, color, width, dash, name in [
        (m, "#0D9E6E", 2.0, "solid", "Media"),
        (m + sd, "#94A3B8", 1.0, "dash", "+1 SD"),
        (m - sd, "#94A3B8", 1.0, "dash", "-1 SD"),
        (m + 2 * sd, "#F59E0B", 1.4, "dash", "+2 SD"),
        (m - 2 * sd, "#F59E0B", 1.4, "dash", "-2 SD"),
        (m + 3 * sd, "#E53E3E", 1.8, "dot", "+3 SD"),
        (m - 3 * sd, "#E53E3E", 1.8, "dot", "-3 SD"),
    ]:
        fig.add_hline(
            y=y_v,
            line_color=color,
            line_width=width,
            line_dash=dash,
            annotation_text=name,
            annotation_position="right",
            annotation_font=dict(color=color, size=10, family="Inter"),
        )
    fig.add_trace(
        go.Scatter(
            x=df_series["Fecha"],
            y=df_series["Valor"],
            mode="lines",
            line=dict(color="#CBD5E1", width=1.5),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    for estado, color in [("Verde", "#0D9E6E"), ("Ámbar", "#F59E0B"), ("Rojo", "#E53E3E")]:
        sub = df_series[df_series["Estado"] == estado]
        if sub.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub["Fecha"],
                y=sub["Valor"],
                mode="markers",
                name=estado,
                marker=dict(size=9, color=color, line=dict(color="#FFFFFF", width=1.5)),
            )
        )
    fig.update_layout(
        template="plotly_white",
        title=dict(
            text=f"Levey-Jennings — {analito} · {nivel_label}",
            font=dict(size=13, color="#1C2B3A", family="Inter"),
        ),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FAFBFC",
        font=dict(color="#475569", family="Inter"),
        legend=dict(orientation="h", y=1.08, x=1, xanchor="right"),
        xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", tickformat="%d %b", title="Fecha"),
        yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Valor"),
        height=380,
        width=760,
        margin=dict(l=10, r=110, t=55, b=40),
    )
    return fig


def fig_to_png_bytes(fig):
    try:
        return fig.to_image(format="png", scale=2)
    except Exception:
        return None
