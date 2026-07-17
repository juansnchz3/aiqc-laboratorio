# ==============================================================
# AIQC – Entrada/salida de datos
#   · build_demo()        : datos simulados (Amilasa, ALT)
#   · leer_archivo()      : CSV / Excel subidos
#   · leer_csv_github()   : sync OpenLab vía GitHub API
#   · normalizar_df()     : homogeneiza columnas y niveles
# ==============================================================
import io
from datetime import datetime, timedelta

import pandas as pd
import numpy as np
import requests
import streamlit as st

from .config import get_section


# ==============================================================
# DATOS DEMO
# ==============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def build_demo():
    np.random.seed(42)
    today = pd.Timestamp.now().replace(hour=0, minute=0, second=0, microsecond=0)
    dates = [today - timedelta(days=29 - i) for i in range(30)]
    DEMO = {
        "Amilasa": {
            "N": {
                "media": 50.0,
                "sd": 2.0,
                "patron": [0] * 20 + [0.4, 0.7, 1.0, 1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.1],
            },
            "PB": {"media": 25.0, "sd": 1.5, "patron": [0] * 27 + [-2.2, -2.5, -2.8]},
            "PA": {"media": 150.0, "sd": 6.0, "patron": [0] * 25 + [1.1, 1.3, 1.5, 1.8, 2.2]},
        },
        "ALT (Transaminasa)": {
            "N": {"media": 35.0, "sd": 2.5, "patron": [0] * 30},
            "PB": {"media": 12.0, "sd": 1.5, "patron": [0] * 26 + [1.2, -1.3, 1.4, -1.5]},
            "PA": {"media": 120.0, "sd": 8.0, "patron": [0] * 30},
        },
    }
    rows = []
    for analito, niveles in DEMO.items():
        for nivel_cod, cfg in niveles.items():
            media = cfg["media"]
            sd = cfg["sd"]
            patron = cfg["patron"]
            for i, d in enumerate(dates):
                drift = patron[i] * sd
                ruido = np.random.normal(0, sd * 0.6)
                rows.append(
                    {
                        "Fecha": d,
                        "Analito": analito,
                        "Nivel": nivel_cod,
                        "Valor": round(media + drift + ruido, 3),
                        "Media_Objetivo": media,
                        "SD_Objetivo": sd,
                        "Lote": "LOT-DEMO-2025",
                    }
                )
    return pd.DataFrame(rows)


# ==============================================================
# CARGA CSV/XLSX – normalización
# ==============================================================
COL_SYNONYMS = {
    "Fecha": ["fecha", "date", "dia", "timestamp", "time", "datetime"],
    "Analito": ["analito", "analyte", "test", "prueba", "parametro", "magnitud"],
    "Nivel": ["nivel", "level", "control_level", "qc_level", "tipo_control"],
    "Valor": ["valor", "value", "resultado", "result", "medicion", "concentracion"],
    "Media_Objetivo": ["media_objetivo", "media", "mean", "target", "objetivo", "xbar"],
    "SD_Objetivo": ["sd_objetivo", "sd", "desviacion", "std", "sigma", "desvest"],
    "Lote": ["lote", "lot", "batch", "lote_reactivo", "reactivo"],
}


def _norm(s):
    return (
        s.lower().strip().translate(str.maketrans("áéíóúàèìòùäëïöüÁÉÍÓÚ", "aeiouaeiouaeiouAEIOU"))
    )


