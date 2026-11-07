-- Pregunta de negocio:
--   ¿Cómo evolucionó la matriz de generación por tipo de planta?
--   En un año de El Niño se espera menos generación hidráulica y más térmica.
--
-- Resultado: generación anual en GWh y participación porcentual dentro de
-- cada año. Se incluyen las cuatro tecnologías principales (hidráulica,
-- térmica, solar y eólica); se excluyen Cogenerador y 'No informado'.
--
-- Nota: 2026 solo llega hasta el 30 de septiembre.

SELECT
    f.anio,
    r.tipo,
    ROUND(SUM(g.generacion_kwh) / 1e6, 1) AS generacion_gwh,
    ROUND(
        100.0 * SUM(g.generacion_kwh)
        / SUM(SUM(g.generacion_kwh)) OVER (PARTITION BY f.anio),
        1
    ) AS participacion_pct
FROM fact_generacion_recurso AS g
JOIN dim_fecha AS f
    ON g.fecha_id = f.fecha_id
JOIN dim_recurso AS r
    ON g.recurso_id = r.recurso_id
WHERE r.tipo IN ('Hidráulica', 'Térmica', 'Solar', 'Eólica')
GROUP BY f.anio, r.tipo
ORDER BY f.anio, generacion_gwh DESC;
