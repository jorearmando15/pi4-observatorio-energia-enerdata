# Perfilamiento de datos — Capa Bronce

> **Proyecto:** Observatorio Energía y Clima — Proyecto Integrado IV  
> **Capa analizada:** `data/bronze/` (dato tal cual llegó + columnas de linaje)  
> **Fecha de generación:** 2026-10-27 11:13 UTC-5  
> **Archivos analizados:** 12 Parquet  
> **Herramientas:** pandas 3.1.0, pyarrow 26.0.0  

## Metodología

- Se leen los 12 archivos Parquet de `data/bronze/` sin modificarlos.
- **Nulo:** se cuenta como nulo tanto `NaN` como cadena vacía o solo espacios. Esto es importante en bronce porque los valores vacíos de XM llegan como `""` y no como `NaN`.
- **Duplicado:** fila idéntica en todas las columnas del archivo, incluidas las de linaje.
- **Porcentaje de nulos:** se calcula sobre las columnas de datos (se excluyen `_fuente`, `_origen` y `_extraido_en`, que son metadatos).
- **Tipos:** se reporta el tipo físico de pandas y el tipo lógico esperado. En bronce todos los valores se conservan como texto para no alterar la fuente.
- **Contraste con la fuente:** el Excel `data/insumos/ventas_enerandes_2023_2026.xlsx` se lee con `header=None` y `dtype=str`, igual que el extractor, para comparar filas y duplicados de las 4 hojas contra los Parquet de EnerAndes.

Para regenerar este documento:

```powershell
.\\.venv\\Scripts\\python.exe scripts\\perfilar.py
```

---

## Tabla resumen

| Archivo | Fuente | Filas | Columnas | Duplicados | Celdas nulas (datos) | % nulos | Rango de fechas | Tamaño |
|---|---|---:|---:|---:|---:|---:|---|---:|
| `xm_precio_bolsa.parquet` | XM | 1,004 | 30 | 0 | 0 | 0.00% | 2024-01-01 → 2026-09-30 | 261 KB |
| `xm_demanda.parquet` | XM | 1,004 | 30 | 0 | 0 | 0.00% | 2024-01-01 → 2026-09-30 | 283 KB |
| `xm_embalses.parquet` | XM | 1,004 | 6 | 0 | 0 | 0.00% | 2024-01-01 → 2026-09-30 | 16 KB |
| `xm_aportes.parquet` | XM | 1,004 | 6 | 0 | 0 | 0.00% | 2024-01-01 → 2026-09-30 | 20 KB |
| `xm_generacion.parquet` | XM | 350,361 | 30 | 0 | 2,473,215 | 26.14% | 2024-01-01 → 2026-09-30 | 43,127 KB |
| `xm_listado_recursos.parquet` | XM | 2,493 | 14 | 2 | 0 | 0.00% | 2026-10-25 → 2026-10-25 | 74 KB |
| `ideam_precipitacion_diaria.parquet` | IDEAM | 29,804 | 11 | 0 | 0 | 0.00% | 2025-01-01 → 2026-07-24 | 102 KB |
| `noaa_oni.parquet` | NOAA | 920 | 7 | 0 | 0 | 0.00% | 1950 (DJF) → 2026 (JAS) | 10 KB |
| `enerandes_ventas_2023.parquet` | EnerAndes | 1,114 | 10 | 32 | 37 | 0.47% | 2023-01 → 2023-12 | 33 KB |
| `enerandes_ventas_2024.parquet` | EnerAndes | 1,114 | 11 | 32 | 28 | 0.31% | 2024-01 → 2024-12 | 35 KB |
| `enerandes_ventas_2025.parquet` | EnerAndes | 1,117 | 10 | 32 | 41 | 0.52% | 2025-01 → 2025-12 | 33 KB |
| `enerandes_ventas_2026.parquet` | EnerAndes | 839 | 10 | 24 | 42 | 0.72% | 2026-01 → 2026-09 | 27 KB |
| **Total** | — | **391,778** | **175** | **122** | **2,473,363** | **25.19%** | — | — |

> Las columnas incluyen las 3 de linaje (`_fuente`, `_origen`, `_extraido_en`). El porcentaje de nulos se calcula solo sobre columnas de datos.

### Contraste con el Excel de origen (EnerAndes)

| Hoja del Excel | Filas Excel | Filas Parquet | Duplicados Excel | Duplicados Parquet | Columnas | ¿Coincide? |
|---|---:|---:|---:|---:|---:|---|
| `Ventas 2023` | 1,114 | 1,114 | 32 | 32 | 7 | Sí |
| `Ventas 2024` | 1,114 | 1,114 | 32 | 32 | 8 | Sí |
| `Ventas 2025` | 1,117 | 1,117 | 32 | 32 | 7 | Sí |
| `Ventas 2026` | 839 | 839 | 24 | 24 | 7 | Sí |

Las 4 hojas coinciden en filas, columnas y duplicados con sus Parquet: la capa bronce conserva el archivo original sin agregar ni quitar registros.

---

## Perfil por archivo

