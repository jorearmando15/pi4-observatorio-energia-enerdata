"""Ejecuta todas las limpiezas de la capa plata."""
from src.silver import enerandes, ideam, noaa, reporte_calidad, trm, xm
from src.utils import log


def main() -> None:
    log("Iniciando la limpieza completa de la capa plata")
    for limpiador in (enerandes, xm, ideam, noaa, trm):
        limpiador.main()
    reporte_calidad.generar_reporte()
    log("Reporte de calidad actualizado en docs/reporte_calidad.md")
    log("Limpieza de la capa plata terminada")


if __name__ == "__main__":
    main()
