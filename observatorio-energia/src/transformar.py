"""Construye las capas plata y oro a partir de los datos de bronce."""
import subprocess
import sys
from pathlib import Path

from src import config
from src.silver import pipeline as pipeline_plata


def _buscar_ejecutable_dbt() -> Path:
    nombre = "dbt.exe" if sys.platform == "win32" else "dbt"
    ejecutable = Path(sys.executable).resolve().parent / nombre
    if not ejecutable.is_file():
        raise FileNotFoundError(
            f"No se encontró dbt en {ejecutable}. "
            "Instala las dependencias con "
            "python -m pip install -r requirements.txt."
        )
    return ejecutable


def main() -> int:
    print("[transformar] Iniciando limpieza y validación de la capa plata", flush=True)
    pipeline_plata.main()
    print("[transformar] Capa plata completada", flush=True)

    ejecutable_dbt = _buscar_ejecutable_dbt()
    comando = [
        str(ejecutable_dbt),
        "build",
        "--project-dir",
        str(config.RAIZ / "dbt"),
        "--profiles-dir",
        str(config.RAIZ / "dbt"),
    ]
    print("[transformar] Construyendo y probando la capa oro con dbt", flush=True)
    resultado = subprocess.run(comando, cwd=config.RAIZ, check=False)
    if resultado.returncode != 0:
        print(
            f"[transformar] dbt build terminó con código {resultado.returncode}",
            file=sys.stderr,
            flush=True,
        )
        return resultado.returncode

    print("[transformar] Capas plata y oro completadas correctamente", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
