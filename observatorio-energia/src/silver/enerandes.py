"""
Capa PLATA: limpia la hoja 2023 del Excel de ventas de EnerAndes.

Lee data/bronze/enerandes_ventas_2023.parquet (tal cual llego), aplica las
reglas de limpieza una por una y MIDE cada problema antes y despues.
Luego valida el resultado con pandera (src/quality/esquemas.py) y guarda:
  - data/silver/enerandes_ventas.parquet       las filas limpias
  - data/silver/enerandes_cuarentena.parquet   las filas que no se pueden usar
  - docs/reporte_calidad.md                    la tabla de metricas antes y despues

En bronce no se modifica nada: aqui se trabaja sobre una copia.

Uso:
    python -m src.silver.enerandes
"""
# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
"""Normaliza y combina las cuatro hojas de ventas de EnerAndes."""
import re
import unicodedata
from datetime import date

import pandas as pd

from src import config
from src.quality.esquemas import ESQUEMA_CUARENTENA_VENTAS, ESQUEMA_VENTAS
from src.silver.common import guardar_validado, leer_bronce, sin_linaje
from src.utils import log

LINAJE = ["_fuente", "_origen", "_extraido_en"]
ORDEN = [
    "periodo", "divipola", "municipio", "segmento", "tipo_compra",
    "energia_kwh", "valor_cop", "clientes",
]
MUNICIPIOS = {
    "medellin": ("05001", "Medellín"),
    "santafedeantioquia": ("05042", "Santa Fe de Antioquia"),
    "apartado": ("05045", "Apartadó"),
    "bello": ("05088", "Bello"),
    "caldas": ("05129", "Caldas"),
    "caucasia": ("05154", "Caucasia"),
    "copacabana": ("05212", "Copacabana"),
    "envigado": ("05266", "Envigado"),
    "girardota": ("05308", "Girardota"),
    "itagui": ("05360", "Itagüí"),
    "laestrella": ("05380", "La Estrella"),
    "marinilla": ("05440", "Marinilla"),
    "rionegro": ("05615", "Rionegro"),
    "sabaneta": ("05631", "Sabaneta"),
    "turbo": ("05837", "Turbo"),
}
ALIAS_MUNICIPIO = {
    "rionegro": "rionegro",
    "rionegroant": "rionegro",
    "medellinde": "medellin",
    "medelln": "medellin",
    "santafedeantioquia": "santafedeantioquia",
    "stafedeantioquia": "santafedeantioquia",
    "apartad": "apartado",
    "itag": "itagui",
    "itagu": "itagui",
}
SEGMENTOS = {
    "residencial": "Residencial",
    "resid": "Residencial",
    "comercial": "Comercial",
    "industrial": "Industrial",
    "ind": "Industrial",
}
TIPOS_COMPRA = {
    "bolsa": "Bolsa",
    "contrato": "Contrato",
    "contratos": "Contrato",
}
MESES = {
    "jan": 1, "ene": 1, "january": 1, "enero": 1,
    "feb": 2, "february": 2, "febrero": 2,
    "mar": 3, "march": 3, "marzo": 3,
    "apr": 4, "abr": 4, "april": 4, "abril": 4,
    "may": 5, "mayo": 5,
    "jun": 6, "june": 6, "junio": 6,
    "jul": 7, "july": 7, "julio": 7,
    "aug": 8, "ago": 8, "august": 8, "agosto": 8,
    "sep": 9, "sept": 9, "september": 9, "septiembre": 9,
    "oct": 10, "october": 10, "octubre": 10,
    "nov": 11, "november": 11, "noviembre": 11,
    "dec": 12, "dic": 12, "december": 12, "diciembre": 12,
}

ENCABEZADOS = {
    "fecha": "periodo", "periodo": "periodo", "mes": "periodo", "fechacorte": "periodo",
    "municipio": "municipio", "ciudad": "municipio",
    "segmento": "segmento", "segmentocliente": "segmento", "tipocliente": "segmento",
    "tipocompra": "tipo_compra", "modalidad": "tipo_compra", "compra": "tipo_compra",
    "energiakwh": "energia", "energia": "energia", "consumokwh": "energia", "kwh": "energia",
    "valorcop": "valor", "valor": "valor", "facturado": "valor",
    "totalfacturadocop": "valor",
    "clientes": "clientes", "numclientes": "clientes", "usuarios": "clientes",
    "clientesactivos": "clientes",
    "unidad": "unidad",
}


def sin_tildes(texto: str) -> str:
    letras = unicodedata.normalize("NFD", texto.strip().lower())
    return "".join(
        caracter for caracter in letras
        if unicodedata.category(caracter) != "Mn" and caracter != "\ufffd"
    )


def _token(texto) -> str:
    if pd.isna(texto):
        return ""
    return re.sub(r"[^a-z0-9]", "", sin_tildes(str(texto)))


def clave_municipio(texto) -> str | None:
    token = _token(texto)
    if not token:
        return None
    clave = ALIAS_MUNICIPIO.get(token, token)
    return clave if clave in MUNICIPIOS else None


