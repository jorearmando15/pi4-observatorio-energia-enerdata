-- Staging: generacion horaria por recurso de XM, pasada de ancho a largo.
-- El bronce trae una fila por dia y recurso, con 24 columnas (Hour01..Hour24).
-- Aqui cada columna se convierte en una fila: una por dia, hora y recurso.
--
-- Muchas celdas vienen vacias (''): significan que el recurso no reporto
-- generacion en esa hora y se descartan.
--
-- Grano del resultado: un dia, una hora y un recurso.

with largo as (
    select *
    from (unpivot (
        select
            try_cast("Date" as date) as fecha,
            upper(trim("code")) as recurso_id,
            "Hour01", "Hour02", "Hour03", "Hour04", "Hour05", "Hour06",
            "Hour07", "Hour08", "Hour09", "Hour10", "Hour11", "Hour12",
            "Hour13", "Hour14", "Hour15", "Hour16", "Hour17", "Hour18",
            "Hour19", "Hour20", "Hour21", "Hour22", "Hour23", "Hour24"
        from {{ source('bronce', 'xm_generacion') }}
    ) on "Hour01", "Hour02", "Hour03", "Hour04", "Hour05", "Hour06",
         "Hour07", "Hour08", "Hour09", "Hour10", "Hour11", "Hour12",
         "Hour13", "Hour14", "Hour15", "Hour16", "Hour17", "Hour18",
         "Hour19", "Hour20", "Hour21", "Hour22", "Hour23", "Hour24"
    into name hora_col value generacion_raw)
)

select
    -- Llave de dim_fecha: la fecha como numero AAAAMMDD
    cast(strftime(fecha, '%Y%m%d') as integer) as fecha_id,
    fecha,
    -- 'Hour07' -> 7
    cast(right(hora_col, 2) as integer) as hora,
    -- Llave de dim_recurso: el codigo del recurso (planta)
    recurso_id,
    -- Generacion en kWh
    try_cast(generacion_raw as double) as generacion_kwh
from largo
where fecha is not null
  and recurso_id is not null
  and generacion_raw is not null
  and trim(cast(generacion_raw as varchar)) <> ''
