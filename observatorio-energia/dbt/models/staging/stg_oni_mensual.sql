-- Staging: indice ONI de NOAA, una fila por mes.
-- NOAA publica el ONI por trimestre movil (DJF, JFM, ... NDJ). Para unirlo a
-- dim_fecha se le asigna al mes central de cada temporada:
--   DJF -> enero, JFM -> febrero, ..., NDJ -> diciembre.
--
-- La fase ENSO se clasifica con el umbral clasico de NOAA sobre la anomalia:
--   >= +0.5 -> El Niño; <= -0.5 -> La Niña; el resto -> Neutral.
--
-- Grano del resultado: un mes.

with base as (
    select
        cast("YR" as integer) as anio,
        upper(trim("SEAS")) as temporada,
        try_cast("ANOM" as double) as oni,
        case upper(trim("SEAS"))
            when 'DJF' then 1
            when 'JFM' then 2
            when 'FMA' then 3
            when 'MAM' then 4
            when 'AMJ' then 5
            when 'MJJ' then 6
            when 'JJA' then 7
            when 'JAS' then 8
            when 'ASO' then 9
            when 'SON' then 10
            when 'OND' then 11
            when 'NDJ' then 12
        end as mes
    from {{ source('bronce', 'noaa_oni') }}
)

select
    anio,
    mes,
    -- Llave de dim_fecha: el dia 1 de ese mes, como AAAAMMDD
    cast(anio * 10000 + mes * 100 + 1 as integer) as fecha_id,
    temporada,
    oni,
    case
        when oni >= 0.5 then 'El Niño'
        when oni <= -0.5 then 'La Niña'
        else 'Neutral'
    end as fase_enso
from base
where mes is not null
  and oni is not null
