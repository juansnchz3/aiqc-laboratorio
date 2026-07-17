# ==============================================================
# Tests del núcleo estadístico (aiqc/qc_rules.py)
# Series construidas a partir de Z-scores conocidos: Valor = media + z*sd.
# ==============================================================
import pandas as pd
import pytest

from aiqc.qc_rules import (
    evaluar_westgard,
    evaluar_r4s,
    calcular_ewma,
    calcular_cusum,
    calcular_sigma,
)

MEDIA = 100.0
SD = 5.0


def serie_desde_z(z_list, analito="Glucosa", nivel="N", media=MEDIA, sd=SD):
    fechas = pd.date_range("2026-01-01", periods=len(z_list), freq="D")
    return pd.DataFrame(
        {
            "Fecha": fechas,
            "Analito": analito,
            "Nivel": nivel,
            "Valor": [media + z * sd for z in z_list],
            "Media_Objetivo": media,
            "SD_Objetivo": sd,
            "Lote": "LOT-TEST",
        }
    )


# ==============================================================
# WESTGARD
# ==============================================================
class TestWestgard:
    def test_serie_en_control_todo_verde(self):
        df = evaluar_westgard(serie_desde_z([0.2, -0.5, 0.8, -0.3, 0.1]))
        assert (df["Estado"] == "Verde").all()
        assert (df["Regla_Violada"] == "—").all()

    def test_z_score_calculado(self):
        df = evaluar_westgard(serie_desde_z([1.0, -2.0]))
        assert df["Z_Score"].tolist() == pytest.approx([1.0, -2.0])

    def test_1_3s_rojo(self):
        df = evaluar_westgard(serie_desde_z([0.0, 3.2]))
        u = df.iloc[-1]
        assert (u["Regla_Violada"], u["Estado"], u["Score_Riesgo"]) == ("1_3s", "Rojo", 90)

    def test_1_3s_negativo(self):
        df = evaluar_westgard(serie_desde_z([0.0, -3.0]))
        assert df.iloc[-1]["Regla_Violada"] == "1_3s"

    def test_2_2s_rojo(self):
        df = evaluar_westgard(serie_desde_z([0.0, 2.3, 2.4]))
        assert df.iloc[1]["Regla_Violada"] == "1_2s (warn)"  # aún no hay pareja
        u = df.iloc[-1]
        assert (u["Regla_Violada"], u["Estado"]) == ("2_2s", "Rojo")

    def test_2_2s_no_dispara_signos_opuestos(self):
        df = evaluar_westgard(serie_desde_z([2.3, -2.4]))
        assert df.iloc[-1]["Regla_Violada"] == "1_2s (warn)"

    def test_4_1s_ambar(self):
        df = evaluar_westgard(serie_desde_z([0.0, 1.2, 1.3, 1.1, 1.4]))
        u = df.iloc[-1]
        assert (u["Regla_Violada"], u["Estado"]) == ("4_1s", "Ámbar")

    def test_10_x_ambar(self):
        df = evaluar_westgard(serie_desde_z([0.5] * 10))
        u = df.iloc[-1]
        assert (u["Regla_Violada"], u["Estado"]) == ("10_x", "Ámbar")
        assert df.iloc[8]["Regla_Violada"] == "—"  # con 9 aún no

    def test_1_2s_warning(self):
        df = evaluar_westgard(serie_desde_z([0.0, 2.2]))
        u = df.iloc[-1]
        assert (u["Regla_Violada"], u["Estado"]) == ("1_2s (warn)", "Ámbar")

    def test_ordena_por_fecha(self):
        df_in = serie_desde_z([0.0, 3.5]).iloc[::-1]  # desordenada
        df = evaluar_westgard(df_in)
        assert df.iloc[-1]["Regla_Violada"] == "1_3s"

    def test_score_riesgo_verde_proporcional_a_z(self):
        df = evaluar_westgard(serie_desde_z([1.0]))
        assert df.iloc[0]["Score_Riesgo"] == 18


