"""Generación del reporte de calidad con resultados de la capa plata."""
from pathlib import Path

import pandas as pd

from src import config
from src.silver.common import sin_linaje
from src.silver.enerandes import limpiar as limpiar_enerandes

CONJUNTOS_POR_FUENTE = {
    "EnerAndes": [
        ("enerandes_ventas_2023", "enerandes_ventas"),
        ("enerandes_ventas_2024", "enerandes_ventas"),
        ("enerandes_ventas_2025", "enerandes_ventas"),
        ("enerandes_ventas_2026", "enerandes_ventas"),
    ],
    "XM": [
        ("xm_precio_bolsa", "xm_precio_bolsa"),
        ("xm_demanda", "xm_demanda"),
        ("xm_generacion", "xm_generacion"),
        ("xm_embalses", "xm_embalses"),
        ("xm_aportes", "xm_aportes"),
        ("xm_listado_recursos", "xm_listado_recursos"),
    ],
    "IDEAM": [
        ("ideam_precipitacion_diaria", "ideam_precipitacion_diaria"),
        ("ideam_temperatura_diaria", "ideam_temperatura_diaria"),
    ],
    "NOAA": [("noaa_oni", "noaa_oni")],
    "TRM": [("trm_diaria", "trm_diaria")],
}

TABLAS_CUARENTENA = {
    "EnerAndes": "enerandes_cuarentena",
    "XM": "xm_listado_recursos_cuarentena",
}


def _leer_parquet(directorio: Path, nombre: str) -> pd.DataFrame | None:
    ruta = directorio / f"{nombre}.parquet"
    return pd.read_parquet(ruta) if ruta.exists() else None


def _no_vacio(serie: pd.Series) -> pd.Series:
    return serie.notna() & serie.astype("string").str.strip().ne("")


def _fechas_invalidas(df: pd.DataFrame, columna: str) -> int:
    return int(pd.to_datetime(df[columna], errors="coerce").isna().sum())


def _fechas_invalidas_filas(df: pd.DataFrame, columnas: list[str]) -> int:
    invalidas = pd.Series(False, index=df.index)
    for columna in columnas:
        invalidas |= pd.to_datetime(df[columna], errors="coerce").isna()
    return int(invalidas.sum())


def _numeros_invalidos(
    df: pd.DataFrame,
    columnas: list[str],
    permitir_vacios: bool = False,
    minimo: float | None = None,
    maximo: float | None = None,
) -> int:
    invalidas = pd.Series(False, index=df.index)
    for columna in columnas:
        original = df[columna]
        numerico = pd.to_numeric(original, errors="coerce")
        invalido = numerico.isna()
        if permitir_vacios:
            invalido &= original.notna() & original.astype("string").str.strip().ne("")
        if minimo is not None:
            invalido |= numerico.lt(minimo)
        if maximo is not None:
            invalido |= numerico.gt(maximo)
        invalidas |= invalido
    return int(invalidas.sum())


def _enteros_invalidos(
    df: pd.DataFrame, columna: str, minimo: float
) -> int:
    valores = pd.to_numeric(df[columna], errors="coerce")
    return int((valores.isna() | valores.mod(1).ne(0) | valores.lt(minimo)).sum())


def _fuera_de_rango(
    df: pd.DataFrame,
    rangos: dict[str, tuple[float | None, float | None]],
) -> int:
    invalidas = pd.Series(False, index=df.index)
    for columna, (minimo, maximo) in rangos.items():
        valores = pd.to_numeric(df[columna], errors="coerce")
        invalido = valores.isna()
        if minimo is not None:
            invalido |= valores.lt(minimo)
        if maximo is not None:
            invalido |= valores.gt(maximo)
        invalidas |= invalido
    return int(invalidas.sum())


def _vacios(df: pd.DataFrame, columnas: list[str]) -> int:
    return int((~pd.concat([_no_vacio(df[col]) for col in columnas], axis=1).all(axis=1)).sum())


