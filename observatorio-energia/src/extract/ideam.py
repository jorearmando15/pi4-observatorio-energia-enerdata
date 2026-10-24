"""
Fuente 2 - IDEAM en datos.gov.co (plataforma Socrata, lenguaje de consulta SoQL).
  - El dataset tiene MILLONES de observaciones (una cada pocos minutos desde 2005)
  - Por eso FILTRAMOS ($where) y AGREGAMOS ($select + $group) EN EL SERVIDOR:
    viaja un resumen diario por estacion, no millones de filas
  - Ademas paginamos con $limit / $offset por si una ventana trae muchas filas
Documentacion SoQL: https://dev.socrata.com/docs/queries/
"""
# ---------------------------------------------------------------------------
# IMPORTS (traer codigo que ya existe)
# ---------------------------------------------------------------------------
import pandas as pd     # pandas: libreria de tablas. "as pd" le pone el nombre corto pd.
                        # Aqui se usa para convertir la lista de filas en tabla (DataFrame).

from src import config  # config.py de este proyecto: URL del IDEAM, departamento, fechas, ventana.
from src.utils import guardar_bronce, http_json, log, ventanas, ya_existe
# Funciones de utils.py de este proyecto:
#   guardar_bronce: guarda la tabla en Parquet con 3 columnas de linaje
#   http_json:      le envia un pedido a una API y devuelve la respuesta; reintenta si falla
#   log:            escribe un mensaje en pantalla con la hora
#   ventanas:       parte un rango de fechas en bloques (aqui, de 7 dias)
#   ya_existe:      dice si el archivo ya esta en bronce (para no descargarlo otra vez)

# ---------------------------------------------------------------------------
# CONSTANTES: valores fijos de este extractor (en MAYUSCULAS por convencion)
# ---------------------------------------------------------------------------
NOMBRE = "ideam_precipitacion_diaria"     # nombre del archivo en bronce

NOMBRE_TEMP = "ideam_temperatura_diaria"  # EA1: temperatura del aire
CAMPOS = "codigoestacion, nombreestacion, municipio, latitud, longitud"   # columnas que se piden
PAGINA = 50000

# Agregaciones que se calculan EN EL SERVIDOR (SoQL) para cada dataset
AGREGADOS_PRECIPITACION = "sum(valorobservado) AS precipitacion_mm, count(*) AS n_obs"
AGREGADOS_TEMPERATURA = ("avg(valorobservado) AS temp_media_c, min(valorobservado) AS temp_min_c, "
                         "max(valorobservado) AS temp_max_c, count(*) AS n_obs")                            # filas maximas por pedido ($limit)

# ---------------------------------------------------------------------------
# NOTA sobre "offset: int" o "-> dict" en las funciones:
# son ANOTACIONES DE TIPO. Dicen que tipo de dato se espera (int = numero entero,
# bool = verdadero/falso, dict = diccionario) y que devuelve la funcion.
# Python no las obliga: sirven para que el codigo se entienda mejor.
# ---------------------------------------------------------------------------


def consulta_soql(inicio, fin, offset: int, agregados: str = AGREGADOS_PRECIPITACION) -> dict:
    """Arma los parametros SoQL: filtrar Antioquia y fechas, y agregar por estacion y dia."""
    return {
        "$select": f"{CAMPOS}, date_trunc_ymd(fechaobservacion) AS fecha, "
                   f"{agregados}",
        "$where": f"departamento = '{config.IDEAM_DEPARTAMENTO}' AND "
                  f"fechaobservacion BETWEEN '{inicio}T00:00:00' AND '{fin}T23:59:59'",
        "$group": f"{CAMPOS}, fecha",
        "$order": "fecha, codigoestacion",
        "$limit": PAGINA,
        "$offset": offset,
    }


def extraer_dataset(url: str, nombre: str, agregados: str, etiqueta: str, forzar: bool) -> None:
    """Descarga un dataset del IDEAM, semana por semana, agregado en el servidor."""
    if ya_existe(nombre, forzar):
        return
    filas = []
    for inicio, fin in ventanas(config.IDEAM_FECHA_INICIO, config.FECHA_FIN, config.IDEAM_DIAS_VENTANA):
        offset = 0
        total = 0
        while True:
            lote = http_json("GET", url, params=consulta_soql(inicio, fin, offset, agregados))
            filas.extend(lote)
            total += len(lote)
            if len(lote) < PAGINA:
                break
            offset += PAGINA
        log(f"   {etiqueta} semana {inicio} a {fin}: {total} filas")
    guardar_bronce(pd.DataFrame(filas), nombre, fuente="IDEAM", origen=url)


def extraer(forzar: bool = False) -> None:
    """Descarga la lluvia y la temperatura diarias por estacion y las guarda en bronce."""
    log("IDEAM - datos abiertos (SoQL)")
    extraer_dataset(config.IDEAM_URL, NOMBRE, AGREGADOS_PRECIPITACION, "precipitacion", forzar)
    extraer_dataset(config.IDEAM_TEMP_URL, NOMBRE_TEMP, AGREGADOS_TEMPERATURA, "temperatura", forzar)


# ---------------------------------------------------------------------------
# Este bloque solo se ejecuta cuando se corre ESTE archivo directamente:
#     python -m src.extract.ideam
# Cuando otro archivo lo importa (como pipeline.py), este bloque NO se ejecuta.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys      # sys.argv: lista con lo que se escribio en el comando
    extraer(forzar="--forzar" in sys.argv)   # True si el comando trae --forzar
