-- Dimension FECHA: una fila por dia, del 2023-01-01 al 2026-12-31.
-- Grano: un dia.
--
-- Se genera el calendario completo con range() y a cada dia se le agregan
-- mes, trimestre, dia de la semana y la fase ENSO del mes (indice ONI).

with dias as (
    -- Un dia por cada fecha del rango (1.461 filas).
    select cast(dia as date) as fecha
    from range(
        date '2023-01-01',
        date '2026-12-31' + interval 1 day,
        interval 1 day
    ) as t(dia)
),

calendario as (
    select
        -- Llave: la fecha como numero AAAAMMDD (20230101)
        cast(strftime(fecha, '%Y%m%d') as integer) as fecha_id,
        fecha,
        cast(strftime(fecha, '%Y') as integer) as anio,
        -- Llave de dim_mes: AAAAMM (202301)
        cast(strftime(fecha, '%Y%m') as integer) as mes_id,
        cast(strftime(fecha, '%m') as integer) as mes,
        case cast(strftime(fecha, '%m') as integer)
            when 1 then 'Enero'
            when 2 then 'Febrero'
            when 3 then 'Marzo'
            when 4 then 'Abril'
            when 5 then 'Mayo'
            when 6 then 'Junio'
            when 7 then 'Julio'
            when 8 then 'Agosto'
            when 9 then 'Septiembre'
            when 10 then 'Octubre'
            when 11 then 'Noviembre'
            when 12 then 'Diciembre'
        end as nombre_mes,
        -- Trimestre: (mes + 2) // 3 -> 1, 2, 3 o 4.
        (cast(strftime(fecha, '%m') as integer) + 2) // 3 as trimestre,
        cast(strftime(fecha, '%d') as integer) as dia,
        -- Dia de la semana ISO: 1 = lunes ... 7 = domingo.
        cast(strftime(fecha, '%u') as integer) as dia_semana,
        case cast(strftime(fecha, '%u') as integer)
            when 1 then 'Lunes'
            when 2 then 'Martes'
            when 3 then 'Miércoles'
            when 4 then 'Jueves'
            when 5 then 'Viernes'
            when 6 then 'Sábado'
            when 7 then 'Domingo'
        end as nombre_dia_semana
    from dias
)

select
    c.fecha_id,
    c.fecha,
    c.anio,
    c.mes_id,
    c.mes,
    c.nombre_mes,
    c.trimestre,
    c.dia,
    c.dia_semana,
    c.nombre_dia_semana,
    -- Si el mes no tiene dato de NOAA queda "Sin dato" (no se pierde el dia).
    coalesce(o.fase_enso, 'Sin dato') as fase_enso
from calendario c
left join {{ ref('stg_oni_mensual') }} o
    on c.anio = o.anio
   and c.mes = o.mes
