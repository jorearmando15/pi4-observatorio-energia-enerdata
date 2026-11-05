-- Staging: precio de bolsa nacional de XM, pasado de ancho a largo.
-- El bronce trae una fila por dia y 24 columnas (Hour01..Hour24). Aqui cada
-- columna se convierte en una fila: una por dia y hora.
--
-- Grano del resultado: un dia y una hora.

with largo as (
    -- unpivot toma las 24 columnas Hour.. y las convierte en dos columnas:
    -- hora_col (el nombre de la columna) y precio_raw (el valor).
    select *
    from (unpivot (
        select
            try_cast("Date" as date) as fecha,
            "code" as codigo,
            "Hour01", "Hour02", "Hour03", "Hour04", "Hour05", "Hour06",
            "Hour07", "Hour08", "Hour09", "Hour10", "Hour11", "Hour12",
            "Hour13", "Hour14", "Hour15", "Hour16", "Hour17", "Hour18",
            "Hour19", "Hour20", "Hour21", "Hour22", "Hour23", "Hour24"
        from {{ source('bronce', 'xm_precio_bolsa') }}
    ) on "Hour01", "Hour02", "Hour03", "Hour04", "Hour05", "Hour06",
         "Hour07", "Hour08", "Hour09", "Hour10", "Hour11", "Hour12",
         "Hour13", "Hour14", "Hour15", "Hour16", "Hour17", "Hour18",
         "Hour19", "Hour20", "Hour21", "Hour22", "Hour23", "Hour24"
    into name hora_col value precio_raw)
)

select
    -- Llave de dim_fecha: la fecha como numero AAAAMMDD
    cast(strftime(fecha, '%Y%m%d') as integer) as fecha_id,
    fecha,
    -- 'Hour07' -> 7
    cast(right(hora_col, 2) as integer) as hora,
    -- Precio de bolsa en COP/kWh
    try_cast(precio_raw as double) as precio_cop_kwh
from largo
where fecha is not null
  and precio_raw is not null
  and trim(cast(precio_raw as varchar)) <> ''