### 1. `xm_precio_bolsa.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | XM |
| Filas | 1,004 |
| Columnas totales | 30 (incluye 3 de linaje) |
| Columnas de datos | 27 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 0 |
| Celdas nulas (datos) | 0 de 27,108 (0.00%) |
| Rango de fechas | 2024-01-01 → 2026-09-30 |
| Detalle temporal | 1,004 días únicos con datos |
| Tamaño en disco | 261.0 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `Date` | `str` | Fecha ISO `YYYY-MM-DD` (texto) |
| `Id` | `str` | Entidad XM (`Sistema` en estas series) |
| `code` | `str` | Código del recurso; en generación identifica la planta |
| `Hour01` … `Hour24` | `str` | 24 valores horarios numéricos almacenados como texto |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje: fuente, URL y timestamp UTC |

#### Porcentaje de nulos por columna

| Columna(s) | Nulos | % de filas |
|---|---:|---:|
| `Hour01` … `Hour24` (24 columnas) | 0 | 0.00% |
| `Date`, `Id`, `code` | 0 | 0.00% |
| `_fuente`, `_origen`, `_extraido_en` | 0 | 0.00% |

#### Filas duplicadas

No se encontraron filas duplicadas exactas (0 filas).

#### Observaciones

Serie diaria completa: 1,004 filas, 1,004 días únicos, sin nulos y sin duplicados.

---

### 2. `xm_demanda.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | XM |
| Filas | 1,004 |
| Columnas totales | 30 (incluye 3 de linaje) |
| Columnas de datos | 27 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 0 |
| Celdas nulas (datos) | 0 de 27,108 (0.00%) |
| Rango de fechas | 2024-01-01 → 2026-09-30 |
| Detalle temporal | 1,004 días únicos con datos |
| Tamaño en disco | 282.6 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `Date` | `str` | Fecha ISO `YYYY-MM-DD` (texto) |
| `Id` | `str` | Entidad XM (`Sistema` en estas series) |
| `code` | `str` | Código del recurso; en generación identifica la planta |
| `Hour01` … `Hour24` | `str` | 24 valores horarios numéricos almacenados como texto |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje: fuente, URL y timestamp UTC |

#### Porcentaje de nulos por columna

| Columna(s) | Nulos | % de filas |
|---|---:|---:|
| `Hour01` … `Hour24` (24 columnas) | 0 | 0.00% |
| `Date`, `Id`, `code` | 0 | 0.00% |
| `_fuente`, `_origen`, `_extraido_en` | 0 | 0.00% |

#### Filas duplicadas

No se encontraron filas duplicadas exactas (0 filas).

#### Observaciones

Serie diaria completa: 1,004 filas, 1,004 días únicos, sin nulos y sin duplicados.

---

### 3. `xm_embalses.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | XM |
| Filas | 1,004 |
| Columnas totales | 6 (incluye 3 de linaje) |
| Columnas de datos | 3 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 0 |
| Celdas nulas (datos) | 0 de 3,012 (0.00%) |
| Rango de fechas | 2024-01-01 → 2026-09-30 |
| Detalle temporal | 1,004 días únicos con datos |
| Tamaño en disco | 15.9 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `Date` | `str` | Fecha diaria ISO (texto) |
| `Id` | `str` | Entidad XM (`Sistema`) |
| `Value` | `str` | Valor numérico diario almacenado como texto |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna(s) | Nulos | % de filas |
|---|---:|---:|
| `Date`, `Id`, `Value` | 0 | 0.00% |
| `_fuente`, `_origen`, `_extraido_en` | 0 | 0.00% |

#### Filas duplicadas

No se encontraron filas duplicadas exactas (0 filas).

#### Observaciones

Serie diaria completa. `Value` va de 0.28564 a 0.85961 (media 0.65257); 0 valores fuera de [0, 1] y 86.06% por encima de 0.5.

---

### 4. `xm_aportes.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | XM |
| Filas | 1,004 |
| Columnas totales | 6 (incluye 3 de linaje) |
| Columnas de datos | 3 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 0 |
| Celdas nulas (datos) | 0 de 3,012 (0.00%) |
| Rango de fechas | 2024-01-01 → 2026-09-30 |
| Detalle temporal | 1,004 días únicos con datos |
| Tamaño en disco | 20.1 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `Date` | `str` | Fecha diaria ISO (texto) |
| `Id` | `str` | Entidad XM (`Sistema`) |
| `Value` | `str` | Valor numérico diario almacenado como texto |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna(s) | Nulos | % de filas |
|---|---:|---:|
| `Date`, `Id`, `Value` | 0 | 0.00% |
| `_fuente`, `_origen`, `_extraido_en` | 0 | 0.00% |

#### Filas duplicadas

No se encontraron filas duplicadas exactas (0 filas).

#### Observaciones

Serie diaria completa: 1,004 filas, 1,004 días únicos, sin nulos y sin duplicados.

---

