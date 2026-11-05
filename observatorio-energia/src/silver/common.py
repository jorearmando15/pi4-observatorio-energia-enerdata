"""Helpers compartidos para los programas de la capa plata."""
import pandas as pd

from src import config

LINAJE = ["_fuente", "_origen", "_extraido_en"]


def leer_bronce(nombre: str) -> pd.DataFrame:
    return pd.read_parquet(config.DIR_BRONZE / f"{nombre}.parquet")


def sin_linaje(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=LINAJE, errors="ignore").copy()


def numero(serie: pd.Series, nombre: str, permitir_vacios: bool = False) -> pd.Series:
    texto = serie.astype("string").str.strip()
    vacios = texto.isna() | texto.eq("")
    valores = pd.to_numeric(texto.mask(vacios), errors="coerce")
    invalidos = valores.isna() & ~vacios
    if invalidos.any():
        ejemplos = texto[invalidos].drop_duplicates().head(5).tolist()
        raise ValueError(f"Valores no numéricos en {nombre}: {ejemplos}")
    if not permitir_vacios and valores.isna().any():
        raise ValueError(f"Hay valores vacíos en la columna obligatoria {nombre}")
    return valores


def fechas(serie: pd.Series, nombre: str) -> pd.Series:
    valores = pd.to_datetime(serie, errors="coerce")
    if valores.isna().any():
        ejemplos = serie[valores.isna()].drop_duplicates().head(5).tolist()
        raise ValueError(f"Fechas inválidas en {nombre}: {ejemplos}")
    return valores.dt.normalize()


def guardar_validado(
    df: pd.DataFrame, nombre: str, esquema
) -> None:
    esquema.validate(df, lazy=True)
    config.DIR_SILVER.mkdir(parents=True, exist_ok=True)
    df.to_parquet(config.DIR_SILVER / f"{nombre}.parquet", index=False)
