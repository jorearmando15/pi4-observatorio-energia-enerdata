-- Staging: unifica las 4 hojas de EnerAndes (2023-2026) en un solo esquema.
-- La capa plata solo tenia limpia la hoja 2023, asi que aqui se aplican las
-- mismas reglas de limpieza, pero en SQL y para las 4 hojas:
--   1. quitar titulos, encabezados, filas vacias y la fila TOTAL;
--   2. unificar formatos de fecha (YYYY-MM, MM/YYYY, DD/MM/YYYY, mmm-YY);
--   3. eliminar filas duplicadas exactas;
--   4. normalizar municipio (con DIVIPOLA), segmento y tipo de compra;
--   5. convertir la energia a kWh (en 2024 hay filas en MWh);
--   6. descartar energias nulas o negativas (no se pueden sumar).
--
-- Grano del resultado: una fila por mes, municipio, segmento y tipo de compra
-- (antes de agregar; el hecho hace la suma final).

with crudo as (
    select
        col_0 as fecha_raw,
        col_1 as municipio_raw,
        col_2 as segmento_raw,
        col_3 as compra_raw,
        col_4 as energia_raw,
        'kWh' as unidad,
        col_5 as valor_raw,
        col_6 as clientes_raw,
        2023 as anio_origen
    from {{ source('bronce', 'enerandes_ventas_2023') }}

    union all

    select
        col_0, col_1, col_2, col_3, col_4,
        col_5 as unidad,
        col_6, col_7,
        2024
    from {{ source('bronce', 'enerandes_ventas_2024') }}

    union all

    select
        col_0, col_1, col_2, col_3, col_4,
        'kWh',
        col_5, col_6,
        2025
    from {{ source('bronce', 'enerandes_ventas_2025') }}

    union all

    select
        col_0, col_1, col_2, col_3, col_4,
        'kWh',
        col_5, col_6,
        2026
    from {{ source('bronce', 'enerandes_ventas_2026') }}
),

-- Cada hoja usa un formato de fecha distinto. Se prueban los 4 y se deja el
-- primero que funcione. Las filas de titulo, encabezado, TOTAL y vacias
-- quedan con fecha nula y se descartan en el siguiente paso.
con_fecha as (
    select
        *,
        coalesce(
            try_strptime(trim(fecha_raw), '%Y-%m'),
            try_strptime(trim(fecha_raw), '%d/%m/%Y'),
            try_strptime(trim(fecha_raw), '%m/%Y'),
            try_strptime(trim(fecha_raw), '%b-%y')
        ) as fecha
    from crudo
),

-- distinct quita las copias exactas que vienen del Excel (120 en total).
limpio as (
    select distinct
        fecha,
        municipio_raw,
        segmento_raw,
        compra_raw,
        energia_raw,
        unidad,
        valor_raw,
        clientes_raw,
        anio_origen
    from con_fecha
    where fecha is not null
),

-- Clave del municipio: minusculas, sin espacios externos y sin tildes.
-- ('Medellín D.E.' -> 'medellin d.e.'; 'Itagüí' -> 'itagui').
con_clave as (
    select
        *,
        replace(
            replace(
                replace(
                    replace(
                        replace(
                            replace(
                                replace(lower(trim(municipio_raw)), 'á', 'a'),
                            'é', 'e'),
                        'í', 'i'),
                    'ó', 'o'),
                'ú', 'u'),
            'ü', 'u'),
        'ñ', 'n') as municipio_key
    from limpio
),

-- Catalogo de municipios: clave normalizada -> codigo DIVIPOLA y nombre oficial.
municipios (municipio_key, municipio_id, municipio) as (
    values
        ('medellin', '05001', 'Medellín'),
        ('medellin d.e.', '05001', 'Medellín'),
        ('santa fe de antioquia', '05042', 'Santa Fe de Antioquia'),
        ('santafe de antioquia', '05042', 'Santa Fe de Antioquia'),
        ('sta fe de antioquia', '05042', 'Santa Fe de Antioquia'),
        ('apartado', '05045', 'Apartadó'),
        ('bello', '05088', 'Bello'),
        ('caldas', '05129', 'Caldas'),
        ('caucasia', '05154', 'Caucasia'),
        ('copacabana', '05212', 'Copacabana'),
        ('envigado', '05266', 'Envigado'),
        ('girardota', '05308', 'Girardota'),
        ('itagui', '05360', 'Itagüí'),
        ('la estrella', '05380', 'La Estrella'),
        ('marinilla', '05440', 'Marinilla'),
        ('rio negro', '05615', 'Rionegro'),
        ('rionegro', '05615', 'Rionegro'),
        ('rionegro (ant)', '05615', 'Rionegro'),
        ('sabaneta', '05631', 'Sabaneta'),
        ('turbo', '05837', 'Turbo')
),

normalizado as (
    select
        -- Llaves de las dimensiones. La fecha se lleva siempre al dia 1 del mes
        -- porque el grano de ventas es mensual.
        cast(strftime(date_trunc('month', c.fecha), '%Y%m') as integer) as mes_id,
        cast(strftime(date_trunc('month', c.fecha), '%Y%m%d') as integer) as fecha_id,
        cast(date_trunc('month', c.fecha) as date) as fecha,
        m.municipio_id,
        m.municipio,
        case
            when lower(trim(c.segmento_raw)) in ('ind', 'industrial') then 'Industrial'
            when lower(trim(c.segmento_raw)) in ('resid.', 'residencial') then 'Residencial'
            when lower(trim(c.segmento_raw)) = 'comercial' then 'Comercial'
            else 'No informado'
        end as segmento,
        case
            when lower(trim(c.compra_raw)) = 'bolsa' then 'Bolsa'
            when lower(trim(c.compra_raw)) in ('contrato', 'contratos') then 'Contrato'
        end as tipo_compra,
        -- La energia se lleva toda a kWh: 1 MWh = 1.000 kWh.
        try_cast(c.energia_raw as double)
            * case when upper(trim(c.unidad)) = 'MWH' then 1000 else 1 end as energia_kwh,
        try_cast(c.valor_raw as double) as valor_cop,
        try_cast(c.clientes_raw as integer) as clientes,
        c.anio_origen
    from con_clave c
    left join municipios m
        on c.municipio_key = m.municipio_key
)

select
    strftime(fecha, '%Y-%m') as periodo,
    mes_id,
    fecha_id,
    fecha,
    municipio_id,
    municipio,
    segmento,
    tipo_compra,
    energia_kwh,
    valor_cop,
    clientes,
    anio_origen
from normalizado
where energia_kwh is not null
  and energia_kwh >= 0
