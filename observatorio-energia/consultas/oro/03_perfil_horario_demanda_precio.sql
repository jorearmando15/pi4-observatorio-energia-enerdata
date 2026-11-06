-- Pregunta de negocio:
--   ¿En qué horas del día se concentra la demanda y cuándo la energía es más cara?
--
-- Por qué importa:
--   Permite identificar las horas pico (mayor demanda) y las horas caras
--   (mayor precio), insumo para estrategias de compra y respuesta de demanda.
--
-- La hora va de 1 a 24, donde 1 = 00:00-01:00 y 24 = 23:00-24:00.

SELECT
    hora,
    CAST(ROUND(AVG(precio_cop_kwh), 0) AS BIGINT) AS precio_promedio_cop_kwh,
    CAST(ROUND(AVG(demanda_kwh), 0) AS BIGINT)    AS demanda_promedio_kwh
FROM fact_mercado_horario
GROUP BY hora
ORDER BY hora;
