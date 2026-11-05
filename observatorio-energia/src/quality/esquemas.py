"""
Reglas de calidad de la capa plata, escritas con pandera.

Un ESQUEMA es la lista de condiciones que una tabla limpia DEBE cumplir:
que columnas tiene, de que tipo es cada una y que valores acepta.
Si una sola fila no cumple, pandera detiene el programa y dice cual fila
y cual regla fallo. Asi, ningun dato sucio llega a la capa oro.

Uso (desde otro archivo):
    from src.quality.esquemas import ESQUEMA_VENTAS
    ESQUEMA_VENTAS.validate(tabla, lazy=True)
"""
# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
# pandera: libreria para revisar que una tabla de pandas cumpla reglas.
# .pandas es la parte de pandera para tablas de pandas; "as pa" le da el nombre corto pa
import pandera.pandas as pa
# Column: las reglas de UNA columna (su tipo y sus condiciones)
# Check: una condicion, por ejemplo ">= 0" o "esta en esta lista"
from pandera.pandas import Check, Column

# ---------------------------------------------------------------------------
# VALORES ACEPTADOS en las columnas de categorias
# ---------------------------------------------------------------------------
# Los unicos 4 valores que puede tener la columna segmento
SEGMENTOS = ["Residencial", "Comercial", "Industrial", "No informado"]
# Los unicos 2 valores que puede tener la columna tipo_compra
TIPOS_COMPRA = ["Bolsa", "Contrato"]

# ---------------------------------------------------------------------------
# EL ESQUEMA de la tabla limpia
# ---------------------------------------------------------------------------
# pa.DataFrameSchema(...) crea el esquema. Recibe un diccionario
# {nombre de columna: Column(tipo, condicion)} y algunas reglas de toda la tabla
ESQUEMA_VENTAS = pa.DataFrameSchema(
    {
        # periodo: texto (str) que cumpla el patron AAAA-MM con un mes de 01 a 12.
        # r"^\d{4}-(0[1-9]|1[0-2])$" es una expresion regular (un patron de texto):
        #   ^ inicio, \d{4} cuatro digitos, - un guion, (0[1-9]|1[0-2]) del 01 al 12, $ fin
        # Ejemplo: '2023-04' cumple; '2023-13' y 'TOTAL' no cumplen
        "periodo": Column(str, Check.str_matches(r"^\d{4}-(0[1-9]|1[0-2])$")),
        # divipola: texto de exactamente 5 digitos (^\d{5}$). '05001' cumple; '5001' no
        "divipola": Column(str, Check.str_matches(r"^\d{5}$")),
        # municipio: texto, sin condicion extra (el nombre oficial ya viene de MUNICIPIOS)
        "municipio": Column(str),
        # segmento: texto que este en la lista SEGMENTOS (.isin = "esta en")
        "segmento": Column(str, Check.isin(SEGMENTOS)),
        # tipo_compra: texto que este en la lista TIPOS_COMPRA: solo Bolsa o Contrato
        "tipo_compra": Column(str, Check.isin(TIPOS_COMPRA)),
        # energia_kwh: numero con decimales (float) mayor o igual a 0 (ge = greater or equal)
        "energia_kwh": Column(float, Check.ge(0)),
        # valor_cop: numero >= 0; nullable=True permite celdas vacias (regla 9 de la limpieza)
        "valor_cop": Column(float, Check.ge(0), nullable=True),
        # clientes: numero entero (int) mayor o igual a 0
        "clientes": Column(int, Check.ge(0)),
    },
    # unique: no puede haber dos filas con el mismo periodo, municipio, segmento y tipo
    # de compra; si las hay, es una venta repetida
    unique=["periodo", "divipola", "segmento", "tipo_compra"],
    # strict=True: la tabla no puede traer columnas que no esten en este esquema
    strict=True,
)

ESQUEMA_CUARENTENA_VENTAS = pa.DataFrameSchema(
    {
        "periodo": Column(str, nullable=True),
        "divipola": Column(str, nullable=True),
        "municipio": Column(str, nullable=True),
        "segmento": Column(str, nullable=True),
        "tipo_compra": Column(str, nullable=True),
        "energia_kwh": Column(float, nullable=True),
        "valor_cop": Column(float, nullable=True),
        "clientes": Column(float, nullable=True),
        "_anio": Column(int, nullable=True),
        "_fila_origen": Column(float, nullable=True),
        "_motivo": Column(str, Check.str_length(min_value=1)),
    },
    unique=["_anio", "_fila_origen"],
    strict=True,
)

