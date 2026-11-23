-- STAGING: precio de bolsa y precio de contrato, UNA FILA POR DIA (desde 2023).

select
    cast(b."Date" as date)                 as fecha,
    -- Lo que cuesta la energia comprada en BOLSA ese dia (COP/kWh)
    try_cast(b."Value" as double)          as precio_bolsa_cop_kwh,
    -- Lo que cuesta, en promedio, la energia comprada por CONTRATO (COP/kWh)
    try_cast(c."Value" as double)          as precio_contrato_cop_kwh
from {{ source('bronce', 'xm_precio_bolsa_diario') }} as b
left join {{ source('bronce', 'xm_precio_contrato') }} as c on b."Date" = c."Date"
