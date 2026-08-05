# ==============================================================
# AIQC – Artificial Intelligence for Quality Control
# Versión: 4.13 – Demo mejorada + OpenLab + cobas 8000
# Deploy: streamlit run app.py
# Deps: pip install streamlit plotly pandas numpy fpdf2
#       openpyxl google-generativeai kaleido requests bcrypt
# ==============================================================
import logging

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

from aiqc.config import get_section
from aiqc.styles import CSS
from aiqc.knowledge_base import (
    NIVELES,
    BIORAD_KB,
    GRUPOS_ANALITICOS,
    TEA_CLIA,
    TEA_DEFAULT,
    nivel_badge,
)
from aiqc.database import (
    init_db,
    render_login,
    registrar_auditoria,
    tiene_permiso,
    load_acciones,
    save_accion,
    hash_password,
)
from aiqc.data_io import build_demo, leer_archivo, leer_csv_github, auto_refresh_github
from aiqc.measurements import (
    guardar_mediciones,
    cargar_mediciones,
    borrar_fuente,
    resumen_fuentes,
)
from aiqc.qc_rules import (
    evaluar_westgard,
    evaluar_r4s,
    calcular_ewma,
    calcular_cusum,
    calcular_sigma,
)
from aiqc.charts import (
    estado_badge,
    render_kb_panel,
    render_r4s_alert,
    build_lj_figure,
    build_ewma_figure,
    build_cusum_figure,
)
from aiqc.reports import generar_csv, generar_pdf
from aiqc.ai_assistant import necesita_datos_qc, ia_responde_gemini
from aiqc.overview import construir_resumen, render_overview_panel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("AIQC")

st.set_page_config(
    page_title="AIQC – Quality Control",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={"Get help": None, "Report a bug": None, "About": "AIQC v4.13 · Control de Calidad"},
)

# ==============================================================
# ESTILOS
# ==============================================================
st.markdown(CSS, unsafe_allow_html=True)

# ==============================================================
# INIT
# ==============================================================
if "db_con" not in st.session_state:
    st.session_state["db_con"] = init_db()
db_con = st.session_state["db_con"]

if not st.session_state.get("auth"):
    render_login(db_con)
    st.stop()

usuario_sesion = st.session_state.get(
    "usuario", {"username": "sistema", "rol": "tecnico", "nombre": ""}
)
usuario_actual = usuario_sesion["username"]
rol_actual = usuario_sesion["rol"]

# Rehidratar datos persistidos: si session_state está vacío (recarga, nuevo
# login) pero hay mediciones en la BD, se recuperan. Así los datos cargados
# sobreviven a recargas de página. Solo una vez por sesión de servidor.
if not st.session_state.get("_persistencia_rehidratada"):
    df_manual_bd = cargar_mediciones(db_con, fuente="manual")
    if not df_manual_bd.empty and st.session_state.get("df_manual") is None:
        st.session_state["df_manual"] = df_manual_bd
        st.session_state["data_src_manual"] = f"💾 Datos guardados ({len(df_manual_bd)} filas)"
    df_github_bd = cargar_mediciones(db_con, fuente="github")
    if not df_github_bd.empty and st.session_state.get("df_github") is None:
        st.session_state["df_github"] = df_github_bd
        st.session_state["data_src_github"] = f"💾 Datos guardados ({len(df_github_bd)} filas)"
    st.session_state["_persistencia_rehidratada"] = True

ESTADO_CLS = {"Verde": "estado-verde", "Ámbar": "estado-ambar", "Rojo": "estado-rojo"}
# Estado como texto con emoji para st.dataframe (no renderiza HTML/badges).
ESTADO_TXT = {"Verde": "🟢 Verde", "Ámbar": "🟡 Ámbar", "Rojo": "🔴 Rojo"}


# ==============================================================
# EVALUACIÓN CACHEADA
# Westgard/R-4s se evalúan UNA vez por rerun y por rango; todas las
# secciones (sidebar, tabs, registro) consumen estos diccionarios.
# ==============================================================
@st.cache_data(show_spinner=False)
def evaluar_todo(df_all, f_min=None, f_max=None):
    """{(analito, nivel): df evaluado con Westgard} en el rango dado (o completo)."""
    df_rango = df_all
    if f_min is not None and f_max is not None:
        df_rango = df_all[
            (df_all["Fecha"] >= pd.Timestamp(f_min)) & (df_all["Fecha"] <= pd.Timestamp(f_max))
        ]
    return {
        (an, niv): evaluar_westgard(sub.copy())
        for (an, niv), sub in df_rango.groupby(["Analito", "Nivel"])
    }


@st.cache_data(show_spinner=False)
def evaluar_r4s_todo(df_all, f_min, f_max):
    """{analito: resultado R-4s (o None)} en el rango dado."""
    return {an: evaluar_r4s(df_all, an, f_min, f_max) for an in df_all["Analito"].unique()}


