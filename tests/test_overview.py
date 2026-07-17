# ==============================================================
# Tests del panel de resumen (aiqc/overview.py) — solo la capa de datos.
# render_overview_panel embebe HTML vía streamlit y no se testea aquí.
# ==============================================================
import pandas as pd

from aiqc.overview import construir_resumen
from aiqc.qc_rules import evaluar_westgard


def eval_serie(z_list, analito="Glucosa", nivel="N", media=100.0, sd=5.0):
    fechas = pd.date_range("2026-01-01", periods=len(z_list), freq="D")
    df = pd.DataFrame(
        {
            "Fecha": fechas,
            "Analito": analito,
            "Nivel": nivel,
            "Valor": [media + z * sd for z in z_list],
            "Media_Objetivo": media,
            "SD_Objetivo": sd,
            "Lote": "L1",
        }
    )
    return evaluar_westgard(df)


class TestConstruirResumen:
    def test_vacio(self):
        assert construir_resumen({}, {}) == []

    def test_un_analito_un_nivel(self):
        ec = {("Glucosa", "N"): eval_serie([0.1, -0.2, 0.0])}
        r = construir_resumen(ec, {})
        assert len(r) == 1
        assert r[0]["analito"] == "Glucosa"
        assert r[0]["peor_estado"] == "Verde"
        assert r[0]["niveles"][0]["nivel"] == "N"

    def test_peor_estado_es_el_maximo(self):
        ec = {
            ("Glucosa", "N"): eval_serie([0.0, 0.1]),  # Verde
            ("Glucosa", "PA"): eval_serie([0.0, 3.5], nivel="PA"),  # Rojo (1_3s)
        }
        r = construir_resumen(ec, {})
        assert r[0]["peor_estado"] == "Rojo"

    def test_ordena_rojo_primero(self):
        ec = {
            ("Sodio", "N"): eval_serie([0.0, 0.1], analito="Sodio"),  # Verde
            ("Glucosa", "N"): eval_serie([0.0, 3.5]),  # Rojo
        }
        r = construir_resumen(ec, {})
        assert [a["analito"] for a in r] == ["Glucosa", "Sodio"]

    def test_niveles_ordenados_n_pb_pa(self):
        ec = {
            ("Glucosa", "PA"): eval_serie([0.0], nivel="PA"),
            ("Glucosa", "N"): eval_serie([0.0], nivel="N"),
            ("Glucosa", "PB"): eval_serie([0.0], nivel="PB"),
        }
        r = construir_resumen(ec, {})
        assert [n["nivel"] for n in r[0]["niveles"]] == ["N", "PB", "PA"]

    def test_ignora_dfs_vacios(self):
        ec = {("Glucosa", "N"): eval_serie([0.0]), ("Glucosa", "PB"): pd.DataFrame()}
        r = construir_resumen(ec, {})
        assert len(r[0]["niveles"]) == 1

    def test_incluye_r4s(self):
        ec = {("Glucosa", "N"): eval_serie([0.0])}
        r4s = {"Glucosa": {"label_a": "Normal", "label_b": "Pat. Alto"}}
        r = construir_resumen(ec, r4s)
        assert r[0]["r4s"]["label_a"] == "Normal"

    def test_sin_r4s_es_none(self):
        ec = {("Glucosa", "N"): eval_serie([0.0])}
        r = construir_resumen(ec, {})
        assert r[0]["r4s"] is None

    def test_campos_de_nivel(self):
        ec = {("Glucosa", "N"): eval_serie([0.0, 2.2])}  # último 1_2s warn
        n = construir_resumen(ec, {})[0]["niveles"][0]
        assert set(n) == {"nivel", "nivel_label", "estado", "valor", "z", "regla", "score"}
        assert n["estado"] == "Ámbar"
