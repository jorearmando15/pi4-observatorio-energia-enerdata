-- Prueba singular: el grano de fact_ventas_mensual debe ser unico.
-- Grano: un mes, un municipio, un segmento y un tipo de compra.
-- Si esta consulta devuelve filas, hay combinaciones repetidas y la prueba falla.

select
    mes_id,
    municipio_id,
    segmento_id,
    tipo_compra,
    count(*) as filas
from {{ ref('fact_ventas_mensual') }}
group by mes_id, municipio_id, segmento_id, tipo_compra
having count(*) > 1
