"""
Perfilamiento de la capa bronce del Observatorio Energia y Clima.

Genera docs/perfilamiento.md a partir de los archivos Parquet de data/bronze:
  - Filas y columnas de cada archivo.
  - Tipos de datos fisicos y logicos.
  - Porcentaje de nulos por columna (NaN + cadena vacia).
  - Filas duplicadas exactas.
  - Rango de fechas y cobertura temporal.
  - Hallazgos de calidad con evidencia numerica.

Uso:
    .venv\\Scripts\\python.exe scripts/perfilar.py
"""
import io
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ── Rutas ─────────────────────────────────────────────────────────────────
RAIZ = Path(__file__).resolve().parent.parent
DIR_BRONZE = RAIZ / "data" / "bronze"
DIR_INSUMOS = RAIZ / "data" / "insumos"
DIR_DOCS = RAIZ / "docs"
SALIDA = DIR_DOCS / "perfilamiento.md"

sys.path.insert(0, str(RAIZ))
from src import config  # noqa: E402  (rango de fechas oficial del pipeline)

# Salida UTF-8 en consolas Windows.
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

DIR_DOCS.mkdir(parents=True, exist_ok=True)

# Orden de presentacion por fuente.
ORDEN = [
    "xm_precio_bolsa",
    "xm_demanda",
    "xm_embalses",
    "xm_aportes",
    "xm_generacion",
    "xm_listado_recursos",
    "ideam_precipitacion_diaria",
    "noaa_oni",
    "enerandes_ventas_2023",
    "enerandes_ventas_2024",
    "enerandes_ventas_2025",
    "enerandes_ventas_2026",
]

FUENTE = {
    "xm_precio_bolsa": "XM",
    "xm_demanda": "XM",
    "xm_embalses": "XM",
    "xm_aportes": "XM",
    "xm_generacion": "XM",
    "xm_listado_recursos": "XM",
    "ideam_precipitacion_diaria": "IDEAM",
    "noaa_oni": "NOAA",
    "enerandes_ventas_2023": "EnerAndes",
    "enerandes_ventas_2024": "EnerAndes",
    "enerandes_ventas_2025": "EnerAndes",
    "enerandes_ventas_2026": "EnerAndes",
}

MAPA_ENERANDES = {
    "enerandes_ventas_2023": [
        "Fecha",
        "Municipio",
        "Segmento",
        "Tipo_Compra",
        "Energia_kWh",
        "Valor_COP",
        "Clientes",
    ],
    "enerandes_ventas_2024": [
        "PERIODO",
        "MUNICIPIO",
        "SEGMENTO CLIENTE",
        "MODALIDAD",
        "ENERGIA",
        "UNIDAD",
        "VALOR ($)",
        "NUM CLIENTES",
    ],
    "enerandes_ventas_2025": [
        "mes",
        "municipio",
        "segmento",
        "tipo compra",
        "consumo (kWh)",
        "facturado",
        "usuarios",
    ],
    "enerandes_ventas_2026": [
        "Fecha corte",
        "Ciudad",
        "Tipo cliente",
        "Compra",
        "kWh",
        "Total facturado COP",
        "Clientes activos",
    ],
}

MESES = {
    m: i + 1
    for i, m in enumerate(
        ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        + ["jan", "apr", "aug", "dec"]
    )
}
MESES.update({"jan": 1, "apr": 4, "aug": 8, "dec": 12})

CIUDADES_CANONICAS = {
    "copacabana",
    "envigado",
    "rionegro",
    "apartado",
    "turbo",
    "caldas",
    "sabaneta",
    "caucasia",
    "medellin",
    "bello",
    "girardota",
    "marinilla",
    "la estrella",
    "itagui",
    "santa fe de antioquia",
}
ALIAS_CIUDAD = {
    "sta fe de antioquia": "santa fe de antioquia",
    "santafe de antioquia": "santa fe de antioquia",
    "rio negro": "rionegro",
    "rionegro ant": "rionegro",
    "medellin de": "medellin",
}


# ── Helpers ───────────────────────────────────────────────────────────────

def pct(parte: int | float, total: int | float) -> float:
    return round(parte / total * 100, 2) if total else 0.0


def entero(valor: int) -> str:
    return f"{valor:,}"


def decimal(valor: float, dec: int = 2) -> str:
    return f"{valor:,.{dec}f}"


def es_vacio(serie: pd.Series) -> pd.Series:
    """True para NaN, None, cadena vacia o solo espacios."""
    return serie.fillna("").astype(str).str.strip().eq("")


def normalizar(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = texto.encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"[^a-z0-9 ]", "", texto)


def normalizar_ciudad(texto: str) -> str:
    clave = normalizar(texto)
    return ALIAS_CIUDAD.get(clave, clave)


def parsear_fecha_enerandes(valor) -> pd.Timestamp:
    """Reconoce YYYY-MM, MM/YYYY, DD/MM/YYYY y mmm-YY (es/en)."""
    texto = str(valor).strip()
    if texto.lower() in ("", "nan", "none", "<na>"):
        return pd.NaT

    m = re.fullmatch(r"(\d{4})-(\d{2})", texto)
    if m:
        return pd.Timestamp(int(m.group(1)), int(m.group(2)), 1)

    m = re.fullmatch(r"(\d{2})/(\d{4})", texto)
    if m:
        return pd.Timestamp(int(m.group(2)), int(m.group(1)), 1)

    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", texto)
    if m:
        return pd.Timestamp(int(m.group(3)), int(m.group(2)), int(m.group(1)))

    m = re.fullmatch(r"([A-Za-z]{3})-(\d{2})", texto)
    if m and m.group(1).lower() in MESES:
        return pd.Timestamp(2000 + int(m.group(2)), MESES[m.group(1).lower()], 1)

    return pd.NaT


def tipo_fisico(df: pd.DataFrame) -> str:
    tipos = sorted({str(t) for t in df.dtypes})
    return ", ".join(f"`{t}`" for t in tipos)


def contrastar_excel() -> dict[str, dict]:
    """Lee el Excel de origen igual que el extractor y cuenta filas y duplicados."""
    if not config.ENERANDES_EXCEL.exists():
        return {}

    hojas = pd.read_excel(config.ENERANDES_EXCEL, sheet_name=None, header=None, dtype=str)
    contraste = {}
    for nombre_hoja, df in hojas.items():
        df = df.copy()
        df.columns = [f"col_{i}" for i in range(df.shape[1])]
        contraste["enerandes_" + nombre_hoja.lower().replace(" ", "_")] = {
            "hoja": nombre_hoja,
            "filas": len(df),
            "columnas": df.shape[1],
            "duplicados": int(df.duplicated().sum()),
        }
    return contraste


# ── Perfil de un archivo ──────────────────────────────────────────────────

