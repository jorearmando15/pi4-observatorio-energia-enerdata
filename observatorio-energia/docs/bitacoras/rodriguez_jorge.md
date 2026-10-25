# Bitácora – Jorge Rodríguez

**Rol:** Data Engineer / Technical Lead  
**Puntos a cargo:** Punto 1 (Estructura inicial del repositorio y gestión del equipo), Punto 2 (Extracción de datos de XM ampliada a 2024-2026, métricas y catálogo de recursos), Punto 9 (Verificación de entregables, cumplimiento de commits/PRs del equipo y etiquetado de la entrega `ea1`)

## Registro de actividades

| Qué hice | Resultado | Dificultades y aprendizajes |
|---|---|---|
| **Punto 1.** Creé la estructura inicial del proyecto EA1, inicialicé el repositorio Git y configuré la extracción inicial con Python (Commit `7a9d456`). | Arquitectura base del proyecto creada y lista para el desarrollo del pipeline. | Organización modular de carpetas y scripts para garantizar escalabilidad. |
| **Punto 1.** Creé la rama de trabajo de Data Engineer para aislar el desarrollo del pipeline (Commit `aa69e4b`). | Separación del entorno de trabajo en Git según los roles establecidos. | Gestión adecuada de ramas mediante Git Flow. |
| **Punto 1.** Resolví conflictos de integración en el `README.md` originados al fusionar cambios con la rama de Lina (Commit `b97114b`). | Sincronización exitosa del repositorio conservando los aportes de los integrantes. | Identificación y resolución manual de conflictos de merge en Git. |
| **Punto 2.** Amplié la extracción de XM al rango 2024-2026, agregando métricas de generación por planta (`Gene`), aportes hídricos (`AporEner`) y catálogo (`ListadoRecursos`) (Commit `9e96d5e` / PR #10). | Generación de 6 archivos crudos en la capa bronce (`precio_bolsa`, `demanda`, `embalses`, `aportes`, `xm_generacion`, `xm_listado_recursos`). | Manejo de endpoints con lógica de ventanas de 30 días e integración de endpoints tipo catálogo (`lists`) con estructura JSON anidada (`Items > ListEntities > Values`). |
| **Punto 9.** Revisé que cada integrante del equipo cumpliera con el mínimo de 3 commits propios y mínimo 1 Pull Request propio revisado por un compañero, asegurando que mantuvieran sus bitácoras en `docs/bitacoras/`. | Verificación del 100% de los criterios de contribución e historia en Git para todo el equipo. | Coordinación del equipo y aseguramiento de calidad y trazabilidad antes del cierre del entregable. |
| **Punto 9.** Finalicé el hito de la entrega ejecutando la creación y publicación de la etiqueta oficial mediante los comandos `git tag ea1` y `git push origin ea1`. | Tag `ea1` publicado en GitHub para marcar el estado del repositorio al momento de la entrega. | Versionamiento formal de lanzamientos y entregas mediante Git Tags. |

## Pull Requests propios
- **PR #10:** `feat(xm): amplia extraccion a 2024-2026 con Gene, AporEner y ListadoRecursos` (Merged a `main`).

## Pull Requests que revisé e integré (Merges a main)
- **PR #13:** `feat(ideam): amplia precipitacion desde 2025 y agrega temperatura...` de `@LinaSeguro` (Commit `9c3711d`).
- **PR #14:** `feat(trm): agrega fuente propia TRM e integra al pipeline` de `@LinaSeguro` (Commit `67fe0ec`).
- **PR #15:** `test: añadir pruebas unitarias y de integración para la extracción...` de `@yusepruiz` (Commit `be3f16d`).