def _duplicados(df: pd.DataFrame, columnas: list[str]) -> int:
    return int(df.duplicated(subset=columnas, keep=False).sum())


def _regla(
    nombre: str,
    antes: int | str,
    despues: int | str,
    cuarentena: int = 0,
) -> dict:
    return {
        "regla": nombre,
        "antes": antes,
        "despues": despues,
        "cuarentena": cuarentena,
    }


def _reglas_xm_horario(bronce: pd.DataFrame, plata: pd.DataFrame) -> list[dict]:
    horas = [f"Hour{hora:02}" for hora in range(1, 25)]
    valores_invalidos = _numeros_invalidos(bronce, horas, permitir_vacios=True, minimo=0)
    despues_valores = _numeros_invalidos(
        plata, ["valor"], permitir_vacios=True, minimo=0
    )
    return [
        _regla("Fecha interpretable", _fechas_invalidas(bronce, "Date"),
               _fechas_invalidas(plata, "fecha")),
        _regla("Identificador no vacío", _vacios(bronce, ["Id"]),
               _vacios(plata, ["id"])),
        _regla("Valores horarios numéricos y no negativos", valores_invalidos,
               despues_valores),
        _regla("Clave fecha/hora/identificador única",
               _duplicados(bronce, ["Date", "Id", "code"]),
               _duplicados(plata, ["fecha", "hora", "id", "codigo"])),
    ]


def _reglas_xm_diario(
    bronce: pd.DataFrame, plata: pd.DataFrame, es_embalse: bool
) -> list[dict]:
    minimo, maximo = (0, 1) if es_embalse else (0, None)
    regla_valor = (
        "Valor numérico entre 0 y 1"
        if es_embalse
        else "Valor numérico no negativo"
    )
    return [
        _regla("Fecha interpretable", _fechas_invalidas(bronce, "Date"),
               _fechas_invalidas(plata, "fecha")),
        _regla("Identificador no vacío", _vacios(bronce, ["Id"]),
               _vacios(plata, ["id"])),
        _regla(regla_valor,
               _numeros_invalidos(bronce, ["Value"], minimo=minimo, maximo=maximo),
               _numeros_invalidos(plata, ["valor"], minimo=minimo, maximo=maximo)),
        _regla("Clave fecha/identificador única",
               _duplicados(bronce, ["Date", "Id"]),
               _duplicados(plata, ["fecha", "id"])),
    ]


def _reglas_xm_recursos(bronce: pd.DataFrame, plata: pd.DataFrame) -> list[dict]:
    duplicados = bronce["Code"].astype("string").str.strip().duplicated(keep=False)
    duplicados_plata = plata["codigo"].duplicated(keep=False)
    cuarentena = _leer_parquet(config.DIR_SILVER, "xm_listado_recursos_cuarentena")
    filas_cuarentena = len(cuarentena) if cuarentena is not None else 0
    return [
        _regla("Código y nombre no vacíos",
               _vacios(bronce, ["Code", "Name"]),
               _vacios(plata, ["codigo", "nombre"])),
        _regla("Fechas del catálogo interpretables",
               _fechas_invalidas_filas(bronce, ["Date", "OperStartdate"]),
               _fechas_invalidas_filas(plata, ["fecha_corte", "fecha_operacion"])),
        _regla("Código de recurso único", int(duplicados.sum()),
               int(duplicados_plata.sum()),
               filas_cuarentena),
    ]


