-- Tabla de HECHOS: precio y demanda, UNA HORA por fila (rango de la clase).
-- Responde: P4 (patrones de demanda por hora, dia de la semana y mes; hora pico).

select
    fecha,
    hora,
    -- isodow: dia de la semana, 1 = lunes ... 7 = domingo
    isodow(fecha)                                as dia_semana,
    -- El nombre del dia, para mostrarlo en el dashboard
    ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes',
     'Sábado', 'Domingo'][isodow(fecha)]         as dia_nombre,
    cast(date_trunc('month', fecha) as date)     as mes,
    precio_cop_kwh,
    demanda_kwh
from {{ ref('stg_mercado_horario') }}
