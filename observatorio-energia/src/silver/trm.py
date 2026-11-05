"""Limpieza de la tasa representativa del mercado."""
from src.quality.esquemas import ESQUEMA_TRM
from src.silver.common import fechas, guardar_validado, leer_bronce, numero, sin_linaje
from src.utils import log


def limpiar(bronce):
    df = sin_linaje(bronce)
    tabla = df[["valor", "unidad", "vigenciadesde", "vigenciahasta"]].copy()
    tabla["fecha"] = fechas(tabla.pop("vigenciadesde"), "vigenciadesde")
    tabla["fecha_hasta"] = fechas(tabla.pop("vigenciahasta"), "vigenciahasta")
    tabla["valor_cop_por_usd"] = numero(tabla.pop("valor"), "valor").astype(float)
    tabla["unidad"] = tabla["unidad"].astype("string").str.strip().str.upper()
    return tabla[["fecha", "fecha_hasta", "valor_cop_por_usd", "unidad"]]


def main() -> None:
    log("TRM - limpieza de la tasa de cambio")
    tabla = limpiar(leer_bronce("trm_diaria"))
    guardar_validado(tabla, "trm_diaria", ESQUEMA_TRM)
    log(f"   trm_diaria: {len(tabla):,} filas")


if __name__ == "__main__":
    main()