# ==============================================================
# R-4s (multi-nivel)
# ==============================================================
class TestR4s:
    F_MIN = pd.Timestamp("2026-01-01").date()
    F_MAX = pd.Timestamp("2026-12-31").date()

    def test_dispara_con_niveles_opuestos(self):
        df = pd.concat(
            [
                serie_desde_z([0.0, 2.2], nivel="N"),
                serie_desde_z([0.0, -2.1], nivel="PA", media=200.0, sd=8.0),
            ]
        )
        r = evaluar_r4s(df, "Glucosa", self.F_MIN, self.F_MAX)
        assert r is not None and r["dispara"]
        assert r["diferencia"] == pytest.approx(4.3)

    def test_no_dispara_mismo_signo(self):
        df = pd.concat(
            [
                serie_desde_z([2.2], nivel="N"),
                serie_desde_z([2.5], nivel="PA", media=200.0, sd=8.0),
            ]
        )
        assert evaluar_r4s(df, "Glucosa", self.F_MIN, self.F_MAX) is None

    def test_no_dispara_diferencia_menor_de_4(self):
        df = pd.concat(
            [
                serie_desde_z([1.8], nivel="N"),
                serie_desde_z([-1.9], nivel="PA", media=200.0, sd=8.0),
            ]
        )
        assert evaluar_r4s(df, "Glucosa", self.F_MIN, self.F_MAX) is None

    def test_requiere_dos_niveles(self):
        df = serie_desde_z([2.5, -2.5], nivel="N")
        assert evaluar_r4s(df, "Glucosa", self.F_MIN, self.F_MAX) is None


# ==============================================================
# EWMA
# ==============================================================
class TestEwma:
    def test_vacio(self):
        r = calcular_ewma([])
        assert r["ewma"] == [] and r["inicio_deriva"] is None

    def test_serie_centrada_verde(self):
        r = calcular_ewma([0.1, -0.1, 0.05, -0.05, 0.0])
        assert all(e == "Verde" for e in r["estados"])
        assert r["inicio_deriva"] is None

    def test_deriva_sostenida_llega_a_rojo(self):
        # z constante = 2 → EWMA converge a 2 y cruza el límite de acción (3σ_EWMA=1.0 con λ=0.2)
        r = calcular_ewma([2.0] * 20, lam=0.20)
        assert r["estados"][-1] == "Rojo"
        assert r["inicio_deriva"] is not None

    def test_limites_para_lambda(self):
        r = calcular_ewma([0.0], lam=0.20)
        assert r["sigma_ewma"] == pytest.approx(0.3333, abs=1e-4)
        assert r["lim_act"] == pytest.approx(3 * r["sigma_ewma"], abs=1e-3)


# ==============================================================
# CUSUM
# ==============================================================
class TestCusum:
    def test_vacio(self):
        r = calcular_cusum([])
        assert r["primera_alarma"] is None and r["max_cp"] == 0

    def test_sin_deriva_sin_alarma(self):
        r = calcular_cusum([0.2, -0.3, 0.1, -0.1] * 5)
        assert r["primera_alarma"] is None

    def test_deriva_ascendente(self):
        # z=1.5, k=0.5 → C+ crece 1.0 por punto → supera h=5 en el índice 5
        r = calcular_cusum([1.5] * 10, k=0.5, h=5.0)
        assert r["primera_alarma"] == 5
        assert r["tipo_deriva"] == "ascendente"

    def test_deriva_descendente(self):
        r = calcular_cusum([-1.5] * 10, k=0.5, h=5.0)
        assert r["tipo_deriva"] == "descendente"


# ==============================================================
# SIGMA METRICS
# ==============================================================
class TestSigma:
    def test_vacio(self):
        assert calcular_sigma(pd.DataFrame(), 10.0) == {}

    def test_sin_sesgo_clase_mundial(self):
        # CV = 5/100 = 5% ; sesgo 0 ; TEa 30 → sigma = 6
        df = serie_desde_z([0.0] * 10)
        r = calcular_sigma(df, 30.0)
        assert r["sigma"] == pytest.approx(6.0)
        assert r["categoria"] == "Clase Mundial"

    def test_sesgo_reduce_sigma(self):
        # Todos los valores a +1SD → sesgo = 5% → sigma = (30-5)/5 = 5
        df = serie_desde_z([1.0] * 10)
        r = calcular_sigma(df, 30.0)
        assert r["sigma"] == pytest.approx(5.0)
        assert r["sesgo_pct"] == pytest.approx(5.0)

    def test_categorias(self):
        df = serie_desde_z([0.0] * 5)
        assert calcular_sigma(df, 17.5)["categoria"] == "Aceptable"  # 3.5σ
        assert calcular_sigma(df, 10.0)["categoria"] == "Revisar metodo"  # 2σ
        assert calcular_sigma(df, 22.5)["categoria"] == "Buena calidad"  # 4.5σ
