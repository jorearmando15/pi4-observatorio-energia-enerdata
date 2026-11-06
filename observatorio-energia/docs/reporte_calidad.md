# Reporte de calidad de datos

Reporte generado por `python -m src.silver.pipeline` a partir de los Parquet de bronce, plata y cuarentena disponibles.

## Resumen por fuente y conjunto

### EnerAndes

| Conjunto | Filas antes (bronce) | Filas después (plata) | Filas en cuarentena |
|---|---:|---:|---:|
| `enerandes_ventas_2023` | 1114 | 1064 | 16 |
| `enerandes_ventas_2024` | 1114 | 1071 | 9 |
| `enerandes_ventas_2025` | 1117 | 1071 | 9 |
| `enerandes_ventas_2026` | 839 | 801 | 9 |

### XM

| Conjunto | Filas antes (bronce) | Filas después (plata) | Filas en cuarentena |
|---|---:|---:|---:|
| `xm_precio_bolsa` | 1004 | 24096 | 0 |
| `xm_demanda` | 1004 | 24096 | 0 |
| `xm_generacion` | 350361 | 8408664 | 0 |
| `xm_embalses` | 1004 | 1004 | 0 |
| `xm_aportes` | 1004 | 1004 | 0 |
| `xm_listado_recursos` | 2502 | 2498 | 2 |

### IDEAM

| Conjunto | Filas antes (bronce) | Filas después (plata) | Filas en cuarentena |
|---|---:|---:|---:|
| `ideam_precipitacion_diaria` | 29804 | 29804 | 0 |
| `ideam_temperatura_diaria` | 17349 | 17349 | 0 |

### NOAA

| Conjunto | Filas antes (bronce) | Filas después (plata) | Filas en cuarentena |
|---|---:|---:|---:|
| `noaa_oni` | 921 | 921 | 0 |

### TRM

| Conjunto | Filas antes (bronce) | Filas después (plata) | Filas en cuarentena |
|---|---:|---:|---:|
| `trm_diaria` | 649 | 649 | 0 |

## Reglas y métricas antes/después

Los valores de las columnas antes/después son filas que incumplen la regla. En transformaciones que amplían el grano (por ejemplo, 24 horas por registro), se cuentan las filas del grano propio de cada capa.

### EnerAndes

| Conjunto | Regla | Incumplen antes | Incumplen después | En cuarentena |
|---|---|---:|---:|---:|
| `enerandes_ventas_2023` | Filas de encabezado: Detectar encabezado por nombres | 1 | 0 | 0 |
| `enerandes_ventas_2023` | Filas de totales: Excluir totales, no ventas | 1 | 0 | 0 |
| `enerandes_ventas_2023` | Filas duplicadas: Conservar una fila por llave | 32 | 0 | 0 |
| `enerandes_ventas_2023` | Filas en cuarentena: Conservar las filas no corregibles | 16 | 16 | 16 |
| `enerandes_ventas_2024` | Filas de encabezado: Detectar encabezado por nombres | 1 | 0 | 0 |
| `enerandes_ventas_2024` | Filas de totales: Excluir totales, no ventas | 1 | 0 | 0 |
| `enerandes_ventas_2024` | Filas duplicadas: Conservar una fila por llave | 32 | 0 | 0 |
| `enerandes_ventas_2024` | Filas en cuarentena: Conservar las filas no corregibles | 9 | 9 | 9 |
| `enerandes_ventas_2025` | Filas de encabezado: Detectar encabezado por nombres | 1 | 0 | 0 |
| `enerandes_ventas_2025` | Filas de totales: Excluir totales, no ventas | 1 | 0 | 0 |
| `enerandes_ventas_2025` | Filas duplicadas: Conservar una fila por llave | 32 | 0 | 0 |
| `enerandes_ventas_2025` | Filas en cuarentena: Conservar las filas no corregibles | 9 | 9 | 9 |
| `enerandes_ventas_2026` | Filas de encabezado: Detectar encabezado por nombres | 1 | 0 | 0 |
| `enerandes_ventas_2026` | Filas de totales: Excluir totales, no ventas | 1 | 0 | 0 |
| `enerandes_ventas_2026` | Filas duplicadas: Conservar una fila por llave | 24 | 0 | 0 |
| `enerandes_ventas_2026` | Filas en cuarentena: Conservar las filas no corregibles | 9 | 9 | 9 |

### XM

