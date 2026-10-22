"""
Utilidades comunes a todos los extractores:
  - log():            mensajes con hora
  - http_json() / http_texto(): peticiones con REINTENTOS y espera exponencial
  - ya_existe():      idempotencia (no volver a descargar lo que ya esta)
  - guardar_bronce(): guarda en Parquet agregando columnas de LINAJE
"""
# ---------------------------------------------------------------------------
# IMPORTS
# Primero las librerias que trae Python, luego las instaladas con pip,
# y al final los archivos de este mismo proyecto. Es la convencion de Python.
# ---------------------------------------------------------------------------
import time                                            # time.sleep(): esperar segundos
from datetime import datetime, timedelta, timezone     # datetime: fecha y hora actual
                                                       # timedelta: sumar dias a una fecha
                                                       # timezone: zona horaria (UTC)

import pandas as pd     # pandas: tablas (DataFrame). "as pd" = nombre corto
import requests         # requests: hacer peticiones a internet (GET, POST)

from src import config  # la configuracion central de este proyecto (src/config.py)


def log(mensaje: str) -> None:
    """Escribe un mensaje en pantalla con la hora delante: [21:30:32] mensaje."""
    # f"..." es un f-string: lo que va entre { } se reemplaza por su valor.
    # :%H:%M:%S formatea la hora como horas:minutos:segundos.
    # flush=True obliga a mostrarlo de inmediato (sin esperar).
    print(f"[{datetime.now():%H:%M:%S}] {mensaje}", flush=True)


def _con_reintentos(funcion, descripcion: str):
    """Ejecuta funcion(); si falla, espera 2, 4, 8... segundos y reintenta."""
    # El guion bajo al inicio (_con_reintentos) indica que es de uso interno.
    for intento in range(1, config.HTTP_REINTENTOS + 1):       # intento = 1, 2, 3, 4
        try:                                                   # try: intentar...
            return funcion()                                   # si funciona, termina aqui
        except requests.RequestException as error:             # ...si falla la red:
            if intento == config.HTTP_REINTENTOS:              # era el ultimo intento:
                raise RuntimeError(f"Fallo definitivo en {descripcion}: {error}") from error
            espera = 2 ** intento                              # ** = potencia: 2, 4, 8 s
            log(f"   ! intento {intento} fallo ({type(error).__name__}); reintento en {espera} s")
            time.sleep(espera)                                 # espera y vuelve al for


def http_json(metodo: str, url: str, **kwargs):
    """GET o POST que devuelve JSON, con reintentos."""
    # **kwargs recibe parametros extra con nombre (json=..., params=...)
    # y los pasa tal cual a requests.
    def llamar():                                              # funcion dentro de funcion
        r = requests.request(metodo, url, timeout=config.HTTP_TIMEOUT, **kwargs)
        r.raise_for_status()           # convierte 4xx/5xx en excepcion
        return r.json()                # convierte el texto JSON en dict o list de Python
    return _con_reintentos(llamar, f"{metodo} {url}")


def http_texto(url: str) -> str:
    """GET que devuelve texto plano, con reintentos."""
    def llamar():
        r = requests.get(url, timeout=config.HTTP_TIMEOUT)
        r.raise_for_status()
        return r.text                  # el contenido como texto
    return _con_reintentos(llamar, f"GET {url}")


def ventanas(inicio, fin, dias: int):
    """Parte el rango [inicio, fin] en bloques de 'dias' dias."""
    # Ejemplo con dias=30: (1-ene, 30-ene), (31-ene, 1-mar), ... hasta fin.
    a = inicio
    while a <= fin:
        b = min(a + timedelta(days=dias - 1), fin)     # fin del bloque, sin pasarse de fin
        yield a, b                                     # yield: entrega un bloque y sigue
        a = b + timedelta(days=1)                      # el siguiente empieza al otro dia


def ruta_bronce(nombre: str):
    """Ruta del archivo en bronce: data/bronze/<nombre>.parquet"""
    return config.DIR_BRONZE / f"{nombre}.parquet"


def ya_existe(nombre: str, forzar: bool) -> bool:
    """Idempotencia: si el archivo ya esta y no se pide forzar, no se descarga."""
    if ruta_bronce(nombre).exists() and not forzar:
        log(f"   = {nombre}.parquet ya existe; se omite (use --forzar para repetir)")
        return True
    return False


def guardar_bronce(df: pd.DataFrame, nombre: str, fuente: str, origen: str) -> None:
    """Guarda TAL CUAL llego + 3 columnas de linaje. En bronce no se modifica nada."""
    df = df.copy()                                           # copia: no tocar la tabla original
    df["_fuente"] = fuente                                   # de donde vino
    df["_origen"] = origen                                   # URL o archivo exacto
    df["_extraido_en"] = datetime.now(timezone.utc).isoformat(timespec="seconds")   # cuando (UTC)
    config.DIR_BRONZE.mkdir(parents=True, exist_ok=True)     # crea data/bronze si no existe
    df.to_parquet(ruta_bronce(nombre), index=False)          # guarda en Parquet (con pyarrow)
    log(f"   + {nombre}.parquet guardado: {len(df):,} filas x {df.shape[1]} columnas")
