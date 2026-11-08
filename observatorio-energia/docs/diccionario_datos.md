# Diccionario de datos – Capa oro

> **Proyecto:** Observatorio Energía y Clima – Equipo EnerData  
> **Capa:** Oro (modelo estrella)  
> **Base de datos:** `data/observatorio.duckdb`, esquema `main`  
> **Modelos dbt:** `dbt/models/marts/`

Este diccionario describe **una tabla por cada tabla de la capa oro**. Para cada
columna se indica el tipo de dato en DuckDB, qué representa y de dónde viene
(fuente original, modelo de staging o cálculo dentro del modelo dbt).

**Tipos de dato usados:** `INTEGER`, `BIGINT`, `DOUBLE`, `VARCHAR`, `DATE` y
`BOOLEAN`. Los tipos corresponden a la base DuckDB generada por dbt.

## Resumen de tablas

| Tabla | Tipo | Grano | Filas |
|---|---|---|---:|
| `dim_fecha` | Dimensión | Un día | 1.461 |
| `dim_mes` | Dimensión | Un mes | 45 |
| `dim_municipio` | Dimensión | Un municipio | 15 |
| `dim_segmento` | Dimensión | Un segmento | 4 |
| `dim_recurso` | Dimensión | Un recurso (planta) | 2.501 |
| `fact_ventas_mensual` | Hecho | Mes + municipio + segmento + tipo de compra | 4.007 |
| `fact_mercado_horario` | Hecho | Día + hora | 24.096 |
| `fact_generacion_recurso` | Hecho | Día + hora + recurso | 5.935.449 |

## Fuentes y linaje

| Fuente original | Archivo bronce | Modelo staging | Tablas oro |
|---|---|---|---|
| EnerAndes (Excel 2023-2026) | `enerandes_ventas_2023` … `enerandes_ventas_2026` | `stg_ventas` | `dim_mes`, `dim_municipio`, `dim_segmento`, `fact_ventas_mensual` |
| XM – ListadoRecursos | `xm_listado_recursos.parquet` | `stg_listado_recursos` | `dim_recurso` |
| XM – Precio de bolsa | `xm_precio_bolsa.parquet` | `stg_xm_precio` | `fact_mercado_horario` |
| XM – Demanda real | `xm_demanda.parquet` | `stg_xm_demanda` | `fact_mercado_horario` |
| XM – Generación | `xm_generacion.parquet` | `stg_xm_generacion` | `dim_recurso`, `fact_generacion_recurso` |
| NOAA – Índice ONI | `noaa_oni.parquet` | `stg_oni_mensual` | `dim_fecha` |

---

## 1. `dim_fecha`

**Grano:** un día. **Llave:** `fecha_id`. **Filas:** 1.461 (2023-01-01 a 2026-12-31).

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `fecha_id` | `INTEGER` | Llave de la fecha en formato AAAAMMDD (por ejemplo, `20260930`). | Calculada en `dim_fecha.sql` con `strftime(fecha, '%Y%m%d')` sobre el calendario generado. |
| `fecha` | `DATE` | Fecha completa del día. | Serie diaria generada con `range('2023-01-01', '2026-12-31' + 1 día, 1 día)`. |
| `anio` | `INTEGER` | Año de la fecha. | Calculada con `strftime(fecha, '%Y')`. |
| `mes_id` | `INTEGER` | Año y mes en formato AAAAMM (por ejemplo, `202609`). Permite relacionar la fecha con el mes. | Calculada con `strftime(fecha, '%Y%m')`. |
| `mes` | `INTEGER` | Número del mes, de 1 a 12. | Calculada con `strftime(fecha, '%m')`. |
| `nombre_mes` | `VARCHAR` | Nombre del mes en español: Enero, Febrero, …, Diciembre. | `CASE` sobre `mes` en `dim_fecha.sql`. |
| `trimestre` | `INTEGER` | Trimestre del año, de 1 a 4. | Calculada como `(mes + 2) // 3`. |
| `dia` | `INTEGER` | Día del mes, de 1 a 31. | Calculada con `strftime(fecha, '%d')`. |
| `dia_semana` | `INTEGER` | Día de la semana ISO: 1 = lunes, …, 7 = domingo. | Calculada con `strftime(fecha, '%u')`. |
| `nombre_dia_semana` | `VARCHAR` | Nombre del día en español: Lunes, Martes, …, Domingo. | `CASE` sobre `dia_semana` en `dim_fecha.sql`. |
| `fase_enso` | `VARCHAR` | Fase ENSO del mes: `El Niño`, `La Niña`, `Neutral` o `Sin dato`. | `stg_oni_mensual` (NOAA `noaa_oni.parquet`), unido por año y mes. Si el mes no tiene ONI, se deja `Sin dato`. |