### 5. `xm_generacion.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | XM |
| Filas | 350,361 |
| Columnas totales | 30 (incluye 3 de linaje) |
| Columnas de datos | 27 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 0 |
| Celdas nulas (datos) | 2,473,215 de 9,459,747 (26.14%) |
| Rango de fechas | 2024-01-01 → 2026-09-30 |
| Detalle temporal | 1,004 días únicos con datos |
| Tamaño en disco | 43,127.0 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `Date` | `str` | Fecha ISO `YYYY-MM-DD` (texto) |
| `Id` | `str` | Entidad XM (`Sistema` en estas series) |
| `code` | `str` | Código del recurso; en generación identifica la planta |
| `Hour01` … `Hour24` | `str` | 24 valores horarios numéricos almacenados como texto |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje: fuente, URL y timestamp UTC |

#### Porcentaje de nulos por columna

| Columna | Nulos | % de filas |
|---|---:|---:|
| `Date` | 0 | 0.00% |
| `Id` | 0 | 0.00% |
| `code` | 0 | 0.00% |
| `Hour01` | 182,025 | 51.95% |
| `Hour02` | 184,023 | 52.52% |
| `Hour03` | 184,632 | 52.70% |
| `Hour04` | 184,818 | 52.75% |
| `Hour05` | 183,644 | 52.42% |
| `Hour06` | 156,067 | 44.54% |
| `Hour07` | 52,273 | 14.92% |
| `Hour08` | 37,162 | 10.61% |
| `Hour09` | 30,427 | 8.68% |
| `Hour10` | 26,803 | 7.65% |
| `Hour11` | 24,801 | 7.08% |
| `Hour12` | 24,116 | 6.88% |
| `Hour13` | 24,048 | 6.86% |
| `Hour14` | 23,722 | 6.77% |
| `Hour15` | 24,072 | 6.87% |
| `Hour16` | 26,508 | 7.57% |
| `Hour17` | 31,434 | 8.97% |
| `Hour18` | 40,140 | 11.46% |
| `Hour19` | 141,440 | 40.37% |
| `Hour20` | 175,967 | 50.22% |
| `Hour21` | 177,096 | 50.55% |
| `Hour22` | 177,907 | 50.78% |
| `Hour23` | 179,809 | 51.32% |
| `Hour24` | 180,281 | 51.46% |

#### Filas duplicadas

No se encontraron filas duplicadas exactas (0 filas).

#### Observaciones

Cobertura recurso-día: 350,361 de 635,532 combinaciones posibles (55.13%). Faltan 285,171 combinaciones. Filas por recurso: mínimo 1, mediana 556.0, máximo 1,004.
Valores horarios: mínimo 0.01, máximo 1260993.17, negativos 0. Las cadenas vacías afectan 2,473,215 de 8,408,664 celdas horarias (29.41%).

---

### 6. `xm_listado_recursos.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | XM |
| Filas | 2,493 |
| Columnas totales | 14 (incluye 3 de linaje) |
| Columnas de datos | 11 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 2 |
| Celdas nulas (datos) | 0 de 27,423 (0.00%) |
| Rango de fechas | 2026-10-25 → 2026-10-25 |
| Detalle temporal | 1 día único con datos |
| Tamaño en disco | 74.0 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `Date` | `str` | Fecha del corte del catálogo |
| `Id` | `str` | Entidad XM (`Sistema`) |
| `Code` | `str` | Código único del recurso |
| `Name` | `str` | Nombre del recurso |
| `Type` | `str` | Tipo de generación (SOLAR, HIDRAULICA, …) |
| `Disp` | `str` | Tipo de despacho |
| `RecType` | `str` | Tipo de recurso |
| `CompanyCode` | `str` | Código de la empresa |
| `EnerSource` | `str` | Fuente primaria de energía |
| `OperStartdate` | `str` | Fecha de inicio de operación |
| `State` | `str` | Estado del recurso (OPERACION, PRUEBAS, …) |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna(s) | Nulos | % de filas |
|---|---:|---:|
| `Date`, `Id`, `Code`, `Name`, `Type`, `Disp`, `RecType`, `CompanyCode`, `EnerSource`, `OperStartdate`, `State` | 0 | 0.00% |
| `_fuente`, `_origen`, `_extraido_en` | 0 | 0.00% |

#### Filas duplicadas

Se encontraron **2 filas duplicadas** (0.08%) que corresponden a los códigos `5J8H`, `5PUN`. El catálogo tiene 2,493 filas pero solo 2,491 códigos únicos.

Filas duplicadas:

| `Date` | `Code` | `Name` | `Type` | `State` |
|---|---|---|---|---|
| 2026-10-25 | 5J8H | GRANJA SOLAR ASTURIAS | SOLAR | PRUEBAS |
| 2026-10-25 | 5J8H | GRANJA SOLAR ASTURIAS | SOLAR | PRUEBAS |

#### Observaciones

Catálogo con 2,491 códigos únicos. 235 filas (9.43%) usan variantes de mayúsculas/minúsculas en `Type` o `State` (por ejemplo `SOLAR`/`Solar`, `OPERACION`/`Operacion`).

---

