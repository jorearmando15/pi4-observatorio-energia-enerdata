-- Dimension RECURSO: una fila por planta de generacion.
-- Grano: un recurso.
--
-- Se unen dos fuentes:
--   1. el catalogo de XM (ListadoRecursos), que trae nombre, tipo y estado;
--   2. los codigos que aparecen generando en xm_generacion.
-- Algunos codigos generan pero no estan en el catalogo: se conservan con
-- datos "No informado" y en_catalogo = false, para que la llave del hecho
-- siempre exista en la dimension.

with catalogo as (
    select *
    from {{ ref('stg_listado_recursos') }}
),

usados as (
    -- Recursos que efectivamente aparecen en la generacion horaria.
    select distinct recurso_id
    from {{ ref('stg_xm_generacion') }}
),

todos as (
    select recurso_id from catalogo
    union
    select recurso_id from usados
)

select
    t.recurso_id,
    coalesce(c.nombre, t.recurso_id) as nombre,
    coalesce(c.tipo, 'No informado') as tipo,
    coalesce(c.estado, 'No informado') as estado,
    c.fuente_energia,
    c.fecha_operacion,
    case when c.recurso_id is not null then true else false end as en_catalogo
from todos t
left join catalogo c
    on t.recurso_id = c.recurso_id