# ==============================================================
# SIDEBAR
# ==============================================================
auto_refresh_github()
with st.sidebar:
    st.markdown('<div class="sb-logo">🔬</div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-title">AIQC</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sb-sub">Quality Control · v4.13 · OpenLab + cobas 8000</div>',
        unsafe_allow_html=True,
    )
    # Variante oscura del badge: los .role-* de la tabla de Usuarios llevan
    # fondo claro y aquí, sobre el sidebar, quedaban ilegibles.
    rol_badge_css = {
        "admin": "rol-admin",
        "supervisor": "rol-supervisor",
        "tecnico": "rol-tecnico",
    }.get(rol_actual, "rol-tecnico")
    st.markdown(
        f'<div class="sb-user"><span>👤 '
        f'{usuario_sesion.get("nombre", "") or usuario_actual}</span>'
        f'<span class="sb-role {rol_badge_css}">{rol_actual.upper()}</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown('<div class="sb-sec">📂 Fuente de datos</div>', unsafe_allow_html=True)
    # Etiquetas cortas: «Subir archivo» + «GitHub / OpenLab» sumaban 292 px en
    # un sidebar de 256 y la segunda pestaña se cortaba.
    tab_src1, tab_src2 = st.tabs(["📤 Archivo", "☁ GitHub"])

    with tab_src1:
        uploaded = st.file_uploader(
            "CSV o Excel",
            type=["csv", "xlsx", "xls"],
            help="Columnas: Fecha, Analito, Nivel (N/PB/PA), Valor, Media_Objetivo, SD_Objetivo, Lote.",
            key="uploader_manual",
        )
        if uploaded and uploaded.name != st.session_state.get("_ultimo_archivo_cargado"):
            df_cargado, aviso = leer_archivo(uploaded)
            if df_cargado is not None:
                if aviso:
                    st.warning(aviso)
                # Persistir en la BD (append con dedup por fuente 'manual').
                try:
                    nuevas, actualizadas = guardar_mediciones(
                        db_con, df_cargado, fuente="manual", usuario=usuario_actual
                    )
                    df_persistido = cargar_mediciones(db_con, fuente="manual")
                    st.session_state["df_manual"] = df_persistido
                    detalle = f"{uploaded.name}: {nuevas} nuevas, {actualizadas} actualizadas"
                except Exception as e:
                    # Si la persistencia falla, la app sigue con los datos en memoria.
                    logger.exception("Fallo al persistir mediciones manuales")
                    st.session_state["df_manual"] = df_cargado
                    df_persistido = df_cargado
                    detalle = f"{uploaded.name} (solo en memoria: {e})"
                st.session_state["data_src_manual"] = f"📄 {uploaded.name}"
                st.session_state["_ultimo_archivo_cargado"] = uploaded.name
                registrar_auditoria(db_con, usuario_actual, "CARGA_ARCHIVO", detalle)
                st.markdown(
                    f'<div class="data-pill">✅ <b>{uploaded.name}</b><br>'
                    f"{len(df_persistido)} filas acumuladas · "
                    f'{df_persistido["Analito"].nunique()} analito(s)</div>',
                    unsafe_allow_html=True,
                )
                st.rerun()
            else:
                st.error(aviso)

    with tab_src2:
        cfg_gh = get_section("github")
        tiene_config = bool(cfg_gh.get("usuario") and cfg_gh.get("repo") and cfg_gh.get("archivo"))
        if not tiene_config:
            st.warning("Configura `[github]` en `.streamlit/secrets.toml`.")
        else:
            ultima_sync = st.session_state.get("github_last_sync")
            msg_gh = st.session_state.get("data_src_github", "Sin sincronizar aún")
            if ultima_sync:
                st.markdown(
                    f'<div class="sync-pill">☁ <b>OpenLab · GitHub</b><br>{msg_gh}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("Pulsa para cargar datos desde OpenLab vía GitHub.")
            if st.button(
                "🔄 Sincronizar ahora", use_container_width=True, type="primary", key="btn_sync_gh"
            ):
                with st.spinner("Conectando con GitHub…"):
                    df_gh, msg = leer_csv_github()
                if df_gh is not None:
                    try:
                        guardar_mediciones(db_con, df_gh, fuente="github", usuario=usuario_actual)
                        df_gh = cargar_mediciones(db_con, fuente="github")
                    except Exception:
                        logger.exception("Fallo al persistir mediciones de GitHub")
                    st.session_state["df_github"] = df_gh
                    st.session_state["data_src_github"] = msg
                    st.session_state["github_last_sync"] = datetime.now()
                    registrar_auditoria(db_con, usuario_actual, "SYNC_GITHUB", msg)
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
            auto_sync = st.checkbox(
                "Auto-sincronizar al iniciar",
                key="auto_sync_gh",
                help="Recarga datos automáticamente cada 60 min desde GitHub",
            )
            if auto_sync and st.session_state.get("df_github") is None:
                with st.spinner("Cargando datos OpenLab desde GitHub…"):
                    df_gh, msg = leer_csv_github()
                if df_gh is not None:
                    try:
                        guardar_mediciones(db_con, df_gh, fuente="github", usuario=usuario_actual)
                        df_gh = cargar_mediciones(db_con, fuente="github")
                    except Exception:
                        logger.exception("Fallo al persistir mediciones de GitHub (auto-sync)")
                    st.session_state["df_github"] = df_gh
                    st.session_state["data_src_github"] = msg
                    st.session_state["github_last_sync"] = datetime.now()
                    st.rerun()

    # Datos persistidos: resumen y borrado por fuente.
    fuentes_bd = resumen_fuentes(db_con)
    if fuentes_bd:
        total_filas = sum(f["filas"] for f in fuentes_bd.values())
        with st.expander(f"💾 Datos guardados ({total_filas} filas)", expanded=False):
            for fuente, info in fuentes_bd.items():
                cols_bd = st.columns([3, 1])
                cols_bd[0].caption(
                    f"**{fuente}** · {info['filas']} filas · {info['analitos']} analito(s)"
                )
                if cols_bd[1].button("🗑", key=f"del_fuente_{fuente}", help=f"Borrar '{fuente}'"):
                    borrar_fuente(db_con, fuente)
                    registrar_auditoria(db_con, usuario_actual, "BORRAR_MEDICIONES", fuente)
                    for k in ("df_manual", "df_github", "data_src_manual", "data_src_github"):
                        if fuente in k or (fuente == "github" and "github" in k):
                            st.session_state.pop(k, None)
                    if fuente == "manual":
                        st.session_state.pop("df_manual", None)
                        st.session_state.pop("_ultimo_archivo_cargado", None)
                    else:
                        st.session_state.pop("df_github", None)
                    st.rerun()
            st.caption(
                "⚠ En Streamlit Cloud el disco es efímero: estos datos se borran "
                "al reiniciarse o redesplegarse la app."
            )

    st.markdown("---")

    # Prioridad: GitHub > Manual > Demo
    df_github = st.session_state.get("df_github")
    df_manual = st.session_state.get("df_manual")
    if df_github is not None:
        df_all = df_github
        data_src = "☁ OpenLab·GitHub"
    elif df_manual is not None:
        df_all = df_manual
        data_src = st.session_state.get("data_src_manual", "📄 Archivo")
    else:
        df_all = build_demo()
        data_src = "🔬 Modo Demo"
        st.markdown(
            """
        <div style="background:linear-gradient(135deg,#1A6FC4,#0D9E6E);
        border-radius:10px;padding:12px 14px;margin-bottom:8px">
        <div style="color:#FFFFFF;font-weight:700;font-size:.85rem">🔬 MODO DEMO ACTIVO</div>
        <div style="color:rgba(255,255,255,.85);font-size:.75rem;margin-top:3px">
        Datos simulados de Amilasa y ALT.<br>
        En producción conecta con OpenLab vía GitHub.
        </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        if st.button("🔄 Reiniciar demo", use_container_width=True, key="btn_reset_demo"):
            st.cache_data.clear()
            st.rerun()

    analito = st.selectbox(
        "Analito activo", options=sorted(df_all["Analito"].unique()), key="sel_analito"
    )
    niveles_analito = sorted(df_all[df_all["Analito"] == analito]["Nivel"].unique())
    nivel_options = {NIVELES.get(n, NIVELES["N"])["label"]: n for n in niveles_analito}
    nivel_sel_label = st.selectbox(
        "Nivel de control",
        options=list(nivel_options.keys()),
        key="sel_nivel",
        help="N=Normal · PB=Patológico Bajo · PA=Patológico Alto",
    )
    nivel_activo = nivel_options[nivel_sel_label]

    fechas_d = sorted(df_all["Fecha"].dropna().unique())
    if len(fechas_d) >= 2:
        f_min = st.date_input(
            "Desde",
            value=pd.Timestamp(fechas_d[0]).date(),
            min_value=pd.Timestamp(fechas_d[0]).date(),
            max_value=pd.Timestamp(fechas_d[-1]).date(),
            key="f1",
        )
        f_max = st.date_input(
            "Hasta",
            value=pd.Timestamp(fechas_d[-1]).date(),
            min_value=pd.Timestamp(fechas_d[0]).date(),
            max_value=pd.Timestamp(fechas_d[-1]).date(),
            key="f2",
        )
    else:
        f_min = f_max = pd.Timestamp(fechas_d[0]).date() if fechas_d else datetime.today().date()

    st.markdown("---")
    st.markdown('<div class="sb-sec">🚦 Estado del laboratorio</div>', unsafe_allow_html=True)
    eval_completo = evaluar_todo(df_all)
    r4s_por_analito = evaluar_r4s_todo(df_all, f_min, f_max)
    for an in sorted(df_all["Analito"].unique()):
        for niv in sorted(df_all[df_all["Analito"] == an]["Nivel"].unique()):
            sub = eval_completo.get((an, niv))
            if sub is None or sub.empty:
                continue
            est = sub.iloc[-1]["Estado"]
            led = {"Verde": "🟢", "Ámbar": "🟡", "Rojo": "🔴"}.get(est, "⚪")
            st.markdown(f"{led} **{an}** · {NIVELES.get(niv, NIVELES['N'])['label']} — {est}")
        r4s_sb = r4s_por_analito.get(an)
        if r4s_sb:
            st.markdown(f"⚡ **{an}** · R-4s: {r4s_sb['label_a']} vs {r4s_sb['label_b']}")

    st.markdown("---")
    if st.button("Cerrar sesión", use_container_width=True):
        registrar_auditoria(db_con, usuario_actual, "LOGOUT", "")
        st.session_state["auth"] = False
        st.session_state["usuario"] = None
        st.rerun()
    st.caption(f"Fuente: {data_src}")

# ==============================================================
# DATOS ACTIVOS
# ==============================================================
eval_rango = evaluar_todo(df_all, f_min, f_max)
df_series = eval_rango.get((analito, nivel_activo), pd.DataFrame())
ultima = df_series.iloc[-1] if not df_series.empty else None
analitos_ls = sorted(df_all["Analito"].unique())
r4s_result = r4s_por_analito.get(analito)
estado_actual = ultima["Estado"] if ultima is not None else "Verde"

# ==============================================================
# CABECERA
# ==============================================================
st.markdown(
    f"""
<div class="aiqc-header">
<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
<div>
<h2>🔬 AIQC – Control de Calidad</h2>
<div class="meta">
<span class="hd-chip">Fuente&nbsp;<b>{data_src}</b></span>
<span class="hd-chip">📅 {f_min.strftime('%d/%m/%Y')} → {f_max.strftime('%d/%m/%Y')}</span>
<span class="hd-chip">👤 <b>{usuario_actual}</b></span>
</div>
</div>
<div style="font-size:1.1rem">{estado_badge(estado_actual)}</div>
</div>
</div>
""",
    unsafe_allow_html=True,
)

# ==============================================================
# BARRA DE CONTEXTO (solo lectura)
# La selección se hace en el sidebar; duplicar aquí los widgets creaba
# estados divergentes y errores de session_state al sincronizarlos.
# ==============================================================
st.markdown(
    f'<div class="quick-bar">'
    f'<span class="qb-item"><span class="qb-lbl">Analito</span>'
    f'<span class="qb-val">🔬 {analito}</span></span>'
    f'<span class="qb-item"><span class="qb-lbl">Nivel</span>'
    f'<span class="qb-val">{nivel_badge(nivel_activo)}</span></span>'
    f'<span class="qb-item"><span class="qb-lbl">Período</span>'
    f'<span class="qb-val">📅 {f_min.strftime("%d/%m/%Y")} → {f_max.strftime("%d/%m/%Y")}</span></span>'
    f"</div>",
    unsafe_allow_html=True,
)

# Banner demo
if data_src == "🔬 Modo Demo":
    st.markdown(
        """
    <div class="demo-banner">
    <div class="db-icon">🔬</div>
    <div>
    <div class="db-title">Modo demostración activo</div>
    <div class="db-text">
    Datos <b>simulados</b> de Amilasa (N, PB, PA) y ALT con alarmas reales de Westgard.
    En producción los datos se cargan automáticamente desde
    <b>OpenLab → GitHub → App</b> en tiempo real.
    </div>
    </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


# ==============================================================
# PÁGINAS
# Cada sección es una función que se registra en st.navigation al final.
# Leen el estado compartido (df_all, eval_rango, ultima…) del ámbito de
# módulo, ya calculado arriba; st.navigation solo ejecuta la página activa.
# ==============================================================
def _page_header(icon, titulo, subtitulo="", accent="#1A6FC4"):
    """Encabezado visual uniforme para cada página de análisis.

    `accent` colorea la loseta del icono y la línea inferior (--ph-accent),
    dando a cada página una identidad cromática propia. Los sufijos hex
    (1C/0A/45) son el canal alfa del color en formato #RRGGBBAA.
    """
    sub = f"<p>{subtitulo}</p>" if subtitulo else ""
    st.markdown(
        f'<div class="page-head" style="--ph-accent:{accent}">'
        f'<div class="ph-icon" style="background:linear-gradient(135deg,{accent}1C,{accent}0A);'
        f'border-color:{accent}45">{icon}</div>'
        f'<div class="ph-txt"><h3>{titulo}</h3>{sub}</div></div>',
        unsafe_allow_html=True,
    )


# ── PÁGINA: DASHBOARD ────────────────────────────────────────
def _page_dashboard():
    _page_header("📊", "Dashboard", "Visión general del control de calidad", accent="#1A6FC4")
    # Panel semáforo: vista global del laboratorio (matriz analito × nivel),
    # nativo (st.markdown). Reusa los dicts ya evaluados y cacheados.
    resumen_lab = construir_resumen(eval_rango, r4s_por_analito)
    render_overview_panel(resumen_lab)
    st.markdown("---")

    if df_series.empty or ultima is None:
        st.warning("No hay datos para el analito/nivel/rango seleccionado.")
    else:
        score = int(ultima["Score_Riesgo"])
        zscore = round(ultima["Z_Score"], 2)
        risk_c = {"Verde": "#0D9E6E", "Ámbar": "#F59E0B", "Rojo": "#E53E3E"}.get(
            ultima["Estado"], "#0D9E6E"
        )
        estado_cls = ESTADO_CLS.get(ultima["Estado"], "")
        k1, k2, k3, k4, k5 = st.columns(5)
        for col, val, lbl, color, sub in [
            (k1, f"{ultima['Valor']}", "Valor Actual", "#1A6FC4", "Última medición"),
            (k2, f"{ultima['Media_Objetivo']}", "Media Objetivo", "#4F6FA8", "μ objetivo"),
            (k3, f"±{ultima['SD_Objetivo']}", "SD Objetivo", "#6B5CA5", "σ objetivo"),
            (
                k4,
                f"{zscore:+.2f}σ",
                "Z-Score",
                "#E53E3E" if abs(zscore) >= 2 else "#0D9E6E",
                "Z=(x-μ)/σ",
            ),
            (k5, f"{score}/100", "Score de Riesgo", risk_c, ultima["Estado"]),
        ]:
            with col:
                st.markdown(
                    f'<div class="kpi-card {estado_cls}"><div class="kpi-val" style="color:{color}">{val}</div>'
                    f'<div class="kpi-lbl">{lbl}</div><div class="kpi-sub">{sub}</div></div>',
                    unsafe_allow_html=True,
                )
        if r4s_result:
            st.markdown("<br>", unsafe_allow_html=True)
            render_r4s_alert(r4s_result)
        if ultima["Estado"] != "Verde":
            st.markdown("<br>", unsafe_allow_html=True)
            render_kb_panel(analito, ultima["Estado"], ultima["Regla_Violada"], nivel_activo)
        st.markdown("<br>", unsafe_allow_html=True)
        nivs_analito = sorted(df_all[df_all["Analito"] == analito]["Nivel"].unique())
        if len(nivs_analito) > 1:
            st.markdown(
                '<div class="sec-head">Comparativa de niveles — Levey-Jennings</div>',
                unsafe_allow_html=True,
            )
            tabs_niveles = st.tabs(
                [
                    f"{NIVELES.get(n, NIVELES['N'])['icon']} {NIVELES.get(n, NIVELES['N'])['label']}"
                    for n in nivs_analito
                ]
            )
            for tab_n, niv in zip(tabs_niveles, nivs_analito):
                with tab_n:
                    sub_n = eval_rango.get((analito, niv), pd.DataFrame())
                    if sub_n.empty:
                        st.info("Sin datos para este nivel.")
                    else:
                        fig_n = build_lj_figure(sub_n, analito, niv)
                        fig_n.update_layout(height=400, margin=dict(l=10, r=130, t=60, b=10))
                        st.plotly_chart(fig_n, use_container_width=True)
        else:
            fig = build_lj_figure(df_series, analito, nivel_activo)
            fig.update_layout(height=460, width=None, margin=dict(l=10, r=130, t=60, b=10))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown('<div class="sec-head">Últimas 7 mediciones</div>', unsafe_allow_html=True)
        tail = df_series.tail(7)[
            ["Fecha", "Valor", "Z_Score", "Regla_Violada", "Score_Riesgo", "Estado", "Lote"]
        ].copy()
        tail["Estado"] = tail["Estado"].map(ESTADO_TXT).fillna(tail["Estado"])
        st.dataframe(
            tail.rename(
                columns={"Z_Score": "Z-Score", "Regla_Violada": "Regla", "Score_Riesgo": "Score"}
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "Valor": st.column_config.NumberColumn("Valor", format="%.2f"),
                "Z-Score": st.column_config.NumberColumn("Z-Score", format="%+.2f σ"),
                "Score": st.column_config.ProgressColumn(
                    "Score", min_value=0, max_value=100, format="%d"
                ),
            },
        )


# ── TAB 2: EWMA / CUSUM ──────────────────────────────────────
def _page_ewma():
    _page_header("📉", "EWMA / CUSUM", "Detección temprana de tendencias", accent="#7C3AED")
    if df_series.empty or ultima is None:
        st.warning("No hay datos para el analito/nivel/rango seleccionado.")
    else:
        z_scores = df_series["Z_Score"].tolist()
        fechas = df_series["Fecha"].tolist()
        with st.expander("⚙ Parámetros EWMA y CUSUM", expanded=False):
            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                lam = st.slider("λ EWMA", 0.05, 0.50, 0.20, 0.05, key="ewma_lam")
            with col_p2:
                cusum_k = st.slider("k CUSUM", 0.25, 1.0, 0.5, 0.25, key="cusum_k")
            with col_p3:
                cusum_h = st.slider("h CUSUM", 2.0, 8.0, 5.0, 0.5, key="cusum_h")
        ewma_r = calcular_ewma(z_scores, lam=lam)
        cusum_r = calcular_cusum(z_scores, k=cusum_k, h=cusum_h)
        ewma_estado = ewma_r["estados"][-1] if ewma_r["estados"] else "Verde"
        cusum_alarma = cusum_r["primera_alarma"] is not None
        risk_ewma = {"Verde": "#0D9E6E", "Ámbar": "#F59E0B", "Rojo": "#E53E3E"}.get(
            ewma_estado, "#0D9E6E"
        )
        risk_cusum = "#E53E3E" if cusum_alarma else "#0D9E6E"
        n_ambar_ewma = sum(1 for e in ewma_r["estados"] if e == "Ámbar")
        n_rojo_ewma = sum(1 for e in ewma_r["estados"] if e == "Rojo")
        kc1, kc2, kc3, kc4, kc5 = st.columns(5)
        for col, val, lbl, color, sub in [
            (kc1, f"{ewma_r['ultimo_ewma']:+.3f}σ", "EWMA Actual", risk_ewma, ewma_estado),
            (kc2, f"{ewma_r['sigma_ewma']:.4f}", "σ EWMA", "#4F6FA8", f"λ={lam}"),
            (kc3, f"{n_rojo_ewma}", "Puntos Rojo", "#E53E3E", f"{n_ambar_ewma} ámbar"),
            (kc4, f"{cusum_r['max_cp']:.2f}", "CUSUM+ Máx", risk_cusum, f"h={cusum_h}"),
            (kc5, f"{cusum_r['max_cm']:.2f}", "CUSUM− Máx", risk_cusum, f"k={cusum_k}"),
        ]:
            with col:
                st.markdown(
                    f'<div class="kpi-card"><div class="kpi-val" style="color:{color}">{val}</div>'
                    f'<div class="kpi-lbl">{lbl}</div><div class="kpi-sub">{sub}</div></div>',
                    unsafe_allow_html=True,
                )
        st.markdown("<br>", unsafe_allow_html=True)
        alerta_mostrada = False
        if ewma_estado == "Rojo":
            st.error(f"🔴 **EWMA ROJA** — Deriva sostenida: **{ewma_r['ultimo_ewma']:+.3f}σ**")
            alerta_mostrada = True
        elif ewma_estado == "Ámbar":
            inicio = ewma_r["inicio_deriva"]
            fecha_inicio = fechas[inicio].strftime("%d/%m/%Y") if inicio is not None else "—"
            st.warning(
                f"⚠ **EWMA ÁMBAR** — Tendencia desde **{fecha_inicio}**: **{ewma_r['ultimo_ewma']:+.3f}σ**"
            )
            alerta_mostrada = True
        if cusum_alarma:
            fecha_cusum = fechas[cusum_r["primera_alarma"]].strftime("%d/%m/%Y")
            tipo_txt = "ascendente ↑" if cusum_r["tipo_deriva"] == "ascendente" else "descendente ↓"
            st.error(f"🔴 **CUSUM alarma** — Deriva {tipo_txt} desde **{fecha_cusum}**")
            alerta_mostrada = True
        if not alerta_mostrada:
            st.success(
                f"✅ Proceso bajo control — EWMA={ewma_r['ultimo_ewma']:+.3f}σ "
                f"C+={cusum_r['max_cp']:.2f} C−={cusum_r['max_cm']:.2f}"
            )
        st.markdown('<div class="sec-head">Gráfico EWMA</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_ewma_figure(fechas, z_scores, ewma_r, analito, nivel_activo),
            use_container_width=True,
        )
        st.markdown('<div class="sec-head">Gráfico CUSUM</div>', unsafe_allow_html=True)
        st.plotly_chart(
            build_cusum_figure(fechas, cusum_r, analito, nivel_activo), use_container_width=True
        )
        st.markdown('<div class="sec-head">Tabla EWMA / CUSUM</div>', unsafe_allow_html=True)
        tabla_ec = pd.DataFrame(
            {
                "Fecha": list(fechas),
                "Z-Score": z_scores,
                "EWMA": ewma_r["ewma"],
                "Estado EWMA": [ESTADO_TXT.get(e, e) for e in ewma_r["estados"]],
                "CUSUM+": cusum_r["cusum_pos"],
                "CUSUM−": cusum_r["cusum_neg"],
                "Alarma": ["🔴 Sí" if a else "✅ No" for a in cusum_r["alarma_any"]],
            }
        )
        st.dataframe(
            tabla_ec,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Fecha": st.column_config.DateColumn("Fecha", format="DD/MM/YYYY"),
                "Z-Score": st.column_config.NumberColumn("Z-Score", format="%+.3f"),
                "EWMA": st.column_config.NumberColumn("EWMA", format="%.4f"),
                "CUSUM+": st.column_config.NumberColumn("CUSUM+", format="%.3f"),
                "CUSUM−": st.column_config.NumberColumn("CUSUM−", format="%.3f"),
            },
        )


# ── TAB 3: SIGMA METRICS ─────────────────────────────────────
def _page_sigma():
    _page_header("📈", "Sigma Metrics", "Evaluación de calidad analítica", accent="#0D9E6E")
    with st.expander("⚙ Editar límites TEa por analito", expanded=False):
        tea_editado = {}
        cols_tea = st.columns(min(len(analitos_ls), 3))
        for i, an in enumerate(analitos_ls):
            with cols_tea[i % len(cols_tea)]:
                tea_editado[an] = st.number_input(
                    f"TEa% — {an.split('(')[0].strip()}",
                    min_value=1.0,
                    max_value=50.0,
                    value=float(TEA_CLIA.get(an, (TEA_DEFAULT, "", ""))[0]),
                    step=0.5,
                    key=f"tea_{an}",
                )
    st.markdown("<br>", unsafe_allow_html=True)
    niveles_globales = sorted(df_all["Nivel"].unique())
    sigma_data = []
    for an in analitos_ls:
        for niv in niveles_globales:
            sub = eval_rango.get((an, niv), pd.DataFrame())
            if sub.empty:
                continue
            sig = calcular_sigma(sub, tea_editado.get(an, TEA_DEFAULT))
            if sig:
                sigma_data.append(
                    {
                        "analito": an,
                        "nivel": niv,
                        "nivel_label": NIVELES.get(niv, NIVELES["N"])["label"],
                        **sig,
                    }
                )
    if not sigma_data:
        st.warning("Sin datos suficientes.")
    else:
        for niv in niveles_globales:
            niv_cfg = NIVELES.get(niv, NIVELES["N"])
            niv_data = [d for d in sigma_data if d["nivel"] == niv]
            if not niv_data:
                continue
            st.markdown(
                f'<div class="sec-head">{niv_cfg["icon"]} {niv_cfg["label"]}</div>',
                unsafe_allow_html=True,
            )
            cols_s = st.columns(len(niv_data))
            for col, d in zip(cols_s, niv_data):
                with col:
                    st.markdown(
                        f'<div class="kpi-card"><div class="kpi-val" style="color:{d["color"]}">{d["sigma"]}σ</div>'
                        f'<div class="kpi-lbl">{d["analito"].split("(")[0].strip()}</div>'
                        f'<div class="kpi-sub">{d["categoria"]}</div></div>',
                        unsafe_allow_html=True,
                    )
        st.markdown("<br>", unsafe_allow_html=True)
        fig_s = go.Figure()
        colores_nivel = {"N": "#1A6FC4", "PB": "#F59E0B", "PA": "#E53E3E"}
        for niv in niveles_globales:
            niv_data = [d for d in sigma_data if d["nivel"] == niv]
            if not niv_data:
                continue
            fig_s.add_trace(
                go.Bar(
                    name=NIVELES.get(niv, NIVELES["N"])["label"],
                    x=[d["analito"].split("(")[0].strip() for d in niv_data],
                    y=[d["sigma"] for d in niv_data],
                    marker_color=colores_nivel.get(niv, "#1A6FC4"),
                    marker_line_color="#FFFFFF",
                    marker_line_width=1.5,
                    text=[f"{d['sigma']}σ" for d in niv_data],
                    textposition="outside",
                )
            )
        for y_v, color, lbl in [(6, "#0D9E6E", "6σ"), (4, "#1A6FC4", "4σ"), (3, "#F59E0B", "3σ")]:
            fig_s.add_hline(
                y=y_v,
                line_color=color,
                line_width=1.5,
                line_dash="dash",
                annotation_text=lbl,
                annotation_position="right",
                annotation_font=dict(color=color, size=11),
            )
        for y0, y1, col in [
            (6, 10, "rgba(13,158,110,.07)"),
            (4, 6, "rgba(26,111,196,.06)"),
            (3, 4, "rgba(245,158,11,.06)"),
            (0, 3, "rgba(229,62,62,.06)"),
        ]:
            fig_s.add_hrect(y0=y0, y1=y1, fillcolor=col, line_width=0)
        fig_s.update_layout(
            template="plotly_white",
            barmode="group",
            title=dict(
                text="Sigma Metrics por Analito y Nivel",
                font=dict(size=15, color="#1C2B3A", family="Inter"),
            ),
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FAFBFC",
            font=dict(color="#475569", family="Inter"),
            xaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Analito"),
            yaxis=dict(gridcolor="#F1F5F9", linecolor="#E2E8F0", title="Sigma (σ)", range=[0, 11]),
            height=440,
            margin=dict(l=10, r=130, t=60, b=10),
            legend=dict(orientation="h", y=1.08, x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_s, use_container_width=True)
        st.markdown('<div class="sec-head">Detalle</div>', unsafe_allow_html=True)
        st.dataframe(
            pd.DataFrame(
                [
                    {
                        "Analito": d["analito"],
                        "Nivel": d["nivel_label"],
                        "N": d["n"],
                        "Media": d["media"],
                        "SD": d["sd"],
                        "CV%": d["cv_pct"],
                        "Sesgo%": d["sesgo_pct"],
                        "TEa%": d["tea_pct"],
                        "Sigma": d["sigma"],
                        "Categoría": d["categoria"],
                    }
                    for d in sigma_data
                ]
            ),
            use_container_width=True,
            hide_index=True,
            column_config={
                "CV%": st.column_config.NumberColumn("CV%", format="%.2f%%"),
                "Sesgo%": st.column_config.NumberColumn("Sesgo%", format="%.2f%%"),
                "TEa%": st.column_config.NumberColumn("TEa%", format="%.1f%%"),
                "Sigma": st.column_config.NumberColumn("Sigma", format="%.2f σ"),
            },
        )
        for d in sigma_data:
            s = d["sigma"]
            lbl = f"**{d['analito']} [{d['nivel_label']}]** — **{s}σ**"
            if s >= 6:
                st.success(f"{lbl} · clase mundial.")
            elif s >= 4:
                st.info(f"{lbl} · buena calidad.")
            elif s >= 3:
                st.warning(f"{lbl} · aceptable.")
            else:
                st.error(f"{lbl} · deficiente. Revisar.")


# ── TAB 4: GUÍA BIO-RAD ──────────────────────────────────────
def _page_biorad():
    _page_header("📋", "Guía Bio-Rad", "Acciones correctivas recomendadas", accent="#D97706")
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        an_kb = st.selectbox(
            "Analito a consultar", options=list(BIORAD_KB.keys()), key="kb_analito_sel"
        )
    with col_sel2:
        estado_kb = st.selectbox(
            "Simular estado",
            options=["Rojo (1_3s)", "Ámbar (4_1s / 10_x)", "Verde (informativo)"],
            key="kb_estado_sel",
        )
    estado_sim = "Rojo" if "Rojo" in estado_kb else "Ámbar" if "Ámbar" in estado_kb else "Verde"
    regla_sim = "1_3s" if estado_sim == "Rojo" else "4_1s" if estado_sim == "Ámbar" else "—"
    st.markdown("<br>", unsafe_allow_html=True)
    render_kb_panel(an_kb, estado_sim, regla_sim, nivel_activo)
    st.markdown("---")
    st.markdown(
        '<div class="sec-head">🔴 Alarmas activas en el período seleccionado</div>',
        unsafe_allow_html=True,
    )
    hay_alarmas = False
    for an in analitos_ls:
        for niv in sorted(df_all["Nivel"].unique()):
            sub = eval_rango.get((an, niv), pd.DataFrame())
            if sub.empty:
                continue
            u = sub.iloc[-1]
            if u["Estado"] != "Verde":
                hay_alarmas = True
                render_kb_panel(an, u["Estado"], u["Regla_Violada"], niv)
        r4s_br = r4s_por_analito.get(an)
        if r4s_br:
            hay_alarmas = True
            st.markdown(
                f"""<div class="biorad-card-red"><b>⚡ R-4s — {an}</b><br>
<small>{r4s_br['label_a']} (Z={r4s_br['z_a']:+.2f}) vs {r4s_br['label_b']} (Z={r4s_br['z_b']:+.2f})
— Diff={r4s_br['diferencia']:.2f}σ — Acción: repetir ambos niveles. No recalibrar.</small></div>""",
                unsafe_allow_html=True,
            )
    if not hay_alarmas:
        st.success("✅ No hay alarmas activas.")
    st.markdown("---")
    st.markdown(
        '<div class="sec-head">📚 Cobertura de la base de conocimiento</div>',
        unsafe_allow_html=True,
    )
    for grupo, analitos_grupo in GRUPOS_ANALITICOS.items():
        con_ficha = [a for a in analitos_grupo if a in BIORAD_KB]
        chips = "".join(f'<span class="kb-chip">{a}</span>' for a in con_ficha)
        st.markdown(
            f'<div class="kb-group"><span class="kb-group-name">{grupo}</span>{chips}</div>',
            unsafe_allow_html=True,
        )


# ── TAB 5: ASISTENTE IA ──────────────────────────────────────
def _page_chat():
    _page_header(
        "🤖", "Asistente AIQC", "Análisis conversacional · Google Gemini", accent="#0891B2"
    )
    modelo_activo = st.session_state.get("gemini_model_active", "models/gemini-2.5-flash")
    st.markdown(
        f'<div class="gemini-banner">🟢 <b>Google Gemini</b> · Modelo: <code>{modelo_activo}</code> · '
        f"Bio-Rad KB + cobas 8000 + R-4s + EWMA/CUSUM + OpenLab sync · Conversación libre habilitada.</div>",
        unsafe_allow_html=True,
    )
    if "messages" not in st.session_state:
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "content": (
                    "¡Hola! Soy el **Asistente AIQC v4.13** 👋\n\n"
                    "Tengo acceso a los datos de laboratorio, la base de conocimiento Bio-Rad "
                    "y el manual del **cobas® 8000**.\n\n"
                    "Prueba a preguntarme:\n"
                    "- *¿Hay alguna alarma activa?*\n"
                    "- *¿Qué indica el EWMA de la Amilasa en Patológico Bajo?*\n"
                    "- *¿Cómo proceso la bandeja verde del cobas 8000?*\n"
                    "- *Dame un plan correctivo para la alarma R-4s*\n"
                    "- O cualquier otra consulta 😊"
                ),
            }
        ]
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])
    if prompt := st.chat_input("Escribe tu consulta o pregunta…"):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        with st.chat_message("assistant", avatar="🤖"):
            spinner_txt = (
                "Analizando datos QC, cobas 8000, Bio-Rad KB…"
                if necesita_datos_qc(prompt)
                else "Pensando…"
            )
            with st.spinner(spinner_txt):
                resp = ia_responde_gemini(
                    prompt, st.session_state["messages"], df_all, analitos_ls, f_min, f_max
                )
            st.markdown(resp)
        st.session_state["messages"].append({"role": "assistant", "content": resp})
        registrar_auditoria(db_con, usuario_actual, "CHAT_QUERY", prompt[:120])
    if st.button("🗑 Nueva conversación", key="clr"):
        st.session_state["messages"] = [st.session_state["messages"][0]]
        st.rerun()