---

## 2. `dim_mes`

**Grano:** un mes. **Llave:** `mes_id`. **Filas:** 45 (2023-01 a 2026-09).

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `mes_id` | `INTEGER` | Llave del mes en formato AAAAMM (por ejemplo, `202304`). | `stg_ventas.mes_id`, calculado a partir del periodo de EnerAndes. |
| `periodo` | `VARCHAR` | Periodo en texto con formato `AAAA-MM` (por ejemplo, `2023-04`). | `stg_ventas.periodo`, calculado con `strftime(fecha, '%Y-%m')`. |
| `anio` | `INTEGER` | Año del periodo. | `dim_mes.sql`: `left(periodo, 4)`. |
| `mes` | `INTEGER` | Número del mes, de 1 a 12. | `dim_mes.sql`: `right(periodo, 2)`. |
| `trimestre` | `INTEGER` | Trimestre del año, de 1 a 4. | `dim_mes.sql`: `(mes + 2) // 3`. |

---

## 3. `dim_municipio`

**Grano:** un municipio. **Llave:** `municipio_id`. **Filas:** 15.

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `municipio_id` | `VARCHAR` | Código DIVIPOLA de 5 dígitos del municipio (por ejemplo, `05001` para Medellín). | `stg_ventas.municipio_id`, asignado con el catálogo de municipios de `stg_ventas.sql` a partir del nombre escrito en EnerAndes. |
| `municipio` | `VARCHAR` | Nombre oficial del municipio (por ejemplo, `Medellín`, `Itagüí`). | Catálogo de municipios de `stg_ventas.sql`; se usa el nombre oficial, no la variante del Excel. |

---

## 4. `dim_segmento`

**Grano:** un segmento. **Llave:** `segmento_id`. **Filas:** 4.

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `segmento_id` | `BIGINT` | Llave numérica del segmento, asignada en orden alfabético. | `dim_segmento.sql`: `row_number() over (order by segmento)`. |
| `segmento` | `VARCHAR` | Nombre del segmento: `Comercial`, `Industrial`, `No informado` o `Residencial`. | `stg_ventas.segmento`, normalizado desde la columna Segmento de EnerAndes. |

---

## 5. `dim_recurso`

**Grano:** un recurso (planta). **Llave:** `recurso_id`. **Filas:** 2.501.

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `recurso_id` | `VARCHAR` | Código del recurso o planta en XM (por ejemplo, `2QBW`). | `stg_listado_recursos.recurso_id` (`xm_listado_recursos.Code`) y, para códigos que solo generan, `stg_xm_generacion.recurso_id` (`xm_generacion.code`). |
| `nombre` | `VARCHAR` | Nombre de la planta. | `xm_listado_recursos.Name`; si el código no está en el catálogo, se usa el mismo código como nombre. |
| `tipo` | `VARCHAR` | Tipo de planta: `Solar`, `Hidráulica`, `Térmica`, `Eólica`, `Cogenerador` o `No informado`. | `xm_listado_recursos.Type`, normalizado (mayúsculas/minúsculas y tildes) en `stg_listado_recursos.sql`. |
| `estado` | `VARCHAR` | Estado del recurso: `Operación`, `Pruebas` o `No informado`. | `xm_listado_recursos.State`, normalizado en `stg_listado_recursos.sql`. |
| `fuente_energia` | `VARCHAR` | Fuente de energía declarada por XM (por ejemplo, `AGUA`, `GAS`). | `xm_listado_recursos.EnerSource`. |
| `fecha_operacion` | `DATE` | Fecha de inicio de operación del recurso. | `xm_listado_recursos.OperStartdate`, convertida a fecha. |
| `en_catalogo` | `BOOLEAN` | `true` si el recurso está en `ListadoRecursos`; `false` si solo aparece generando. | Calculado en `dim_recurso.sql` con el `LEFT JOIN` contra el catálogo. |

