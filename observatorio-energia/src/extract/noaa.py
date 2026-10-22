"""
Fuente 3 - NOAA: indice ONI de El Nino (archivo de texto separado por espacios).
  Columnas: SEAS (trimestre movil, ej. JAS), YR (anio), TOTAL (temp. del mar), ANOM (anomalia)
  ANOM >= +0.5  -> El Nino      ANOM <= -0.5 -> La Nina
"""
# ---------------------------------------------------------------------------
# IMPORTS (traer codigo que ya existe)
# ---------------------------------------------------------------------------
import io               # io: libreria de Python para manejar entradas y salidas.
                        # io.StringIO hace que un texto en memoria se lea como si fuera un archivo.

import pandas as pd     # pandas: libreria de tablas. "as pd" le pone el nombre corto pd.
                        # Aqui se usa read_csv para leer el texto como tabla.

from src import config  # config.py de este proyecto: la URL del archivo de NOAA.
from src.utils import guardar_bronce, http_texto, log, ya_existe
# Funciones de utils.py de este proyecto:
#   guardar_bronce: guarda la tabla en Parquet con 3 columnas de linaje
#   http_texto:     descarga un archivo de texto de internet; reintenta si falla
#   log:            escribe un mensaje en pantalla con la hora
#   ya_existe:      dice si el archivo ya esta en bronce (para no descargarlo otra vez)

NOMBRE = "noaa_oni"     # CONSTANTE: nombre del archivo en bronce


def extraer(forzar: bool = False) -> None:
    """Descarga el archivo del indice ONI y lo guarda en bronce."""
    # forzar: bool = False -> ANOTACION DE TIPO (forzar es verdadero/falso) con valor
    # por defecto False: si no se indica nada, no se repiten descargas.
    # -> None: la funcion no devuelve nada, solo hace el trabajo.
    log("NOAA - indice ONI (El Nino)")
    if ya_existe(NOMBRE, forzar):               # si el archivo ya esta en bronce...
        return                                  # ...termina aqui, sin descargar
    texto = http_texto(config.NOAA_ONI_URL)     # descarga el .txt completo como un texto
    # read_csv lee "archivos" con columnas. Como el texto esta en memoria y no en el
    # disco, io.StringIO(texto) lo presenta como si fuera un archivo.
    # sep=r"\s+": uno o mas espacios separan las columnas
    # dtype=str: en bronce guardamos el texto tal cual, sin convertir tipos
    df = pd.read_csv(io.StringIO(texto), sep=r"\s+", dtype=str)
    guardar_bronce(df, NOMBRE, fuente="NOAA", origen=config.NOAA_ONI_URL)   # data/bronze/noaa_oni.parquet


# ---------------------------------------------------------------------------
# Este bloque solo se ejecuta cuando se corre ESTE archivo directamente:
#     python -m src.extract.noaa
# Cuando otro archivo lo importa (como pipeline.py), este bloque NO se ejecuta.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys      # sys.argv: lista con lo que se escribio en el comando
    extraer(forzar="--forzar" in sys.argv)   # True si el comando trae --forzar
