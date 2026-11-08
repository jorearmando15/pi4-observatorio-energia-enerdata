# Bitácora – Raúl Niño

**Rol:** BI Analyst / Storyteller

**Puntos a cargo:** 1 (equipo y repositorio, en conjunto), 4 (mantener NOAA y EnerAndes) y 6 (reproducibilidad)

**Actividad #2:** Puntos 4 (reporte de calidad) y 7 (reproducibilidad de las capas plata y oro).

## Registro de actividades

| Qué hice | Resultado | Dificultades y aprendizajes |
| --- | --- | --- |
| **Punto 1.** Creé la rama de trabajo `RaulNino-BIAnalyst`, participé en la conformación del equipo y agregué mis datos al `README.md` (Commit `35482ef`). | Datos agregados en el `README.md` con el usuario `@Buclex` y rol asignado de **BI Analyst / Storyteller**. | Adaptación al flujo de trabajo con Git/GitHub en el repositorio `observatorio-energia` y alineación inicial de roles con el equipo. |
| **Punto 4.** Ejecuté y verifiqué los extractores de NOAA (`noaa.py`) y EnerAndes (`enerandes.py`). Añadí pruebas unitarias para validar la conservación de datos crudos y campos de linaje (`fuente`, `origen`, `fecha_extraccion`). Documenté en `README.md` y ejecuté `python -m src.pipeline` (Commit `ed36fe5`). | Archivos `noaa_oni` y `enerandes_ventas_2023` a `2026` guardados en `data/bronze/` en formato Parquet con linaje. Pasaron 2/2 pruebas unitarias (`python -m unittest discover -s tests -v`). | El Excel de EnerAndes se lee con `header=None` y `dtype=str` (`col_0`, `col_1`...), preservando títulos y totales para la capa Plata. El pipeline es idempotente (omite descargas si el archivo Parquet ya existe). |
| **Punto 6.** Implementé `src/muestras.py` para generar muestras representativas de datos de bronce en formato CSV con un máximo de 200 filas por archivo. Actualicé el `README.md` con el comando `python -m src.muestras` (Commit `214aff9`). | Generación de 9 archivos CSV en `data/sample/`, cada uno limitado a máximo 200 filas, manteniendo encabezados y campos de linaje. Pruebas de generador validadas con archivos pequeños/vacíos. | Entender la configuración de `.gitignore`: excluye `data/bronze/` para evitar subir datos pesados, pero permite `data/sample/`. Se identificó la necesidad de validar autorización antes de publicar datos sensibles de ventas de EnerAndes. |
| **Punto 6.** Probé el pipeline desde cero en un entorno virtual limpio (`.venv`, `pip install -r requirements.txt`, `python -m src.pipeline`) y actualicé la documentación del `README.md`. | Pipeline ejecuta de manera autónoma sin intervención manual ni errores. | Ajuste en estimación de tiempos de ejecución en la documentación: la inclusión de extractores más pesados (como IDEAM) incrementa el tiempo respecto a la estimación inicial. |
| **Actividad #2, punto 4.** Elaboré `docs/reporte_calidad.md` con tablas para EnerAndes, XM, IDEAM, NOAA y TRM. Documenté las reglas aplicadas y las métricas de incumplimiento antes y después; para EnerAndes registré los problemas del Excel, y para el catálogo XM documenté el conflicto del código `PRG1`, que aparecía asociado a dos nombres distintos. Las filas conflictivas se envían completas a cuarentena, sin elegir arbitrariamente una descripción ni relajar la unicidad exigida en plata (Commit `090b43b`). | El reporte contiene más de 15 reglas (68 métricas en la generación validada), conteos por fuente y motivos de cuarentena. EnerAndes conserva 43 filas en cuarentena: 25 por energía vacía/no numérica y 18 por energía negativa. XM conserva las 2 filas conflictivas de `PRG1` en `xm_listado_recursos_cuarentena.parquet`; el catálogo plata queda con 2.498 códigos únicos. | Las dos descripciones distintas para `PRG1` no permitían decidir cuál era correcta con los datos disponibles. La solución fue apartar ambas filas y registrar el motivo, preservando la trazabilidad y la regla de unicidad de la tabla plata. |
| **Actividad #2, punto 7.** Creé `src/transformar.py` para orquestar la limpieza y validación de todas las fuentes plata y, si esa etapa termina bien, ejecutar `dbt build` para construir y probar oro. Añadí pruebas del orden de ejecución y del manejo de errores, y actualicé el `README.md` con el comando único `python -m src.transformar` (Commit `561695d`). | El flujo se reconstruyó desde cero en una copia aislada con los datos de bronce: se generaron plata, cuarentenas y el reporte; dbt construyó 8 tablas marts y 6 vistas staging, con 76 de 76 resultados aprobados. La suite de Python pasó 46 pruebas y 2 subtests. | El comando reutiliza los datos de bronce y no los descarga. dbt debe ejecutarse solo después de validar plata; si una etapa falla, el proceso debe detenerse y reportar el error. La prueba desde cero se hizo en una copia temporal para no borrar ni sobrescribir resultados locales. |

## Pull Requests propios

* **PR #11:** `feat: Creacion de rama y modificacion README` (Merged / Base).
* **PR #12:** `feat: issue Mantener funetes NOAA y EerAndes realizada` (Revisado por Yusep Ruiz / Open — integra commits `ed36fe5` y `214aff9` resolviendo las issues #4 y #6).
* **PR #38:** `feat: punto 4 reporte de calidad` (Merged — commit `090b43b`).
* **PR #40:** `feat: punto 7 automatiza la construcción de las capas plata y oro` (Merged — commit `561695d`).

## Pull Requests que revisé

* **PR #16:** Revisión del commit inicial `8eff925` de `@yusepruiz` Creación del perfilamiento de la información.