# ── TAB 6: REGISTRO ──────────────────────────────────────────
def _page_log():
    col_ttl, col_csv, col_pdf = st.columns([3, 1, 1])
    with col_ttl:
        _page_header(
            "📝",
            "Registro de Incidencias",
            "Trazabilidad de acciones correctivas",
            accent="#475569",
        )
        st.caption(f"Fuente activa: {data_src} · Usuario: {usuario_actual}")
    lab_nombre = get_section("lab").get("nombre", "LAB. CENTRAL")
    with col_csv:
        st.markdown("<br>", unsafe_allow_html=True)
        csv_placeholder = st.empty()
    with col_pdf:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📄 Descargar PDF", use_container_width=True, type="primary"):
            if not tiene_permiso(rol_actual, "supervisor"):
                st.error("❌ Solo supervisores y administradores pueden generar PDF.")
            else:
                with st.spinner("Generando informe…"):
                    try:
                        pdf_bytes = generar_pdf(
                            df_all, analitos_ls, data_src, f_min, f_max, lab_nombre
                        )
                        fname = f"AIQC_Informe_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                        st.download_button(
                            "⬇ Guardar PDF",
                            data=pdf_bytes,
                            file_name=fname,
                            mime="application/pdf",
                            use_container_width=True,
                        )
                        registrar_auditoria(db_con, usuario_actual, "EXPORT_PDF", fname)
                        st.success("✅ Informe generado.")
                    except Exception as e:
                        st.error(f"Error: {e}")

    niveles_globales_log = sorted(df_all["Nivel"].unique())
    all_log_frames = []
    for an in analitos_ls:
        for niv in niveles_globales_log:
            sub = eval_rango.get((an, niv), pd.DataFrame())
            if not sub.empty:
                sub = sub.copy()
                sub["_nivel_label"] = NIVELES.get(niv, NIVELES["N"])["label"]
                all_log_frames.append(sub)
    df_full_log = pd.concat(all_log_frames, ignore_index=True) if all_log_frames else pd.DataFrame()
    df_log = (
        df_full_log[df_full_log["Estado"] != "Verde"].copy().reset_index(drop=True)
        if not df_full_log.empty
        else pd.DataFrame()
    )

    if df_log.empty:
        st.success("✅ Sin violaciones en el período seleccionado.")
        with csv_placeholder:
            st.download_button(
                "⬇ Exportar CSV",
                data=b"Sin violaciones",
                file_name="AIQC_sin_incidencias.csv",
                mime="text/csv",
                use_container_width=True,
                disabled=True,
            )
    else:
        acciones_db = load_acciones(db_con)
        hcols = st.columns([1.4, 2.0, 1.4, 1.1, 1.2, 1.3, 1.4, 1.4, 1.3])
        for c, lbl in zip(
            hcols,
            [
                "📅 Fecha",
                "🔬 Analito",
                "Nivel",
                "Valor",
                "Z-Score",
                "Regla",
                "Score",
                "Estado",
                "✅ Acción",
            ],
        ):
            c.markdown(f"**{lbl}**")
        st.markdown("<hr style='border-color:#E2E8F0'>", unsafe_allow_html=True)
        # Clave estable e independiente del filtro activo: si cambia el rango de
        # fechas, el check "Hecha" sigue apuntando a la misma violación. Solo se
        # añade sufijo numérico si hay violaciones idénticas repetidas en el día.
        claves_vistas = {}
        claves_log = []
        for _, row in df_log.iterrows():
            base = (
                f"{row['Fecha'].date()}_{row['Analito']}_"
                f"{row.get('_nivel_label', 'N')}_{row['Regla_Violada']}"
            )
            n_rep = claves_vistas.get(base, 0)
            claves_vistas[base] = n_rep + 1
            claves_log.append(base if n_rep == 0 else f"{base}_{n_rep}")
        for idx, row in df_log.iterrows():
            key = claves_log[idx]
            rcols = st.columns([1.4, 2.0, 1.4, 1.1, 1.2, 1.3, 1.4, 1.4, 1.3])
            rcols[0].write(row["Fecha"].strftime("%d/%m/%Y"))
            rcols[1].write(row["Analito"])
            rcols[2].markdown(nivel_badge(row.get("Nivel", "N")), unsafe_allow_html=True)
            rcols[3].write(str(row["Valor"]))
            rcols[4].write(f"{row['Z_Score']:+.2f}σ")
            rcols[5].write(row["Regla_Violada"])
            rcols[6].write(f"{int(row['Score_Riesgo'])}/100")
            rcols[7].markdown(estado_badge(row["Estado"]), unsafe_allow_html=True)
            prev = acciones_db.get(key, False)
            nuevo = rcols[8].checkbox("Hecha", value=prev, key=f"accion_{key}")
            if nuevo != prev:
                save_accion(db_con, key, nuevo, usuario=usuario_actual)
            st.markdown("<hr style='border-color:#E2E8F0'>", unsafe_allow_html=True)
        acciones_db = load_acciones(db_con)
        total = len(df_log)
        hechas = sum(acciones_db.get(k, False) for k in claves_log)
        pend = total - hechas
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total violaciones", total)
        m2.metric("Acciones tomadas ✅", hechas)
        m3.metric("Pendientes ⏳", pend)
        m4.metric("% completado", f"{int(hechas / total * 100) if total else 0}%")
        csv_bytes = generar_csv(df_log, acciones_db, claves_log)
        with csv_placeholder:
            st.download_button(
                "⬇ Exportar CSV",
                data=csv_bytes,
                file_name=f"AIQC_Incidencias_{f_min.strftime('%Y%m%d')}_{f_max.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                help="CSV con separador ';' y UTF-8 BOM — compatible con Excel español.",
            )
        if hechas == total:
            st.success("🎉 Trazabilidad completa.")
        elif pend:
            st.warning(f"⚠ {pend} violación(es) pendiente(s).")