---

## 6. `fact_ventas_mensual`

**Grano:** un mes, un municipio, un segmento y un tipo de compra. **Filas:** 4.007 (2023-01 a 2026-09).

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `mes_id` | `INTEGER` | Llave foránea a `dim_mes`: mes de la venta en formato AAAAMM. | `stg_ventas.mes_id`, calculado desde la fecha de EnerAndes. |
| `fecha_id` | `INTEGER` | Llave foránea a `dim_fecha`: día 1 del mes en formato AAAAMMDD. | `stg_ventas.fecha_id`, calculado con `date_trunc('month', fecha)`. |
| `municipio_id` | `VARCHAR` | Llave foránea a `dim_municipio`: código DIVIPOLA. | `stg_ventas.municipio_id`, asignado con el catálogo de municipios. |
| `segmento_id` | `BIGINT` | Llave foránea a `dim_segmento`. | `dim_segmento.segmento_id`, unido por el nombre del segmento. |
| `tipo_compra` | `VARCHAR` | Tipo de compra: `Bolsa` o `Contrato`. | `stg_ventas.tipo_compra`, normalizado desde la columna Tipo_Compra de EnerAndes. |
| `energia_kwh` | `DOUBLE` | Energía vendida en kWh. Es una medida aditiva. | `stg_ventas.energia_kwh`, desde Energia_kWh de EnerAndes. En 2024 las filas en MWh se multiplican por 1.000. |
| `valor_cop` | `DOUBLE` | Valor facturado en pesos colombianos (COP). Es una medida aditiva. | `stg_ventas.valor_cop`, desde Valor_COP de EnerAndes. |
| `clientes` | `INTEGER` | Número de clientes del mes para esa combinación. Es un conteo mensual, no una medida acumulable entre meses. | `stg_ventas.clientes`, desde Clientes de EnerAndes. |

---

## 7. `fact_mercado_horario`

**Grano:** un día y una hora. **Filas:** 24.096 (1.004 días × 24 horas).

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `fecha_id` | `INTEGER` | Llave foránea a `dim_fecha`: fecha del dato en formato AAAAMMDD. | `stg_xm_precio.fecha_id` y `stg_xm_demanda.fecha_id`, calculados desde `Date` de XM. |
| `hora` | `INTEGER` | Hora del día, de 1 a 24 (1 = 00:00-01:00; 24 = 23:00-24:00). | `UNPIVOT` de las columnas `Hour01` … `Hour24` de XM. |
| `precio_cop_kwh` | `DOUBLE` | Precio de bolsa nacional en COP/kWh. No es aditivo: para agregarlo se promedia. | `stg_xm_precio.precio_cop_kwh`, desde `PrecBolsNaci` de XM. |
| `demanda_kwh` | `DOUBLE` | Demanda real del sistema en kWh. Es aditiva en el tiempo. | `stg_xm_demanda.demanda_kwh`, desde `DemaReal` de XM. |

---

## 8. `fact_generacion_recurso`

**Grano:** un día, una hora y un recurso. **Filas:** 5.935.449.

| Columna | Tipo | Descripción | Origen |
|---|---|---|---|
| `fecha_id` | `INTEGER` | Llave foránea a `dim_fecha`: fecha del dato en formato AAAAMMDD. | `stg_xm_generacion.fecha_id`, calculado desde `Date` de XM. |
| `hora` | `INTEGER` | Hora del día, de 1 a 24 (1 = 00:00-01:00; 24 = 23:00-24:00). | `UNPIVOT` de las columnas `Hour01` … `Hour24` de XM. |
| `recurso_id` | `VARCHAR` | Llave foránea a `dim_recurso`: código de la planta en XM. | `stg_xm_generacion.recurso_id`, desde `code` de XM (en mayúsculas y sin espacios). |
| `generacion_kwh` | `DOUBLE` | Energía generada por la planta en kWh. Es aditiva entre plantas y horas. | `stg_xm_generacion.generacion_kwh`, desde `Gene` de XM. Las celdas vacías no se convierten en filas. |
