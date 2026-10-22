"""
Fuente 4 - Archivo interno de EnerAndes (Excel con una hoja por anio).
  Cada hoja tiene encabezados DISTINTOS y algunas traen un titulo encima.
  Regla de bronce: NO se modifica. Guardamos cada hoja tal cual, como texto,
  incluidas las filas de titulo y la fila TOTAL. Limpiar es trabajo de la capa plata.
"""
# ---------------------------------------------------------------------------
# IMPORTS (traer codigo que ya existe)
# ---------------------------------------------------------------------------
import pandas as pd     # pandas: libreria de tablas. "as pd" le pone el nombre corto pd.
                        # Aqui se usa read_excel para leer el Excel (usa openpyxl por debajo).

from src import config  # config.py de este proyecto: la ruta del Excel (data/insumos/...).
from src.utils import guardar_bronce, log, ya_existe
# Funciones de utils.py de este proyecto:
#   guardar_bronce: guarda la tabla en Parquet con 3 columnas de linaje
#   log:            escribe un mensaje en pantalla con la hora
#   ya_existe:      dice si el archivo ya esta en bronce (para no repetir el trabajo)


def extraer(forzar: bool = False) -> None:
    """Lee las 4 hojas del Excel de EnerAndes y guarda cada una en bronce."""
    # forzar: bool = False -> ANOTACION DE TIPO (forzar es verdadero/falso) con valor
    # por defecto False: si no se indica nada, no se repite el trabajo.
    # -> None: la funcion no devuelve nada, solo hace el trabajo.
    log("EnerAndes - Excel interno")
    archivo = config.ENERANDES_EXCEL               # ruta completa del Excel
    if not archivo.exists():                       # .exists(): el archivo esta en el disco?
        # raise detiene el programa con un error y un mensaje claro de que hacer
        raise FileNotFoundError(f"No se encontro {archivo}. Copielo en data/insumos/.")

    # sheet_name=None -> lee TODAS las hojas y devuelve un diccionario {nombre_hoja: tabla}
    # header=None     -> no interpreta ninguna fila como encabezado (tal cual)
    # dtype=str       -> todo como texto, sin convertir
    hojas = pd.read_excel(archivo, sheet_name=None, header=None, dtype=str)
    for nombre_hoja, df in hojas.items():          # .items(): recorre el diccionario, una vuelta por hoja
        # .lower() pasa a minusculas y .replace(" ", "_") cambia espacios por guion bajo:
        # "Ventas 2024" -> "enerandes_ventas_2024"
        nombre = "enerandes_" + nombre_hoja.lower().replace(" ", "_")
        if ya_existe(nombre, forzar):
            continue                               # continue: salta a la siguiente hoja
        # Como no hay encabezado, pandas nombra las columnas 0, 1, 2...
        # Parquet exige nombres de texto: se cambian por col_0, col_1, col_2...
        # df.shape[1] = numero de columnas de la hoja.
        df.columns = [f"col_{i}" for i in range(df.shape[1])]
        guardar_bronce(df, nombre, fuente="EnerAndes", origen=f"{archivo.name}#{nombre_hoja}")


# ---------------------------------------------------------------------------
# Este bloque solo se ejecuta cuando se corre ESTE archivo directamente:
#     python -m src.extract.enerandes
# Cuando otro archivo lo importa (como pipeline.py), este bloque NO se ejecuta.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys      # sys.argv: lista con lo que se escribio en el comando
    extraer(forzar="--forzar" in sys.argv)   # True si el comando trae --forzar
