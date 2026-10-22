"""
Fuente 1 - API REST de XM (operador del mercado electrico colombiano).
  - Metodo POST con un cuerpo JSON
  - Maximo 30 dias por consulta  ->  pedimos por VENTANAS
  - No requiere usuario ni clave
Documentacion: https://github.com/EquipoAnaliticaXM/API_XM
"""
# ---------------------------------------------------------------------------
# IMPORTS (traer codigo que ya existe)
# ---------------------------------------------------------------------------
import pandas as pd     # pandas: libreria de tablas. "as pd" le pone el nombre corto pd.
                        # Aqui se usa para convertir la lista de filas en tabla (DataFrame).

from src import config  # config.py de este proyecto: URL de XM, fechas y lista de metricas.
from src.utils import guardar_bronce, http_json, log, ventanas, ya_existe
# Funciones de utils.py de este proyecto:
#   guardar_bronce: guarda la tabla en Parquet con 3 columnas de linaje
#   http_json:      le envia un pedido a una API y devuelve la respuesta; reintenta si falla
#   log:            escribe un mensaje en pantalla con la hora
#   ventanas:       parte un rango de fechas en bloques de 30 dias
#   ya_existe:      dice si el archivo ya esta en bronce (para no descargarlo otra vez)


# ---------------------------------------------------------------------------
# NOTA sobre "respuesta: dict" o "-> list" en las funciones:
# son ANOTACIONES DE TIPO. Dicen que tipo de dato se espera (dict = diccionario,
# str = texto, bool = verdadero/falso, list = lista) y que devuelve la funcion
# (-> list). Python no las obliga: sirven para que el codigo se entienda mejor.
# ---------------------------------------------------------------------------


def aplanar(respuesta: dict, periodo: str) -> list:
    """Convierte el JSON anidado de XM en filas planas, SIN cambiar los valores."""
    filas = []                                     # lista vacia donde se van guardando las filas
    # .get("Items", []) toma la lista "Items" de la respuesta;
    # si XM no la mando, devuelve una lista vacia [] en vez de fallar.
    for item in respuesta.get("Items", []):        # cada item es un dia
        if periodo == "hourly":                    # datos por hora (precio, demanda)
            for entidad in item["HourlyEntities"]:
                # Cada fila es un diccionario {columna: valor}.
                # ** desempaca el diccionario Values: agrega Hour01 ... Hour24 a la fila.
                filas.append({"Date": item["Date"], "Id": entidad["Id"], **entidad["Values"]})
        else:                                      # datos diarios (embalses)
            for entidad in item["DailyEntities"]:
                filas.append({"Date": item["Date"], "Id": entidad["Id"], "Value": entidad["Value"]})
    return filas                                   # entrega la lista de filas


def extraer_metrica(metrica: str, entidad: str, periodo: str, nombre: str, forzar: bool) -> None:
    """Descarga una metrica de XM en ventanas de 30 dias y la guarda en bronce."""
    if ya_existe(nombre, forzar):                  # si el archivo ya esta en bronce...
        return                                     # ...termina aqui, sin descargar
    url = config.XM_URL.format(periodo=periodo)    # reemplaza {periodo} por hourly o daily
    filas = []                                     # aqui se juntan las filas de todas las ventanas
    for inicio, fin in ventanas(config.FECHA_INICIO, config.FECHA_FIN, config.XM_MAX_DIAS):
        # El pedido, con los mismos 5 campos del comando de prueba de la Parte 3.1.
        # str(inicio) convierte la fecha en texto "2026-01-01", como la pide XM.
        cuerpo = {"MetricId": metrica, "Entity": entidad,
                  "StartDate": str(inicio), "EndDate": str(fin), "Filter": []}
        respuesta = http_json("POST", url, json=cuerpo)          # envia el pedido con POST
        nuevas = aplanar(respuesta, periodo)                     # JSON anidado -> filas
        filas.extend(nuevas)                                     # agrega las filas de esta ventana
        log(f"   {metrica} {inicio} a {fin}: {len(nuevas)} filas")   # len() = cuantas filas
    # pd.DataFrame(filas) convierte la lista de filas en una tabla de pandas,
    # y guardar_bronce() la guarda en data/bronze/<nombre>.parquet
    guardar_bronce(pd.DataFrame(filas), nombre, fuente="XM", origen=f"{url} MetricId={metrica}")


def extraer(forzar: bool = False) -> None:
    """Descarga las 3 metricas de XM definidas en config.XM_METRICAS."""
    # forzar: bool = False -> si no se indica nada, forzar vale False (no repetir descargas).
    log("XM - API REST del mercado electrico")
    # Cada elemento de XM_METRICAS es una tupla de 4 valores;
    # el for la desempaca en 4 variables a la vez.
    for metrica, entidad, periodo, nombre in config.XM_METRICAS:
        extraer_metrica(metrica, entidad, periodo, nombre, forzar)


# ---------------------------------------------------------------------------
# Este bloque solo se ejecuta cuando se corre ESTE archivo directamente:
#     python -m src.extract.xm
# Cuando otro archivo lo importa (como pipeline.py), este bloque NO se ejecuta.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys      # sys.argv: lista con lo que se escribio en el comando
    extraer(forzar="--forzar" in sys.argv)   # True si el comando trae --forzar
