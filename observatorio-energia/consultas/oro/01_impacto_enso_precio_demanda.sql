-- Pregunta de negocio:
--   ¿Cómo cambian el precio de bolsa y la demanda cuando el país está en
--   fase El Niño, La Niña o Neutral?
--
-- Por qué importa:
--   Es la pregunta central del reto (riesgo energético ante El Niño 2026).
--   Si el precio promedio es más alto en El Niño, el riesgo de costo aumenta.
--
-- Nota: se excluyen las 720 horas de septiembre de 2026 que aún no tienen
-- dato ONI (fase_enso = 'Sin dato').

SELECT
    f.fase_enso,
    COUNT(*)                                         AS horas,
    CAST(ROUND(AVG(m.precio_cop_kwh), 0) AS BIGINT)  AS precio_promedio_cop_kwh,
    CAST(ROUND(AVG(m.demanda_kwh), 0) AS BIGINT)     AS demanda_promedio_kwh,
    CAST(ROUND(MAX(m.precio_cop_kwh), 0) AS BIGINT)  AS precio_maximo_cop_kwh
FROM fact_mercado_horario AS m
JOIN dim_fecha AS f
    ON m.fecha_id = f.fecha_id
WHERE f.fase_enso IN ('El Niño', 'La Niña', 'Neutral')
GROUP BY f.fase_enso
ORDER BY precio_promedio_cop_kwh DESC;
