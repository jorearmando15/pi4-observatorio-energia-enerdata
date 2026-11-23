-- STAGING: embalses y aportes hidricos, UNA FILA POR DIA (desde 2015).

select
    cast(e."Date" as date)                                     as fecha,
    -- XM da el volumen util como fraccion (0.75); x 100 -> porcentaje (75.0)
    try_cast(e."Value" as double) * 100                        as embalses_pct,
    -- Aportes en % de la media historica: 100 = lo normal; 60 = llovio
    -- mucho menos de lo normal en las cuencas. nullif evita dividir por 0
    try_cast(a."Value" as double)
        / nullif(try_cast(m."Value" as double), 0) * 100       as aportes_pct
from {{ source('bronce', 'xm_embalses') }} as e
left join {{ source('bronce', 'xm_aportes') }} as a on e."Date" = a."Date"
left join {{ source('bronce', 'xm_aportes_media') }} as m on e."Date" = m."Date"