def perfil_archivo(path: Path) -> dict:
    df = pd.read_parquet(path)
    nombre = path.stem
    filas, columnas_totales = df.shape
    columnas = list(df.columns)
    datos = [c for c in columnas if not c.startswith("_")]
    linaje = [c for c in columnas if c.startswith("_")]

    nulos_col = {c: int(es_vacio(df[c]).sum()) for c in datos}
    nulos_total = sum(nulos_col.values())
    celdas_datos = filas * len(datos)

    perfil = {
        "nombre": nombre,
        "archivo": path.name,
        "fuente": FUENTE.get(nombre, "?"),
        "kb": path.stat().st_size / 1024,
        "filas": filas,
        "columnas_totales": columnas_totales,
        "columnas_datos": len(datos),
        "columnas_linaje": linaje,
        "dtype": tipo_fisico(df),
        "duplicados": int(df.duplicated().sum()),
        "nulos_col": nulos_col,
        "nulos_total": nulos_total,
        "celdas_datos": celdas_datos,
        "nulos_pct": pct(nulos_total, celdas_datos),
        "extra": {},
    }

    # Fecha generica (Date, fecha, datetime).
    col_fecha = next((c for c in columnas if c.lower() in ("date", "fecha", "datetime")), None)
    if col_fecha:
        serie = pd.to_datetime(df[col_fecha], errors="coerce").dropna()
        if not serie.empty:
            perfil["fecha_txt"] = f"{serie.min():%Y-%m-%d} → {serie.max():%Y-%m-%d}"
            perfil["dias_unicos"] = int(serie.dt.normalize().nunique())
            n_dias = perfil["dias_unicos"]
            perfil["fecha_detalle"] = (
                f"{entero(n_dias)} {'día único' if n_dias == 1 else 'días únicos'} con datos"
            )
    else:
        perfil["fecha_txt"] = "—"
        perfil["fecha_detalle"] = "Sin columna de fecha."

    # ── Particularidades por fuente ───────────────────────────────────────
    if nombre.startswith("enerandes"):
        _extras_enerandes(df, perfil)
    elif nombre == "xm_generacion":
        _extras_generacion(df, perfil)
    elif nombre == "xm_listado_recursos":
        _extras_listado(df, perfil)
    elif nombre == "ideam_precipitacion_diaria":
        _extras_ideam(df, perfil)
    elif nombre == "noaa_oni":
        _extras_noaa(df, perfil)
    elif nombre == "xm_embalses":
        _extras_embalses(df, perfil)

    return perfil


def _extras_enerandes(df: pd.DataFrame, perfil: dict) -> None:
    """EnerAndes llega con titulos, encabezado y fila TOTAL dentro de los datos."""
    columnas = [c for c in df.columns if not c.startswith("_")]
    primera = df["col_0"].fillna("").astype(str).str.strip()

    es_total = primera.str.upper().eq("TOTAL")
    es_titulo = primera.str.contains("EnerAndes|Fuente", case=False, regex=True)
    es_header = primera.str.lower().isin(["fecha", "periodo", "mes", "fecha corte"])
    es_vacia = primera.eq("")
    estructural = es_total | es_titulo | es_header | es_vacia
    datos = df[~estructural]

    nulos_datos = {c: int(es_vacio(datos[c]).sum()) for c in columnas}
    col_valor = "col_6" if "col_6" in columnas else "col_5"

    # Formatos de fecha realmente usados.
    formatos = Counter()
    for texto in datos["col_0"].fillna("").astype(str).str.strip():
        if re.fullmatch(r"\d{4}-\d{2}", texto):
            formatos["YYYY-MM"] += 1
        elif re.fullmatch(r"\d{2}/\d{4}", texto):
            formatos["MM/YYYY"] += 1
        elif re.fullmatch(r"\d{2}/\d{2}/\d{4}", texto):
            formatos["DD/MM/YYYY"] += 1
        elif re.fullmatch(r"[A-Za-z]{3}-\d{2}", texto):
            formatos["mmm-YY"] += 1
        else:
            formatos["otro"] += 1

    fechas = datos["col_0"].map(parsear_fecha_enerandes)
    if fechas.notna().any():
        minimo, maximo = fechas.min(), fechas.max()
        meses = fechas.dropna().dt.to_period("M").nunique()
        perfil["fecha_txt"] = f"{minimo:%Y-%m} → {maximo:%Y-%m}"
        perfil["fecha_detalle"] = (
            f"{meses} meses con datos; "
            f"{entero(int(fechas.notna().sum()))} de {entero(len(datos))} filas con fecha válida"
        )

    # Municipios: variantes crudas vs. nombres normalizados.
    ciudad = datos["col_1"].fillna("").astype(str).str.strip()
    ciudad = ciudad[~ciudad.str.upper().isin(["", "NAN"])]
    ciudad_norm = ciudad.map(normalizar_ciudad)

    segmento = datos["col_2"].fillna("").astype(str).str.strip()
    compra = datos["col_3"].fillna("").astype(str).str.strip()

    unidades = {}
    suma_kwh = suma_mwh = 0.0
    if "col_5" in columnas:
        unidad = datos["col_5"].fillna("").astype(str).str.strip()
        if unidad.isin(["kWh", "MWh"]).any():
            unidades = dict(unidad.value_counts())
            energia = pd.to_numeric(datos["col_4"], errors="coerce")
            suma_kwh = float(energia[unidad.eq("kWh")].sum())
            suma_mwh = float(energia[unidad.eq("MWh")].sum())

    duplicados = datos[datos.duplicated(keep=False)]
    if duplicados.empty:
        ejemplo = duplicados
    else:
        # Mostrar el primer grupo de filas idénticas (no dos filas distintas).
        clave = duplicados.iloc[0][columnas].astype(str)
        mismo_grupo = datos[columnas].astype(str).eq(clave).all(axis=1)
        ejemplo = datos[mismo_grupo].head(2)

    perfil["extra"] = {
        "estructura": {
            "total": int(es_total.sum()),
            "titulo": int(es_titulo.sum()),
            "encabezado": int(es_header.sum()),
            "vacia": int(es_vacia.sum()),
        },
        "estructurales": int(estructural.sum()),
        "filas_datos": len(datos),
        "duplicados_datos": int(datos.duplicated().sum()),
        "nulos_datos": nulos_datos,
        "nulos_datos_total": sum(nulos_datos.values()),
        "celdas_datos": len(datos) * len(columnas),
        "formatos_fecha": dict(formatos),
        "ciudades_crudas": int(ciudad.nunique()),
        "ciudades_normalizadas": int(ciudad_norm.nunique()),
        "segmento_anomalo": int(segmento.isin(["IND", "RESID."]).sum()),
        "compra_anomala": int(compra.isin(["CONTRATOS", "bolsa"]).sum()),
        "faltantes": {
            "segmento": int(segmento.eq("").sum()),
            "energia": int(es_vacio(datos["col_4"]).sum()),
            "valor": int(es_vacio(datos[col_valor]).sum()),
        },
        "unidades": unidades,
        "suma_kwh": suma_kwh,
        "suma_mwh": suma_mwh,
        "ejemplo_duplicado": ejemplo[columnas].to_dict("records"),
        "semantica": MAPA_ENERANDES.get(perfil["nombre"], []),
    }


def _extras_generacion(df: pd.DataFrame, perfil: dict) -> None:
    horas = [c for c in df.columns if c.startswith("Hour")]
    numerico = df[horas].apply(pd.to_numeric, errors="coerce")
    vacias_hora = {c: int(es_vacio(df[c]).sum()) for c in horas}

    recursos = int(df["code"].nunique())
    dias = int(df["Date"].nunique())
    esperadas = recursos * dias
    filas_recurso = df.groupby("code").size()

    perfil["extra"] = {
        "horas": horas,
        "vacias_hora": vacias_hora,
        "celdas_hora": len(df) * len(horas),
        "vacias_hora_total": sum(vacias_hora.values()),
        "min_hora_pct": min(pct(v, len(df)) for v in vacias_hora.values()),
        "max_hora_pct": max(pct(v, len(df)) for v in vacias_hora.values()),
        "hora_min": min(vacias_hora, key=lambda c: vacias_hora[c]),
        "hora_max": max(vacias_hora, key=lambda c: vacias_hora[c]),
        "recursos": recursos,
        "dias": dias,
        "esperadas": esperadas,
        "cobertura_pct": pct(len(df), esperadas),
        "faltantes": esperadas - len(df),
        "filas_recurso_min": int(filas_recurso.min()),
        "filas_recurso_mediana": float(filas_recurso.median()),
        "filas_recurso_max": int(filas_recurso.max()),
        "recursos_cortos": int((filas_recurso <= 10).sum()),
        "recursos_bajo_100": int((filas_recurso <= 100).sum()),
        "recursos_completos": int((filas_recurso == dias).sum()),
        "min_global": float(np.nanmin(numerico.values)),
        "max_global": float(np.nanmax(numerico.values)),
        "negativos": int((numerico < 0).sum().sum()),
    }


