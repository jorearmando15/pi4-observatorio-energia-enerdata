# Bitácora – Jorge Rodríguez

**Rol:** Data Engineer / Technical Lead  

**Actividad #1**
**Puntos a cargo:** Punto 1 (Estructura inicial del repositorio y gestión del equipo), Punto 2 (Extracción de datos de XM ampliada a 2024-2026, métricas y catálogo de recursos), Punto 9 (Verificación de entregables, cumplimiento de commits/PRs del equipo y etiquetado de la entrega `ea1`)

**Actividad #2**
**Puntos a cargo:** Punto 2 (limpieza de las demás fuentes en la capa plata) y parte del Punto 3 (esquemas Pandera y pruebas pytest para las fuentes implementadas). También quedan registradas abajo mis contribuciones anteriores a la estructura del repositorio, la extracción de XM y la entrega `ea1`.

## Registro de actividades

| Qué hice | Resultado | Dificultades y aprendizajes |
|---|---|---|
| **Punto 1.** Creé la estructura inicial del proyecto EA1, inicialicé el repositorio Git y configuré la extracción inicial con Python (Commit `7a9d456`). | Arquitectura base del proyecto creada y lista para el desarrollo del pipeline. | Organización modular de carpetas y scripts para garantizar escalabilidad. |
| **Punto 1.** Creé la rama de trabajo de Data Engineer para aislar el desarrollo del pipeline (Commit `aa69e4b`). | Separación del entorno de trabajo en Git según los roles establecidos. | Gestión adecuada de ramas mediante Git Flow. |
| **Punto 1.** Resolví conflictos de integración en el `README.md` originados al fusionar cambios con la rama de Lina (Commit `b97114b`). | Sincronización exitosa del repositorio conservando los aportes de los integrantes. | Identificación y resolución manual de conflictos de merge en Git. |
| **Punto 2.** Amplié la extracción de XM al rango 2024-2026, agregando métricas de generación por planta (`Gene`), aportes hídricos (`AporEner`) y catálogo (`ListadoRecursos`) (Commit `9e96d5e` / PR #10). | Generación de 6 archivos crudos en la capa bronce (`precio_bolsa`, `demanda`, `embalses`, `aportes`, `xm_generacion`, `xm_listado_recursos`). | Manejo de endpoints con lógica de ventanas de 30 días e integración de endpoints tipo catálogo (`lists`) con estructura JSON anidada (`Items > ListEntities > Values`). |
| **Punto 9.** Revisé que cada integrante del equipo cumpliera con el mínimo de 3 commits propios y mínimo 1 Pull Request propio revisado por un compañero, asegurando que mantuvieran sus bitácoras en `docs/bitacoras/`. | Verificación del 100% de los criterios de contribución e historia en Git para todo el equipo. | Coordinación del equipo y aseguramiento de calidad y trazabilidad antes del cierre del entregable. |
| **Punto 9.** Finalicé el hito de la entrega ejecutando la creación y publicación de la etiqueta oficial mediante los comandos `git tag ea1` y `git push origin ea1`. | Tag `ea1` publicado en GitHub para marcar el estado del repositorio al momento de la entrega. | Versionamiento formal de lanzamientos y entregas mediante Git Tags. |
| **Punto 2. Capa plata XM.** Agregué `src/silver/xm.py` para limpiar precio de bolsa, demanda y generación. El programa transforma las columnas `Hour01`-`Hour24` al formato largo con una fila por fecha, hora y entidad/recurso; convierte fecha y valores a tipos adecuados y conserva identificadores/códigos. También normaliza las métricas diarias de embalses y aportes y el catálogo `ListadoRecursos`. | Se generaron en `data/silver/` 24.096 filas para precio, 24.096 para demanda y 8.408.664 para generación, además de embalses, aportes y catálogo. | Pasar de columnas por hora a filas facilita consultas horarias y agregaciones. Las celdas vacías de generación deben conservarse como nulas, no cambiarse a cero porque eso alteraría la medición. |
| **Punto 2. IDEAM, NOAA y fuente propia.** Agregué `src/silver/ideam.py` para tipar fechas, coordenadas y mediciones de precipitación y temperatura manteniendo el municipio/estación; `src/silver/noaa.py` asigna cada temporada ONI a su mes central y calcula la fase ENSO; `src/silver/trm.py` normaliza la fuente propia TRM y sus fechas de vigencia. | Se generaron tablas plata de precipitación (29.804 filas), temperatura (17.349), ONI mensual (920) y TRM (649). | La asignación al mes central evita atribuir DJF a diciembre. La fase usa los límites exactos solicitados: ONI >= 0,5 El Niño, ONI <= -0,5 La Niña y Neutral entre ambos. |
| **Parte del Punto 3. Calidad de las fuentes a mi cargo.** Definí en `src/quality/esquemas.py` esquemas Pandera para XM (horarios, embalses, aportes y recursos), IDEAM (precipitación y temperatura), NOAA y TRM. Cada limpiador valida antes de escribir en plata. Añadí pruebas con ejemplos pequeños en `tests/test_plata.py`, incluyendo XM de 24 columnas a filas horarias y umbrales de fase ONI. | Las tablas reales se procesaron y validaron mediante `python -m src.silver.pipeline`. La ejecución de `python -m pytest` terminó con 41 pruebas aprobadas. | Las reglas ejecutables permiten detectar tipos, rangos, categorías o duplicados inválidos antes de que los datos lleguen a consultas analíticas. Las pruebas unitarias mantienen los casos clave reproducibles sin llamar APIs. |

## Pull Requests propios
- **PR #10:** `feat(xm): amplia extraccion a 2024-2026 con Gene, AporEner y ListadoRecursos` (Merged a `main`).
- **PR #34:** `feat(silver): implementar limpieza de XM, IDEAM, NOAA, TRM y pipeline…` (Commit `82b59e6`).
- **PR #35:** `docs: actualizar README` (Commit `88f70fe`).

## Pull Requests que revisé e integré (Merges a main)
- **PR #13:** `feat(ideam): amplia precipitacion desde 2025 y agrega temperatura...` de `@LinaSeguro` (Commit `9c3711d`).
- **PR #14:** `feat(trm): agrega fuente propia TRM e integra al pipeline` de `@LinaSeguro` (Commit `67fe0ec`).
- **PR #15:** `test: añadir pruebas unitarias y de integración para la extracción...` de `@yusepruiz` (Commit `be3f16d`).
- **PR #32:** `feat(silver): agregar limpieza y consolidacion de ventas EnerAndes 20…` de `@LinaSeguro` (Commit `d94e9c6`).
- **PR #33:** `feat(quality): definir esquemas de Pandera para ventas y cuarentena` de `@LinaSeguro` (Commit `dd993d6`).
- **PR #36:** `test(silver/docs): agregar pruebas de reglas de transformacion y actualiza bitacora.` de `@LinaSeguro` (Commit `921ca80`).