### 7. `ideam_precipitacion_diaria.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | IDEAM |
| Filas | 29,804 |
| Columnas totales | 11 (incluye 3 de linaje) |
| Columnas de datos | 8 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 0 |
| Celdas nulas (datos) | 0 de 238,432 (0.00%) |
| Rango de fechas | 2025-01-01 → 2026-07-24 |
| Detalle temporal | 537 días con datos de 638 esperados (2025-01-01 → 2026-09-30); faltan 101 días |
| Tamaño en disco | 102.0 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `codigoestacion` | `str` | Código de la estación IDEAM |
| `nombreestacion` | `str` | Nombre de la estación |
| `municipio` | `str` | Municipio de Antioquia |
| `latitud` | `str` | Latitud decimal almacenada como texto |
| `longitud` | `str` | Longitud decimal almacenada como texto |
| `fecha` | `str` | Fecha ISO `YYYY-MM-DDT00:00:00.000` |
| `precipitacion_mm` | `str` | Precipitación diaria agregada (mm), texto |
| `n_obs` | `str` | Número de observaciones usadas en la agregación |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna(s) | Nulos | % de filas |
|---|---:|---:|
| `codigoestacion`, `nombreestacion`, `municipio`, `latitud`, `longitud`, `fecha`, `precipitacion_mm`, `n_obs` | 0 | 0.00% |
| `_fuente`, `_origen`, `_extraido_en` | 0 | 0.00% |

#### Filas duplicadas

No se encontraron filas duplicadas exactas (0 filas).

#### Observaciones

72 estaciones en 50 municipios. Cobertura: 537 de 638 días esperados (84.17%); faltan 101 días. Faltan 8,860 combinaciones estación-día (22.92%).
Precipitación: media 7.88 mm, p99 77.80 mm, máximo 3081.80 mm. 42.29% de los registros son cero.

---

### 8. `noaa_oni.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | NOAA |
| Filas | 920 |
| Columnas totales | 7 (incluye 3 de linaje) |
| Columnas de datos | 4 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 0 |
| Celdas nulas (datos) | 0 de 3,680 (0.00%) |
| Rango de fechas | 1950 (DJF) → 2026 (JAS) |
| Detalle temporal | 77 años; 920 temporadas trimestrales; 2026 solo tiene 8/12 |
| Tamaño en disco | 9.6 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `SEAS` | `str` | Trimestre móvil (DJF, JFM, …, NDJ) |
| `YR` | `str` | Año de la temporada |
| `TOTAL` | `str` | Temperatura media del mar (°C), texto |
| `ANOM` | `str` | Anomalía ONI (°C); ≥ +0.5 El Niño, ≤ −0.5 La Niña |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna(s) | Nulos | % de filas |
|---|---:|---:|
| `SEAS`, `YR`, `TOTAL`, `ANOM` | 0 | 0.00% |
| `_fuente`, `_origen`, `_extraido_en` | 0 | 0.00% |

#### Filas duplicadas

No se encontraron filas duplicadas exactas (0 filas).

#### Observaciones

920 temporadas de 77 años (-2.04 a 2.59 °C de anomalía). 234 temporadas cumplen El Niño (≥ 0.5) y 238 cumplen La Niña (≤ −0.5).

---

### 9. `enerandes_ventas_2023.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | EnerAndes |
| Filas | 1,114 |
| Columnas totales | 10 (incluye 3 de linaje) |
| Columnas de datos | 7 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 32 |
| Celdas nulas (datos) | 37 de 7,798 (0.47%) |
| Rango de fechas | 2023-01 → 2023-12 |
| Detalle temporal | 12 meses con datos; 1,112 de 1,112 filas con fecha válida |
| Tamaño en disco | 32.8 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `col_0` | `str` | Fecha (texto) |
| `col_1` | `str` | Municipio (texto) |
| `col_2` | `str` | Segmento (texto) |
| `col_3` | `str` | Tipo_Compra (texto) |
| `col_4` | `str` | Energia_kWh (texto) |
| `col_5` | `str` | Valor_COP (texto) |
| `col_6` | `str` | Clientes (texto) |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna | Nulos en el archivo | % del archivo | Nulos en filas de datos | % de datos |
|---|---:|---:|---:|---:|
| `col_0` | 0 | 0.00% | 0 | 0.00% |
| `col_1` | 1 | 0.09% | 0 | 0.00% |
| `col_2` | 16 | 1.44% | 15 | 1.35% |
| `col_3` | 1 | 0.09% | 0 | 0.00% |
| `col_4` | 10 | 0.90% | 9 | 0.81% |
| `col_5` | 8 | 0.72% | 7 | 0.63% |
| `col_6` | 1 | 0.09% | 0 | 0.00% |

#### Filas duplicadas

Se encontraron **32 filas duplicadas** en las 1,112 filas de datos (2.88%). Todas forman pares idénticos. La hoja `Ventas 2023` del Excel original tiene exactamente 32 duplicados sobre 1,114 filas, por lo que se heredaron de la fuente y no los introdujo el pipeline.

Ejemplo del primer par duplicado:

| `col_0` | `col_1` | `col_2` | `col_3` | `col_4` | `col_5` | `col_6` |
|---|---|---|---|---|---|---|
| 2023-04 | Apartadó | Residencial | CONTRATOS | 718835 | 610187821 | 4493 |
| 2023-04 | Apartadó | Residencial | CONTRATOS | 718835 | 610187821 | 4493 |

#### Observaciones

