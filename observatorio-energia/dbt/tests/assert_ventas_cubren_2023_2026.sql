-- Prueba singular: las ventas deben cubrir los cuatro anios pedidos (2023-2026).
-- Si falta algun anio, la consulta devuelve esa fila y la prueba falla.

with anios_ventas as (
    select distinct cast(left(cast(mes_id as varchar), 4) as integer) as anio
    from {{ ref('fact_ventas_mensual') }}
),

esperados as (
    select anio
    from (values (2023), (2024), (2025), (2026)) as t(anio)
)

select e.anio
from esperados e
left join anios_ventas v
    on e.anio = v.anio
where v.anio is null