def normalizar_df(df):
    df_n = {_norm(c): c for c in df.columns}
    rename = {}
    for interno, sins in COL_SYNONYMS.items():
        for s in sins:
            if s in df_n:
                rename[df_n[s]] = interno
                break
        if interno not in rename.values():
            for cn, co in df_n.items():
                if any(s in cn or cn in s for s in sins):
                    rename[co] = interno
                    break
    df2 = df.rename(columns=rename)
    obligatorias = ["Fecha", "Analito", "Valor", "Media_Objetivo", "SD_Objetivo"]
    faltan = [c for c in obligatorias if c not in df2.columns]
    if faltan:
        return None, f"Columnas no encontradas: {', '.join(faltan)}."
    if "Nivel" not in df2.columns:
        df2["Nivel"] = "N"
    if "Lote" not in df2.columns:
        df2["Lote"] = "N/A"
    df2["Fecha"] = pd.to_datetime(df2["Fecha"], dayfirst=True, errors="coerce")
    df2["Valor"] = pd.to_numeric(df2["Valor"], errors="coerce")
    df2["Media_Objetivo"] = pd.to_numeric(df2["Media_Objetivo"], errors="coerce")
    df2["SD_Objetivo"] = pd.to_numeric(df2["SD_Objetivo"], errors="coerce")
    nivel_map = {
        "n": "N",
        "normal": "N",
        "nivel 1": "N",
        "nivel1": "N",
        "n1": "N",
        "1": "N",
        "pb": "PB",
        "patologico bajo": "PB",
        "bajo": "PB",
        "nivel 2": "PB",
        "n2": "PB",
        "2": "PB",
        "pa": "PA",
        "patologico alto": "PA",
        "alto": "PA",
        "nivel 3": "PA",
        "n3": "PA",
        "3": "PA",
    }
    df2["Nivel"] = df2["Nivel"].astype(str).map(lambda x: nivel_map.get(_norm(x), "N"))
    n_antes = len(df2)
    df2 = df2.dropna(subset=obligatorias)
    if df2.empty:
        return None, "Sin filas válidas."
    n_descartadas = n_antes - len(df2)
    aviso = (
        f"⚠ {n_descartadas} fila(s) descartada(s) por fecha o valor ilegible."
        if n_descartadas
        else ""
    )
    return df2[obligatorias + ["Nivel", "Lote"]].reset_index(drop=True), aviso


def leer_archivo(uploaded):
    name = uploaded.name.lower()
    try:
        raw = (
            pd.read_csv(uploaded, sep=None, engine="python")
            if name.endswith(".csv")
            else pd.read_excel(uploaded)
        )
        return normalizar_df(raw)
    except Exception as e:
        return None, f"Error: {e}"


# ==============================================================
# GITHUB SYNC (OpenLab)
# ==============================================================
def leer_csv_github():
    try:
        cfg = get_section("github")
        usuario = cfg.get("usuario", "")
        repo = cfg.get("repo", "")
        rama = cfg.get("rama", "main")
        archivo = cfg.get("archivo", "data/controles_qc.csv")
        token = cfg.get("token", "")
        if not all([usuario, repo, archivo]):
            return None, "Faltan datos en secrets.toml — sección [github]."
        url = f"https://api.github.com/repos/{usuario}/{repo}/contents/{archivo}?ref={rama}"
        headers = {"Accept": "application/vnd.github.raw+json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        r = requests.get(url, headers=headers, timeout=20)
        if r.status_code == 404:
            return None, f"Archivo no encontrado: `{archivo}`."
        if r.status_code == 401:
            return None, "Token de GitHub inválido."
        if r.status_code != 200:
            return None, f"Error GitHub {r.status_code}: {r.text[:200]}"
        contenido = r.content
        try:
            df_raw = pd.read_csv(io.BytesIO(contenido), sep=";", encoding="utf-8-sig")
        except Exception:
            df_raw = pd.read_csv(
                io.BytesIO(contenido), sep=None, engine="python", encoding="utf-8-sig"
            )
        df, aviso = normalizar_df(df_raw)
        if df is None:
            return None, f"CSV descargado pero formato incorrecto: {aviso}"
        ts = datetime.now().strftime("%d/%m/%Y %H:%M")
        extra = f" · {aviso}" if aviso else ""
        return df, f"✅ {len(df)} filas · {df['Analito'].nunique()} analito(s) · sync {ts}{extra}"
    except requests.exceptions.ConnectionError:
        return None, "Sin conexión a internet."
    except Exception as e:
        return None, f"Error inesperado: {str(e)[:200]}"


def auto_refresh_github():
    cfg_gh = get_section("github")
    if not (cfg_gh.get("usuario") and cfg_gh.get("repo") and cfg_gh.get("archivo")):
        return
    ahora = datetime.now()
    ultima = st.session_state.get("github_last_sync")
    if ultima is None or (ahora - ultima).total_seconds() > 3600:
        df_gh, msg = leer_csv_github()
        if df_gh is not None:
            st.session_state["df_github"] = df_gh
            st.session_state["data_src_github"] = msg
            st.session_state["github_last_sync"] = ahora
