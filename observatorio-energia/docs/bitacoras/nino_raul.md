# Bitácora – Raúl Niño

**Rol:** BI Analyst / Storyteller

**Puntos a cargo:** 1 (equipo y repositorio, en conjunto), 4 (mantener NOAA y EnerAndes) y 6 (reproducibilidad)

## Registro de actividades

| Qué hice | Resultado | Dificultades y aprendizajes |
| --- | --- | --- |
| **Punto 1.** Creé la rama de trabajo `RaulNino-BIAnalyst`, participé en la conformación del equipo y agregué mis datos al `README.md` (Commit `35482ef`). | Datos agregados en el `README.md` con el usuario `@Buclex` y rol asignado de **BI Analyst / Storyteller**. | Adaptación al flujo de trabajo con Git/GitHub en el repositorio `observatorio-energia` y alineación inicial de roles con el equipo. |
| **Punto 4.** Ejecuté y verifiqué los extractores de NOAA (`noaa.py`) y EnerAndes (`enerandes.py`). Añadí pruebas unitarias para validar la conservación de datos crudos y campos de linaje (`fuente`, `origen`, `fecha_extraccion`). Documenté en `README.md` y ejecuté `python -m src.pipeline` (Commit `ed36fe5`). | Archivos `noaa_oni` y `enerandes_ventas_2023` a `2026` guardados en `data/bronze/` en formato Parquet con linaje. Pasaron 2/2 pruebas unitarias (`python -m unittest discover -s tests -v`). | El Excel de EnerAndes se lee con `header=None` y `dtype=str` (`col_0`, `col_1`...), preservando títulos y totales para la capa Plata. El pipeline es idempotente (omite descargas si el archivo Parquet ya existe). |
| **Punto 6.** Implementé `src/muestras.py` para generar muestras representativas de datos de bronce en formato CSV con un máximo de 200 filas por archivo. Actualicé el `README.md` con el comando `python -m src.muestras` (Commit `214aff9`). | Generación de 9 archivos CSV en `data/sample/`, cada uno limitado a máximo 200 filas, manteniendo encabezados y campos de linaje. Pruebas de generador validadas con archivos pequeños/vacíos. | Entender la configuración de `.gitignore`: excluye `data/bronze/` para evitar subir datos pesados, pero permite `data/sample/`. Se identificó la necesidad de validar autorización antes de publicar datos sensibles de ventas de EnerAndes. |
| **Punto 6.** Probé el pipeline desde cero en un entorno virtual limpio (`.venv`, `pip install -r requirements.txt`, `python -m src.pipeline`) y actualicé la documentación del `README.md`. | Pipeline ejecuta de manera autónoma sin intervención manual ni errores. | Ajuste en estimación de tiempos de ejecución en la documentación: la inclusión de extractores más pesados (como IDEAM) incrementa el tiempo respecto a la estimación inicial. |

## Pull Requests propios

* **PR #11:** `feat: Creacion de rama y modificacion README` (Merged / Base).
* **PR #12:** `feat: issue Mantener funetes NOAA y EerAndes realizada` (Revisado por Yusep Ruiz / Open — integra commits `ed36fe5` y `214aff9` resolviendo las issues #4 y #6).

## Pull Requests que revisé

* **PR #16:** Revisión del commit inicial `8eff925` de `@yusepruiz` Creación del perfilamiento de la información.
