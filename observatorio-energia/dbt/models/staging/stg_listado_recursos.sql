-- Staging: catalogo de recursos (plantas) de XM, una fila por recurso.
-- El bronce puede traer el mismo codigo mas de una vez; aqui se deja una sola
-- fila por codigo: la del listado mas reciente.
--
-- Grano del resultado: un recurso (planta).

with catalogo as (
    select
        upper(trim("Code")) as recurso_id,
        trim("Name") as nombre,
        -- El bronce mezcla mayusculas y minusculas ('SOLAR', 'Solar'):
        -- se unifica a una sola forma para que la dimension sea consistente.
        case lower(trim("Type"))
            when 'solar' then 'Solar'
            when 'hidraulica' then 'Hidráulica'
            when 'termica' then 'Térmica'
            when 'eolica' then 'Eólica'
            when 'cogenerador' then 'Cogenerador'
            else coalesce(trim("Type"), 'No informado')
        end as tipo,
        -- Igual con el estado: 'OPERACION' y 'Operacion' son lo mismo.
        case lower(trim("State"))
            when 'operacion' then 'Operación'
            when 'pruebas' then 'Pruebas'
            else coalesce(trim("State"), 'No informado')
        end as estado,
        trim("EnerSource") as fuente_energia,
        try_cast("OperStartdate" as date) as fecha_operacion,
        -- Numera las filas de cada codigo; rn = 1 es la mas reciente.
        row_number() over (
            partition by upper(trim("Code"))
            order by try_cast("Date" as date) desc
        ) as rn
    from {{ source('bronce', 'xm_listado_recursos') }}
    where trim("Code") <> ''
)

select
    recurso_id,
    nombre,
    tipo,
    estado,
    fuente_energia,
    fecha_operacion
from catalogo
where rn = 1
