"""
Punto de entrada unico del pipeline de extraccion (capa BRONCE).

Uso:
    python -m src.pipeline              # descarga lo que falte
    python -m src.pipeline --forzar     # vuelve a descargar todo
"""
# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
import sys      # sys.argv: lista con lo que se escribio en el comando (ej. --forzar)
import time     # time.time(): segundos actuales, para medir cuanto tarda

import pandas as pd     # pandas: para abrir cada Parquet y contar filas y columnas

from src import config                              # configuracion central
from src.extract import enerandes, ideam, noaa, xm, trm # los 4 extractores (src/extract/*.py)
from src.utils import log                           # mensajes con hora


def resumen() -> None:
    """Muestra una tabla con los archivos de la capa bronce."""
    log("Resumen de la capa bronce:")
    # :<34 alinea a la izquierda en 34 espacios; :>10 a la derecha en 10.
    print(f"   {'archivo':<34}{'filas':>10}{'columnas':>10}{'KB':>8}")
    for archivo in sorted(config.DIR_BRONZE.glob("*.parquet")):    # cada .parquet, en orden
        df = pd.read_parquet(archivo)
        # len(df) = filas; df.shape[1] = columnas; st_size // 1024 = tamano en KB
        print(f"   {archivo.name:<34}{len(df):>10,}{df.shape[1]:>10}{archivo.stat().st_size // 1024:>8}")


def main() -> None:
    forzar = "--forzar" in sys.argv       # True si el comando trae --forzar
    inicio = time.time()                  # hora de inicio, para medir
    log(f"Pipeline bronce | rango {config.FECHA_INICIO} a {config.FECHA_FIN} | forzar={forzar}")
    for extractor in (xm, ideam, noaa, enerandes, trm):   # los 4 + 1 opcional extractores, EN ORDEN
        extractor.extraer(forzar)                    # todos tienen la funcion extraer()
    resumen()
    log(f"Listo en {time.time() - inicio:.0f} s")    # :.0f = sin decimales


# Este bloque solo se ejecuta cuando se corre el archivo directamente
# (python -m src.pipeline), no cuando otro archivo lo importa.
if __name__ == "__main__":
    main()
