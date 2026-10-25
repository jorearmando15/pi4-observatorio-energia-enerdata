# Bitácora – Yusep Ruiz

**Rol:** Data Quality Analyst  
**Puntos a cargo:** 1 (equipo y repositorio, en conjunto) y 2 (pruebas unitarias, integración de la extracción, idempotencia del pipeline y perfilamiento de datos)

## Registro de actividades

| Qué hice | Resultado | Dificultades y aprendizajes |
|---|---|---|
| **Punto 1.** Creé la rama de trabajo `rama-yusepruiz-dataqualityanalyst`, participé en la conformación del equipo y agregué mis datos al `README.md` (Commit `eb647d5`). | Registro oficial en la tabla de integrantes con usuario `@yusepruiz` y rol asignado de **Data Quality Analyst**. | Definición de flujos Git y establecimiento de estándares iniciales de calidad para el proyecto. |
| **Punto 2.** Diseñé e implementé la suite de pruebas unitarias e integración para la extracción de datos y la validación de idempotencia (`test_pipeline.py`, `test_utils.py`, `test_xm.py`), actualizando `requirements.txt` con `pytest` (Commit `27f35e7` / PR #15). | Cobertura de pruebas para la partición de fechas (`ventanas`), validación de archivos en bronce (`ya_existe`), aplanamiento de JSONs/catálogos de XM y control de ejecución con/sin `--forzar`. | Uso de `unittest.mock.patch` y `tmp_path` para simular respuestas HTTP de APIs sin realizar descargas reales ni impactar almacenamiento. |
| **Punto 2.** Revisé, aprobé y ejecuté el merge de la Pull Request #12 de Raúl Niño sobre la conservación de fuentes crudas de NOAA y EnerAndes y la generación de muestras CSV (Commit `79697e9`). | Integración exitosa a `main` de `noaa.py`, `enerandes.py`, `src/muestras.py`, 9 archivos CSV en `data/sample/` y sus pruebas automatizadas. | Verificación rigurosa de que la idempotencia y el linaje de datos (`_fuente`, `_origen`, `_extraido_en`) se mantuvieran intactos antes del merge. |
| **Punto 2.** Desarrollé el perfilamiento de la información de las fuentes de la capa bronce en la rama `rama-yusepruiz-dataqualityanalyst` (PR #16). | Creación del perfilamiento de datos (1.993 líneas añadidas), evaluando nulos, tipos de datos, cardinalidades y completitud entre las fuentes. | Manejo de estructuras de datos variadas (JSONs anidados de XM, SoQL de datos abiertos y hojas heterogéneas de Excel) para estandarizar el perfilamiento de calidad. |

## Pull Requests propios
- **PR #15:** `test: añadir pruebas unitarias y de integración para la extracción de datos y la idempotencia del pipeline` (Merged a `main`).
- **PR #16:** `Rama yusepruiz dataqualityanalyst - Creación del perfilamiento de la información`.

## Pull Requests que revisé
- **PR #12:** `feat: issue Mantener funetes NOAA y EerAndes realizada` de `@Buclex` (Revisión técnica, aprobación de calidad y merge completado).
