# Bitácora – Lina Johana Seguro

**Rol:** Analytics Engineer  
**Puntos a cargo:** 1 (equipo y repositorio, en conjunto), 3 (ampliar el IDEAM) y 5 (fuente propia - TRM)

## Registro de actividades

| Qué hice | Resultado | Dificultades y aprendizajes |
| --- | --- | --- |
| **Punto 1.** Creé la rama de trabajo `LinaSeguro`, participé en la conformación del equipo y registré mi rol en el `README.md` (Commit `c1d2c33`). | Registro oficial en `README.md` como **Analytics Engineer** (`@LinaSeguro`). | Coordinación inicial de la estructura del equipo y flujo de trabajo colaborativo en GitHub. |
| **Punto 3.** Amplié el rango de precipitación del IDEAM desde 2025 (`IDEAM_FECHA_INICIO = date(2025, 1, 1)`) e incorporé la fuente de temperatura del aire (`sbwg-7ju4`). Refactoricé `src/extract/ideam.py` con SoQL para calcular media, mínima y máxima en el servidor (Commit `d75b047`). | Generación de `ideam_precipitacion_diaria` (29.804 filas × 11 cols) e `ideam_temperatura_diaria` (17.349 filas × 13 cols) en `data/bronze/`. | El IDEAM es la fuente más lenta (solicitudes por semanas). El cálculo de agregaciones vía SoQL en el servidor evitó descargar millones de registros crudos. Se observó un retraso de publicación del IDEAM (últimos datos al 2026-07-24). |
| **Punto 5.** Seleccioné la TRM (USD/COP, dataset `32sa-8pi3` de datos.gov.co) como fuente propia. Desarrollé `src/extract/trm.py` con filtrado SoQL en servidor, agregué `TRM_URL` en `config.py` e integré el extractor en `src/pipeline.py` (Commit `fc0cf71`). | Archivo `trm_diaria.parquet` (649 filas × 7 cols) generado en `data/bronze/` con campos de linaje. | La TRM solo publica en días hábiles (649 filas para ~1.004 días). Se identificó su valor para cruzar con precios de bolsa (XM) en periodos de sequía donde aumenta la generación térmica basada en combustibles cotizados en dólares. |
| **Punto 5.** Documenté la TRM en el `README.md` (justificación del cruce económico) y desarrollé la suite de pruebas unitarias en `tests/test_trm.py` (Commit `fc0cf71`). | Documentación actualizada en `README.md` y 2/2 pruebas unitarias pasando exitosamente con red simulada (`monkeypatch`). | Diseñar pruebas con red simulada permite validar la lógica de extracción, filtrado SoQL e idempotencia sin requerir conexión a internet ni consumo de cuota de API. |

## Pull Requests propios

- **PR #13:** `feat(ideam): amplia precipitacion desde 2025 y agrega temperatura del aire` (Merged — commit `d75b047`).
- **PR #14:** `feat(trm): agrega fuente propia TRM e integra al pipeline` (Merged — commit `fc0cf71`).

## Pull Requests que revisé

- **PR #10:** `feat(xm): amplia extraccion a 2024-2026 con Gene, AporEner y ListadoRecursos` de Jorge Rodríguez (`@jorgerodriguezdev`). Revisión y Merge ejecutado (Commit `96730e6`).
- **PR #11:** `feat: Creacion de rama y modificacion README` de Raúl Niño (`@Buclex`). Revisión y Merge ejecutado (Commit `b1e1f70`).
