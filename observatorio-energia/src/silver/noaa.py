"""Limpieza del ONI trimestral móvil de NOAA a una serie mensual."""
import pandas as pd

from src.quality.esquemas import ESQUEMA_NOAA_ONI
from src.silver.common import guardar_validado, leer_bronce, numero, sin_linaje
from src.utils import log

MES_CENTRAL = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4,
    "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8,
    "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}


def fase_oni(valor: float) -> str:
    if valor >= 0.5:
        return "El Niño"
    if valor <= -0.5:
        return "La Niña"
    return "Neutral"


def limpiar(bronce: pd.DataFrame) -> pd.DataFrame:
    df = sin_linaje(bronce)
    estaciones = df["SEAS"].astype("string").str.strip().str.upper()
    meses = estaciones.map(MES_CENTRAL)
    if meses.isna().any():
        desconocidas = estaciones[meses.isna()].drop_duplicates().tolist()
        raise ValueError(f"Trimestres NOAA desconocidos: {desconocidas}")
    anios = numero(df["YR"], "YR")
    if (anios % 1 != 0).any():
        raise ValueError("YR debe contener años enteros")
    oni = numero(df["ANOM"], "ANOM").astype(float)
    fecha = pd.to_datetime(
        {"year": anios.astype(int), "month": meses.astype(int), "day": 1},
        errors="coerce",
    )
    if fecha.isna().any():
        raise ValueError("NOAA contiene años o meses inválidos")
    tabla = pd.DataFrame({"fecha": fecha, "oni": oni})
    tabla["fase"] = tabla["oni"].map(fase_oni)
    return tabla.drop_duplicates().reset_index(drop=True)


def main() -> None:
    log("NOAA - limpieza de ONI trimestral a mensual")
    tabla = limpiar(leer_bronce("noaa_oni"))
    guardar_validado(tabla, "noaa_oni", ESQUEMA_NOAA_ONI)
    log(f"   noaa_oni: {len(tabla):,} filas")


if __name__ == "__main__":
    main()
