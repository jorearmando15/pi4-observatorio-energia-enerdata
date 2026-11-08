-- Prueba singular: el grano de fact_generacion_recurso debe ser unico.
-- Grano: un dia, una hora y un recurso.
-- Si esta consulta devuelve filas, hay combinaciones repetidas.

select
    fecha_id,
    hora,
    recurso_id,
    count(*) as filas
from {{ ref('fact_generacion_recurso') }}
group by fecha_id, hora, recurso_id
having count(*) > 1
