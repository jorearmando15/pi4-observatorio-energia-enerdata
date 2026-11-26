# Bitácora – Lina Johana Seguro

*Rol:* Analytics Engineer Act 1-2
*Rol:*  BI Analyst Act 3

*Actividad #1*
*Puntos a cargo:* 1 (equipo y repositorio, en conjunto), 3 (ampliar el IDEAM) y 5 (fuente propia - TRM)

*Actividad #2*
*Puntos a cargo:* Punto 1 (limpieza y consolidación de EnerAndes en plata) y parte del Punto 3 (esquemas Pandera y pruebas pytest de EnerAndes). También quedan registradas abajo mis contribuciones anteriores a IDEAM y TRM.

*Actividad #3*
*Puntos a cargo:* Punto 3 (ejecución y verificación de las pruebas automáticas con pytest dentro del workflow de GitHub Actions). También realicé la revisión de los resultados de ejecución y la comprobación de los artefactos generados en la capa oro y la actualización de mi bitácora. 

## Registro de actividades

| Qué hice | Resultado | Dificultades y aprendizajes |
| --- | --- | --- |
| *Punto 1.* Creé la rama de trabajo LinaSeguro, participé en la conformación del equipo y registré mi rol en el README.md (Commit c1d2c33). | Registro oficial en README.md como *Analytics Engineer* (@LinaSeguro). | Coordinación inicial de la estructura del equipo y flujo de trabajo colaborativo en GitHub. |
| *Punto 3.* Amplié el rango de precipitación del IDEAM desde 2025 (IDEAM_FECHA_INICIO = date(2025, 1, 1)) e incorporé la fuente de temperatura del aire (sbwg-7ju4). Refactoricé src/extract/ideam.py con SoQL para calcular media, mínima y máxima en el servidor (Commit d75b047). | Generación de ideam_precipitacion_diaria (29.804 filas × 11 cols) e ideam_temperatura_diaria (17.349 filas × 13 cols) en data/bronze/. | El IDEAM es la fuente más lenta (solicitudes por semanas). El cálculo de agregaciones vía SoQL en el servidor evitó descargar millones de registros crudos. Se observó un retraso de publicación del IDEAM (últimos datos al 2026-07-24). |
| *Punto 5.* Seleccioné la TRM (USD/COP, dataset 32sa-8pi3 de datos.gov.co) como fuente propia. Desarrollé src/extract/trm.py con filtrado SoQL en servidor, agregué TRM_URL en config.py e integré el extractor en src/pipeline.py (Commit fc0cf71). | Archivo trm_diaria.parquet (649 filas × 7 cols) generado en data/bronze/ con campos de linaje. | La TRM solo publica en días hábiles (649 filas para ~1.004 días). Se identificó su valor para cruzar con precios de bolsa (XM) en periodos de sequía donde aumenta la generación térmica basada en combustibles cotizados en dólares. |
| *Punto 5.* Documenté la TRM en el README.md (justificación del cruce económico) y desarrollé la suite de pruebas unitarias en tests/test_trm.py (Commit fc0cf71). | Documentación actualizada en README.md y 2/2 pruebas unitarias pasando exitosamente con red simulada (monkeypatch). | Diseñar pruebas con red simulada permite validar la lógica de extracción, filtrado SoQL e idempotencia sin requerir conexión a internet ni consumo de cuota de API. |
| *Punto 1. Capa plata EnerAndes.* Amplié src/silver/enerandes.py para leer los Parquet de bronce de las cuatro hojas (2023-2026), encontrar los encabezados aunque haya títulos o notas, mapear sus nombres de columnas y unificar los registros en una tabla común. Normalicé periodos AAAA-MM, mar-24, 03/2024 y fecha día/mes/año de 2026; estandaricé municipios/DIVIPOLA, segmentos y modalidades; convertí MWh a kWh; y excluí totales y encabezados repetidos. | data/silver/enerandes_ventas.parquet contiene 4.007 ventas limpias. El reporte de calidad queda en docs/reporte_calidad.md. | La fecha 01/03/2026 debía interpretarse como primero de marzo y no como enero. Para evitar inventar información, filas con datos no corregibles se conservan en cuarentena en vez de descartarse o completar valores por suposición. |
| *Punto 1 y parte del Punto 3.* Guardé en data/silver/enerandes_cuarentena.parquet las filas que no podían formar una venta válida, junto con año, fila de origen y motivo. En src/quality/esquemas.py definí los esquemas Pandera para ventas y cuarentena; en src/silver/enerandes.py se validan ambas tablas antes de guardarlas. Agregué en tests/test_plata.py pruebas de conversión MWh→kWh y de lectura de fechas, además de conservar las pruebas previas de EnerAndes. | Se generaron 43 filas de cuarentena y el consolidado validó contra Pandera. La suite completa reportó 41 pruebas aprobadas. | La llave de negocio permite identificar registros repetidos aunque el texto original tenga diferencias. Los tests con ejemplos pequeños verifican reglas específicas sin depender del Excel completo ni de internet. |

## Registro de actividades – Actividad 3

