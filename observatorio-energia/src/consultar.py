"""
Ejecuta las consultas SQL de la carpeta consultas/ con DuckDB, directo sobre Parquet.

Uso:
    python -m src.consultar
"""
# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
import os       # os: funciones del sistema operativo; os.chdir() cambia de carpeta

import duckdb   # duckdb: motor SQL que lee archivos Parquet sin base de datos

from src import config       # configuracion central (para saber la carpeta raiz)
from src.utils import log    # mensajes con hora


def main() -> None:
    os.chdir(config.RAIZ)               # las rutas de los .sql son relativas a la raiz
    con = duckdb.connect()              # base de datos en memoria: no crea archivos
    for archivo in sorted((config.RAIZ / "consultas").glob("*.sql")):   # cada .sql, en orden
        log(f"Consulta: {archivo.name}")
        sql = archivo.read_text(encoding="utf-8")          # el texto de la consulta
        print(con.sql(sql).df().to_string(index=False))    # ejecutar, pasar a tabla y mostrar
        print()                                            # linea en blanco


if __name__ == "__main__":
    main()
