"""
Fuente propia - TRM (Tasa de Cambio Representativa del Mercado), pesos por dolar.
  - Es el dato oficial diario USD/COP (fuente: TRM - Banco de la Republica)
  - Se publica en datos.gov.co (plataforma Socrata), igual que el IDEAM
  - Es un dataset pequeno (una fila por periodo de vigencia): se filtra por fechas
    con SoQL en el servidor y se pagina con $limit / $offset
  - Bronce: se guarda tal cual llega, sin convertir tipos
"""
# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
import pandas as pd     # pandas: convierte la lista de filas en tabla (DataFrame)

from src import config  # config.py: URL de la TRM y rango de fechas
from src.utils import guardar_bronce, http_json, log, ya_existe
# Funciones de utils.py: guardar_bronce (Parquet + linaje), http_json (con reintentos),
# log (mensaje con hora) y ya_existe (idempotencia)

# ---------------------------------------------------------------------------
# CONSTANTES
# ---------------------------------------------------------------------------
NOMBRE = "trm_diaria"            # nombre del archivo en bronce
CAMPO_FECHA = "vigenciadesde"    # columna de fecha del dataset (confirmar con ?$limit=2)
PAGINA = 50000                   # filas maximas por pedido ($limit)


def consulta_soql(inicio, fin, offset: int) -> dict:
    """Arma los parametros SoQL: filtra por fechas y ordena, en el servidor."""
    return {
        "$where": f"{CAMPO_FECHA} BETWEEN '{inicio}T00:00:00' AND '{fin}T23:59:59'",
        "$order": CAMPO_FECHA,
        "$limit": PAGINA,
        "$offset": offset,
    }


def extraer(forzar: bool = False) -> None:
    """Descarga la TRM del rango de config.FECHA_INICIO a config.FECHA_FIN y la guarda en bronce."""
    log("TRM - tasa de cambio USD/COP (datos abiertos)")
    if ya_existe(NOMBRE, forzar):                 # si el archivo ya esta en bronce, termina
        return
    filas = []
    offset = 0
    while True:                                   # paginacion: hasta la ultima pagina
        lote = http_json("GET", config.TRM_URL,
                         params=consulta_soql(config.FECHA_INICIO, config.FECHA_FIN, offset))
        filas.extend(lote)
        if len(lote) < PAGINA:                    # llegaron menos filas que el limite: era la ultima
            break
        offset += PAGINA
    log(f"   TRM {config.FECHA_INICIO} a {config.FECHA_FIN}: {len(filas)} filas")
    guardar_bronce(pd.DataFrame(filas), NOMBRE, fuente="TRM - Banco de la Republica (datos.gov.co)",
                   origen=config.TRM_URL)


# Este bloque solo se ejecuta al correr ESTE archivo directamente:
#     python -m src.extract.trm
if __name__ == "__main__":
    import sys
    extraer(forzar="--forzar" in sys.argv)
