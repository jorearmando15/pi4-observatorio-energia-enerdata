"""
Fuente 1 - API REST de XM (operador del mercado electrico colombiano).
  - Metodo POST con un cuerpo JSON
  - Maximo 30 dias por consulta  ->  pedimos por VENTANAS
  - No requiere usuario ni clave
Documentacion: https://github.com/EquipoAnaliticaXM/API_XM
"""
# pandas: para armar la tabla con las filas descargadas
import pandas as pd

# config: las metricas, las fechas y la URL (src/config.py)
from src import config
# Las utilidades comunes: guardar en bronce, pedir JSON con reintentos, mensajes,
# partir el rango en ventanas y no repetir descargas
from src.utils import guardar_bronce, http_json, log, ventanas, ya_existe


def aplanar(respuesta: dict, periodo: str) -> list:
    """Convierte el JSON anidado de XM en filas planas, SIN cambiar los valores."""
    filas = []
    # Items: un elemento por dia
    for item in respuesta.get("Items", []):
        if periodo == "hourly":
            # Por hora: los valores vienen en "Values" (Hour01 ... Hour24)
            for entidad in item["HourlyEntities"]:
                # ** = copia todas las columnas de Values en la fila
                filas.append({"Date": item["Date"], "Id": entidad["Id"], **entidad["Values"]})
        elif periodo == "lists":
            # Las listas traen los atributos en "Values": una fila por elemento
            for entidad in item["ListEntities"]:
                filas.append({"Date": item["Date"], "Id": entidad["Id"], **entidad["Values"]})
        else:
            # Por dia: un solo valor, en "Value"
            for entidad in item["DailyEntities"]:
                filas.append({"Date": item["Date"], "Id": entidad["Id"], "Value": entidad["Value"]})
    return filas

def aplanar_listado(respuesta: dict) -> list:
    """Aplana la respuesta de un catalogo: Items -> ListEntities -> Values."""
    filas = []
    for item in respuesta.get("Items", []):
        for entidad in item.get("ListEntities", []):
            fila = {}
            if "Date" in item:
                fila["Date"] = item["Date"]
            if "Id" in entidad:
                fila["Id"] = entidad["Id"]
            fila.update(entidad.get("Values", {}))
            filas.append(fila)
    return filas


def extraer_metrica(metrica: str, entidad: str, periodo: str, nombre: str, desde, forzar: bool) -> None:
    """Descarga una metrica de XM desde la fecha 'desde' hasta FECHA_FIN, por ventanas de 30 dias."""
    # Si el archivo ya esta en bronce (y no se pidio --forzar), no se descarga otra vez
    if ya_existe(nombre, forzar):
        return
    # La URL segun el periodo: .../hourly o .../daily
    url = config.XM_URL.format(periodo=periodo)
    filas = []
    # desde = la fecha de inicio de ESTA metrica (FECHA_INICIO, FECHA_PRECIO o FECHA_HISTORIA)
    for inicio, fin in ventanas(desde, config.FECHA_FIN, config.XM_MAX_DIAS):
        # El cuerpo de la peticion: que metrica, de que entidad y entre que fechas
        cuerpo = {"MetricId": metrica, "Entity": entidad,
                  "StartDate": str(inicio), "EndDate": str(fin), "Filter": []}
        # POST con reintentos: si XM no responde, espera y vuelve a intentar
        respuesta = http_json("POST", url, json=cuerpo)
        # Las filas de esta ventana se agregan a la lista total
        nuevas = aplanar(respuesta, periodo)
        filas.extend(nuevas)
        log(f"   {metrica} {inicio} a {fin}: {len(nuevas)} filas")
    # Se guarda TAL CUAL llego, con las columnas de linaje
    guardar_bronce(pd.DataFrame(filas), nombre, fuente="XM", origen=f"{url} MetricId={metrica}")


def extraer_lista(metrica: str, entidad: str, nombre: str, forzar: bool) -> None:
    """Una lista de XM (por ejemplo, las plantas): una sola consulta, sin ventanas."""
    if ya_existe(nombre, forzar):
        return
    # La URL de las listas: https://servapibi.xm.com.co/lists
    url = config.XM_URL.format(periodo="lists")
    # Las listas no dependen del rango: se pide un solo dia, el ultimo
    cuerpo = {"MetricId": metrica, "Entity": entidad,
              "StartDate": str(config.FECHA_FIN), "EndDate": str(config.FECHA_FIN), "Filter": []}
    filas = aplanar(http_json("POST", url, json=cuerpo), "lists")
    log(f"   {metrica}: {len(filas)} filas")
    guardar_bronce(pd.DataFrame(filas), nombre, fuente="XM", origen=f"{url} MetricId={metrica}")


def extraer(forzar: bool = False) -> None:
    """Descarga todas las metricas y listas de XM que estan en config.py."""
    log("XM - API REST del mercado electrico")
    # Cada metrica trae su propia fecha de inicio (desde)
    for metrica, entidad, periodo, nombre, desde in config.XM_METRICAS:
        extraer_metrica(metrica, entidad, periodo, nombre, desde, forzar)
    # Y las listas (las plantas con su tipo)
    for metrica, entidad, nombre in config.XM_LISTAS:
        extraer_lista(metrica, entidad, nombre, forzar)


# Si se ejecuta este archivo solo (python -m src.extract.xm), descarga XM
if __name__ == "__main__":
    extraer()
