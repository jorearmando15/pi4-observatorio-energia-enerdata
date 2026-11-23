-- Tabla de HECHOS: el mercado y el clima, UN MES por fila (desde 2015).
-- Responde: P1 (embalses), P2 (ONI, aportes y precio) y sirve para P5 (precio
-- de bolsa del mes de cada venta).

with hidrologia as (
    -- date_trunc('month', fecha): el primer dia del mes. Asi se agrupa por mes
    select date_trunc('month', fecha) as mes,
           avg(embalses_pct)          as embalses_pct,
           avg(aportes_pct)           as aportes_pct
    from {{ ref('stg_hidrologia_diaria') }}
    group by 1
),
precio as (
    select date_trunc('month', fecha) as mes,
           avg(precio_bolsa_cop_kwh)  as precio_bolsa_cop_kwh,
           avg(precio_contrato_cop_kwh) as precio_contrato_cop_kwh
    from {{ ref('stg_precios_diarios') }}
    group by 1
)

select
    -- La llave con el mismo formato de dim_mes: 2023-04 -> 202304
    cast(strftime(h.mes, '%Y%m') as integer)  as mes_id,
    cast(h.mes as date)                       as mes,
    round(h.embalses_pct, 1)                  as embalses_pct,
    round(h.aportes_pct, 1)                   as aportes_pct,
    -- Los precios y los aportes existen desde 2023: antes quedan NULL
    round(p.precio_bolsa_cop_kwh, 1)          as precio_bolsa_cop_kwh,
    round(p.precio_contrato_cop_kwh, 1)       as precio_contrato_cop_kwh,
    o.oni,
    o.fase_enso
from hidrologia as h
left join precio as p on h.mes = p.mes
left join {{ ref('stg_oni') }} as o on h.mes = o.mes
