-- Pregunta de negocio:
--   ¿Qué municipios concentran las ventas de energía de EnerAndes?
--
-- Resultado: top 10 de municipios por energía vendida, con el valor facturado
-- y el promedio de clientes por mes. Sirve para priorizar mercados y campañas
-- comerciales.
--
-- Nota: 'clientes' en el hecho es un conteo mensual. Primero se suma por mes
-- y después se promedia entre meses; sumarlo directamente contaría varias
-- veces al mismo cliente.

WITH ventas AS (
    SELECT
        m.municipio,
        SUM(v.energia_kwh) AS energia_kwh,
        SUM(v.valor_cop)   AS valor_cop
    FROM fact_ventas_mensual AS v
    JOIN dim_municipio AS m
        ON v.municipio_id = m.municipio_id
    GROUP BY m.municipio
),

clientes_mes AS (
    SELECT
        m.municipio,
        v.mes_id,
        SUM(v.clientes) AS clientes
    FROM fact_ventas_mensual AS v
    JOIN dim_municipio AS m
        ON v.municipio_id = m.municipio_id
    GROUP BY m.municipio, v.mes_id
),

clientes_promedio AS (
    SELECT
        municipio,
        AVG(clientes) AS clientes_promedio_mes
    FROM clientes_mes
    GROUP BY municipio
)

SELECT
    v.municipio,
    ROUND(v.energia_kwh / 1e6, 1)                          AS energia_gwh,
    CAST(ROUND(v.valor_cop / 1e6, 0) AS BIGINT)            AS valor_millones_cop,
    CAST(ROUND(c.clientes_promedio_mes, 0) AS BIGINT)      AS clientes_promedio_mes
FROM ventas AS v
JOIN clientes_promedio AS c
    ON v.municipio = c.municipio
ORDER BY energia_gwh DESC
LIMIT 10;
