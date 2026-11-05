-- Tabla de HECHOS: la generacion de energia por planta.
-- Grano: un dia, una hora y un recurso (planta).

select
    -- Llave a dim_fecha.
    g.fecha_id,
    -- Hora del dia: 1, 2, ..., 24.
    g.hora,
    -- Llave a dim_recurso.
    g.recurso_id,
    -- La MEDIDA: energia generada en kWh.
    g.generacion_kwh
from {{ ref('stg_xm_generacion') }} as g