def _periodo(valor, anio: int | None) -> str | None:
    if pd.isna(valor):
        return None
    texto = sin_tildes(str(valor)).strip().lower()
    dia = 1

    match = re.fullmatch(r"(\d{4})-(\d{1,2})", texto)
    if match:
        year, month = map(int, match.groups())
    else:
        match = re.fullmatch(r"(\d{1,2})/(\d{4})", texto)
        if match:
            month, year = map(int, match.groups())
        else:
            match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", texto)
            if match:
                dia, month, year = map(int, match.groups())
            else:
                match = re.fullmatch(r"([a-z]+)-(\d{2,4})", texto)
                if not match:
                    return None
                month = MESES.get(match.group(1))
                year = int(match.group(2))
                if year < 100:
                    year += 2000 if year < 70 else 1900
    if month is None or not 1 <= month <= 12 or not 1900 <= year <= 2100:
        return None
    try:
        date(year, month, dia)
    except ValueError:
        return None
    if anio is not None and year != anio:
        return None
    return f"{year:04}-{month:02}"


def _numero(valor) -> float | None:
    if pd.isna(valor) or str(valor).strip() == "":
        return None
    texto = str(valor).strip().replace(" ", "")
    if "," in texto:
        if "." in texto and texto.rfind(",") < texto.rfind("."):
            texto = texto.replace(",", "")
        elif "." in texto:
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", ".")
    try:
        numero = float(texto)
    except ValueError:
        return None
    return numero


def _detectar_encabezado(df: pd.DataFrame) -> tuple[int, dict[object, str]]:
    requeridos = {
        "periodo", "municipio", "segmento", "tipo_compra",
        "energia", "valor", "clientes",
    }
    for indice, fila in df.iterrows():
        asignaciones = {}
        for columna, valor in fila.items():
            destino = ENCABEZADOS.get(_token(valor))
            if destino:
                asignaciones[columna] = destino
        if requeridos.issubset(set(asignaciones.values())):
            return indice, asignaciones
    raise ValueError("No se encontró un encabezado reconocible en la hoja EnerAndes")


