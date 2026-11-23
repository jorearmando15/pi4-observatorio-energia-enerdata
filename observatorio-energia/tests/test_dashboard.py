"""Pruebas de los calculos del dashboard (pregunta propia)."""
import pandas as pd

from dashboard.datos import (ajuste_lineal, correlacion_oni_matriz, detalle_mensual,
                             generacion_vs_oni, intervalos_enso, matriz_por_fase)


def _generacion() -> pd.DataFrame:
    """Generacion mensual de juguete: hidraulica y termica para 4 meses."""
    return pd.DataFrame(
        {
            "mes": pd.to_datetime(
                ["2024-01-01", "2024-01-01", "2024-02-01", "2024-02-01",
                 "2024-03-01", "2024-03-01", "2024-04-01", "2024-04-01"]
            ),
            "tipo": ["HIDRAULICA", "TERMICA"] * 4,
            "participacion_pct": [50.0, 45.0, 75.0, 20.0, 85.0, 10.0, 80.0, 15.0],
        }
    )


def _mercado() -> pd.DataFrame:
    """ONI de juguete. Abril no tiene ONI: debe quedar como 'Sin dato'."""
    return pd.DataFrame(
        {
            "mes": pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
            "oni": [2.0, 0.0, -1.0],
            "fase_enso": ["El Niño", "Neutral", "La Niña"],
        }
    )


def test_generacion_vs_oni_pasa_tipos_a_columnas():
    tabla = generacion_vs_oni(_generacion(), _mercado())

    assert list(tabla["mes"]) == sorted(tabla["mes"])
    assert {"hidraulica_pct", "termica_pct", "oni", "fase_enso"} <= set(tabla.columns)
    enero = tabla.loc[tabla["mes"] == pd.Timestamp("2024-01-01")].iloc[0]
    assert enero["termica_pct"] == 45.0
    assert enero["fase_enso"] == "El Niño"


def test_generacion_vs_oni_marca_sin_dato_si_falta_el_oni():
    tabla = generacion_vs_oni(_generacion(), _mercado())

    abril = tabla.loc[tabla["mes"] == pd.Timestamp("2024-04-01")].iloc[0]
    assert abril["fase_enso"] == "Sin dato"
    assert pd.isna(abril["oni"])


def test_matriz_por_fase_promedia_ordena_y_cuenta_los_meses():
    resumen = matriz_por_fase(generacion_vs_oni(_generacion(), _mercado()))

    assert list(resumen["fase_enso"]) == ["El Niño", "Neutral", "La Niña"]
    nino = resumen.loc[resumen["fase_enso"] == "El Niño"].iloc[0]
    assert nino["termica_pct"] == 45.0
    assert nino["hidraulica_pct"] == 50.0
    assert nino["meses"] == 1
    assert nino["etiqueta"] == "El Niño (1 mes)"


def test_correlacion_oni_matriz_tiene_el_signo_esperado():
    correlaciones = correlacion_oni_matriz(generacion_vs_oni(_generacion(), _mercado()))
    valores = correlaciones.set_index("tipo")["correlacion"]

    # Mas ONI = mas termica y menos hidraulica
    assert valores["termica"] > 0.9
    assert valores["hidraulica"] < -0.9


def test_intervalos_enso_cubren_un_mes():
    intervalos = intervalos_enso(generacion_vs_oni(_generacion(), _mercado()))

    enero = intervalos.loc[intervalos["mes"] == pd.Timestamp("2024-01-01")].iloc[0]
    assert enero["mes_fin"] == pd.Timestamp("2024-02-01")
    assert enero["fase_enso"] == "El Niño"


def test_detalle_mensual_ordena_y_formatea():
    detalle = detalle_mensual(generacion_vs_oni(_generacion(), _mercado()))

    assert list(detalle["Mes"]) == ["2024-01", "2024-02", "2024-03", "2024-04"]
    assert "Térmica (%)" in detalle.columns
    assert detalle.loc[detalle["Mes"] == "2024-01", "Térmica (%)"].iloc[0] == 45.0


def test_ajuste_lineal_calcula_pendiente_y_r2():
    ajuste = ajuste_lineal(generacion_vs_oni(_generacion(), _mercado()),
                           "oni", "termica_pct")

    assert ajuste["pendiente"] > 0
    assert 0.9 < ajuste["r2"] <= 1
    assert ajuste["n"] == 3


def test_ajuste_lineal_sin_datos_suficientes():
    ajuste = ajuste_lineal(pd.DataFrame({"x": [1.0], "y": [2.0]}), "x", "y")

    assert ajuste["pendiente"] is None
    assert ajuste["r2"] is None
    assert ajuste["n"] == 1
