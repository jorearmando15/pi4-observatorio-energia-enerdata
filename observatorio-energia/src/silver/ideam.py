"""Limpieza de precipitación y temperatura diaria del IDEAM."""
import pandas as pd

from src.quality.esquemas import (
    ESQUEMA_IDEAM_PRECIPITACION,
    ESQUEMA_IDEAM_TEMPERATURA,
)
from src.silver.common import fechas, guardar_validado, leer_bronce, numero, sin_linaje
from src.utils import log

BASE = [
    "codigoestacion", "nombreestacion", "municipio",
    "latitud", "longitud", "fecha",
]


def _limpiar_base(bronce: pd.DataFrame) -> pd.DataFrame:
    df = sin_linaje(bronce)
    df["codigoestacion"] = df["codigoestacion"].astype("string").str.strip()
    df["nombreestacion"] = df["nombreestacion"].astype("string").str.strip()
    df["municipio"] = df["municipio"].astype("string").str.strip()
    df["fecha"] = fechas(df["fecha"], "fecha")
    for columna in ["latitud", "longitud"]:
        df[columna] = numero(df[columna], columna).astype(float)
    return df


def _conteo_entero(serie: pd.Series) -> pd.Series:
    conteo = numero(serie, "n_obs")
    if (conteo % 1 != 0).any():
        raise ValueError("n_obs debe contener números enteros")
    return conteo.astype(int)


def limpiar_precipitacion(bronce: pd.DataFrame) -> pd.DataFrame:
    df = _limpiar_base(bronce)
    df["precipitacion_mm"] = numero(df["precipitacion_mm"], "precipitacion_mm").astype(float)
    df["n_obs"] = _conteo_entero(df["n_obs"])
    return df[BASE + ["precipitacion_mm", "n_obs"]].drop_duplicates().reset_index(drop=True)


def limpiar_temperatura(bronce: pd.DataFrame) -> pd.DataFrame:
    df = _limpiar_base(bronce)
    columnas = ["temp_media_c", "temp_min_c", "temp_max_c"]
    for columna in columnas:
        df[columna] = numero(df[columna], columna).astype(float)
    df["n_obs"] = _conteo_entero(df["n_obs"])
    return df[BASE + columnas + ["n_obs"]].drop_duplicates().reset_index(drop=True)


def main() -> None:
    log("IDEAM - limpieza de precipitación y temperatura")
    for nombre, limpiar, esquema in [
        ("ideam_precipitacion_diaria", limpiar_precipitacion, ESQUEMA_IDEAM_PRECIPITACION),
        ("ideam_temperatura_diaria", limpiar_temperatura, ESQUEMA_IDEAM_TEMPERATURA),
    ]:
        tabla = limpiar(leer_bronce(nombre))
        guardar_validado(tabla, nombre, esquema)
        log(f"   {nombre}: {len(tabla):,} filas")


if __name__ == "__main__":
    main()