| Conjunto | Regla | Incumplen antes | Incumplen después | En cuarentena |
|---|---|---:|---:|---:|
| `xm_precio_bolsa` | Fecha interpretable | 0 | 0 | 0 |
| `xm_precio_bolsa` | Identificador no vacío | 0 | 0 | 0 |
| `xm_precio_bolsa` | Valores horarios numéricos y no negativos | 0 | 0 | 0 |
| `xm_precio_bolsa` | Clave fecha/hora/identificador única | 0 | 0 | 0 |
| `xm_demanda` | Fecha interpretable | 0 | 0 | 0 |
| `xm_demanda` | Identificador no vacío | 0 | 0 | 0 |
| `xm_demanda` | Valores horarios numéricos y no negativos | 0 | 0 | 0 |
| `xm_demanda` | Clave fecha/hora/identificador única | 0 | 0 | 0 |
| `xm_generacion` | Fecha interpretable | 0 | 0 | 0 |
| `xm_generacion` | Identificador no vacío | 0 | 0 | 0 |
| `xm_generacion` | Valores horarios numéricos y no negativos | 0 | 0 | 0 |
| `xm_generacion` | Clave fecha/hora/identificador única | 0 | 0 | 0 |
| `xm_embalses` | Fecha interpretable | 0 | 0 | 0 |
| `xm_embalses` | Identificador no vacío | 0 | 0 | 0 |
| `xm_embalses` | Valor numérico entre 0 y 1 | 0 | 0 | 0 |
| `xm_embalses` | Clave fecha/identificador única | 0 | 0 | 0 |
| `xm_aportes` | Fecha interpretable | 0 | 0 | 0 |
| `xm_aportes` | Identificador no vacío | 0 | 0 | 0 |
| `xm_aportes` | Valor numérico no negativo | 0 | 0 | 0 |
| `xm_aportes` | Clave fecha/identificador única | 0 | 0 | 0 |
| `xm_listado_recursos` | Código y nombre no vacíos | 0 | 0 | 0 |
| `xm_listado_recursos` | Fechas del catálogo interpretables | 0 | 0 | 0 |
| `xm_listado_recursos` | Código de recurso único | 6 | 0 | 2 |

### IDEAM

| Conjunto | Regla | Incumplen antes | Incumplen después | En cuarentena |
|---|---|---:|---:|---:|
| `ideam_precipitacion_diaria` | Estación y municipio no vacíos | 0 | 0 | 0 |
| `ideam_precipitacion_diaria` | Fecha interpretable | 0 | 0 | 0 |
| `ideam_precipitacion_diaria` | Coordenadas dentro del rango geográfico | 0 | 0 | 0 |
| `ideam_precipitacion_diaria` | Mediciones numéricas y en rango | 0 | 0 | 0 |
| `ideam_precipitacion_diaria` | Número de observaciones entero y positivo | 0 | 0 | 0 |
| `ideam_precipitacion_diaria` | Clave estación/fecha única | 0 | 0 | 0 |
| `ideam_temperatura_diaria` | Estación y municipio no vacíos | 0 | 0 | 0 |
| `ideam_temperatura_diaria` | Fecha interpretable | 0 | 0 | 0 |
| `ideam_temperatura_diaria` | Coordenadas dentro del rango geográfico | 0 | 0 | 0 |
| `ideam_temperatura_diaria` | Mediciones numéricas y en rango | 0 | 0 | 0 |
| `ideam_temperatura_diaria` | Número de observaciones entero y positivo | 0 | 0 | 0 |
| `ideam_temperatura_diaria` | Clave estación/fecha única | 0 | 0 | 0 |
| `ideam_temperatura_diaria` | Temperatura mínima no supera la media | 0 | 0 | 0 |
| `ideam_temperatura_diaria` | Temperatura media no supera la máxima | 0 | 0 | 0 |

### NOAA

| Conjunto | Regla | Incumplen antes | Incumplen después | En cuarentena |
|---|---|---:|---:|---:|
| `noaa_oni` | Temporada ONI reconocida | 0 | 0 | 0 |
| `noaa_oni` | Año entero | 0 | 0 | 0 |
| `noaa_oni` | Anomalía ONI numérica y entre -5 y 5 | 0 | 0 | 0 |
| `noaa_oni` | Fecha mensual única | 0 | 0 | 0 |
| `noaa_oni` | Fase coherente con el umbral ONI | No aplica: la fase se deriva en plata | 0 | 0 |

### TRM

| Conjunto | Regla | Incumplen antes | Incumplen después | En cuarentena |
|---|---|---:|---:|---:|
| `trm_diaria` | Fechas de vigencia interpretables | 0 | 0 | 0 |
| `trm_diaria` | Vigencia final igual o posterior a la inicial | 0 | 0 | 0 |
| `trm_diaria` | Tasa numérica positiva | 0 | 0 | 0 |
| `trm_diaria` | Unidad COP | 0 | 0 | 0 |
| `trm_diaria` | Fecha inicial única | 0 | 0 | 0 |

## Detalle de cuarentena

| Fuente | Conjunto | Motivo | Filas |
|---|---|---|---:|
| EnerAndes | `enerandes_cuarentena` | energía vacía o no numérica | 25 |
| EnerAndes | `enerandes_cuarentena` | energía negativa | 18 |
| XM | `xm_listado_recursos_cuarentena` | codigo duplicado con descripciones distintas | 2 |

IDEAM, NOAA y TRM no generan una tabla de cuarentena: las validaciones incompatibles detienen la ejecución en vez de apartar filas.

En el catálogo XM, los duplicados exactos se eliminan durante la normalización; los códigos que conservan descripciones distintas se envían completos a cuarentena. Por eso el número bruto de filas con código repetido puede ser mayor que las filas finalmente cuarentenadas.

Las reglas de EnerAndes incluyen la detección de encabezados, totales, duplicados y filas no corregibles. Una fila puede incumplir más de una regla; por ello, los conteos de reglas no deben sumarse como un total de filas único.