# ── TAB 7: USUARIOS ──────────────────────────────────────────
def _page_usuarios():
    _page_header("👥", "Gestión de Usuarios", "Altas, roles y permisos de acceso", accent="#BE185D")
    if not tiene_permiso(rol_actual, "admin"):
        st.warning("🔒 Solo los administradores pueden gestionar usuarios.")
        st.info(f"Tu rol actual es **{rol_actual}**. Contacta con el administrador.")
    else:
        st.markdown('<div class="sec-head">Usuarios registrados</div>', unsafe_allow_html=True)
        users = db_con.execute(
            "SELECT id,username,rol,nombre,activo,creado_en,ultimo_acceso FROM usuarios ORDER BY id"
        ).fetchall()
        for uid, uname, rol_u, nombre_u, activo_u, creado, ultimo in users:
            rol_css = {
                "admin": "role-admin",
                "supervisor": "role-supervisor",
                "tecnico": "role-tecnico",
            }.get(rol_u, "role-tecnico")
            activo_icon = "🟢" if activo_u else "🔴"
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            with c1:
                st.markdown(
                    f'<div class="audit-row">{activo_icon} <b>{uname}</b> '
                    f'&nbsp;<span class="{rol_css}">{rol_u.upper()}</span>'
                    f'{"&nbsp;<i>" + nombre_u + "</i>" if nombre_u else ""}</div>',
                    unsafe_allow_html=True,
                )
            with c2:
                st.caption(f"Creado: {creado[:10] if creado else '—'}")
            with c3:
                st.caption(f"Último acceso: {ultimo[:16] if ultimo else 'nunca'}")
            with c4:
                if uname != usuario_actual:
                    btn_lbl = "Desactivar" if activo_u else "Activar"
                    if st.button(btn_lbl, key=f"toggle_{uid}", use_container_width=True):
                        db_con.execute(
                            "UPDATE usuarios SET activo=? WHERE id=?", (0 if activo_u else 1, uid)
                        )
                        db_con.commit()
                        registrar_auditoria(
                            db_con, usuario_actual, f"USUARIO_{btn_lbl.upper()}", uname
                        )
                        st.rerun()

        st.markdown("---")
        st.markdown('<div class="sec-head">Crear nuevo usuario</div>', unsafe_allow_html=True)
        with st.form("form_nuevo_usuario", clear_on_submit=True):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                nuevo_user = st.text_input("Nombre de usuario*", placeholder="tecnico01")
                nuevo_nombre = st.text_input("Nombre completo", placeholder="Ana García")
            with col_f2:
                nuevo_pwd = st.text_input(
                    "Contraseña*", type="password", placeholder="Min. 8 caracteres"
                )
                nuevo_rol = st.selectbox("Rol", options=["tecnico", "supervisor", "admin"])
            if st.form_submit_button("➕ Crear usuario", type="primary", use_container_width=True):
                if not nuevo_user or not nuevo_pwd:
                    st.error("Usuario y contraseña son obligatorios.")
                elif len(nuevo_pwd) < 8:
                    st.error("La contraseña debe tener al menos 8 caracteres.")
                else:
                    existe = db_con.execute(
                        "SELECT id FROM usuarios WHERE username=?", (nuevo_user,)
                    ).fetchone()
                    if existe:
                        st.error(f"El usuario '{nuevo_user}' ya existe.")
                    else:
                        pwd_h = hash_password(nuevo_pwd)
                        db_con.execute(
                            "INSERT INTO usuarios (username,password_hash,rol,nombre) VALUES (?,?,?,?)",
                            (nuevo_user, pwd_h, nuevo_rol, nuevo_nombre),
                        )
                        db_con.commit()
                        registrar_auditoria(
                            db_con, usuario_actual, "USUARIO_CREADO", f"{nuevo_user} [{nuevo_rol}]"
                        )
                        st.success(f"✅ Usuario **{nuevo_user}** creado con rol **{nuevo_rol}**.")
                        st.rerun()

        st.markdown("---")
        st.markdown('<div class="sec-head">Cambiar contraseña</div>', unsafe_allow_html=True)
        with st.form("form_cambiar_pwd", clear_on_submit=True):
            usuarios_lista = [
                r[0]
                for r in db_con.execute(
                    "SELECT username FROM usuarios ORDER BY username"
                ).fetchall()
            ]
            cambiar_a = st.selectbox("Usuario", options=usuarios_lista)
            nueva_pwd = st.text_input(
                "Nueva contraseña*", type="password", placeholder="Min. 8 caracteres"
            )
            confirmar_pwd = st.text_input("Confirmar contraseña*", type="password")
            if st.form_submit_button("🔑 Cambiar contraseña", type="primary"):
                if len(nueva_pwd) < 8:
                    st.error("Mínimo 8 caracteres.")
                elif nueva_pwd != confirmar_pwd:
                    st.error("Las contraseñas no coinciden.")
                else:
                    pwd_h = hash_password(nueva_pwd)
                    db_con.execute(
                        "UPDATE usuarios SET password_hash=? WHERE username=?", (pwd_h, cambiar_a)
                    )
                    db_con.commit()
                    registrar_auditoria(db_con, usuario_actual, "CAMBIO_PASSWORD", cambiar_a)
                    st.success(f"✅ Contraseña de **{cambiar_a}** actualizada.")

        st.markdown("---")
        st.markdown('<div class="sec-head">Registro de auditoría</div>', unsafe_allow_html=True)
        _, col_aud2 = st.columns([3, 1])
        with col_aud2:
            n_registros = st.number_input(
                "Mostrar últimos", min_value=10, max_value=500, value=50, step=10, key="aud_n"
            )
        audit_rows = db_con.execute(
            "SELECT ts,usuario,accion,detalle FROM auditoria ORDER BY id DESC LIMIT ?",
            (int(n_registros),),
        ).fetchall()
        if not audit_rows:
            st.info("Sin registros de auditoría aún.")
        else:
            for ts, aud_user, accion, detalle in audit_rows:
                # Tokens «tinta» de styles.py: los colores vivos como texto
                # sobre la fila clara no llegaban a 4.5:1 (la marca de tiempo
                # se quedaba en 2.50:1).
                color_accion = {
                    "LOGIN_OK": "var(--teal-ink)",
                    "LOGIN_FALLIDO": "var(--red-ink)",
                    "LOGOUT": "var(--faint)",
                    "EXPORT_PDF": "var(--brand-dark)",
                    "SYNC_GITHUB": "#5A4C90",
                }.get(accion, "#475569")
                st.markdown(
                    f'<div class="audit-row">'
                    f'<span style="color:var(--faint);font-size:.75rem">{ts[:16]}</span>&nbsp;&nbsp;'
                    f'<b style="color:var(--text)">{aud_user}</b>&nbsp;&nbsp;'
                    f'<span style="color:{color_accion};font-weight:700;font-size:.78rem">{accion}</span>'
                    f'{"&nbsp;&nbsp;<span style=color:var(--muted);font-size:.78rem>" + detalle[:80] + "</span>" if detalle else ""}'
                    f"</div>",
                    unsafe_allow_html=True,
                )


