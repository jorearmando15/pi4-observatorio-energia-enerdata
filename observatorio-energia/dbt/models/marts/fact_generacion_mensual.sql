-- Tabla de HECHOS: generacion por TIPO de planta, UN MES Y UN TIPO por fila.
-- Responde: P3 (de donde viene la energia y como cambia en epoca seca).

with por_mes as (
    select cast(date_trunc('month', fecha) as date) as mes,
           tipo,
           sum(energia_kwh) / 1e6                   as energia_gwh   -- kWh -> GWh
    from {{ ref('stg_generacion_diaria') }}
    group by all
)

select
    mes,
    tipo,
    round(energia_gwh, 1)                                            as energia_gwh,
    -- La participacion: la energia de este tipo / toda la energia del mes.
    -- over (partition by mes) = la suma de TODOS los tipos de ese mes
    round(energia_gwh / sum(energia_gwh) over (partition by mes) * 100, 1) as participacion_pct
from por_mes