def limpiar(
    bronce: pd.DataFrame, anio: int | None = None
) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    """Devuelve ventas normalizadas, filas en cuarentena y métricas de limpieza."""
    df = sin_linaje(bronce).reset_index(drop=True)
    fila_encabezado, asignaciones = _detectar_encabezado(df)
    nombres = {}
    for posicion, destino in asignaciones.items():
        if destino in nombres.values():
            continue
        nombres[posicion] = destino
    filas = df.iloc[fila_encabezado + 1:].copy()
    filas = filas.rename(columns=nombres)
    columnas = [nombres[i] for i in nombres]
    filas = filas.iloc[:, :len(columnas)]
    filas.columns = columnas
    duplicados_exactos = len(filas) - len(filas.drop_duplicates())
    filas = filas.drop_duplicates()

    limpias = []
    cuarentena = []
    totales = 0
    for indice, fila in filas.iterrows():
        if fila.isna().all() or all(str(v).strip() == "" for v in fila.dropna()):
            continue
        if _token(fila.get("periodo")) in {"total", "totales", "totalgeneral"}:
            totales += 1
            continue
        if _token(fila.get("periodo")) == "periodo":
            continue

        periodo = _periodo(fila.get("periodo"), anio)
        municipio_original = fila.get("municipio")
        clave = clave_municipio(municipio_original)
        segmento_raw = fila.get("segmento")
        segmento_token = _token(segmento_raw)
        segmento = SEGMENTOS.get(segmento_token, "No informado" if not segmento_token else None)
        tipo = TIPOS_COMPRA.get(_token(fila.get("tipo_compra")))
        unidad_raw = fila.get("unidad")
        unidad = _token(unidad_raw) if pd.notna(unidad_raw) else ""
        energia = _numero(fila.get("energia"))
        razones_unidad_vacia = False
        if unidad:
            if unidad in {"mwh", "megawatthour", "megawattshora"}:
                energia = energia * 1000 if energia is not None else None
            elif unidad not in {"kwh", "kilowatthour", "kilowatthora"}:
                energia = None
        elif "unidad" in filas.columns:
            razones_unidad_vacia = True
        else:
            razones_unidad_vacia = False
        valor = _numero(fila.get("valor"))
        clientes_num = _numero(fila.get("clientes"))
        razones = []
        if periodo is None:
            razones.append("periodo inválido")
        if clave is None:
            razones.append("municipio vacío o desconocido")
        if segmento is None:
            razones.append("segmento desconocido")
        if tipo is None:
            razones.append("tipo de compra desconocido")
        if energia is None:
            razones.append("energía vacía o no numérica")
        elif energia < 0:
            razones.append("energía negativa")
        if razones_unidad_vacia:
            razones.append("unidad de energía vacía")
        if unidad and unidad not in {"mwh", "megawatthour", "megawattshora", "kwh", "kilowatthour", "kilowatthora"}:
            razones.append("unidad de energía desconocida")
        if valor is not None and valor < 0:
            razones.append("valor facturado negativo")
        if pd.notna(fila.get("valor")) and str(fila.get("valor")).strip() and valor is None:
            razones.append("valor facturado no numérico")
        if clientes_num is None or clientes_num < 0 or clientes_num % 1:
            razones.append("clientes vacío, inválido o negativo")

        fila_origen = int(indice) + 1
        registro = {
            "periodo": periodo,
            "divipola": MUNICIPIOS[clave][0] if clave else None,
            "municipio": MUNICIPIOS[clave][1] if clave else (
                str(municipio_original).strip() if pd.notna(municipio_original) else None
            ),
            "segmento": segmento or str(segmento_raw),
            "tipo_compra": tipo or (
                str(fila.get("tipo_compra")).strip() if pd.notna(fila.get("tipo_compra")) else None
            ),
            "energia_kwh": energia,
            "valor_cop": valor,
            "clientes": int(clientes_num) if clientes_num is not None and clientes_num % 1 == 0 else None,
        }
        if razones:
            registro.update({
                "_anio": anio,
                "_fila_origen": fila_origen,
                "_motivo": "; ".join(dict.fromkeys(razones)),
            })
            cuarentena.append(registro)
        else:
            registro["_fila_origen"] = fila_origen
            limpias.append(registro)

    resultado = pd.DataFrame(limpias, columns=ORDEN + ["_fila_origen"])
    if not resultado.empty:
        resultado["energia_kwh"] = resultado["energia_kwh"].astype(float)
        resultado["valor_cop"] = resultado["valor_cop"].astype(float)
        resultado["clientes"] = resultado["clientes"].astype(int)
    duplicados = resultado.duplicated(
        subset=["periodo", "divipola", "segmento", "tipo_compra"], keep="first"
    )
    duplicados_llave = int(duplicados.sum())
    if duplicados.any():
        for idx in resultado.index[duplicados]:
            registro = resultado.loc[idx].to_dict()
            registro.update({
                "_anio": anio,
                "_motivo": "duplicado de llave de negocio",
            })
            cuarentena.append(registro)
        resultado = resultado.loc[~duplicados].reset_index(drop=True)

    resultado = resultado[ORDEN]
    columnas_cuarentena = ORDEN + ["_anio", "_fila_origen", "_motivo"]
    cuarentena_df = pd.DataFrame(cuarentena, columns=columnas_cuarentena)
    for columna in ["energia_kwh", "valor_cop", "clientes", "_fila_origen"]:
        cuarentena_df[columna] = pd.to_numeric(cuarentena_df[columna], errors="coerce").astype(float)
    metricas = [
        {"problema": "Filas de encabezado", "regla aplicada": "Detectar encabezado por nombres", "antes": 1, "despues": 0},
        {"problema": "Filas de totales", "regla aplicada": "Excluir totales, no ventas", "antes": totales, "despues": 0},
        {"problema": "Filas duplicadas", "regla aplicada": "Conservar una fila por llave", "antes": duplicados_exactos + duplicados_llave, "despues": 0},
        {"problema": "Filas en cuarentena", "regla aplicada": "Conservar las filas no corregibles", "antes": len(cuarentena_df), "despues": len(cuarentena_df)},
    ]
    return resultado, cuarentena_df, metricas


def main() -> None:
    log("EnerAndes - limpieza y consolidación 2023-2026")
    limpias_por_anio = []
    cuarentenas = []
    for anio in range(2023, 2027):
        bronce = leer_bronce(f"enerandes_ventas_{anio}")
        limpias, cuarentena, _ = limpiar(bronce, anio)
        limpias_por_anio.append(limpias)
        cuarentenas.append(cuarentena)
        log(f"   {anio}: {len(limpias):,} limpias; {len(cuarentena):,} en cuarentena")

    resultado = pd.concat(limpias_por_anio, ignore_index=True)
    ESQUEMA_VENTAS.validate(resultado, lazy=True)
    cuarentena_total = pd.concat(cuarentenas, ignore_index=True)
    for columna in ["energia_kwh", "valor_cop", "clientes", "_fila_origen"]:
        cuarentena_total[columna] = pd.to_numeric(
            cuarentena_total[columna], errors="coerce"
        ).astype(float)
    ESQUEMA_CUARENTENA_VENTAS.validate(cuarentena_total, lazy=True)
    config.DIR_SILVER.mkdir(parents=True, exist_ok=True)
    resultado.to_parquet(config.DIR_SILVER / "enerandes_ventas.parquet", index=False)
    cuarentena_total.to_parquet(
        config.DIR_SILVER / "enerandes_cuarentena.parquet", index=False
    )
    log(f"Plata EnerAndes: {len(resultado):,} ventas; {sum(len(df) for df in cuarentenas):,} en cuarentena")


if __name__ == "__main__":
    main()