El archivo tiene 1,112 filas de datos y 2 filas estructurales (0 de título, 1 de encabezado, 1 fila TOTAL, 0 vacía(s)). Los nulos en filas de datos son 31 de 7,784 celdas (0.40%).
Formatos de fecha: YYYY-MM (1,112). Municipios: 29 variantes crudas para 15 nombres normalizados.
Anomalías de categoría: segmento `IND`/`RESID.` en 32 filas; compra `CONTRATOS`/`bolsa` en 52 filas.

---

### 10. `enerandes_ventas_2024.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | EnerAndes |
| Filas | 1,114 |
| Columnas totales | 11 (incluye 3 de linaje) |
| Columnas de datos | 8 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 32 |
| Celdas nulas (datos) | 28 de 8,912 (0.31%) |
| Rango de fechas | 2024-01 → 2024-12 |
| Detalle temporal | 12 meses con datos; 1,112 de 1,112 filas con fecha válida |
| Tamaño en disco | 34.6 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `col_0` | `str` | PERIODO (texto) |
| `col_1` | `str` | MUNICIPIO (texto) |
| `col_2` | `str` | SEGMENTO CLIENTE (texto) |
| `col_3` | `str` | MODALIDAD (texto) |
| `col_4` | `str` | ENERGIA (texto) |
| `col_5` | `str` | UNIDAD (texto) |
| `col_6` | `str` | VALOR ($) (texto) |
| `col_7` | `str` | NUM CLIENTES (texto) |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna | Nulos en el archivo | % del archivo | Nulos en filas de datos | % de datos |
|---|---:|---:|---:|---:|
| `col_0` | 0 | 0.00% | 0 | 0.00% |
| `col_1` | 1 | 0.09% | 0 | 0.00% |
| `col_2` | 4 | 0.36% | 3 | 0.27% |
| `col_3` | 1 | 0.09% | 0 | 0.00% |
| `col_4` | 8 | 0.72% | 7 | 0.63% |
| `col_5` | 1 | 0.09% | 0 | 0.00% |
| `col_6` | 12 | 1.08% | 11 | 0.99% |
| `col_7` | 1 | 0.09% | 0 | 0.00% |

#### Filas duplicadas

Se encontraron **32 filas duplicadas** en las 1,112 filas de datos (2.88%). Todas forman pares idénticos. La hoja `Ventas 2024` del Excel original tiene exactamente 32 duplicados sobre 1,114 filas, por lo que se heredaron de la fuente y no los introdujo el pipeline.

Ejemplo del primer par duplicado:

| `col_0` | `col_1` | `col_2` | `col_3` | `col_4` | `col_5` | `col_6` | `col_7` |
|---|---|---|---|---|---|---|---|
| oct-24 | Bello | Residencial | Contrato | 2581476 | kWh | 2512725094 | 16134 |
| oct-24 | Bello | Residencial | Contrato | 2581476 | kWh | 2512725094 | 16134 |

#### Observaciones

El archivo tiene 1,112 filas de datos y 2 filas estructurales (0 de título, 1 de encabezado, 1 fila TOTAL, 0 vacía(s)). Los nulos en filas de datos son 21 de 8,896 celdas (0.24%).
Formatos de fecha: mmm-YY (370), MM/YYYY (388), YYYY-MM (354). Municipios: 30 variantes crudas para 15 nombres normalizados.
Unidades de energía: kWh (765), MWh (347). Energía declarada: 489,552,798 kWh y 261,999 MWh.
Anomalías de categoría: segmento `IND`/`RESID.` en 40 filas; compra `CONTRATOS`/`bolsa` en 69 filas.

---

### 11. `enerandes_ventas_2025.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | EnerAndes |
| Filas | 1,117 |
| Columnas totales | 10 (incluye 3 de linaje) |
| Columnas de datos | 7 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 32 |
| Celdas nulas (datos) | 41 de 7,819 (0.52%) |
| Rango de fechas | 2025-01 → 2025-12 |
| Detalle temporal | 12 meses con datos; 1,112 de 1,112 filas con fecha válida |
| Tamaño en disco | 33.1 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `col_0` | `str` | mes (texto) |
| `col_1` | `str` | municipio (texto) |
| `col_2` | `str` | segmento (texto) |
| `col_3` | `str` | tipo compra (texto) |
| `col_4` | `str` | consumo (kWh) (texto) |
| `col_5` | `str` | facturado (texto) |
| `col_6` | `str` | usuarios (texto) |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna | Nulos en el archivo | % del archivo | Nulos en filas de datos | % de datos |
|---|---:|---:|---:|---:|
| `col_0` | 1 | 0.09% | 0 | 0.00% |
| `col_1` | 4 | 0.36% | 0 | 0.00% |
| `col_2` | 10 | 0.90% | 6 | 0.54% |
| `col_3` | 4 | 0.36% | 0 | 0.00% |
| `col_4` | 10 | 0.90% | 6 | 0.54% |
| `col_5` | 8 | 0.72% | 4 | 0.36% |
| `col_6` | 4 | 0.36% | 0 | 0.00% |

#### Filas duplicadas

