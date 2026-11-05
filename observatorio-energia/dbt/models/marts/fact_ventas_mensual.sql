-- Tabla de HECHOS: las ventas de energia.
-- Grano: un mes, un municipio, un segmento y un tipo de compra.

select
    -- Llave a dim_mes: '2023-04' -> 202304 (igual que en dim_mes).
    v.mes_id,
    -- Llave a dim_fecha: el dia 1 del mes (20230401).
    v.fecha_id,
    -- Llave a dim_municipio: el codigo DIVIPOLA.
    v.municipio_id,
    -- Llave a dim_segmento: el numero del segmento (viene de la tabla s).
    s.segmento_id,
    -- Un dato descriptivo que se deja en el hecho: Bolsa o Contrato.
    v.tipo_compra,
    -- Las MEDIDAS: los numeros que se suman en el dashboard.
    v.energia_kwh,
    v.valor_cop,
    v.clientes
-- De donde: el modelo stg_ventas, con el nombre corto v.
from {{ ref('stg_ventas') }} as v
-- Se une con dim_segmento para cambiar el nombre del segmento por su llave.
join {{ ref('dim_segmento') }} as s
    on v.segmento = s.segmento
