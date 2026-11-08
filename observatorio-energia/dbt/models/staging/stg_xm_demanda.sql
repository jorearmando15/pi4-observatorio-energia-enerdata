-- Staging: demanda real del sistema de XM, pasada de ancho a largo.
-- El bronce trae una fila por dia y 24 columnas (Hour01..Hour24). Aqui cada
-- columna se convierte en una fila: una por dia y hora.
--
-- Grano del resultado: un dia y una hora.

with largo as (
    select *
    from (unpivot (
        select
            try_cast("Date" as date) as fecha,
            "code" as codigo,
            "Hour01", "Hour02", "Hour03", "Hour04", "Hour05", "Hour06",
            "Hour07", "Hour08", "Hour09", "Hour10", "Hour11", "Hour12",
            "Hour13", "Hour14", "Hour15", "Hour16", "Hour17", "Hour18",
            "Hour19", "Hour20", "Hour21", "Hour22", "Hour23", "Hour24"
        from {{ source('bronce', 'xm_demanda') }}
    ) on "Hour01", "Hour02", "Hour03", "Hour04", "Hour05", "Hour06",
         "Hour07", "Hour08", "Hour09", "Hour10", "Hour11", "Hour12",
         "Hour13", "Hour14", "Hour15", "Hour16", "Hour17", "Hour18",
         "Hour19", "Hour20", "Hour21", "Hour22", "Hour23", "Hour24"
    into name hora_col value demanda_raw)
)

select
    -- Llave de dim_fecha: la fecha como numero AAAAMMDD
    cast(strftime(fecha, '%Y%m%d') as integer) as fecha_id,
    fecha,
    -- 'Hour07' -> 7
    cast(right(hora_col, 2) as integer) as hora,
    -- Demanda real en kWh
    try_cast(demanda_raw as double) as demanda_kwh
from largo
where fecha is not null
  and demanda_raw is not null
  and trim(cast(demanda_raw as varchar)) <> ''