Se encontraron **32 filas duplicadas** en las 1,112 filas de datos (2.88%). Todas forman pares idénticos. La hoja `Ventas 2025` del Excel original tiene exactamente 32 duplicados sobre 1,117 filas, por lo que se heredaron de la fuente y no los introdujo el pipeline.

Ejemplo del primer par duplicado:

| `col_0` | `col_1` | `col_2` | `col_3` | `col_4` | `col_5` | `col_6` |
|---|---|---|---|---|---|---|
| 04/2025 | Copacabana | Residencial | Bolsa | 137786 | 140284508 | 861 |
| 04/2025 | Copacabana | Residencial | Bolsa | 137786 | 140284508 | 861 |

#### Observaciones

El archivo tiene 1,112 filas de datos y 5 filas estructurales (2 de título, 1 de encabezado, 1 fila TOTAL, 1 vacía(s)). Los nulos en filas de datos son 16 de 7,784 celdas (0.21%).
Formatos de fecha: MM/YYYY (1,112). Municipios: 28 variantes crudas para 15 nombres normalizados.
Anomalías de categoría: segmento `IND`/`RESID.` en 50 filas; compra `CONTRATOS`/`bolsa` en 53 filas.

---

### 12. `enerandes_ventas_2026.parquet`

#### Ficha

| Métrica | Valor |
|---|---|
| Fuente | EnerAndes |
| Filas | 839 |
| Columnas totales | 10 (incluye 3 de linaje) |
| Columnas de datos | 7 |
| Tipo físico | `str` |
| Filas duplicadas exactas | 24 |
| Celdas nulas (datos) | 42 de 5,873 (0.72%) |
| Rango de fechas | 2026-01 → 2026-09 |
| Detalle temporal | 9 meses con datos; 834 de 834 filas con fecha válida |
| Tamaño en disco | 26.6 KB |

#### Tipos de datos

| Columna(s) | Tipo físico | Tipo lógico / contenido |
|---|---|---|
| `col_0` | `str` | Fecha corte (texto) |
| `col_1` | `str` | Ciudad (texto) |
| `col_2` | `str` | Tipo cliente (texto) |
| `col_3` | `str` | Compra (texto) |
| `col_4` | `str` | kWh (texto) |
| `col_5` | `str` | Total facturado COP (texto) |
| `col_6` | `str` | Clientes activos (texto) |
| `_fuente`, `_origen`, `_extraido_en` | `str` | Linaje |

#### Porcentaje de nulos por columna

| Columna | Nulos en el archivo | % del archivo | Nulos en filas de datos | % de datos |
|---|---:|---:|---:|---:|
| `col_0` | 1 | 0.12% | 0 | 0.00% |
| `col_1` | 4 | 0.48% | 0 | 0.00% |
| `col_2` | 9 | 1.07% | 5 | 0.60% |
| `col_3` | 4 | 0.48% | 0 | 0.00% |
| `col_4` | 9 | 1.07% | 5 | 0.60% |
| `col_5` | 11 | 1.31% | 7 | 0.84% |
| `col_6` | 4 | 0.48% | 0 | 0.00% |

#### Filas duplicadas

Se encontraron **24 filas duplicadas** en las 834 filas de datos (2.88%). Todas forman pares idénticos. La hoja `Ventas 2026` del Excel original tiene exactamente 24 duplicados sobre 839 filas, por lo que se heredaron de la fuente y no los introdujo el pipeline.

Ejemplo del primer par duplicado:

| `col_0` | `col_1` | `col_2` | `col_3` | `col_4` | `col_5` | `col_6` |
|---|---|---|---|---|---|---|
| 01/03/2026 | Copacabana | Industrial | Bolsa | 107983 | 111298656 | 3 |
| 01/03/2026 | Copacabana | Industrial | Bolsa | 107983 | 111298656 | 3 |

#### Observaciones

El archivo tiene 834 filas de datos y 5 filas estructurales (2 de título, 1 de encabezado, 1 fila TOTAL, 1 vacía(s)). Los nulos en filas de datos son 17 de 5,838 celdas (0.29%).
Formatos de fecha: DD/MM/YYYY (834). Municipios: 28 variantes crudas para 15 nombres normalizados.
Anomalías de categoría: segmento `IND`/`RESID.` en 31 filas; compra `CONTRATOS`/`bolsa` en 47 filas.

---

## Hallazgos de calidad

Los hallazgos se agrupan por fuente y cada uno indica su severidad. Incluyen la evidencia numérica calculada sobre los archivos y una acción sugerida para la capa plata.