# ── TAB 8: CONFIGURACIÓN ─────────────────────────────────────
def _page_cfg():
    _page_header(
        "⚙", "Configuración", "Valores objetivo, TEa y parámetros del laboratorio", accent="#64748B"
    )
    st.caption("Introduce los valores objetivo de tus controles y el lote activo.")
    if "cfg_analitos" not in st.session_state:
        st.session_state["cfg_analitos"] = {}
    if "cfg_lote" not in st.session_state:
        st.session_state["cfg_lote"] = "LOT-2025"

    st.markdown('<div class="sec-head">🏷 Lote de reactivos activo</div>', unsafe_allow_html=True)
    col_lote1, _ = st.columns([2, 3])
    with col_lote1:
        lote_input = st.text_input(
            "Número de lote", value=st.session_state["cfg_lote"], placeholder="Ej: LOT-2025-A"
        )
        if st.button("💾 Guardar lote", type="primary", key="btn_lote"):
            st.session_state["cfg_lote"] = lote_input.strip()
            for k in ["df_github", "df_manual"]:
                if st.session_state.get(k) is not None:
                    st.session_state[k]["Lote"] = lote_input.strip()
            registrar_auditoria(db_con, usuario_actual, "CFG_LOTE", lote_input.strip())
            st.success(f"✅ Lote guardado: **{lote_input.strip()}**")

    st.markdown(
        '<div class="sec-head">🎯 Valores objetivo (Media y SD)</div>', unsafe_allow_html=True
    )
    st.info("Introduce los valores objetivo para cada analito y nivel.", icon="ℹ")
    analitos_cfg = sorted(df_all["Analito"].unique()) if not df_all.empty else []
    niveles_cfg = ["N", "PB", "PA"]
    nivel_nombres = {"N": "Normal", "PB": "Patológico Bajo", "PA": "Patológico Alto"}
    cfg_actualizada = {}
    for an in analitos_cfg:
        st.markdown(f"#### 🔬 {an}")
        cols_niv = st.columns(3)
        for col, niv in zip(cols_niv, niveles_cfg):
            with col:
                saved = st.session_state["cfg_analitos"].get(f"{an}_{niv}", {})
                media_saved = saved.get("media", 0.0)
                sd_saved = saved.get("sd", 0.0)
                sub_datos = df_all[(df_all["Analito"] == an) & (df_all["Nivel"] == niv)]
                if not sub_datos.empty and media_saved == 0.0:
                    media_saved = float(sub_datos["Media_Objetivo"].iloc[0])
                    sd_saved = float(sub_datos["SD_Objetivo"].iloc[0])
                st.markdown(f"**{nivel_nombres[niv]}**")
                media_v = st.number_input(
                    f"Media ({niv})",
                    min_value=0.0,
                    value=float(media_saved),
                    step=0.01,
                    format="%.4f",
                    key=f"media_{an}_{niv}",
                )
                sd_v = st.number_input(
                    f"SD ({niv})",
                    min_value=0.0,
                    value=float(sd_saved),
                    step=0.001,
                    format="%.4f",
                    key=f"sd_{an}_{niv}",
                )
                cfg_actualizada[f"{an}_{niv}"] = {"media": media_v, "sd": sd_v}
        st.markdown("---")
    if st.button("💾 Guardar valores objetivo", type="primary", key="btn_cfg_analitos"):
        st.session_state["cfg_analitos"] = cfg_actualizada
        for fuente_key in ["df_github", "df_manual"]:
            df_f = st.session_state.get(fuente_key)
            if df_f is None:
                continue
            for an in analitos_cfg:
                for niv in niveles_cfg:
                    vals = cfg_actualizada.get(f"{an}_{niv}", {})
                    media_n = vals.get("media", 0.0)
                    sd_n = vals.get("sd", 0.0)
                    if media_n > 0 and sd_n > 0:
                        mask = (df_f["Analito"] == an) & (df_f["Nivel"] == niv)
                        df_f.loc[mask, "Media_Objetivo"] = media_n
                        df_f.loc[mask, "SD_Objetivo"] = sd_n
            st.session_state[fuente_key] = df_f
        registrar_auditoria(
            db_con, usuario_actual, "CFG_VALORES_OBJETIVO", f"{len(cfg_actualizada)} entradas"
        )
        st.success("✅ Valores objetivo guardados y aplicados.")
        st.rerun()

    st.markdown(
        '<div class="sec-head">📊 Estado de la sincronización</div>', unsafe_allow_html=True
    )
    col_s1, col_s2, col_s3 = st.columns(3)
    ultima_s = st.session_state.get("github_last_sync")
    with col_s1:
        st.metric("Fuente activa", data_src.replace("☁ ", "").replace("🔬 ", "").replace("📄 ", ""))
    with col_s2:
        st.metric("Última sync", ultima_s.strftime("%d/%m %H:%M") if ultima_s else "—")
    with col_s3:
        st.metric("Registros", len(df_all) if not df_all.empty else 0)
    tiene_gh = bool(get_section("github").get("usuario") and get_section("github").get("repo"))
    if st.button(
        "🔄 Sincronizar desde GitHub",
        use_container_width=True,
        type="primary",
        key="btn_sync_cfg",
        disabled=not tiene_gh,
    ):
        with st.spinner("Conectando con GitHub…"):
            df_gh, msg = leer_csv_github()
        if df_gh is not None:
            cfg_actual = st.session_state.get("cfg_analitos", {})
            lote_actual = st.session_state.get("cfg_lote", "LOT-2025")
            for an in df_gh["Analito"].unique():
                for niv in df_gh["Nivel"].unique():
                    vals = cfg_actual.get(f"{an}_{niv}", {})
                    if vals.get("media", 0) > 0 and vals.get("sd", 0) > 0:
                        mask = (df_gh["Analito"] == an) & (df_gh["Nivel"] == niv)
                        df_gh.loc[mask, "Media_Objetivo"] = vals["media"]
                        df_gh.loc[mask, "SD_Objetivo"] = vals["sd"]
            df_gh["Lote"] = lote_actual
            try:
                guardar_mediciones(db_con, df_gh, fuente="github", usuario=usuario_actual)
                df_gh = cargar_mediciones(db_con, fuente="github")
            except Exception:
                logger.exception("Fallo al persistir mediciones de GitHub (config)")
            st.session_state["df_github"] = df_gh
            st.session_state["data_src_github"] = msg
            st.session_state["github_last_sync"] = datetime.now()
            registrar_auditoria(db_con, usuario_actual, "SYNC_GITHUB", msg)
            st.success(msg)
            st.rerun()


# ==============================================================
# NAVEGACIÓN (páginas)
# st.navigation sustituye a las 8 tabs: solo ejecuta la página activa
# (las tabs renderizaban las 8 en cada rerun). El nav vive en el sidebar.
# ==============================================================
_paginas = [
    st.Page(_page_dashboard, title="Dashboard", icon="📊", default=True),
    st.Page(_page_ewma, title="EWMA / CUSUM", icon="📉"),
    st.Page(_page_sigma, title="Sigma Metrics", icon="📈"),
    st.Page(_page_biorad, title="Guía Bio-Rad", icon="📋"),
    st.Page(_page_chat, title="Asistente IA", icon="🤖"),
    st.Page(_page_log, title="Registro", icon="📝"),
    st.Page(_page_usuarios, title="Usuarios", icon="👥"),
    st.Page(_page_cfg, title="Configuración", icon="⚙"),
]
st.navigation(_paginas, position="sidebar").run()
