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
CAMPOS = "codigoestacion, nombreestacion, municipio, latitud, longitud"   # columnas que se piden
PAGINA = 50000                            # filas maximas por pedido ($limit)

# ---------------------------------------------------------------------------
# NOTA sobre "offset: int" o "-> dict" en las funciones:
# son ANOTACIONES DE TIPO. Dicen que tipo de dato se espera (int = numero entero,
# bool = verdadero/falso, dict = diccionario) y que devuelve la funcion.
# Python no las obliga: sirven para que el codigo se entienda mejor.
# ---------------------------------------------------------------------------


def consulta_soql(inicio, fin, offset: int) -> dict:
    """Arma los parametros SoQL: filtrar Antioquia y fechas, y sumar la lluvia por dia."""
    # Devuelve un diccionario {parametro: valor}. Son los mismos parametros que se
    # escribieron a mano en la URL del navegador en la Parte 4.1.
    return {
        "$select": f"{CAMPOS}, date_trunc_ymd(fechaobservacion) AS fecha, "      # el dia
                   f"sum(valorobservado) AS precipitacion_mm, count(*) AS n_obs",  # suma y conteo
        "$where": f"departamento = '{config.IDEAM_DEPARTAMENTO}' AND "           # solo Antioquia
                  f"fechaobservacion BETWEEN '{inicio}T00:00:00' AND '{fin}T23:59:59'",   # esa semana
        "$group": f"{CAMPOS}, fecha",             # un grupo por estacion y dia
        "$order": "fecha, codigoestacion",        # ordenado por fecha y estacion
        "$limit": PAGINA,                         # filas por pagina
        "$offset": offset,                        # filas que se saltan (para pedir la pagina siguiente)
    }


def extraer(forzar: bool = False) -> None:
    """Descarga la lluvia diaria por estacion, semana por semana, y la guarda en bronce."""
    # forzar: bool = False -> si no se indica nada, forzar vale False (no repetir descargas).
    log("IDEAM - datos abiertos (SoQL)")
    if ya_existe(NOMBRE, forzar):                 # si el archivo ya esta en bronce...
        return                                    # ...termina aqui, sin descargar
    filas = []                                    # aqui se juntan las filas de todas las semanas
    for inicio, fin in ventanas(config.IDEAM_FECHA_INICIO, config.FECHA_FIN, config.IDEAM_DIAS_VENTANA):
        offset = 0                                # empezar por la primera pagina
        while True:                               # paginacion: repetir hasta la ultima pagina
            # GET con los parametros SoQL; requests los pone en la URL despues de ?
            # La respuesta es una lista de filas (cada fila es un diccionario).
            lote = http_json("GET", config.IDEAM_URL, params=consulta_soql(inicio, fin, offset))
            filas.extend(lote)                    # agrega las filas de esta pagina
            if len(lote) < PAGINA:                # llegaron menos filas que el limite: era la ultima
                break                             # break: sale del while
            offset += PAGINA                      # pedir la siguiente pagina
        log(f"   semana {inicio} a {fin}: {len(lote)} filas")
    # pd.DataFrame(filas) convierte la lista de filas en una tabla de pandas,
    # y guardar_bronce() la guarda en data/bronze/<NOMBRE>.parquet
    guardar_bronce(pd.DataFrame(filas), NOMBRE, fuente="IDEAM", origen=config.IDEAM_URL)


# ---------------------------------------------------------------------------
# Este bloque solo se ejecuta cuando se corre ESTE archivo directamente:
#     python -m src.extract.ideam
# Cuando otro archivo lo importa (como pipeline.py), este bloque NO se ejecuta.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys      # sys.argv: lista con lo que se escribio en el comando
    extraer(forzar="--forzar" in sys.argv)   # True si el comando trae --forzar