1. **[Alta] Nulos encubiertos en `xm_generacion`.** `isna()` reporta 0 nulos, pero hay **2,473,215 celdas horarias vacías** de 8,408,664 (29.41%). El porcentaje por hora va de 6.77% (`Hour14`) a 52.75% (`Hour04`). En el archivo completo, las celdas nulas son 2,473,215 de 9,459,747 (26.14%). **Impacto:** promedios y sumas sesgados si no se convierten las cadenas vacías a `NaN`. **Acción:** en plata, `pd.to_numeric(..., errors='coerce')` y tratar los vacíos como dato faltante.
2. **[Alta] Cobertura incompleta en `xm_generacion`.** Hay 633 recursos y 1,004 días: 635,532 combinaciones posibles, pero solo 350,361 filas (55.13%). Faltan **285,171 combinaciones recurso-día (44.79%)**. Filas por recurso: mínimo 1, mediana 556.0, máximo 1,004; 10 recursos tienen ≤10 días, 95 tienen ≤100 y solo 25 tienen los 1,004 días. **Impacto:** no se puede asumir una serie continua por planta. **Acción:** distinguir “no despachado” de “sin dato” y documentar la regla de negocio.
3. **[Alta] Duplicados exactos en EnerAndes.** Hay **120 filas duplicadas** en 4,170 filas de datos (2.88%): `2023`: 32, `2024`: 32, `2025`: 32, `2026`: 24. Todas son pares idénticos. El Excel de origen también suma 120 duplicados en las 4 hojas, por lo que se heredaron de la fuente. **Impacto:** duplican consumo, facturación y clientes al agregar. **Acción:** deduplicar en plata con la clave de negocio (periodo + municipio + segmento + modalidad) y conservar una fila.
4. **[Media] Estructura no tabular y esquema variable en EnerAndes.** Los 4 archivos suman 14 filas estructurales (títulos, encabezado, fila TOTAL y filas vacías) mezcladas con los datos. Las hojas tienen 7, 8, 7 y 7 columnas de datos, con encabezados distintos y columnas genéricas `col_0`…`col_7`; el 100% de las 175 columnas de los 12 archivos es de tipo texto (`str`). **Impacto:** cualquier consulta directa incluye títulos y totales como si fueran registros. **Acción:** en plata, descartar filas estructurales, mapear cada hoja a un esquema único y castear tipos.
5. **[Media] Fechas heterogéneas en EnerAndes.** Se usan **4 formatos**: MM/YYYY: 1,500, YYYY-MM: 1,466, DD/MM/YYYY: 834, mmm-YY: 370. Solo 2026 tiene fecha a nivel de día (`DD/MM/YYYY`, 834 filas); 2023–2025 son mensuales. Además, 370 filas usan abreviaturas de mes en inglés (`jan-24`, `apr-24`, `aug-24`) mezcladas con `MM/YYYY`. **Impacto:** riesgo de interpretar `DD/MM` como `MM/DD` y de perder el día en los años mensuales. **Acción:** parsear con formatos explícitos y normalizar a `date`/`timestamp`.
6. **[Alta] Unidades mezcladas en EnerAndes 2024.** 347 de 1,112 filas (31.21%) reportan energía en `MWh` y 765 en `kWh`. La energía declarada suma 489,552,798 kWh en las filas kWh y 261,999 MWh en las filas MWh. **Impacto:** sumar ambas columnas sin convertir produce un error de 1,000×. **Acción:** convertir todo a kWh (MWh × 1,000) antes de agregar; 2023, 2025 y 2026 no traen columna de unidad y se asumen kWh.
7. **[Media] Categorías y nulos en campos clave de EnerAndes.** Hay **153 filas (3.67%)** con segmento `IND`/`RESID.` en lugar de `Industrial`/`Residencial`, y **221 filas (5.30%)** con `CONTRATOS`/`bolsa` en lugar de `Contrato`/`Bolsa`. Los municipios tienen 29, 30, 28 y 28 grafías crudas para solo 15 nombres normalizados (`Rio Negro`/`Rionegro (Ant)`, `envigado`, `ITAGUI`, `Sta Fe de Antioquia`). Además, en filas de datos faltan **29 segmentos, 27 energías y 11 valores facturados** (**85 celdas nulas de 30,302, 0.28%**). **Impacto:** agrupaciones fragmentadas y totales incompletos. **Acción:** catálogo de normalización y regla explícita de imputación/rechazo para nulos.
8. **[Media] Duplicados y casing en `xm_listado_recursos`.** El catálogo tiene 2,493 filas y 2,491 códigos únicos: **2 filas duplicadas** (0.08%) de los códigos `5J8H`, `5PUN`. Además, 235 filas (9.43%) usan variantes de mayúsculas/minúsculas (`SOLAR` 2,195 vs `Solar` 37; `OPERACION` 2,087 vs `Operacion` 198). **Impacto:** conteos de plantas y filtros por tipo/estado inconsistentes. **Acción:** deduplicar por `Code` y normalizar `Type`/`State`.
9. **[Media] Desalineación entre catálogo y generación de XM.** El catálogo tiene 2,491 códigos y `xm_generacion` solo 633 recursos; la intersección es 623. Por tanto, **1,868 códigos del catálogo (74.99%) no tienen ningún registro de generación** y 10 recursos de generación no aparecen en el catálogo. **Impacto:** análisis por planta incompletos y posibles recursos nuevos/fuera de catálogo. **Acción:** validar el universo de recursos y usar el catálogo como dimensión con `LEFT JOIN`, no como filtro.
10. **[Alta] Cobertura IDEAM incompleta frente a XM.** Se esperaban 638 días (2025-01-01 → 2026-09-30), pero hay **537 días (84.17%)**; faltan 101 días (15.83%). Entre el primer y último día extraído también faltan 33 días (2025-02-05, 2025-02-06, 2025-02-07, 2025-02-08, 2025-02-09, 2025-02-10, 2025-02-11, 2025-02-12, 2025-02-13, 2025-02-14, 2025-02-15, 2025-02-16, 2025-02-17, 2025-02-18, 2025-02-19, 2025-02-20, 2025-02-21, 2025-02-22, 2025-02-23, 2025-02-24, 2025-02-25, 2025-03-06, 2025-05-17, 2025-05-22, 2025-05-23, 2025-05-24, 2025-08-31, 2025-09-04, 2025-09-09, 2026-01-25, 2026-05-17, 2026-07-05, 2026-07-06). Faltan **8,860 combinaciones estación-día (22.92%)** de 38,664; 72 de 72 estaciones tienen menos de 537 días (mínimo 35). El traslape con la serie XM 2024-01-01 → 2026-09-30 es de solo 537 días (53.49% del periodo XM). **Impacto:** los análisis clima-energía quedan limitados a junio–julio de 2026. **Acción:** reextraer el periodo faltante o declarar explícitamente el alcance en el dashboard.
11. **[Media] Valores extremos y de observación sospechosos en IDEAM.** El máximo de precipitación es **3,081.80 mm** (estación `SAN CARLOS`, municipio SAN CARLOS, 2026-07-24), 391× la media (7.88 mm) y muy por encima del p99 (77.80 mm); hay 12 registros > 300 mm y 42.29% de ceros. `n_obs` tiene mediana 144, máximo 16,302 y 49 filas con más de 2,000 observaciones en un día. **Impacto:** promedios y sumas de lluvia sesgados; posible error de unidad o de agregación. **Acción:** contrastar con metadatos de la estación, revisar duplicados de frecuencia y aplicar una regla de validación/capado.
12. **[Baja] Escala ambigua en `xm_embalses`.** El campo `Value` (`PorcVoluUtilDiar`) va de 0.28564 a 0.85961 (media 0.65257), con 0 valores fuera de [0, 1] y 86.06% por encima de 0.5. **Impacto:** parece una fracción 0–1, no un porcentaje 0–100; graficarlo sin multiplicar por 100 muestra valores 100× menores. **Acción:** documentar la unidad y multiplicar por 100 en la capa de presentación si se reporta como porcentaje.