def _reglas_ideam(
    bronce: pd.DataFrame, plata: pd.DataFrame, temperatura: bool
) -> list[dict]:
    columnas_medicion = (
        ["temp_media_c", "temp_min_c", "temp_max_c"]
        if temperatura else ["precipitacion_mm"]
    )
    reglas = [
        _regla("Estación y municipio no vacíos",
               _vacios(bronce, ["codigoestacion", "municipio"]),
               _vacios(plata, ["codigoestacion", "municipio"])),
        _regla("Fecha interpretable", _fechas_invalidas(bronce, "fecha"),
               _fechas_invalidas(plata, "fecha")),
        _regla("Coordenadas dentro del rango geográfico",
               _fuera_de_rango(bronce, {
                   "latitud": (-90, 90), "longitud": (-180, 180),
               }),
               _fuera_de_rango(plata, {
                   "latitud": (-90, 90), "longitud": (-180, 180),
               })),
        _regla("Mediciones numéricas y en rango",
               _numeros_invalidos(bronce, columnas_medicion,
                                  minimo=-90 if temperatura else 0,
                                  maximo=60 if temperatura else None),
               _numeros_invalidos(plata, columnas_medicion,
                                  minimo=-90 if temperatura else 0,
                                  maximo=60 if temperatura else None)),
        _regla("Número de observaciones entero y positivo",
               _enteros_invalidos(bronce, "n_obs", minimo=1),
               _enteros_invalidos(plata, "n_obs", minimo=1)),
        _regla("Clave estación/fecha única",
               _duplicados(bronce, ["codigoestacion", "fecha"]),
               _duplicados(plata, ["codigoestacion", "fecha"])),
    ]
    if temperatura:
        reglas.extend([
            _regla("Temperatura mínima no supera la media",
                   int((pd.to_numeric(bronce["temp_min_c"], errors="coerce")
                        > pd.to_numeric(bronce["temp_media_c"], errors="coerce")).sum()),
                   int((plata["temp_min_c"] > plata["temp_media_c"]).sum())),
            _regla("Temperatura media no supera la máxima",
                   int((pd.to_numeric(bronce["temp_media_c"], errors="coerce")
                        > pd.to_numeric(bronce["temp_max_c"], errors="coerce")).sum()),
                   int((plata["temp_media_c"] > plata["temp_max_c"]).sum())),
        ])
    return reglas


def _reglas_noaa(bronce: pd.DataFrame, plata: pd.DataFrame) -> list[dict]:
    temporadas = bronce["SEAS"].astype("string").str.strip().str.upper()
    meses_por_temporada = {
        "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4,
        "AMJ": 5, "MJJ": 6, "JJA": 7, "JAS": 8,
        "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
    }
    anios = pd.to_numeric(bronce["YR"], errors="coerce")
    fechas_antes = pd.to_datetime(
        {"year": anios, "month": temporadas.map(meses_por_temporada), "day": 1},
        errors="coerce",
    )
    fase_esperada = plata["oni"].map(
        lambda valor: "El Niño" if valor >= 0.5
        else "La Niña" if valor <= -0.5 else "Neutral"
    )
    return [
        _regla("Temporada ONI reconocida",
               int((~temporadas.isin({
                   "DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
                   "JJA", "JAS", "ASO", "SON", "OND", "NDJ",
               })).sum()),
               int((~plata["fecha"].dt.month.between(1, 12)).sum())),
        _regla("Año entero", _enteros_invalidos(bronce, "YR", minimo=1),
               int((plata["fecha"].dt.year % 1 != 0).sum())),
        _regla("Anomalía ONI numérica y entre -5 y 5",
               _numeros_invalidos(bronce, ["ANOM"], minimo=-5, maximo=5),
               _numeros_invalidos(plata, ["oni"], minimo=-5, maximo=5)),
        _regla("Fecha mensual única",
               int(fechas_antes.duplicated(keep=False).sum()),
               _duplicados(plata, ["fecha"])),
        _regla("Fase coherente con el umbral ONI",
               "No aplica: la fase se deriva en plata",
               int((plata["fase"] != fase_esperada).sum())),
    ]


