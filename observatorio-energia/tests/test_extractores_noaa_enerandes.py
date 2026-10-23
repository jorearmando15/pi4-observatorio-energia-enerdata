import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from src import config
from src.extract import enerandes, noaa


class ExtractoresFuentesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.directorio_original = config.DIR_BRONZE
        config.DIR_BRONZE = Path(self.tempdir.name) / "bronze"

    def tearDown(self) -> None:
        config.DIR_BRONZE = self.directorio_original
        self.tempdir.cleanup()

    def test_noaa_guarda_el_indice_sin_transformar_sus_valores(self) -> None:
        contenido = (
            "SEAS YR TOTAL ANOM\n"
            "DJF 2024 13.2 1.2\n"
            "JFM 2024 13.0 1.0\n"
        )

        with patch.object(noaa, "http_texto", return_value=contenido):
            noaa.extraer()

        resultado = pd.read_parquet(config.DIR_BRONZE / "noaa_oni.parquet")
        esperado = pd.read_csv(io.StringIO(contenido), sep=r"\s+", dtype=str)
        pd.testing.assert_frame_equal(
            resultado[esperado.columns],
            esperado,
            check_dtype=True,
        )
        self.assertEqual(resultado["_fuente"].unique().tolist(), ["NOAA"])
        self.assertEqual(resultado["_origen"].unique().tolist(), [config.NOAA_ONI_URL])

    def test_enerandes_guarda_las_hojas_excel_sin_transformar_sus_celdas(self) -> None:
        archivo_excel = Path(self.tempdir.name) / "ventas.xlsx"
        with pd.ExcelWriter(archivo_excel) as writer:
            pd.DataFrame(
                [
                    ["Reporte ventas", None],
                    ["Codigo", "Valor"],
                    ["001", "125.50"],
                    ["TOTAL", "125.50"],
                ]
            ).to_excel(writer, sheet_name="Ventas 2023", header=False, index=False)
            pd.DataFrame(
                [["Codigo", "Valor"], ["002", "200.00"]]
            ).to_excel(writer, sheet_name="Ventas 2024", header=False, index=False)

        with patch.object(config, "ENERANDES_EXCEL", archivo_excel):
            enerandes.extraer()

        for nombre_hoja, nombre_salida in (
            ("Ventas 2023", "enerandes_ventas_2023"),
            ("Ventas 2024", "enerandes_ventas_2024"),
        ):
            with self.subTest(hoja=nombre_hoja):
                original = pd.read_excel(
                    archivo_excel,
                    sheet_name=nombre_hoja,
                    header=None,
                    dtype=str,
                )
                original.columns = [f"col_{i}" for i in range(original.shape[1])]
                resultado = pd.read_parquet(config.DIR_BRONZE / f"{nombre_salida}.parquet")
                pd.testing.assert_frame_equal(
                    resultado[original.columns],
                    original,
                    check_dtype=True,
                )
                self.assertEqual(resultado["_fuente"].unique().tolist(), ["EnerAndes"])
                self.assertEqual(
                    resultado["_origen"].unique().tolist(),
                    [f"{archivo_excel.name}#{nombre_hoja}"],
                )


if __name__ == "__main__":
    unittest.main()
