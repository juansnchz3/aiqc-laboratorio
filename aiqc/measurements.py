# ==============================================================
# AIQC – Persistencia de mediciones QC (SQLite)
#   · guardar_mediciones() : append con dedup (INSERT OR REPLACE)
#   · cargar_mediciones()  : DataFrame estándar desde la BD
#   · borrar_fuente()      : elimina todas las filas de una fuente
#   · resumen_fuentes()    : conteo por fuente (para la UI)
#
# El contrato de datos es el mismo que en todo el proyecto:
#   Fecha, Analito, Nivel, Valor, Media_Objetivo, SD_Objetivo, Lote.
# Este módulo traduce entre ese DataFrame y las columnas de la tabla
# `mediciones` (definida en database.init_db). Sin dependencias de UI.
#
# NOTA DE DESPLIEGUE: en Streamlit Community Cloud el disco es EFÍMERO;
# la BD sobrevive a recargas y reruns pero NO a un redeploy/reinicio del
# contenedor. Para persistencia duradera usar una BD externa (Postgres,
# Turso/libSQL) vía [db].path o un conector dedicado. Ver ARCHITECTURE.md.
# ==============================================================
import logging

import pandas as pd

logger = logging.getLogger("AIQC")

CONTRATO = ["Fecha", "Analito", "Nivel", "Valor", "Media_Objetivo", "SD_Objetivo", "Lote"]

# Mapeo columna del contrato → columna de la tabla.
_COL_A_DB = {
    "Fecha": "fecha",
    "Analito": "analito",
    "Nivel": "nivel",
    "Valor": "valor",
    "Media_Objetivo": "media_objetivo",
    "SD_Objetivo": "sd_objetivo",
    "Lote": "lote",
}
_DB_A_COL = {v: k for k, v in _COL_A_DB.items()}


def guardar_mediciones(con, df, fuente="manual", usuario="sistema"):
    """Persiste el DataFrame (contrato estándar) en la tabla `mediciones`.

    Usa INSERT OR REPLACE con clave (fecha, analito, nivel, fuente): recargar
    el mismo archivo actualiza las filas existentes en vez de duplicarlas.
    Devuelve (n_guardadas, n_actualizadas).
    """
    if df is None or df.empty:
        return 0, 0
    faltan = [c for c in CONTRATO if c not in df.columns]
    if faltan:
        raise ValueError(f"Faltan columnas del contrato: {', '.join(faltan)}")

    # Cuántas de estas claves ya existían (para informar actualizadas vs nuevas).
    existentes = {
        (r[0], r[1], r[2])
        for r in con.execute(
            "SELECT fecha, analito, nivel FROM mediciones WHERE fuente=?", (fuente,)
        ).fetchall()
    }

    filas = []
    n_actualizadas = 0
    for _, row in df.iterrows():
        fecha_iso = pd.Timestamp(row["Fecha"]).strftime("%Y-%m-%d")
        nivel = row["Nivel"]
        analito = row["Analito"]
        if (fecha_iso, analito, nivel) in existentes:
            n_actualizadas += 1
        filas.append(
            (
                fecha_iso,
                analito,
                nivel,
                float(row["Valor"]),
                float(row["Media_Objetivo"]),
                float(row["SD_Objetivo"]),
                row.get("Lote", "N/A"),
                fuente,
                usuario,
            )
        )
    con.executemany(
        "INSERT OR REPLACE INTO mediciones "
        "(fecha, analito, nivel, valor, media_objetivo, sd_objetivo, lote, "
        " fuente, cargado_por, cargado_en) "
        "VALUES (?,?,?,?,?,?,?,?,?, datetime('now'))",
        filas,
    )
    con.commit()
    n_nuevas = len(filas) - n_actualizadas
    logger.info(
        "Mediciones guardadas: %d nuevas, %d actualizadas (fuente=%s)",
        n_nuevas,
        n_actualizadas,
        fuente,
    )
    return n_nuevas, n_actualizadas


def cargar_mediciones(con, fuente=None):
    """Devuelve un DataFrame (contrato estándar) con las mediciones persistidas.

    Si `fuente` es None se cargan todas las fuentes. DataFrame vacío si no hay.
    """
    sql = (
        "SELECT fecha, analito, nivel, valor, media_objetivo, sd_objetivo, lote " "FROM mediciones"
    )
    params = ()
    if fuente is not None:
        sql += " WHERE fuente=?"
        params = (fuente,)
    sql += " ORDER BY analito, nivel, fecha"
    df = pd.read_sql_query(sql, con, params=params)
    if df.empty:
        return pd.DataFrame(columns=CONTRATO)
    df = df.rename(columns=_DB_A_COL)
    df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")
    return df[CONTRATO].reset_index(drop=True)


def borrar_fuente(con, fuente):
    """Elimina todas las mediciones de una fuente. Devuelve nº de filas borradas."""
    cur = con.execute("DELETE FROM mediciones WHERE fuente=?", (fuente,))
    con.commit()
    logger.info("Mediciones borradas: %d (fuente=%s)", cur.rowcount, fuente)
    return cur.rowcount


def resumen_fuentes(con):
    """{fuente: {"filas": n, "analitos": n, "ultima_carga": ts}} para la UI."""
    rows = con.execute(
        "SELECT fuente, COUNT(*), COUNT(DISTINCT analito), MAX(cargado_en) "
        "FROM mediciones GROUP BY fuente ORDER BY fuente"
    ).fetchall()
    return {
        fuente: {"filas": filas, "analitos": analitos, "ultima_carga": ultima}
        for fuente, filas, analitos, ultima in rows
    }