def _reglas_trm(bronce: pd.DataFrame, plata: pd.DataFrame) -> list[dict]:
    return [
        _regla("Fechas de vigencia interpretables",
               _fechas_invalidas_filas(bronce, ["vigenciadesde", "vigenciahasta"]),
               _fechas_invalidas_filas(plata, ["fecha", "fecha_hasta"])),
        _regla("Vigencia final igual o posterior a la inicial",
               int((pd.to_datetime(bronce["vigenciahasta"], errors="coerce")
                    < pd.to_datetime(bronce["vigenciadesde"], errors="coerce")).sum()),
               int((plata["fecha_hasta"] < plata["fecha"]).sum())),
        _regla("Tasa numérica positiva",
               _numeros_invalidos(bronce, ["valor"], minimo=0.0000001),
               _numeros_invalidos(plata, ["valor_cop_por_usd"], minimo=0.0000001)),
        _regla("Unidad COP",
               int((bronce["unidad"].astype("string").str.strip().str.upper() != "COP").sum()),
               int((plata["unidad"] != "COP").sum())),
        _regla("Fecha inicial única",
               _duplicados(bronce, ["vigenciadesde"]),
               _duplicados(plata, ["fecha"])),
    ]


def _reglas_enerandes() -> list[tuple[str, dict]]:
    reglas = []
    cuarentena_total = _leer_parquet(config.DIR_SILVER, "enerandes_cuarentena")
    for anio in range(2023, 2027):
        bronce = _leer_parquet(config.DIR_BRONZE, f"enerandes_ventas_{anio}")
        if bronce is None:
            continue
        _, _, metricas = limpiar_enerandes(bronce, anio)
        reglas.extend(
            (
                f"enerandes_ventas_{anio}",
                _regla(
                    f"{metrica['problema']}: {metrica['regla aplicada']}",
                    metrica["antes"],
                    metrica["despues"],
                    int((cuarentena_total["_anio"] == anio).sum())
                    if (
                        metrica["problema"] == "Filas en cuarentena"
                        and cuarentena_total is not None
                    )
                    else 0,
                ),
            )
            for metrica in metricas
        )
    return reglas


def _reglas_para_conjunto(
    bronce: pd.DataFrame, plata: pd.DataFrame, nombre: str
) -> list[dict]:
    bronce = sin_linaje(bronce)
    plata = sin_linaje(plata)
    if nombre.startswith("xm_") and nombre in {
        "xm_precio_bolsa", "xm_demanda", "xm_generacion",
    }:
        return _reglas_xm_horario(bronce, plata)
    if nombre in {"xm_embalses", "xm_aportes"}:
        return _reglas_xm_diario(bronce, plata, nombre == "xm_embalses")
    if nombre == "xm_listado_recursos":
        return _reglas_xm_recursos(bronce, plata)
    if nombre.startswith("ideam_"):
        return _reglas_ideam(bronce, plata, "temperatura" in nombre)
    if nombre == "noaa_oni":
        return _reglas_noaa(bronce, plata)
    if nombre == "trm_diaria":
        return _reglas_trm(bronce, plata)
    return []


