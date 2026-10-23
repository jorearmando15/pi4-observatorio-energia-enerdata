"""
Tests de integración liviana para el pipeline.

Verifica que extraer_metrica() OMITA la descarga cuando el archivo
ya existe en bronce y forzar=False.
"""
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from datetime import date

import src.config as config
from src.extract.xm import extraer_metrica


class TestPipelineIdempotencia:
    """Prueba que el pipeline omite archivos ya existentes."""

    def test_omite_archivo_existente(self, tmp_path):
        """
        Si el parquet ya existe y forzar=False, extraer_metrica()
        no debe hacer ninguna llamada HTTP.
        """
        # Redirigir DIR_BRONZE a un directorio temporal con el archivo "ya descargado"
        original_bronze = config.DIR_BRONZE
        config.DIR_BRONZE = tmp_path
        (tmp_path / "xm_test.parquet").write_bytes(b"dummy")

        try:
            with patch("src.utils.http_json") as mock_http:
                extraer_metrica(
                    metrica="PrecBolsNaci",
                    entidad="Sistema",
                    periodo="hourly",
                    nombre="xm_test",
                    forzar=False,
                )
                # No debe haberse llamado a la API
                mock_http.assert_not_called()
        finally:
            config.DIR_BRONZE = original_bronze

    def test_descarga_si_no_existe(self, tmp_path):
        """
        Si el parquet NO existe, extraer_metrica() debe llamar a la API
        al menos una vez.
        """
        original_bronze = config.DIR_BRONZE
        original_inicio = config.FECHA_INICIO
        original_fin    = config.FECHA_FIN

        config.DIR_BRONZE   = tmp_path
        config.FECHA_INICIO = date(2026, 1, 1)
        config.FECHA_FIN    = date(2026, 1, 5)  # rango pequeño → 1 sola ventana

        respuesta_fake = {
            "Items": [
                {
                    "Date": "2026-01-01",
                    "HourlyEntities": [
                        {"Id": "Sistema", "Values": {"Hour01": 100.0}}
                    ],
                }
            ]
        }

        try:
            with patch("src.extract.xm.http_json", return_value=respuesta_fake) as mock_http, \
                 patch("src.extract.xm.guardar_bronce") as mock_guardar:
                extraer_metrica(
                    metrica="PrecBolsNaci",
                    entidad="Sistema",
                    periodo="hourly",
                    nombre="xm_nueva",
                    forzar=False,
                )
                mock_http.assert_called_once()
                mock_guardar.assert_called_once()
        finally:
            config.DIR_BRONZE   = original_bronze
            config.FECHA_INICIO = original_inicio
            config.FECHA_FIN    = original_fin

    def test_forzar_descarga_aunque_exista(self, tmp_path):
        """
        Incluso si el parquet existe, forzar=True debe provocar
        que se llame a la API.
        """
        original_bronze = config.DIR_BRONZE
        original_inicio = config.FECHA_INICIO
        original_fin    = config.FECHA_FIN

        config.DIR_BRONZE   = tmp_path
        config.FECHA_INICIO = date(2026, 1, 1)
        config.FECHA_FIN    = date(2026, 1, 5)

        # Archivo ya existe
        (tmp_path / "xm_existente.parquet").write_bytes(b"dummy")

        respuesta_fake = {
            "Items": [
                {
                    "Date": "2026-01-01",
                    "HourlyEntities": [
                        {"Id": "Sistema", "Values": {"Hour01": 99.0}}
                    ],
                }
            ]
        }

        try:
            with patch("src.extract.xm.http_json", return_value=respuesta_fake) as mock_http, \
                 patch("src.extract.xm.guardar_bronce"):
                extraer_metrica(
                    metrica="PrecBolsNaci",
                    entidad="Sistema",
                    periodo="hourly",
                    nombre="xm_existente",
                    forzar=True,
                )
                mock_http.assert_called_once()
        finally:
            config.DIR_BRONZE   = original_bronze
            config.FECHA_INICIO = original_inicio
            config.FECHA_FIN    = original_fin