_FECHA = Column(pa.DateTime)
_TEXTO = Check.str_length(min_value=1)

def _esquema_xm_horario() -> pa.DataFrameSchema:
    return pa.DataFrameSchema(
        {
            "fecha": _FECHA,
            "hora": Column(int, Check.in_range(1, 24)),
            "id": Column(str, Check.str_length(min_value=1)),
            "codigo": Column(str, nullable=True),
            "valor": Column(float, Check.ge(0), nullable=True),
        },
        unique=["fecha", "hora", "id", "codigo"],
        strict=True,
    )


ESQUEMA_XM_PRECIO = _esquema_xm_horario()
ESQUEMA_XM_DEMANDA = _esquema_xm_horario()
ESQUEMA_XM_GENERACION = _esquema_xm_horario()

ESQUEMA_XM_EMBALSES = pa.DataFrameSchema(
    {
        "fecha": _FECHA,
        "id": Column(str, _TEXTO),
        "valor": Column(float, Check.in_range(0, 1)),
    },
    unique=["fecha", "id"],
    strict=True,
)

ESQUEMA_XM_APORTES = pa.DataFrameSchema(
    {
        "fecha": _FECHA,
        "id": Column(str, _TEXTO),
        "valor": Column(float, Check.ge(0)),
    },
    unique=["fecha", "id"],
    strict=True,
)

ESQUEMA_XM_RECURSOS = pa.DataFrameSchema(
    {
        "fecha_corte": _FECHA,
        "id": Column(str, _TEXTO),
        "codigo": Column(str, _TEXTO),
        "nombre": Column(str, _TEXTO),
        "tipo": Column(str, Check.isin(
            ["HIDRAULICA", "TERMICA", "COGENERADOR", "SOLAR", "EOLICA"]
        )),
        "despacho": Column(str, _TEXTO),
        "tipo_recurso": Column(str, _TEXTO),
        "codigo_empresa": Column(str, _TEXTO),
        "fuente_energia": Column(str, _TEXTO),
        "fecha_operacion": _FECHA,
        "estado": Column(str, Check.isin(["OPERACION", "PRUEBAS"])),
    },
    unique=["codigo"],
    strict=True,
)

ESQUEMA_IDEAM_PRECIPITACION = pa.DataFrameSchema(
    {
        "codigoestacion": Column(str, _TEXTO),
        "nombreestacion": Column(str, _TEXTO),
        "municipio": Column(str, _TEXTO),
        "latitud": Column(float, Check.in_range(-90, 90)),
        "longitud": Column(float, Check.in_range(-180, 180)),
        "fecha": _FECHA,
        "precipitacion_mm": Column(float, Check.ge(0)),
        "n_obs": Column(int, Check.ge(1)),
    },
    unique=["codigoestacion", "fecha"],
    strict=True,
)

ESQUEMA_IDEAM_TEMPERATURA = pa.DataFrameSchema(
    {
        "codigoestacion": Column(str, _TEXTO),
        "nombreestacion": Column(str, _TEXTO),
        "municipio": Column(str, _TEXTO),
        "latitud": Column(float, Check.in_range(-90, 90)),
        "longitud": Column(float, Check.in_range(-180, 180)),
        "fecha": _FECHA,
        "temp_media_c": Column(float, Check.in_range(-90, 60)),
        "temp_min_c": Column(float, Check.in_range(-90, 60)),
        "temp_max_c": Column(float, Check.in_range(-90, 60)),
        "n_obs": Column(int, Check.ge(1)),
    },
    checks=[
        Check(lambda df: (df["temp_min_c"] <= df["temp_media_c"]).all()),
        Check(lambda df: (df["temp_media_c"] <= df["temp_max_c"]).all()),
    ],
    unique=["codigoestacion", "fecha"],
    strict=True,
)

ESQUEMA_NOAA_ONI = pa.DataFrameSchema(
    {
        "fecha": _FECHA,
        "oni": Column(float, Check.in_range(-5, 5)),
        "fase": Column(str, Check.isin(["El Niño", "La Niña", "Neutral"])),
    },
    unique=["fecha"],
    strict=True,
)

ESQUEMA_TRM = pa.DataFrameSchema(
    {
        "fecha": _FECHA,
        "fecha_hasta": _FECHA,
        "valor_cop_por_usd": Column(float, Check.gt(0)),
        "unidad": Column(str, Check.isin(["COP"])),
    },
    unique=["fecha"],
    checks=[Check(lambda df: (df["fecha_hasta"] >= df["fecha"]).all())],
    strict=True,
)