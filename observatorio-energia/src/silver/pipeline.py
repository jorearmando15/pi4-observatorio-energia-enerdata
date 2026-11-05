"""Ejecuta todas las limpiezas de la capa plata."""
from src.silver import enerandes, ideam, noaa, trm, xm
from src.utils import log


def main() -> None:
    log("Iniciando la limpieza completa de la capa plata")
    for limpiador in (enerandes, xm, ideam, noaa, trm):
        limpiador.main()
    log("Limpieza de la capa plata terminada")


if __name__ == "__main__":
    main()