def generar_reporte() -> None:
    filas = [
        "# Reporte de calidad de datos",
        "",
        "Reporte generado por `python -m src.silver.pipeline` a partir de los "
        "Parquet de bronce, plata y cuarentena disponibles.",
        "",
        "## Resumen por fuente y conjunto",
        "",
    ]
    reglas_por_fuente = {"EnerAndes": _reglas_enerandes()}
    for fuente, conjuntos in CONJUNTOS_POR_FUENTE.items():
        filas.extend([
            f"### {fuente}",
            "",
            "| Conjunto | Filas antes (bronce) | Filas después (plata) | Filas en cuarentena |",
            "|---|---:|---:|---:|",
        ])
        reglas_por_fuente.setdefault(fuente, [])
        for nombre_bronce, nombre_plata in conjuntos:
            bronce = _leer_parquet(config.DIR_BRONZE, nombre_bronce)
            plata = _leer_parquet(config.DIR_SILVER, nombre_plata)
            antes = len(bronce) if bronce is not None else "No disponible"
            despues = len(plata) if plata is not None else "No ejecutado"
            cantidad_cuarentena = 0
            if fuente == "EnerAndes":
                cuarentena = _leer_parquet(config.DIR_SILVER, "enerandes_cuarentena")
                if cuarentena is not None and "_anio" in cuarentena:
                    cantidad_cuarentena = int((cuarentena["_anio"] == int(nombre_bronce[-4:])).sum())
                if plata is not None:
                    anio = nombre_bronce[-4:]
                    despues = int(plata["periodo"].astype("string").str.startswith(anio).sum())
            elif fuente == "XM" and nombre_bronce == "xm_listado_recursos":
                cuarentena = _leer_parquet(config.DIR_SILVER, "xm_listado_recursos_cuarentena")
                cantidad_cuarentena = len(cuarentena) if cuarentena is not None else 0
            filas.append(
                f"| `{nombre_bronce}` | {antes} | {despues} | {cantidad_cuarentena} |"
            )
            if bronce is not None and plata is not None and fuente != "EnerAndes":
                reglas_por_fuente[fuente].extend(
                    (nombre_bronce, regla)
                    for regla in _reglas_para_conjunto(bronce, plata, nombre_bronce)
                )
        filas.append("")

    filas.extend([
        "## Reglas y métricas antes/después",
        "",
        "Los valores de las columnas antes/después son filas que incumplen la regla. "
        "En transformaciones que amplían el grano (por ejemplo, 24 horas por registro), "
        "se cuentan las filas del grano propio de cada capa.",
        "",
    ])
    for fuente in CONJUNTOS_POR_FUENTE:
        filas.extend([
            f"### {fuente}",
            "",
            "| Conjunto | Regla | Incumplen antes | Incumplen después | En cuarentena |",
            "|---|---|---:|---:|---:|",
        ])
        reglas = reglas_por_fuente.get(fuente, [])
        for item in reglas:
            if fuente == "EnerAndes":
                nombre, regla = item
            else:
                nombre, regla = item
            filas.append(
                f"| `{nombre}` | {regla['regla']} | {regla['antes']} | "
                f"{regla['despues']} | {regla['cuarentena']} |"
            )
        filas.append("")

    filas.extend([
        "## Detalle de cuarentena",
        "",
        "| Fuente | Conjunto | Motivo | Filas |",
        "|---|---|---|---:|",
    ])
    for fuente, nombre_tabla in TABLAS_CUARENTENA.items():
        cuarentena = _leer_parquet(config.DIR_SILVER, nombre_tabla)
        if cuarentena is None or cuarentena.empty:
            filas.append(f"| {fuente} | `{nombre_tabla}` | Sin filas enviadas | 0 |")
            continue
        columna_motivo = "_motivo"
        if columna_motivo not in cuarentena:
            filas.append(
                f"| {fuente} | `{nombre_tabla}` | Motivo no registrado | {len(cuarentena)} |"
            )
            continue
        conteos = cuarentena[columna_motivo].fillna("Motivo no especificado").value_counts()
        for motivo, cantidad in conteos.items():
            filas.append(f"| {fuente} | `{nombre_tabla}` | {motivo} | {cantidad} |")
    filas.extend([
        "",
        "IDEAM, NOAA y TRM no generan una tabla de cuarentena: las validaciones "
        "incompatibles detienen la ejecución en vez de apartar filas.",
        "",
        "En el catálogo XM, los duplicados exactos se eliminan durante la "
        "normalización; los códigos que conservan descripciones distintas se envían "
        "completos a cuarentena. Por eso el número bruto de filas con código repetido "
        "puede ser mayor que las filas finalmente cuarentenadas.",
        "",
        "Las reglas de EnerAndes incluyen la detección de encabezados, totales, "
        "duplicados y filas no corregibles. Una fila puede incumplir más de una regla; "
        "por ello, los conteos de reglas no deben sumarse como un total de filas único.",
        "",
    ])

    config.DIR_DOCS.mkdir(parents=True, exist_ok=True)
    (config.DIR_DOCS / "reporte_calidad.md").write_text(
        "\n".join(filas), encoding="utf-8"
    )


if __name__ == "__main__":
    generar_reporte()
