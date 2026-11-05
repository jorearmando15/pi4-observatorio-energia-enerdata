"""Limpieza de las métricas y del catálogo de recursos de XM."""
import pandas as pd
from src.quality.esquemas import (
    ESQUEMA_XM_APORTES,
    ESQUEMA_XM_DEMANDA,
    ESQUEMA_XM_EMBALSES,
    ESQUEMA_XM_GENERACION,
    ESQUEMA_XM_PRECIO,
    ESQUEMA_XM_RECURSOS,
)
from src.silver.common import fechas, leer_bronce, numero, guardar_validado, sin_linaje
from src.utils import log

HORAS = [f"Hour{i:02}" for i in range(1, 25)]
HORARIOS = {
    "xm_precio_bolsa": ESQUEMA_XM_PRECIO,
    "xm_demanda": ESQUEMA_XM_DEMANDA,
    "xm_generacion": ESQUEMA_XM_GENERACION,
}


def limpiar_horario(bronce: pd.DataFrame) -> pd.DataFrame:
    df = sin_linaje(bronce)
    faltantes = [col for col in ["Date", "Id", *HORAS] if col not in df]
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas de XM: {faltantes}")

    columnas = ["Date", "Id"]
    if "code" in df:
        columnas.append("code")
    else:
        df["code"] = pd.NA
        columnas.append("code")
    df = df[columnas + HORAS].copy()
    df["Date"] = fechas(df["Date"], "Date")
    df["Id"] = df["Id"].astype("string").str.strip()
    df["code"] = df["code"].astype("string").str.strip()

    for hora in HORAS:
        df[hora] = numero(df[hora], hora, permitir_vacios=True)

    resultado = df.melt(
        id_vars=["Date", "Id", "code"],
        value_vars=HORAS,
        var_name="hora",
        value_name="valor",
    )
    resultado["hora"] = resultado["hora"].str.removeprefix("Hour").astype(int)
    resultado["valor"] = resultado["valor"].astype(float)
    resultado = resultado.rename(
        columns={"Date": "fecha", "Id": "id", "code": "codigo"}
    )
    return resultado.drop_duplicates().reset_index(drop=True)


def limpiar_diario(bronce: pd.DataFrame) -> pd.DataFrame:
    df = sin_linaje(bronce)
    df = df[["Date", "Id", "Value"]].copy()
    df["Date"] = fechas(df["Date"], "Date")
    df["Id"] = df["Id"].astype("string").str.strip()
    df["Value"] = numero(df["Value"], "Value")
    df = df.rename(columns={"Date": "fecha", "Id": "id", "Value": "valor"})
    return df.drop_duplicates().reset_index(drop=True)


def limpiar_recursos(bronce: pd.DataFrame) -> pd.DataFrame:
    df = sin_linaje(bronce)
    columnas = {
        "Date": "fecha_corte",
        "Id": "id",
        "Code": "codigo",
        "Name": "nombre",
        "Type": "tipo",
        "Disp": "despacho",
        "RecType": "tipo_recurso",
        "CompanyCode": "codigo_empresa",
        "EnerSource": "fuente_energia",
        "OperStartdate": "fecha_operacion",
        "State": "estado",
    }
    df = df[list(columnas)].rename(columns=columnas)
    for columna in [
        "id", "codigo", "nombre", "tipo", "despacho", "tipo_recurso",
        "codigo_empresa", "fuente_energia", "estado",
    ]:
        df[columna] = df[columna].astype("string").str.strip()
    for columna in ["tipo", "despacho", "tipo_recurso", "fuente_energia", "estado"]:
        df[columna] = df[columna].str.upper()
    df["fecha_corte"] = fechas(df["fecha_corte"], "Date")
    df["fecha_operacion"] = fechas(df["fecha_operacion"], "OperStartdate")
    return df.drop_duplicates().reset_index(drop=True)


def main() -> None:
    log("XM - limpieza de datos horarios, diarios y catálogo")
    for nombre, esquema in HORARIOS.items():
        tabla = limpiar_horario(leer_bronce(nombre))
        guardar_validado(tabla, nombre, esquema)
        log(f"   {nombre}: {len(tabla):,} filas")

    for nombre, esquema in [
        ("xm_embalses", ESQUEMA_XM_EMBALSES),
        ("xm_aportes", ESQUEMA_XM_APORTES),
    ]:
        tabla = limpiar_diario(leer_bronce(nombre))
        tabla["valor"] = tabla["valor"].astype(float)
        guardar_validado(tabla, nombre, esquema)
        log(f"   {nombre}: {len(tabla):,} filas")

    recursos = limpiar_recursos(leer_bronce("xm_listado_recursos"))
    guardar_validado(recursos, "xm_listado_recursos", ESQUEMA_XM_RECURSOS)
    log(f"   xm_listado_recursos: {len(recursos):,} filas")


if __name__ == "__main__":
    main()