---

## Fortalezas y consideraciones

- **Series XM completas:** `xm_precio_bolsa`, `xm_demanda`, `xm_embalses` y `xm_aportes` tienen 1,004 filas cada una, 1,004 días únicos, 0 nulos y 0 duplicados en el rango 2024-01-01 → 2026-09-30. Son la base más sólida para series de tiempo.
- **NOAA consistente:** 920 temporadas de 77 años, 0 nulos y 0 duplicados; solo 2026 está parcial (8/12 temporadas), lo cual es esperable para un año en curso.
- **Linaje completo:** los 12 archivos tienen las 3 columnas de linaje (`_fuente`, `_origen`, `_extraido_en`), 175 columnas en total, lo que permite rastrear cada registro hasta su fuente y fecha de extracción.
- **Sin duplicados en 7 de 12 archivos:** los 5 archivos XM de series (`precio_bolsa`, `demanda`, `embalses`, `aportes`, `generacion`), IDEAM y NOAA no presentan filas duplicadas; los 122 duplicados se concentran en las 4 hojas de EnerAndes y en el catálogo XM.
- **Nulos concentrados:** de 9,819,924 celdas de datos, 2,473,363 son nulas (25.19%); 2,473,215 de ellas están en `xm_generacion`. El resto de archivos tiene 0 nulos o valores marginales.
- **Bronce fiel a la fuente:** las 4 hojas de EnerAndes coinciden con sus Parquet en filas, columnas y duplicados, y las filas estructurales también existen en el Excel original; el pipeline no las introdujo. Esto confirma que la capa bronce cumple su objetivo de conservar el dato tal cual.
- **Tipo único por columna:** las 175 columnas de los 12 archivos son de tipo texto (`str`). No hay tipos mezclados dentro de una columna, aunque la conversión a numérico/fecha debe hacerse explícitamente en plata.

## Recomendaciones para la capa plata

1. Convertir a numérico las columnas horarias de XM tratando `""` como `NaN`.
2. Deduplicar EnerAndes y descartar filas de título, encabezado, vacías y `TOTAL`.
3. Normalizar fechas de EnerAndes a un único tipo y formato.
4. Convertir MWh a kWh y unificar el esquema de las 4 hojas de EnerAndes.
5. Normalizar segmento, modalidad y municipios con catálogos controlados.
6. Deduplicar `xm_listado_recursos` por `Code` y normalizar `Type`/`State`.
7. Definir una regla de imputación/rechazo para los nulos de EnerAndes y de generación.
8. Completar la extracción IDEAM o documentar el alcance temporal en el dashboard.
9. Validar los máximos de precipitación y el conteo `n_obs` antes de usarlos.
10. Documentar que `xm_embalses.Value` es una fracción 0–1 y multiplicar por 100 al reportar.

---

*Documento generado automáticamente por `scripts/perfilar.py` el 2026-10-27 11:13 UTC-5.*
