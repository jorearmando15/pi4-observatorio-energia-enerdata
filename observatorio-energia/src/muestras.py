"""Exporta las primeras 200 filas de cada Parquet de bronce a CSV."""
from pathlib import Path

import pyarrow.parquet as pq

from src import config

FILAS_MUESTRA = 200
DIR_SAMPLE = config.RAIZ / "data" / "sample"


def exportar_muestras() -> None:
    """Genera un CSV por cada Parquet, conservando sus columnas y encabezados."""
    archivos = sorted(config.DIR_BRONZE.glob("*.parquet"))
    if not archivos:
        raise FileNotFoundError(
            f"No se encontraron archivos Parquet en {config.DIR_BRONZE}. "
            "Ejecute primero python -m src.pipeline."
        )

    DIR_SAMPLE.mkdir(parents=True, exist_ok=True)

    for archivo in archivos:
        parquet = pq.ParquetFile(archivo)
        primer_lote = next(parquet.iter_batches(batch_size=FILAS_MUESTRA), None)
        if primer_lote is None:
            tabla = parquet.schema_arrow.empty_table()
        else:
            tabla = primer_lote

        destino = DIR_SAMPLE / f"{Path(archivo).stem}.csv"
        tabla.to_pandas().to_csv(destino, index=False, encoding="utf-8")
        print(f"{destino.name}: {tabla.num_rows} filas")

    print(
        "Revise el contenido y la autorizacion de publicacion de cada CSV "
        "antes de agregarlo al repositorio, especialmente los datos de EnerAndes."
    )


if __name__ == "__main__":
    exportar_muestras()
