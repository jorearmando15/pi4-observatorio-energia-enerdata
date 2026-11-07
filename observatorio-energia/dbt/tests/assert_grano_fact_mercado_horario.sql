-- Prueba singular: el grano de fact_mercado_horario debe ser unico.
-- Grano: un dia y una hora.
-- Si esta consulta devuelve filas, hay pares fecha-hora repetidos.

select
    fecha_id,
    hora,
    count(*) as filas
from {{ ref('fact_mercado_horario') }}
group by fecha_id, hora
having count(*) > 1
