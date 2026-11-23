-- STAGING: precio de bolsa y demanda, UNA FILA POR HORA.
-- XM los entrega en formato ANCHO (una columna por hora: Hour01 ... Hour24)
-- y como TEXTO. Aqui se pasan a formato LARGO y a numeros.

-- with = consultas con nombre, que se usan mas abajo
with precio as (
    -- unpivot: convierte las columnas Hour01...Hour24 en filas (hora, valor)
    unpivot (select "Date", columns('^Hour') from {{ source('bronce', 'xm_precio_bolsa') }})
    on columns('^Hour') into name hora value precio
),
demanda as (
    unpivot (select "Date", columns('^Hour') from {{ source('bronce', 'xm_demanda') }})
    on columns('^Hour') into name hora value demanda
)

select
    -- La fecha, como fecha de verdad (llega como texto '2026-01-01')
    cast(p."Date" as date)                         as fecha,
    -- 'Hour01' -> 0, ..., 'Hour24' -> 23: la hora del dia, de 0 a 23
    cast(substr(p.hora, 5, 2) as integer) - 1      as hora,
    -- try_cast: si el texto viene vacio, deja NULL en vez de fallar
    try_cast(p.precio as double)                   as precio_cop_kwh,
    try_cast(d.demanda as double)                  as demanda_kwh
from precio as p
-- join: une cada hora del precio con la misma hora de la demanda
join demanda as d
    on p."Date" = d."Date" and p.hora = d.hora
