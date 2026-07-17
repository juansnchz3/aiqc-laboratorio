# ==============================================================
# Tests de persistencia de mediciones (aiqc/measurements.py)
# BD SQLite en memoria; se crea la tabla `mediciones` a mano igual
# que en database.init_db (evita depender de streamlit al inicializar).
# ==============================================================
import sqlite3

import pandas as pd
import pytest

from aiqc.measurements import (
    CONTRATO,
    guardar_mediciones,
    cargar_mediciones,
    borrar_fuente,
    resumen_fuentes,
)

CREAR_TABLA = """CREATE TABLE mediciones (
    fecha TEXT NOT NULL, analito TEXT NOT NULL, nivel TEXT NOT NULL DEFAULT 'N',
    valor REAL NOT NULL, media_objetivo REAL NOT NULL, sd_objetivo REAL NOT NULL,
    lote TEXT DEFAULT 'N/A', fuente TEXT NOT NULL DEFAULT 'manual',
    cargado_por TEXT DEFAULT 'sistema', cargado_en TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (fecha, analito, nivel, fuente))"""


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.execute(CREAR_TABLA)
    c.commit()
    yield c
    c.close()


def df_ejemplo(n=3, analito="Glucosa", nivel="N", media=100.0):
    fechas = pd.date_range("2026-01-01", periods=n, freq="D")
    return pd.DataFrame(
        {
            "Fecha": fechas,
            "Analito": analito,
            "Nivel": nivel,
            "Valor": [media + i for i in range(n)],
            "Media_Objetivo": media,
            "SD_Objetivo": 5.0,
            "Lote": "L1",
        }
    )


class TestGuardar:
    def test_guardar_devuelve_nuevas(self, con):
        nuevas, actualizadas = guardar_mediciones(con, df_ejemplo(3))
        assert (nuevas, actualizadas) == (3, 0)

    def test_df_vacio_no_hace_nada(self, con):
        assert guardar_mediciones(con, pd.DataFrame()) == (0, 0)
        assert guardar_mediciones(con, None) == (0, 0)

    def test_faltan_columnas_lanza(self, con):
        with pytest.raises(ValueError, match="Faltan columnas"):
            guardar_mediciones(con, df_ejemplo(2).drop(columns=["SD_Objetivo"]))

    def test_recargar_mismo_archivo_no_duplica(self, con):
        guardar_mediciones(con, df_ejemplo(3))
        nuevas, actualizadas = guardar_mediciones(con, df_ejemplo(3))
        assert (nuevas, actualizadas) == (0, 3)
        assert len(cargar_mediciones(con)) == 3  # sigue habiendo 3, no 6

    def test_recarga_actualiza_valor(self, con):
        guardar_mediciones(con, df_ejemplo(1, media=100.0))
        df2 = df_ejemplo(1, media=100.0)
        df2.loc[0, "Valor"] = 999.0
        guardar_mediciones(con, df2)
        cargado = cargar_mediciones(con)
        assert cargado["Valor"].iloc[0] == 999.0

    def test_append_incremental(self, con):
        guardar_mediciones(con, df_ejemplo(3))
        # Nuevas fechas → se acumulan
        df2 = df_ejemplo(3)
        df2["Fecha"] = pd.date_range("2026-02-01", periods=3, freq="D")
        nuevas, _ = guardar_mediciones(con, df2)
        assert nuevas == 3
        assert len(cargar_mediciones(con)) == 6

    def test_fuentes_distintas_no_colisionan(self, con):
        # Misma fecha/analito/nivel pero fuentes distintas → filas separadas
        guardar_mediciones(con, df_ejemplo(2), fuente="manual")
        guardar_mediciones(con, df_ejemplo(2), fuente="github")
        assert len(cargar_mediciones(con)) == 4
        assert len(cargar_mediciones(con, fuente="manual")) == 2


class TestCargar:
    def test_vacio_devuelve_df_con_contrato(self, con):
        df = cargar_mediciones(con)
        assert df.empty
        assert list(df.columns) == CONTRATO

    def test_roundtrip_conserva_contrato(self, con):
        guardar_mediciones(con, df_ejemplo(3))
        df = cargar_mediciones(con)
        assert list(df.columns) == CONTRATO
        assert pd.api.types.is_datetime64_any_dtype(df["Fecha"])
        assert df["Analito"].iloc[0] == "Glucosa"

    def test_filtro_por_fuente(self, con):
        guardar_mediciones(con, df_ejemplo(2, analito="Glucosa"), fuente="manual")
        guardar_mediciones(con, df_ejemplo(2, analito="Sodio"), fuente="github")
        assert cargar_mediciones(con, fuente="github")["Analito"].unique().tolist() == ["Sodio"]


class TestBorrarYResumen:
    def test_borrar_fuente(self, con):
        guardar_mediciones(con, df_ejemplo(3), fuente="manual")
        guardar_mediciones(con, df_ejemplo(3, analito="Sodio"), fuente="github")
        borradas = borrar_fuente(con, "manual")
        assert borradas == 3
        assert len(cargar_mediciones(con)) == 3
        assert cargar_mediciones(con)["Analito"].unique().tolist() == ["Sodio"]

    def test_resumen_fuentes(self, con):
        guardar_mediciones(con, df_ejemplo(3, analito="Glucosa"), fuente="manual")
        guardar_mediciones(con, df_ejemplo(2, analito="Sodio", nivel="PA"), fuente="manual")
        resumen = resumen_fuentes(con)
        assert resumen["manual"]["filas"] == 5
        assert resumen["manual"]["analitos"] == 2
        assert resumen["manual"]["ultima_carga"] is not None
