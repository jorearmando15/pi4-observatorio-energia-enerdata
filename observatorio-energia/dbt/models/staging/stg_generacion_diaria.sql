-- STAGING: generacion por TIPO de planta, UNA FILA POR DIA Y TIPO.

with por_hora as (
    -- Una fila por planta y hora
    unpivot (select "Date", code, columns('^Hour') from {{ source('bronce', 'xm_generacion') }})
    on columns('^Hour') into name hora value kwh
),
tipos as (
    -- El tipo de cada planta. upper(): XM escribe 'SOLAR' y tambien 'Solar'
    select distinct "Code" as code, upper("Type") as tipo
    from {{ source('bronce', 'xm_recursos') }}
)

select
    cast(g."Date" as date)                  as fecha,
    -- coalesce: si una planta no esta en la lista, queda como 'OTRO'
    coalesce(t.tipo, 'OTRO')                as tipo,
    -- La suma de todas las horas de todas las plantas de ese tipo
    sum(try_cast(g.kwh as double))          as energia_kwh
from por_hora as g
left join tipos as t on g.code = t.code
group by all