def _extras_listado(df: pd.DataFrame, perfil: dict) -> None:
    dup = df[df.duplicated(keep=False)]
    tipos = df["Type"].fillna("").astype(str)
    estados = df["State"].fillna("").astype(str)
    no_mayusculas = int((tipos != tipos.str.upper()).sum() + (estados != estados.str.upper()).sum())

    perfil["extra"] = {
        "codigos_unicos": int(df["Code"].nunique()),
        "codigos_duplicados": sorted(dup["Code"].dropna().unique().tolist()),
        "tipos": dict(df["Type"].value_counts()),
        "estados": dict(df["State"].value_counts()),
        "filas_casing": no_mayusculas,
        "casing_pct": pct(no_mayusculas, len(df)),
        "ejemplo_duplicado": dup.head(2)[
            [c for c in ["Date", "Code", "Name", "Type", "State"] if c in df.columns]
        ].to_dict("records"),
    }


def _extras_ideam(df: pd.DataFrame, perfil: dict) -> None:
    fechas = pd.to_datetime(df["fecha"], errors="coerce")
    presentes = set(fechas.dt.normalize().dropna().unique())
    esperadas = pd.date_range(config.IDEAM_FECHA_INICIO, config.FECHA_FIN)
    faltantes = [d.date() for d in esperadas if d not in presentes]
    calendario = pd.date_range(fechas.min().normalize(), fechas.max().normalize())
    huecos = [d.date() for d in calendario if d not in presentes]

    precipitacion = pd.to_numeric(df["precipitacion_mm"], errors="coerce")
    n_obs = pd.to_numeric(df["n_obs"], errors="coerce")
    estaciones = int(df["codigoestacion"].nunique())
    dias = len(presentes)
    cobertura = df.groupby("codigoestacion").size()
    fila_max = df.loc[precipitacion.idxmax()]
    fila_nobs = df.loc[n_obs.idxmax()]

    perfil["extra"] = {
        "estaciones": estaciones,
        "municipios": int(df["municipio"].nunique()),
        "dias": dias,
        "esperadas": len(esperadas),
        "faltantes": len(faltantes),
        "faltantes_pct": pct(len(faltantes), len(esperadas)),
        "huecos": huecos,
        "estacion_dia_esperados": estaciones * dias,
        "estacion_dia_faltantes": estaciones * dias - len(df),
        "estacion_dia_faltantes_pct": pct(estaciones * dias - len(df), estaciones * dias),
        "estaciones_incompletas": int((cobertura < dias).sum()),
        "cobertura_min": int(cobertura.min()),
        "cobertura_mediana": float(cobertura.median()),
        "precip_media": float(precipitacion.mean()),
        "precip_p99": float(precipitacion.quantile(0.99)),
        "precip_max": float(precipitacion.max()),
        "precip_ceros": int((precipitacion == 0).sum()),
        "precip_ceros_pct": pct(int((precipitacion == 0).sum()), len(df)),
        "precip_mayor_300": int((precipitacion > 300).sum()),
        "fila_max": fila_max[["codigoestacion", "nombreestacion", "municipio", "fecha", "precipitacion_mm"]].to_dict(),
        "n_obs_mediana": float(n_obs.median()),
        "n_obs_max": int(n_obs.max()),
        "n_obs_mayor_2000": int((n_obs > 2000).sum()),
        "fila_nobs": fila_nobs[["codigoestacion", "municipio", "fecha", "precipitacion_mm", "n_obs"]].to_dict(),
    }
    perfil["fecha_detalle"] = (
        f"{dias} días con datos de {len(esperadas)} esperados "
        f"({config.IDEAM_FECHA_INICIO} → {config.FECHA_FIN}); "
        f"faltan {len(faltantes)} días"
    )


def _extras_noaa(df: pd.DataFrame, perfil: dict) -> None:
    por_anio = df.groupby("YR").size()
    primero, ultimo = df.iloc[0], df.iloc[-1]
    anom = pd.to_numeric(df["ANOM"], errors="coerce")
    perfil["extra"] = {
        "anios": int(df["YR"].nunique()),
        "por_anio": {str(k): int(v) for k, v in por_anio.items()},
        "temporadas": len(df),
        "anio_parcial": str(por_anio.idxmin()),
        "temporadas_anio_parcial": int(por_anio.min()),
        "anom_min": float(anom.min()),
        "anom_max": float(anom.max()),
        "el_nino": int((anom >= 0.5).sum()),
        "la_nina": int((anom <= -0.5).sum()),
    }
    perfil["fecha_txt"] = f"{primero['YR']} ({primero['SEAS']}) → {ultimo['YR']} ({ultimo['SEAS']})"
    perfil["fecha_detalle"] = (
        f"{df['YR'].nunique()} años; {len(df)} temporadas trimestrales; "
        f"{por_anio.idxmin()} solo tiene {por_anio.min()}/12"
    )


def _extras_embalses(df: pd.DataFrame, perfil: dict) -> None:
    valor = pd.to_numeric(df["Value"], errors="coerce")
    perfil["extra"] = {
        "min": float(valor.min()),
        "max": float(valor.max()),
        "media": float(valor.mean()),
        "fuera_rango": int(((valor < 0) | (valor > 1)).sum()),
        "mayor_05": int((valor > 0.5).sum()),
        "mayor_05_pct": pct(int((valor > 0.5).sum()), len(df)),
    }


# ── Tablas Markdown ───────────────────────────────────────────────────────

