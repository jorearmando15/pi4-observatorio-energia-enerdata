# Bitácora – Yusep Ruiz

**Rol:** Data Quality Analyst  
**Puntos a cargo:** 1 (equipo y repositorio, en conjunto) y 2 (pruebas unitarias, integración de la extracción, idempotencia del pipeline y perfilamiento de datos)  
**Actividad actual:** Punto 1 (esquema estrella en dbt) y Punto 2 (documentación del modelo dimensional, diccionario de datos y consultas de negocio)

## Registro de actividades

| Qué hice | Resultado | Dificultades y aprendizajes |
|---|---|---|
| **Punto 1.** Creé la rama de trabajo `rama-yusepruiz-dataqualityanalyst`, participé en la conformación del equipo y agregué mis datos al `README.md` (Commit `eb647d5`). | Registro oficial en la tabla de integrantes con usuario `@yusepruiz` y rol asignado de **Data Quality Analyst**. | Definición de flujos Git y establecimiento de estándares iniciales de calidad para el proyecto. |
| **Punto 2.** Diseñé e implementé la suite de pruebas unitarias e integración para la extracción de datos y la validación de idempotencia (`test_pipeline.py`, `test_utils.py`, `test_xm.py`), actualizando `requirements.txt` con `pytest` (Commit `27f35e7` / PR #15). | Cobertura de pruebas para la partición de fechas (`ventanas`), validación de archivos en bronce (`ya_existe`), aplanamiento de JSONs/catálogos de XM y control de ejecución con/sin `--forzar`. | Uso de `unittest.mock.patch` y `tmp_path` para simular respuestas HTTP de APIs sin realizar descargas reales ni impactar almacenamiento. |
| **Punto 2.** Revisé, aprobé y ejecuté el merge de la Pull Request #12 de Raúl Niño sobre la conservación de fuentes crudas de NOAA y EnerAndes y la generación de muestras CSV (Commit `79697e9`). | Integración exitosa a `main` de `noaa.py`, `enerandes.py`, `src/muestras.py`, 9 archivos CSV en `data/sample/` y sus pruebas automatizadas. | Verificación rigurosa de que la idempotencia y el linaje de datos (`_fuente`, `_origen`, `_extraido_en`) se mantuvieran intactos antes del merge. |
| **Punto 2.** Desarrollé el perfilamiento de la información de las fuentes de la capa bronce en la rama `rama-yusepruiz-dataqualityanalyst` (PR #16). | Creación del perfilamiento de datos (1.993 líneas añadidas), evaluando nulos, tipos de datos, cardinalidades y completitud entre las fuentes. | Manejo de estructuras de datos variadas (JSONs anidados de XM, SoQL de datos abiertos y hojas heterogéneas de Excel) para estandarizar el perfilamiento de calidad. |

### Actividad de modelo dimensional y capa oro

| Qué hice | Resultado | Dificultades y aprendizajes |
|---|---|---|
| **Punto 1 (2026-11-05).** Amplié `dbt/` con un esquema estrella de 3 tablas de hechos y 5 dimensiones, partiendo de los Parquet de bronce (Commits `47900ea`, `15aed3d`, `586c05c` y `0e5fa7a`). | Hechos: `fact_ventas_mensual` (4.007 filas, 2023-01 a 2026-09), `fact_mercado_horario` (24.096 filas, precio y demanda por hora) y `fact_generacion_recurso` (5.935.449 filas, generación por hora y planta). Dimensiones: `dim_fecha` (1.461 filas, 2023-01-01 a 2026-12-31, con día, mes, trimestre, día de semana y fase ENSO), `dim_mes` (45), `dim_municipio` (15), `dim_segmento` (4) y `dim_recurso` (2.501 plantas). | La capa plata solo tenía limpia la hoja 2023 de EnerAndes, así que `stg_ventas` lee directamente las 4 hojas de bronce y aplica la limpieza en SQL. En `dim_recurso` conservé 10 códigos que solo aparecen generando, marcados con `en_catalogo = false`, para no dejar llaves huérfanas en el hecho. La fase ENSO se asigna desde el ONI de NOAA y los meses sin dato quedan como `Sin dato`. |
| **Punto 1 (2026-11-05).** Documenté el grano de cada hecho en `dbt/models/marts/schema.yml` y agregué las pruebas de integridad del modelo. | Grano documentado: ventas = un mes + municipio + segmento + tipo de compra; mercado = un día + hora; generación = un día + hora + recurso. Pruebas `unique` y `not_null` en las llaves de las 5 dimensiones, `relationships` en las llaves de los 3 hechos y pruebas singulares de unicidad del grano compuesto y de cobertura 2023–2026. | No está instalado `dbt_utils`, por eso escribí las pruebas del grano compuesto como pruebas singulares en `dbt/tests/` en lugar de usar `dbt_utils.unique_combination_of_columns`. Validación final: `dbt build` terminó con `PASS=76 WARN=0 ERROR=0 SKIP=0`. |
| **Punto 2 (2026-11-06).** Creé la documentación del modelo en `docs/modelo_dimensional.md` y el diccionario de datos en `docs/diccionario_datos.md` (Commit `8a478f4`). | Diagrama Mermaid del esquema estrella con las 8 tablas de oro, explicación del grano de los 3 hechos, reglas de integridad y linaje resumido. Diccionario con una tabla por cada tabla oro (columna, tipo de dato, descripción y origen), contrastado contra los tipos reales de DuckDB: 43 columnas en total. | Verifiqué columna por columna que el diccionario coincidiera con `describe` de DuckDB, para que la documentación no quedara desactualizada frente al modelo construido. |
| **Punto 2 (2026-11-06).** Creé 4 consultas de negocio en `consultas/oro/` y publiqué sus resultados en el `README.md` (Commit `e3cef71`). | `01_impacto_enso_precio_demanda.sql` (precio promedio 661 COP/kWh en El Niño vs. 414 en Neutral y 223 en La Niña), `02_matriz_generacion_por_tipo.sql` (hidráulica 81,5% en 2025 y 72,2% en 2026 ene–sep), `03_perfil_horario_demanda_precio.sql` (demanda máxima en las horas 19–21 y precio máximo en la hora 20) y `04_ventas_por_municipio.sql` (Medellín concentra cerca del 44% de la energía vendida). | Las consultas se ejecutan en modo solo lectura sobre `data/observatorio.duckdb`. En ventas por municipio corregí el conteo de clientes: como el hecho trae un conteo mensual, se promedia entre meses en lugar de sumarlo, para no contar varias veces al mismo cliente. Validación final en solo lectura: 67/67 chequeos PASS. |

## Pull Requests propios
- **PR #39:** `Yusepruiz feature/plata oro` — modelo estrella, documentación y consultas de la capa oro (Merged a `main`, 2026-11-07).
- **PR #23:** `feat: Incorporar el pipeline de datos del observatorio energético mediante modelos dbt y esquemas de calidad de datos` (Merged a `main`, 2026-11-03).
- **PR #20:** `doc: actualizar enlace del video` (Merged a `main`, 2026-10-25).
- **PR #19:** `doc: añadir pantallazo de perfilamiento de datos` (Merged a `main`, 2026-10-25).
- **PR #16:** `Rama yusepruiz dataqualityanalyst - Creación del perfilamiento de la información` (Merged a `main`, 2026-10-24).
- **PR #15:** `test: añadir pruebas unitarias y de integración para la extracción de datos y la idempotencia del pipeline` (Merged a `main`, 2026-10-24).

## Pull Requests que revisé y aprobé
- **PR #12:** `feat: issue Mantener fuentes NOAA y EnerAndes realizada` de `@Buclex` (Aprobado, 2026-10-24; revisión técnica de calidad y merge completado).
- **PR #17:** `Implementación de fuentes, pruebas y bitácoras de equipo` de `@jorearmando15` (Aprobado, 2026-10-25).
- **PR #38:** `feat: punto 4 reporte de calidad` de `@Buclex` (Aprobado, 2026-11-06).
- **PR #40:** `feat: punto 7 automatiza la construcción de las capas plata y oro` de `@Buclex` (Aprobado, 2026-11-07).
