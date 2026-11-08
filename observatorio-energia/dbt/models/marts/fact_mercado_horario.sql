-- Tabla de HECHOS: el mercado horario de energia.
-- Grano: un dia y una hora.
--
-- Junta las dos series horarias de XM en la misma fila:
--   - precio de bolsa (COP/kWh)
--   - demanda real del sistema (kWh)

select
    -- Llave a dim_fecha.
    p.fecha_id,
    -- La hora es una dimension degenerada: 1, 2, ..., 24.
    p.hora,
    -- Las MEDIDAS.
    p.precio_cop_kwh,
    d.demanda_kwh
from {{ ref('stg_xm_precio') }} as p
join {{ ref('stg_xm_demanda') }} as d
    on p.fecha_id = d.fecha_id
   and p.hora = d.hora