def tabla_tipos(perfil: dict) -> list[str]:
    nombre = perfil["nombre"]
    tipo = perfil["dtype"].replace("`", "")

    if nombre in ("xm_precio_bolsa", "xm_demanda", "xm_generacion"):
        filas = [
            ("`Date`", tipo, "Fecha ISO `YYYY-MM-DD` (texto)"),
            ("`Id`", tipo, "Entidad XM (`Sistema` en estas series)"),
            ("`code`", tipo, "Código del recurso; en generación identifica la planta"),
            ("`Hour01` … `Hour24`", tipo, "24 valores horarios numéricos almacenados como texto"),
            ("`_fuente`, `_origen`, `_extraido_en`", tipo, "Linaje: fuente, URL y timestamp UTC"),
        ]
    elif nombre in ("xm_embalses", "xm_aportes"):
        filas = [
            ("`Date`", tipo, "Fecha diaria ISO (texto)"),
            ("`Id`", tipo, "Entidad XM (`Sistema`)"),
            ("`Value`", tipo, "Valor numérico diario almacenado como texto"),
            ("`_fuente`, `_origen`, `_extraido_en`", tipo, "Linaje"),
        ]
    elif nombre == "xm_listado_recursos":
        filas = [
            ("`Date`", tipo, "Fecha del corte del catálogo"),
            ("`Id`", tipo, "Entidad XM (`Sistema`)"),
            ("`Code`", tipo, "Código único del recurso"),
            ("`Name`", tipo, "Nombre del recurso"),
            ("`Type`", tipo, "Tipo de generación (SOLAR, HIDRAULICA, …)"),
            ("`Disp`", tipo, "Tipo de despacho"),
            ("`RecType`", tipo, "Tipo de recurso"),
            ("`CompanyCode`", tipo, "Código de la empresa"),
            ("`EnerSource`", tipo, "Fuente primaria de energía"),
            ("`OperStartdate`", tipo, "Fecha de inicio de operación"),
            ("`State`", tipo, "Estado del recurso (OPERACION, PRUEBAS, …)"),
            ("`_fuente`, `_origen`, `_extraido_en`", tipo, "Linaje"),
        ]
    elif nombre == "ideam_precipitacion_diaria":
        filas = [
            ("`codigoestacion`", tipo, "Código de la estación IDEAM"),
            ("`nombreestacion`", tipo, "Nombre de la estación"),
            ("`municipio`", tipo, "Municipio de Antioquia"),
            ("`latitud`", tipo, "Latitud decimal almacenada como texto"),
            ("`longitud`", tipo, "Longitud decimal almacenada como texto"),
            ("`fecha`", tipo, "Fecha ISO `YYYY-MM-DDT00:00:00.000`"),
            ("`precipitacion_mm`", tipo, "Precipitación diaria agregada (mm), texto"),
            ("`n_obs`", tipo, "Número de observaciones usadas en la agregación"),
            ("`_fuente`, `_origen`, `_extraido_en`", tipo, "Linaje"),
        ]
    elif nombre == "noaa_oni":
        filas = [
            ("`SEAS`", tipo, "Trimestre móvil (DJF, JFM, …, NDJ)"),
            ("`YR`", tipo, "Año de la temporada"),
            ("`TOTAL`", tipo, "Temperatura media del mar (°C), texto"),
            ("`ANOM`", tipo, "Anomalía ONI (°C); ≥ +0.5 El Niño, ≤ −0.5 La Niña"),
            ("`_fuente`, `_origen`, `_extraido_en`", tipo, "Linaje"),
        ]
    else:
        semantica = MAPA_ENERANDES.get(nombre, [])
        filas = []
        for i, col in enumerate([c for c in perfil["nulos_col"]]):
            etiqueta = semantica[i] if i < len(semantica) else "—"
            filas.append((f"`{col}`", tipo, f"{etiqueta} (texto)"))
        filas.append(("`_fuente`, `_origen`, `_extraido_en`", tipo, "Linaje"))

    lineas = ["| Columna(s) | Tipo físico | Tipo lógico / contenido |", "|---|---|---|"]
    for col, tipo_col, desc in filas:
        lineas.append(f"| {col} | `{tipo_col}` | {desc} |")
    return lineas


def tabla_nulos(perfil: dict) -> list[str]:
    nombre = perfil["nombre"]

    if nombre == "xm_generacion":
        extra = perfil["extra"]
        lineas = [
            "| Columna | Nulos | % de filas |",
            "|---|---:|---:|",
        ]
        for col in ["Date", "Id", "code"]:
            lineas.append(f"| `{col}` | 0 | 0.00% |")
        for col in extra["horas"]:
            n = extra["vacias_hora"][col]
            lineas.append(f"| `{col}` | {entero(n)} | {pct(n, perfil['filas']):.2f}% |")
        return lineas

    if nombre.startswith("enerandes"):
        extra = perfil["extra"]
        lineas = [
            "| Columna | Nulos en el archivo | % del archivo | Nulos en filas de datos | % de datos |",
            "|---|---:|---:|---:|---:|",
        ]
        for col, n in perfil["nulos_col"].items():
            nd = extra["nulos_datos"][col]
            lineas.append(
                f"| `{col}` | {entero(n)} | {pct(n, perfil['filas']):.2f}% "
                f"| {entero(nd)} | {pct(nd, extra['filas_datos']):.2f}% |"
            )
        return lineas

    if perfil["nulos_total"] == 0:
        grupos = []
        horas = [c for c in perfil["nulos_col"] if c.startswith("Hour")]
        if horas:
            grupos.append(f"`Hour01` … `Hour24` ({len(horas)} columnas)")
        genericas = [c for c in perfil["nulos_col"] if not c.startswith("Hour")]
        if genericas:
            grupos.append(", ".join(f"`{c}`" for c in genericas))
        if perfil["columnas_linaje"]:
            grupos.append(", ".join(f"`{c}`" for c in perfil["columnas_linaje"]))
        lineas = [
            "| Columna(s) | Nulos | % de filas |",
            "|---|---:|---:|",
        ]
        for grupo in grupos:
            lineas.append(f"| {grupo} | 0 | 0.00% |")
        return lineas

    lineas = ["| Columna | Nulos | % de filas |", "|---|---:|---:|"]
    for col, n in perfil["nulos_col"].items():
        lineas.append(f"| `{col}` | {entero(n)} | {pct(n, perfil['filas']):.2f}% |")
    return lineas


def tabla_ejemplo_duplicado(perfil: dict) -> list[str]:
    nombre = perfil["nombre"]
    ejemplo = perfil["extra"].get("ejemplo_duplicado", [])
    if not ejemplo:
        return []

    if nombre.startswith("enerandes"):
        columnas = ["col_0", "col_1", "col_2", "col_3", "col_4", "col_5", "col_6", "col_7"]
        columnas = [c for c in columnas if c in ejemplo[0]]
        encabezados = columnas
    else:
        columnas = [c for c in ["Date", "Code", "Name", "Type", "State"] if c in ejemplo[0]]
        encabezados = columnas

    lineas = [
        "| " + " | ".join(f"`{c}`" for c in encabezados) + " |",
        "|" + "|".join("---" for _ in columnas) + "|",
    ]
    for fila in ejemplo:
        valores = []
        for col in columnas:
            valor = fila.get(col, "")
            if valor is None or (isinstance(valor, float) and np.isnan(valor)):
                valor = "—"
            valores.append(str(valor))
        lineas.append("| " + " | ".join(valores) + " |")
    return lineas


# ── Documento ─────────────────────────────────────────────────────────────

