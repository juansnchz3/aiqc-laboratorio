# ==============================================================
# Tests de normalización de datos de entrada (aiqc/data_io.py)
# ==============================================================
import pandas as pd

from aiqc.data_io import normalizar_df

COLUMNAS_CONTRATO = ["Fecha", "Analito", "Valor", "Media_Objetivo", "SD_Objetivo", "Nivel", "Lote"]


def df_base(**overrides):
    data = {
        "Fecha": ["01/03/2026", "02/03/2026"],
        "Analito": ["Glucosa", "Glucosa"],
        "Nivel": ["N", "N"],
        "Valor": [101.0, 99.0],
        "Media_Objetivo": [100.0, 100.0],
        "SD_Objetivo": [5.0, 5.0],
        "Lote": ["L1", "L1"],
    }
    data.update(overrides)
    return pd.DataFrame(data)


class TestNormalizarDf:
    def test_columnas_canonicas_pasan_tal_cual(self):
        df, msg = normalizar_df(df_base())
        assert df is not None and msg == ""
        assert list(df.columns) == COLUMNAS_CONTRATO
        assert len(df) == 2

    def test_sinonimos_en_ingles(self):
        raw = df_base().rename(
            columns={
                "Fecha": "Date",
                "Analito": "Analyte",
                "Nivel": "Level",
                "Valor": "Result",
                "Media_Objetivo": "Mean",
                "SD_Objetivo": "SD",
                "Lote": "Lot",
            }
        )
        df, msg = normalizar_df(raw)
        assert df is not None
        assert list(df.columns) == COLUMNAS_CONTRATO

    def test_faltan_columnas_obligatorias(self):
        df, msg = normalizar_df(df_base().drop(columns=["Valor", "SD_Objetivo"]))
        assert df is None
        assert "Valor" in msg and "SD_Objetivo" in msg

    def test_nivel_ausente_por_defecto_n(self):
        df, _ = normalizar_df(df_base().drop(columns=["Nivel"]))
        assert (df["Nivel"] == "N").all()

    def test_lote_ausente_por_defecto_na(self):
        df, _ = normalizar_df(df_base().drop(columns=["Lote"]))
        assert (df["Lote"] == "N/A").all()

    def test_mapeo_de_niveles(self):
        raw = df_base(
            Fecha=["01/03/2026"] * 6,
            Analito=["Glucosa"] * 6,
            Nivel=["1", "Nivel 2", "3", "normal", "Patológico Alto", "pb"],
            Valor=[100.0] * 6,
            Media_Objetivo=[100.0] * 6,
            SD_Objetivo=[5.0] * 6,
            Lote=["L1"] * 6,
        )
        df, _ = normalizar_df(raw)
        assert df["Nivel"].tolist() == ["N", "PB", "PA", "N", "PA", "PB"]

    def test_fechas_dayfirst(self):
        df, _ = normalizar_df(df_base(Fecha=["05/03/2026", "06/03/2026"]))
        assert df["Fecha"].iloc[0] == pd.Timestamp("2026-03-05")

    def test_filas_invalidas_descartadas_con_aviso(self):
        raw = df_base(
            Fecha=["01/03/2026", "fecha-mala"],
            Valor=[101.0, "no-numérico"],
        )
        df, msg = normalizar_df(raw)
        assert df is not None and len(df) == 1
        assert "1" in msg and "descartad" in msg.lower()

    def test_sin_filas_validas(self):
        raw = df_base(Valor=["x", "y"])
        df, msg = normalizar_df(raw)
        assert df is None
        assert "Sin filas válidas" in msg