| Qué hice | Resultado | Dificultades y aprendizajes |
| --- | --- | --- |
| **Punto 3. Ejecución de pruebas del workflow.** Revisé y ejecuté las pruebas automatizadas de `tests/test_workflow.py` mediante `pytest`, verificando los disparadores del workflow, el orden de ejecución de las etapas, la publicación del artefacto y la configuración del archivo `.github/workflows/pipeline.yml`. | Se ejecutaron 4 pruebas específicas del workflow. Se identificaron errores relacionados con la referencia a `__file__` y con la validación de los campos de la expresión cron. | Aprendí a interpretar los errores de pytest y a diferenciar entre fallos en el código de las pruebas y problemas en la configuración del workflow. También comprendí la importancia de validar correctamente las expresiones cron. |
| **Punto 3. Verificación de la ejecución del pipeline.** Realicé una ejecución de prueba en el repositorio privado mediante GitHub Actions y revisé los registros de las diferentes etapas para comprobar que el pipeline completara el procesamiento de los datos. | Ejecución exitosa del pipeline completo en GitHub Actions, con una duración aproximada de 58 minutos y 20 segundos. Finalizaron correctamente las etapas de bronce, plata, oro, pruebas con pytest y publicación del artefacto. | La extracción de bronce fue la etapa de mayor duración, con aproximadamente 56 minutos y 59 segundos. Identifiqué la importancia de revisar los tiempos de ejecución y la necesidad de optimizar las consultas a las fuentes externas, especialmente IDEAM. |
| **Punto 3. Verificación del artefacto de la capa oro.** Descargué el artefacto `capa-oro` generado por GitHub Actions y revisé su contenido para comprobar que se hubieran exportado las tablas esperadas. | Se verificó la generación y publicación de los siete archivos Parquet: `dim_mes.parquet`, `dim_municipio.parquet`, `dim_segmento.parquet`, `fact_ventas_mensual.parquet`, `fact_mercado_mensual.parquet`, `fact_mercado_horario.parquet` y `fact_generacion_mensual.parquet`. | Aprendí a verificar los artefactos generados por GitHub Actions y a comprobar que los resultados del procesamiento estuvieran disponibles para su descarga y posterior utilización. |
| **Punto 3. Actualización y documentación de la bitácora.** Registré las actividades realizadas durante la Actividad 3, incluyendo las pruebas ejecutadas, la verificación del pipeline, los resultados obtenidos y las dificultades encontradas. | Bitácora complementada con las contribuciones correspondientes a la Actividad 3 y el rol de BI Analyst. | La documentación de las actividades permite mantener evidencia del trabajo realizado, los resultados obtenidos y los aprendizajes durante el desarrollo del proyecto. |

## Pull Requests propios

- *PR #13:* feat(ideam): amplia precipitacion desde 2025 y agrega temperatura del aire (Merged — commit d75b047).
- *PR #14:* feat(trm): agrega fuente propia TRM e integra al pipeline (Merged — commit fc0cf71).
- *PR #32:* feat(silver): agregar limpieza y consolidacion de ventas EnerAndes(Merged — commit d94e9c6
).
- *PR #33:* feat(quality): definir esquemas de Pandera para ventas y cuarentena(Merged — commit dd993d6
).
- *PR #36:* test(silver): agregar pruebas de reglas de transformacion y actualizar bitacora(Merged — commit 68cbfd7
).
- *PR #55:* docs: actualizar rol de Lina para para EA3 ( commit cf974e9).

- *PR #63: test: agregar pruebas automatizadas para validar la configuración y ejecución del workflow de GitHub Actions- #63
 (  commit  5b51f95)
 (  commit 87b8e6e).
 (  commit d730352).

 - *PR #67:* docs: actualizar bitacora de Lina Seguro.

- *PR #58:* Pull Request que no se llevó a integración, debido a que la actividad correspondiente estaba asignada a otro integrante del equipo, quien debía realizarla.

 - *PR #60:* Pull Request creado por error mediante una acción del agente. Se cerró porque no correspondía a un cambio que debiera integrarse al repositorio.







## Pull Requests que revisé

- *PR #10:* feat(xm): amplia extraccion a 2024-2026 con Gene, AporEner y ListadoRecursos de Jorge Rodríguez (@jorgerodriguezdev). Revisión y Merge ejecutado (Commit 96730e6).
- *PR #11:* feat: Creacion de rama y modificacion README de Raúl Niño (@Buclex). Revisión y Merge ejecutado (Commit b1e1f70).
- *PR #34:*feat(silver): implementar limpieza de XM, IDEAM, NOAA, TRM y pipeline.
 Revisión y Merge ejecutado (Commit 
82b59e6

).
- *PR #35:* docs: actualizar README
 Revisión y Merge ejecutado (Commit 88f70fe
).
- *PR #56:* docs: feat: pipeline automatico con GitHub Actions y exportacion de la capa oro(Commit 8b9d620
).
(Commit 81ce614
).
- *PR #61:* docs: Agregar workflow de GitHub Actions y corregir tests(Commit 013189e
).
(Commit 68a2c37
).
- *PR #64:* docs: actualizar readme y bitacora de Jorge Rodriguez(Commit 88f70fe
).
- *PR #66:* 
Feature/jorge rodriguez automatizacion.