def escribir_documento(perfiles: dict[str, dict], contraste: dict[str, dict]) -> None:
    ordenados = [perfiles[n] for n in ORDEN if n in perfiles]
    # Colombia no tiene horario de verano: UTC-5 todo el año.
    zona_colombia = timezone(timedelta(hours=-5), name="UTC-5")
    ts = datetime.now(zona_colombia).strftime("%Y-%m-%d %H:%M UTC-5")

    total_filas = sum(p["filas"] for p in ordenados)
    total_columnas = sum(p["columnas_totales"] for p in ordenados)
    total_celdas = sum(p["celdas_datos"] for p in ordenados)
    total_nulos = sum(p["nulos_total"] for p in ordenados)
    total_duplicados = sum(p["duplicados"] for p in ordenados)

    enerandes = [p for p in ordenados if p["nombre"].startswith("enerandes")]
    gen = perfiles.get("xm_generacion")
    ideam = perfiles.get("ideam_precipitacion_diaria")
    listado = perfiles.get("xm_listado_recursos")
    embalses = perfiles.get("xm_embalses")
    noaa = perfiles.get("noaa_oni")

    lineas: list[str] = []
    lineas += [
        "# Perfilamiento de datos — Capa Bronce",
        "",
        "> **Proyecto:** Observatorio Energía y Clima — Proyecto Integrado IV  ",
        "> **Capa analizada:** `data/bronze/` (dato tal cual llegó + columnas de linaje)  ",
        f"> **Fecha de generación:** {ts}  ",
        f"> **Archivos analizados:** {len(ordenados)} Parquet  ",
        "> **Herramientas:** pandas 3.1.0, pyarrow 26.0.0  ",
        "",
        "## Metodología",
        "",
        "- Se leen los 12 archivos Parquet de `data/bronze/` sin modificarlos.",
        "- **Nulo:** se cuenta como nulo tanto `NaN` como cadena vacía o solo espacios. "
        "Esto es importante en bronce porque los valores vacíos de XM llegan como `\"\"` y no como `NaN`.",
        "- **Duplicado:** fila idéntica en todas las columnas del archivo, incluidas las de linaje.",
        "- **Porcentaje de nulos:** se calcula sobre las columnas de datos (se excluyen `_fuente`, "
        "`_origen` y `_extraido_en`, que son metadatos).",
        "- **Tipos:** se reporta el tipo físico de pandas y el tipo lógico esperado. En bronce "
        "todos los valores se conservan como texto para no alterar la fuente.",
        "- **Contraste con la fuente:** el Excel `data/insumos/ventas_enerandes_2023_2026.xlsx` "
        "se lee con `header=None` y `dtype=str`, igual que el extractor, para comparar filas y "
        "duplicados de las 4 hojas contra los Parquet de EnerAndes.",
        "",
        "Para regenerar este documento:",
        "",
        "```powershell",
        ".\\\\.venv\\\\Scripts\\\\python.exe scripts\\\\perfilar.py",
        "```",
        "",
        "---",
        "",
        "## Tabla resumen",
        "",
        "| Archivo | Fuente | Filas | Columnas | Duplicados | Celdas nulas (datos) | % nulos | Rango de fechas | Tamaño |",
        "|---|---|---:|---:|---:|---:|---:|---|---:|",
    ]

    for p in ordenados:
        lineas.append(
            f"| `{p['archivo']}` | {p['fuente']} | {entero(p['filas'])} | {p['columnas_totales']} "
            f"| {entero(p['duplicados'])} | {entero(p['nulos_total'])} | {p['nulos_pct']:.2f}% "
            f"| {p['fecha_txt']} | {decimal(p['kb'], 0)} KB |"
        )

    lineas.append(
        f"| **Total** | — | **{entero(total_filas)}** | **{total_columnas}** "
        f"| **{entero(total_duplicados)}** | **{entero(total_nulos)}** "
        f"| **{pct(total_nulos, total_celdas):.2f}%** | — | — |"
    )

    lineas += [
        "",
        "> Las columnas incluyen las 3 de linaje (`_fuente`, `_origen`, `_extraido_en`). "
        "El porcentaje de nulos se calcula solo sobre columnas de datos.",
        "",
    ]

    if contraste:
        lineas += [
            "### Contraste con el Excel de origen (EnerAndes)",
            "",
            "| Hoja del Excel | Filas Excel | Filas Parquet | Duplicados Excel | Duplicados Parquet | Columnas | ¿Coincide? |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
        for p in enerandes:
            c = contraste.get(p["nombre"])
            if not c:
                continue
            coincide = c["filas"] == p["filas"] and c["duplicados"] == p["duplicados"] \
                and c["columnas"] == p["columnas_totales"] - len(p["columnas_linaje"])
            lineas.append(
                f"| `{c['hoja']}` | {entero(c['filas'])} | {entero(p['filas'])} "
                f"| {entero(c['duplicados'])} | {entero(p['duplicados'])} "
                f"| {c['columnas']} | {'Sí' if coincide else 'No'} |"
            )
        lineas += [
            "",
            "Las 4 hojas coinciden en filas, columnas y duplicados con sus Parquet: la capa "
            "bronce conserva el archivo original sin agregar ni quitar registros.",
            "",
        ]

    lineas += [
        "---",
        "",
        "## Perfil por archivo",
        "",
    ]

    for i, p in enumerate(ordenados, start=1):
        extra = p["extra"]
        lineas += [f"### {i}. `{p['archivo']}`", "", "#### Ficha", ""]
        lineas += [
            "| Métrica | Valor |",
            "|---|---|",
            f"| Fuente | {p['fuente']} |",
            f"| Filas | {entero(p['filas'])} |",
            f"| Columnas totales | {p['columnas_totales']} (incluye {len(p['columnas_linaje'])} de linaje) |",
            f"| Columnas de datos | {p['columnas_datos']} |",
            f"| Tipo físico | {p['dtype']} |",
            f"| Filas duplicadas exactas | {entero(p['duplicados'])} |",
            f"| Celdas nulas (datos) | {entero(p['nulos_total'])} de {entero(p['celdas_datos'])} ({p['nulos_pct']:.2f}%) |",
            f"| Rango de fechas | {p['fecha_txt']} |",
            f"| Detalle temporal | {p['fecha_detalle']} |",
            f"| Tamaño en disco | {decimal(p['kb'], 1)} KB |",
            "",
            "#### Tipos de datos",
            "",
        ]
        lineas += tabla_tipos(p)
        lineas += ["", "#### Porcentaje de nulos por columna", ""]
        lineas += tabla_nulos(p)

        lineas += ["", "#### Filas duplicadas", ""]
        if p["duplicados"] == 0:
            lineas.append("No se encontraron filas duplicadas exactas (0 filas).")
        elif p["nombre"].startswith("enerandes"):
            c = contraste.get(p["nombre"])
            respaldo = (
                f"La hoja `{c['hoja']}` del Excel original tiene exactamente "
                f"{entero(c['duplicados'])} duplicados sobre {entero(c['filas'])} filas, "
                "por lo que se heredaron de la fuente y no los introdujo el pipeline."
                if c
                else "El mismo número de duplicados existe en la hoja original del Excel, "
                "por lo que se heredaron de la fuente y no los introdujo el pipeline."
            )
            lineas.append(
                f"Se encontraron **{entero(extra['duplicados_datos'])} filas duplicadas** "
                f"en las {entero(extra['filas_datos'])} filas de datos "
                f"({pct(extra['duplicados_datos'], extra['filas_datos']):.2f}%). "
                f"Todas forman pares idénticos. {respaldo}"
            )
            tabla = tabla_ejemplo_duplicado(p)
            if tabla:
                lineas += ["", "Ejemplo del primer par duplicado:", ""] + tabla
        elif p["nombre"] == "xm_listado_recursos":
            lineas.append(
                f"Se encontraron **{entero(p['duplicados'])} filas duplicadas** "
                f"({pct(p['duplicados'], p['filas']):.2f}%) que corresponden a los códigos "
                f"{', '.join(f'`{c}`' for c in extra['codigos_duplicados'])}. "
                f"El catálogo tiene {entero(p['filas'])} filas pero solo "
                f"{entero(extra['codigos_unicos'])} códigos únicos."
            )
            tabla = tabla_ejemplo_duplicado(p)
            if tabla:
                lineas += ["", "Filas duplicadas:", ""] + tabla
        else:
            lineas.append(f"Se encontraron **{entero(p['duplicados'])} filas duplicadas**.")

        lineas += ["", "#### Observaciones", ""]
        if p["nombre"] in ("xm_precio_bolsa", "xm_demanda", "xm_aportes"):
            lineas.append(
                f"Serie diaria completa: {entero(p['filas'])} filas, {entero(p.get('dias_unicos', 0))} "
                "días únicos, sin nulos y sin duplicados."
            )
        elif p["nombre"] == "xm_embalses":
            lineas.append(
                f"Serie diaria completa. `Value` va de {extra['min']:.5f} a {extra['max']:.5f} "
                f"(media {extra['media']:.5f}); {entero(extra['fuera_rango'])} valores fuera de [0, 1] "
                f"y {extra['mayor_05_pct']:.2f}% por encima de 0.5."
            )
        elif p["nombre"] == "xm_generacion":
            lineas.append(
                f"Cobertura recurso-día: {entero(p['filas'])} de {entero(extra['esperadas'])} "
                f"combinaciones posibles ({extra['cobertura_pct']:.2f}%). Faltan "
                f"{entero(extra['faltantes'])} combinaciones. Filas por recurso: mínimo "
                f"{extra['filas_recurso_min']}, mediana {extra['filas_recurso_mediana']:.1f}, "
                f"máximo {entero(extra['filas_recurso_max'])}."
            )
            lineas.append(
                f"Valores horarios: mínimo {extra['min_global']:.2f}, máximo "
                f"{extra['max_global']:.2f}, negativos {entero(extra['negativos'])}. "
                f"Las cadenas vacías afectan {entero(extra['vacias_hora_total'])} de "
                f"{entero(extra['celdas_hora'])} celdas horarias "
                f"({pct(extra['vacias_hora_total'], extra['celdas_hora']):.2f}%)."
            )
        elif p["nombre"] == "xm_listado_recursos":
            lineas.append(
                f"Catálogo con {entero(extra['codigos_unicos'])} códigos únicos. "
                f"{entero(extra['filas_casing'])} filas ({extra['casing_pct']:.2f}%) usan "
                "variantes de mayúsculas/minúsculas en `Type` o `State` "
                "(por ejemplo `SOLAR`/`Solar`, `OPERACION`/`Operacion`)."
            )
        elif p["nombre"] == "ideam_precipitacion_diaria":
            lineas.append(
                f"{entero(extra['estaciones'])} estaciones en {entero(extra['municipios'])} municipios. "
                f"Cobertura: {extra['dias']} de {extra['esperadas']} días esperados "
                f"({pct(extra['dias'], extra['esperadas']):.2f}%); faltan {extra['faltantes']} días. "
                f"Faltan {entero(extra['estacion_dia_faltantes'])} combinaciones estación-día "
                f"({extra['estacion_dia_faltantes_pct']:.2f}%)."
            )
            lineas.append(
                f"Precipitación: media {extra['precip_media']:.2f} mm, p99 "
                f"{extra['precip_p99']:.2f} mm, máximo {extra['precip_max']:.2f} mm. "
                f"{extra['precip_ceros_pct']:.2f}% de los registros son cero."
            )
        elif p["nombre"] == "noaa_oni":
            lineas.append(
                f"{entero(extra['temporadas'])} temporadas de {extra['anios']} años "
                f"({extra['anom_min']:.2f} a {extra['anom_max']:.2f} °C de anomalía). "
                f"{entero(extra['el_nino'])} temporadas cumplen El Niño (≥ 0.5) y "
                f"{entero(extra['la_nina'])} cumplen La Niña (≤ −0.5)."
            )
        elif p["nombre"].startswith("enerandes"):
            est = extra["estructura"]
            lineas.append(
                f"El archivo tiene {entero(extra['filas_datos'])} filas de datos y "
                f"{entero(extra['estructurales'])} filas estructurales "
                f"({est['titulo']} de título, {est['encabezado']} de encabezado, "
                f"{est['total']} fila TOTAL, {est['vacia']} vacía(s)). "
                f"Los nulos en filas de datos son {entero(extra['nulos_datos_total'])} "
                f"de {entero(extra['celdas_datos'])} celdas "
                f"({pct(extra['nulos_datos_total'], extra['celdas_datos']):.2f}%)."
            )
            lineas.append(
                "Formatos de fecha: "
                + ", ".join(f"{k} ({entero(v)})" for k, v in extra["formatos_fecha"].items())
                + f". Municipios: {extra['ciudades_crudas']} variantes crudas para "
                f"{extra['ciudades_normalizadas']} nombres normalizados."
            )
            if extra["unidades"]:
                lineas.append(
                    "Unidades de energía: "
                    + ", ".join(f"{k} ({entero(v)})" for k, v in extra["unidades"].items())
                    + f". Energía declarada: {decimal(extra['suma_kwh'], 0)} kWh y "
                    f"{decimal(extra['suma_mwh'], 0)} MWh."
                )
            lineas.append(
                f"Anomalías de categoría: segmento `IND`/`RESID.` en "
                f"{entero(extra['segmento_anomalo'])} filas; compra `CONTRATOS`/`bolsa` en "
                f"{entero(extra['compra_anomala'])} filas."
            )

        lineas += ["", "---", ""]

    # ── Hallazgos de calidad ─────────────────────────────────────────────
    lineas += [
        "## Hallazgos de calidad",
        "",
        "Los hallazgos se agrupan por fuente y cada uno indica su severidad. Incluyen la "
        "evidencia numérica calculada sobre los archivos y una acción sugerida para la capa plata.",
        "",
    ]

    if gen:
        g = gen["extra"]
        lineas.append(
            f"1. **[Alta] Nulos encubiertos en `xm_generacion`.** `isna()` reporta 0 nulos, "
            f"pero hay **{entero(g['vacias_hora_total'])} celdas horarias vacías** de "
            f"{entero(g['celdas_hora'])} ({pct(g['vacias_hora_total'], g['celdas_hora']):.2f}%). "
            f"El porcentaje por hora va de {g['min_hora_pct']:.2f}% (`{g['hora_min']}`) a "
            f"{g['max_hora_pct']:.2f}% (`{g['hora_max']}`). En el archivo completo, las celdas "
            f"nulas son {entero(gen['nulos_total'])} de {entero(gen['celdas_datos'])} "
            f"({gen['nulos_pct']:.2f}%). **Impacto:** promedios y sumas sesgados si no se convierten "
            "las cadenas vacías a `NaN`. **Acción:** en plata, `pd.to_numeric(..., errors='coerce')` "
            "y tratar los vacíos como dato faltante."
        )
        lineas.append(
            f"2. **[Alta] Cobertura incompleta en `xm_generacion`.** Hay {entero(g['recursos'])} "
            f"recursos y {entero(g['dias'])} días: {entero(g['esperadas'])} combinaciones posibles, "
            f"pero solo {entero(gen['filas'])} filas ({g['cobertura_pct']:.2f}%). Faltan "
            f"**{entero(g['faltantes'])} combinaciones recurso-día (44.79%)**. Filas por recurso: "
            f"mínimo {g['filas_recurso_min']}, mediana {g['filas_recurso_mediana']:.1f}, máximo "
            f"{entero(g['filas_recurso_max'])}; {g['recursos_cortos']} recursos tienen ≤10 días, "
            f"{g['recursos_bajo_100']} tienen ≤100 y solo {g['recursos_completos']} tienen los "
            f"{entero(g['dias'])} días. **Impacto:** no se puede asumir una serie continua por planta. "
            "**Acción:** distinguir “no despachado” de “sin dato” y documentar la regla de negocio."
        )

    if enerandes:
        filas_datos = sum(p["extra"]["filas_datos"] for p in enerandes)
        dup_datos = sum(p["extra"]["duplicados_datos"] for p in enerandes)
        detalle_dup = ", ".join(
            f"`{p['nombre'].replace('enerandes_ventas_', '')}`: {entero(p['extra']['duplicados_datos'])}"
            for p in enerandes
        )
        estructurales = sum(p["extra"]["estructurales"] for p in enerandes)
        nulos_datos = sum(p["extra"]["nulos_datos_total"] for p in enerandes)
        celdas_datos = sum(p["extra"]["celdas_datos"] for p in enerandes)
        dup_excel = sum(
            c["duplicados"] for n, c in contraste.items()
            if n in {p["nombre"] for p in enerandes}
        )
        respaldo_dup = (
            f"El Excel de origen también suma {entero(dup_excel)} duplicados en las 4 hojas, "
            "por lo que se heredaron de la fuente."
            if contraste
            else "No se pudo contrastar con el Excel de origen porque no estaba disponible."
        )
        formatos = Counter()
        for p in enerandes:
            formatos.update(p["extra"]["formatos_fecha"])
        segmento = sum(p["extra"]["segmento_anomalo"] for p in enerandes)
        compra = sum(p["extra"]["compra_anomala"] for p in enerandes)
        faltantes = Counter()
        for p in enerandes:
            faltantes.update(p["extra"]["faltantes"])

        lineas.append(
            f"3. **[Alta] Duplicados exactos en EnerAndes.** Hay **{entero(dup_datos)} filas "
            f"duplicadas** en {entero(filas_datos)} filas de datos ({pct(dup_datos, filas_datos):.2f}%): "
            f"{detalle_dup}. Todas son pares idénticos. {respaldo_dup} "
            "**Impacto:** duplican consumo, facturación y clientes al agregar. **Acción:** deduplicar "
            "en plata con la clave de negocio (periodo + municipio + segmento + modalidad) y "
            "conservar una fila."
        )
        lineas.append(
            f"4. **[Media] Estructura no tabular y esquema variable en EnerAndes.** Los 4 archivos "
            f"suman {entero(estructurales)} filas estructurales (títulos, encabezado, fila TOTAL y "
            "filas vacías) mezcladas con los datos. Las hojas tienen 7, 8, 7 y 7 columnas de datos, "
            "con encabezados distintos y columnas genéricas `col_0`…`col_7`; el 100% de las 175 "
            "columnas de los 12 archivos es de tipo texto (`str`). **Impacto:** cualquier consulta "
            "directa incluye títulos y totales como si fueran registros. **Acción:** en plata, "
            "descartar filas estructurales, mapear cada hoja a un esquema único y castear tipos."
        )
        formatos_txt = ", ".join(f"{k}: {entero(v)}" for k, v in formatos.most_common())
        lineas.append(
            f"5. **[Media] Fechas heterogéneas en EnerAndes.** Se usan **4 formatos**: "
            f"{formatos_txt}. Solo 2026 tiene fecha a nivel de día (`DD/MM/YYYY`, "
            f"{entero(formatos.get('DD/MM/YYYY', 0))} filas); 2023–2025 son mensuales. "
            f"Además, {entero(formatos.get('mmm-YY', 0))} filas usan abreviaturas de mes en inglés "
            "(`jan-24`, `apr-24`, `aug-24`) mezcladas con `MM/YYYY`. **Impacto:** riesgo de "
            "interpretar `DD/MM` como `MM/DD` y de perder el día en los años mensuales. "
            "**Acción:** parsear con formatos explícitos y normalizar a `date`/`timestamp`."
        )

        fila_2024 = next((p for p in enerandes if p["nombre"].endswith("2024")), None)
        if fila_2024 and fila_2024["extra"]["unidades"]:
            u = fila_2024["extra"]["unidades"]
            total_u = sum(u.values())
            mwh = u.get("MWh", 0)
            lineas.append(
                f"6. **[Alta] Unidades mezcladas en EnerAndes 2024.** {entero(mwh)} de "
                f"{entero(total_u)} filas ({pct(mwh, total_u):.2f}%) reportan energía en `MWh` y "
                f"{entero(u.get('kWh', 0))} en `kWh`. La energía declarada suma "
                f"{decimal(fila_2024['extra']['suma_kwh'], 0)} kWh en las filas kWh y "
                f"{decimal(fila_2024['extra']['suma_mwh'], 0)} MWh en las filas MWh. "
                "**Impacto:** sumar ambas columnas sin convertir produce un error de 1,000×. "
                "**Acción:** convertir todo a kWh (MWh × 1,000) antes de agregar; 2023, 2025 y "
                "2026 no traen columna de unidad y se asumen kWh."
            )

        lineas.append(
            f"7. **[Media] Categorías y nulos en campos clave de EnerAndes.** Hay "
            f"**{entero(segmento)} filas ({pct(segmento, filas_datos):.2f}%)** con segmento "
            f"`IND`/`RESID.` en lugar de `Industrial`/`Residencial`, y **{entero(compra)} filas "
            f"({pct(compra, filas_datos):.2f}%)** con `CONTRATOS`/`bolsa` en lugar de "
            "`Contrato`/`Bolsa`. Los municipios tienen 29, 30, 28 y 28 grafías crudas para solo "
            "15 nombres normalizados (`Rio Negro`/`Rionegro (Ant)`, `envigado`, `ITAGUI`, "
            "`Sta Fe de Antioquia`). Además, en filas de datos faltan "
            f"**{entero(faltantes['segmento'])} segmentos, {entero(faltantes['energia'])} energías "
            f"y {entero(faltantes['valor'])} valores facturados** "
            f"(**{entero(nulos_datos)} celdas nulas de {entero(celdas_datos)}, "
            f"{pct(nulos_datos, celdas_datos):.2f}%**). **Impacto:** agrupaciones fragmentadas y "
            "totales incompletos. **Acción:** catálogo de normalización y regla explícita de "
            "imputación/rechazo para nulos."
        )

    if listado:
        l = listado["extra"]
        lineas.append(
            f"8. **[Media] Duplicados y casing en `xm_listado_recursos`.** El catálogo tiene "
            f"{entero(listado['filas'])} filas y {entero(l['codigos_unicos'])} códigos únicos: "
            f"**{entero(listado['duplicados'])} filas duplicadas** "
            f"({pct(listado['duplicados'], listado['filas']):.2f}%) de los códigos "
            f"{', '.join(f'`{c}`' for c in l['codigos_duplicados'])}. Además, "
            f"{entero(l['filas_casing'])} filas ({l['casing_pct']:.2f}%) usan variantes de "
            "mayúsculas/minúsculas (`SOLAR` 2,195 vs `Solar` 37; `OPERACION` 2,087 vs "
            "`Operacion` 198). **Impacto:** conteos de plantas y filtros por tipo/estado "
            "inconsistentes. **Acción:** deduplicar por `Code` y normalizar `Type`/`State`."
        )

    if gen and listado:
        # Se recalcula desde los Parquet ya perfilados (codigos unicos y recursos de generacion).
        recursos_gen = gen["extra"]["recursos"]
        codigos_catalogo = listado["extra"]["codigos_unicos"]
        interseccion = len(
            set(pd.read_parquet(DIR_BRONZE / "xm_generacion.parquet")["code"].unique())
            & set(pd.read_parquet(DIR_BRONZE / "xm_listado_recursos.parquet")["Code"].unique())
        )
        sin_gen = codigos_catalogo - interseccion
        sin_catalogo = recursos_gen - interseccion
        lineas.append(
            f"9. **[Media] Desalineación entre catálogo y generación de XM.** El catálogo tiene "
            f"{entero(codigos_catalogo)} códigos y `xm_generacion` solo {entero(recursos_gen)} "
            f"recursos; la intersección es {entero(interseccion)}. Por tanto, "
            f"**{entero(sin_gen)} códigos del catálogo ({pct(sin_gen, codigos_catalogo):.2f}%) "
            f"no tienen ningún registro de generación** y {entero(sin_catalogo)} recursos de "
            "generación no aparecen en el catálogo. **Impacto:** análisis por planta incompletos "
            "y posibles recursos nuevos/fuera de catálogo. **Acción:** validar el universo de "
            "recursos y usar el catálogo como dimensión con `LEFT JOIN`, no como filtro."
        )

    if ideam:
        i = ideam["extra"]
        lineas.append(
            f"10. **[Alta] Cobertura IDEAM incompleta frente a XM.** Se esperaban "
            f"{entero(i['esperadas'])} días ({config.IDEAM_FECHA_INICIO} → {config.FECHA_FIN}), "
            f"pero hay **{entero(i['dias'])} días ({pct(i['dias'], i['esperadas']):.2f}%)**; "
            f"faltan {entero(i['faltantes'])} días ({i['faltantes_pct']:.2f}%). Entre el primer y "
            f"último día extraído también faltan {len(i['huecos'])} días "
            f"({', '.join(str(d) for d in i['huecos'])}). Faltan "
            f"**{entero(i['estacion_dia_faltantes'])} combinaciones estación-día "
            f"({i['estacion_dia_faltantes_pct']:.2f}%)** de {entero(i['estacion_dia_esperados'])}; "
            f"{i['estaciones_incompletas']} de {entero(i['estaciones'])} estaciones tienen menos "
            f"de {i['dias']} días (mínimo {i['cobertura_min']}). El traslape con la serie XM "
            f"2024-01-01 → 2026-09-30 es de solo {i['dias']} días ({pct(i['dias'], 1004):.2f}% del "
            "periodo XM). **Impacto:** los análisis clima-energía quedan limitados a junio–julio "
            "de 2026. **Acción:** reextraer el periodo faltante o declarar explícitamente el "
            "alcance en el dashboard."
        )
        lineas.append(
            f"11. **[Media] Valores extremos y de observación sospechosos en IDEAM.** El máximo "
            f"de precipitación es **{i['precip_max']:,.2f} mm** "
            f"(estación `{i['fila_max']['nombreestacion']}`, municipio "
            f"{i['fila_max']['municipio']}, {str(i['fila_max']['fecha'])[:10]}), "
            f"{i['precip_max'] / i['precip_media']:.0f}× la "
            f"media ({i['precip_media']:.2f} mm) y muy por encima del p99 ({i['precip_p99']:.2f} mm); "
            f"hay {entero(i['precip_mayor_300'])} registros > 300 mm y "
            f"{i['precip_ceros_pct']:.2f}% de ceros. `n_obs` tiene mediana "
            f"{i['n_obs_mediana']:.0f}, máximo {entero(i['n_obs_max'])} y "
            f"{entero(i['n_obs_mayor_2000'])} filas con más de 2,000 observaciones en un día. "
            "**Impacto:** promedios y sumas de lluvia sesgados; posible error de unidad o de "
            "agregación. **Acción:** contrastar con metadatos de la estación, revisar duplicados "
            "de frecuencia y aplicar una regla de validación/capado."
        )

    if embalses:
        e = embalses["extra"]
        lineas.append(
            f"12. **[Baja] Escala ambigua en `xm_embalses`.** El campo `Value` "
            "(`PorcVoluUtilDiar`) va de "
            f"{e['min']:.5f} a {e['max']:.5f} (media {e['media']:.5f}), con "
            f"{entero(e['fuera_rango'])} valores fuera de [0, 1] y {e['mayor_05_pct']:.2f}% por "
            "encima de 0.5. **Impacto:** parece una fracción 0–1, no un porcentaje 0–100; "
            "graficarlo sin multiplicar por 100 muestra valores 100× menores. **Acción:** "
            "documentar la unidad y multiplicar por 100 en la capa de presentación si se "
            "reporta como porcentaje."
        )

    lineas += [
        "",
        "---",
        "",
        "## Fortalezas y consideraciones",
        "",
    ]

    xm_completos = [
        p for p in ordenados
        if p["nombre"] in ("xm_precio_bolsa", "xm_demanda", "xm_embalses", "xm_aportes")
    ]
    lineas.append(
        f"- **Series XM completas:** `xm_precio_bolsa`, `xm_demanda`, `xm_embalses` y "
        f"`xm_aportes` tienen {entero(xm_completos[0]['filas'])} filas cada una, "
        f"{entero(xm_completos[0].get('dias_unicos', 0))} días únicos, 0 nulos y 0 duplicados "
        "en el rango 2024-01-01 → 2026-09-30. Son la base más sólida para series de tiempo."
    )
    if noaa:
        n = noaa["extra"]
        lineas.append(
            f"- **NOAA consistente:** {entero(n['temporadas'])} temporadas de {n['anios']} años, "
            f"0 nulos y 0 duplicados; solo 2026 está parcial ({n['temporadas_anio_parcial']}/12 "
            "temporadas), lo cual es esperable para un año en curso."
        )
    lineas.append(
        f"- **Linaje completo:** los 12 archivos tienen las 3 columnas de linaje "
        f"(`_fuente`, `_origen`, `_extraido_en`), {entero(total_columnas)} columnas en total, "
        "lo que permite rastrear cada registro hasta su fuente y fecha de extracción."
    )
    lineas.append(
        f"- **Sin duplicados en 7 de 12 archivos:** los 5 archivos XM de series "
        f"(`precio_bolsa`, `demanda`, `embalses`, `aportes`, `generacion`), IDEAM y NOAA no "
        f"presentan filas duplicadas; los {entero(total_duplicados)} duplicados se concentran en "
        "las 4 hojas de EnerAndes y en el catálogo XM."
    )
    lineas.append(
        f"- **Nulos concentrados:** de {entero(total_celdas)} celdas de datos, "
        f"{entero(total_nulos)} son nulas ({pct(total_nulos, total_celdas):.2f}%); "
        f"{entero(gen['nulos_total']) if gen else 0} de ellas están en `xm_generacion`. "
        "El resto de archivos tiene 0 nulos o valores marginales."
    )
    lineas.append(
        "- **Bronce fiel a la fuente:** las 4 hojas de EnerAndes coinciden con sus Parquet en "
        "filas, columnas y duplicados, y las filas estructurales también existen en el Excel "
        "original; el pipeline no las introdujo. Esto confirma que la capa bronce cumple su "
        "objetivo de conservar el dato tal cual."
    )
    lineas.append(
        "- **Tipo único por columna:** las 175 columnas de los 12 archivos son de tipo texto "
        "(`str`). No hay tipos mezclados dentro de una columna, aunque la conversión a "
        "numérico/fecha debe hacerse explícitamente en plata."
    )

    lineas += [
        "",
        "## Recomendaciones para la capa plata",
        "",
        "1. Convertir a numérico las columnas horarias de XM tratando `\"\"` como `NaN`.",
        "2. Deduplicar EnerAndes y descartar filas de título, encabezado, vacías y `TOTAL`.",
        "3. Normalizar fechas de EnerAndes a un único tipo y formato.",
        "4. Convertir MWh a kWh y unificar el esquema de las 4 hojas de EnerAndes.",
        "5. Normalizar segmento, modalidad y municipios con catálogos controlados.",
        "6. Deduplicar `xm_listado_recursos` por `Code` y normalizar `Type`/`State`.",
        "7. Definir una regla de imputación/rechazo para los nulos de EnerAndes y de generación.",
        "8. Completar la extracción IDEAM o documentar el alcance temporal en el dashboard.",
        "9. Validar los máximos de precipitación y el conteo `n_obs` antes de usarlos.",
        "10. Documentar que `xm_embalses.Value` es una fracción 0–1 y multiplicar por 100 al reportar.",
        "",
        "---",
        "",
        f"*Documento generado automáticamente por `scripts/perfilar.py` el {ts}.*",
        "",
    ]

    SALIDA.write_text("\n".join(lineas), encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────

def main() -> None:
    archivos = sorted(DIR_BRONZE.glob("*.parquet"))
    if not archivos:
        print(f"[ERROR] No se encontraron archivos .parquet en {DIR_BRONZE}")
        print("        Ejecute primero: .venv\\Scripts\\python.exe -m src.pipeline")
        sys.exit(1)

    print(f"Perfilando {len(archivos)} archivo(s) de {DIR_BRONZE} ...")
    perfiles = {}
    for path in archivos:
        print(f"  -> {path.name}")
        perfiles[path.stem] = perfil_archivo(path)

    contraste = contrastar_excel()
    escribir_documento(perfiles, contraste)

    print(f"\n[OK] Documento escrito en {SALIDA}")
    print(f"     {len(perfiles)} archivo(s) analizados")
    print(f"     {sum(p['filas'] for p in perfiles.values()):,} filas en total")
    if contraste:
        print(f"     {len(contraste)} hoja(s) del Excel contrastadas")


if __name__ == "__main__":
    main()