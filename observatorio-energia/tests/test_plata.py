"""Pruebas unitarias de las reglas nuevas de limpieza de la capa plata."""
import pandas as pd

from src.quality.esquemas import (
    ESQUEMA_NOAA_ONI,
    ESQUEMA_XM_PRECIO,
    ESQUEMA_XM_RECURSOS,
    ESQUEMA_XM_RECURSOS_CUARENTENA,
)
from src.silver.enerandes import limpiar as limpiar_enerandes
from src.silver.ideam import limpiar_precipitacion
from src.silver.noaa import limpiar as limpiar_noaa
from src.silver.xm import HORAS, limpiar_horario, separar_recursos


def ventas_ejemplo(encabezados, filas):
    return pd.DataFrame(
        [encabezados, *filas],
        columns=[f"col_{indice}" for indice in range(len(encabezados))],
    )


def test_enerandes_convierte_mwh_a_kwh():
    bronce = ventas_ejemplo(
        ["PERIODO", "MUNICIPIO", "SEGMENTO CLIENTE", "MODALIDAD",
         "ENERGIA", "UNIDAD", "VALOR ($)", "NUM CLIENTES"],
        [["mar-24", "Medellín", "Comercial", "Bolsa", "1.25", "MWh", "2000", "2"]],
    )
    tabla, cuarentena, _ = limpiar_enerandes(bronce, 2024)
    assert tabla.loc[0, "energia_kwh"] == 1250
    assert tabla.loc[0, "periodo"] == "2024-03"
    assert cuarentena.empty


def test_enerandes_lee_mes_anio_y_fecha_dia_mes_anio():
    encabezados_2024 = [
        "PERIODO", "MUNICIPIO", "SEGMENTO CLIENTE", "MODALIDAD",
        "ENERGIA", "UNIDAD", "VALOR ($)", "NUM CLIENTES",
    ]
    filas_2024 = [
        ["03/2024", "Medellín", "Comercial", "Bolsa", "100", "kWh", "200", "2"],
    ]
    tabla_2024, _, _ = limpiar_enerandes(ventas_ejemplo(encabezados_2024, filas_2024), 2024)
    assert tabla_2024.loc[0, "periodo"] == "2024-03"

    encabezados_2026 = [
        "Fecha corte", "Ciudad", "Tipo cliente", "Compra", "kWh",
        "Total facturado COP", "Clientes activos",
    ]
    filas_2026 = [["01/03/2026", "Bello", "Industrial", "Bolsa", "100", "200", "2"]]
    tabla_2026, _, _ = limpiar_enerandes(ventas_ejemplo(encabezados_2026, filas_2026), 2026)
    assert tabla_2026.loc[0, "periodo"] == "2026-03"


def test_noaa_asigna_mes_central_y_fase_en_los_umbral():
    bronce = pd.DataFrame(
        {
            "SEAS": ["DJF", "JFM", "FMA", "MAM"],
            "YR": ["2024"] * 4,
            "ANOM": ["0.5", "-0.5", "0.49", "-0.49"],
        }
    )
    tabla = limpiar_noaa(bronce)
    ESQUEMA_NOAA_ONI.validate(tabla, lazy=True)
    assert tabla["fecha"].dt.month.tolist() == [1, 2, 3, 4]
    assert tabla["fase"].tolist() == ["El Niño", "La Niña", "Neutral", "Neutral"]


def test_xm_convierte_24_horas_en_filas_numericas():
    fila = {"Date": "2026-03-01", "Id": "Sistema", "code": "Sistema"}
    fila.update({hora: str(indice) for indice, hora in enumerate(HORAS, start=1)})
    tabla = limpiar_horario(pd.DataFrame([fila]))
    ESQUEMA_XM_PRECIO.validate(tabla, lazy=True)
    assert len(tabla) == 24
    assert tabla["hora"].tolist() == list(range(1, 25))
    assert tabla["valor"].tolist() == [float(i) for i in range(1, 25)]
    assert pd.api.types.is_numeric_dtype(tabla["valor"])


def test_xm_envia_todos_los_codigos_de_recurso_conflictivos_a_cuarentena():
    bronce = pd.DataFrame(
        {
            "Date": ["2026-11-04", "2026-11-04"],
            "Id": ["Sistema", "Sistema"],
            "Code": ["PRG1", "PRG1"],
            "Name": ["PROELECTRICA 1", "PROELECTRICA"],
            "Type": ["Termica", "Termica"],
            "Disp": ["Despachado", "Despachado"],
            "RecType": ["Normal", "Normal"],
            "CompanyCode": ["PRG", "PRG"],
            "EnerSource": ["Gas", "Gas"],
            "OperStartdate": ["2020-01-01", "2020-01-01"],
            "State": ["Operacion", "Operacion"],
        }
    )

    plata, cuarentena = separar_recursos(bronce)

    assert plata.empty
    assert len(cuarentena) == 2
    assert cuarentena["_motivo"].tolist() == [
        "codigo duplicado con descripciones distintas",
        "codigo duplicado con descripciones distintas",
    ]
    ESQUEMA_XM_RECURSOS.validate(plata, lazy=True)
    ESQUEMA_XM_RECURSOS_CUARENTENA.validate(cuarentena, lazy=True)


def test_ideam_convierte_fecha_y_mediciones_a_tipos_numericos():
    bronce = pd.DataFrame(
        {
            "codigoestacion": ["00123"],
            "nombreestacion": ["Estación de prueba"],
            "municipio": ["Medellín"],
            "latitud": ["6.25"],
            "longitud": ["-75.56"],
            "fecha": ["2026-03-01T00:00:00.000"],
            "precipitacion_mm": ["12.5"],
            "n_obs": ["4"],
        }
    )
    tabla = limpiar_precipitacion(bronce)
    assert tabla.loc[0, "fecha"] == pd.Timestamp("2026-03-01")
    assert tabla.loc[0, "precipitacion_mm"] == 12.5
    assert tabla.loc[0, "n_obs"] == 4
    assert tabla.loc[0, "municipio"] == "Medellín"
