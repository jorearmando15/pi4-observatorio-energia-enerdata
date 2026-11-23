-- STAGING: el indice ONI de NOAA, UNA FILA POR MES.
-- NOAA lo publica por trimestre movil: 'DJF' = diciembre-enero-febrero.
-- Se le asigna al mes del CENTRO: DJF -> enero, JFM -> febrero...

select
    -- make_date(ano, mes, 1): el primer dia del mes
    make_date(
        cast("YR" as integer),
        -- list_position(): en que lugar de la lista esta el trimestre.
        -- DJF -> 1 (enero), JFM -> 2 (febrero) ... NDJ -> 12 (diciembre)
        list_position(['DJF', 'JFM', 'FMA', 'MAM', 'AMJ', 'MJJ',
                       'JJA', 'JAS', 'ASO', 'SON', 'OND', 'NDJ'], "SEAS"),
        1)                                         as mes,
    try_cast("ANOM" as double)                     as oni,
    -- La fase ENSO segun el ONI: +0.5 o mas = El Nino; -0.5 o menos = La Nina
    case
        when try_cast("ANOM" as double) >= 0.5 then 'El Niño'
        when try_cast("ANOM" as double) <= -0.5 then 'La Niña'
        else 'Neutral'
    end                                            as fase_enso
from {{ source('bronce', 'noaa_oni') }}
