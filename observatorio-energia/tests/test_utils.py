"""
Tests para src/utils.py.

Cubre:
  - ventanas(): partición de rango de fechas en bloques
  - ya_existe(): idempotencia (omitir archivos existentes)
"""
from datetime import date, timedelta
from unittest.mock import patch

import pytest

from src.utils import ventanas, ya_existe


# ---------------------------------------------------------------------------
# ventanas()
# ---------------------------------------------------------------------------

class TestVentanas:
    """Pruebas para la función ventanas()."""

    def test_rango_menor_que_bloque(self):
        """Si el rango es menor que el bloque, devuelve un único par."""
        inicio = date(2026, 1, 1)
        fin    = date(2026, 1, 10)  # 10 días < bloque de 30
        resultado = list(ventanas(inicio, fin, 30))
        assert resultado == [(inicio, fin)]

    def test_rango_exactamente_un_bloque(self):
        """Rango exactamente igual al tamaño del bloque → un solo par."""
        inicio = date(2026, 1, 1)
        fin    = date(2026, 1, 30)  # exactamente 30 días
        resultado = list(ventanas(inicio, fin, 30))
        assert len(resultado) == 1
        assert resultado[0] == (inicio, fin)

    def test_multiples_ventanas(self):
        """Rango mayor que el bloque genera varios pares consecutivos."""
        inicio = date(2026, 1, 1)
        fin    = date(2026, 3, 31)  # ~90 días → 3 ventanas de 30 días
        resultado = list(ventanas(inicio, fin, 30))
        assert len(resultado) == 3

    def test_ventanas_contiguas_sin_solapamiento(self):
        """El día final de una ventana + 1 es el día inicial de la siguiente."""
        inicio = date(2026, 1, 1)
        fin    = date(2026, 4, 30)
        pares  = list(ventanas(inicio, fin, 30))
        for i in range(len(pares) - 1):
            _, fin_actual       = pares[i]
            inicio_siguiente, _ = pares[i + 1]
            assert inicio_siguiente == fin_actual + timedelta(days=1)

    def test_ultima_ventana_no_supera_fin(self):
        """El último par nunca debe superar la fecha de fin."""
        inicio = date(2026, 1, 1)
        fin    = date(2026, 2, 10)  # no es múltiplo exacto de 30
        pares  = list(ventanas(inicio, fin, 30))
        assert pares[-1][1] == fin

    def test_inicio_igual_a_fin(self):
        """Un rango de un solo día genera exactamente un par (mismo día)."""
        dia = date(2026, 6, 15)
        resultado = list(ventanas(dia, dia, 30))
        assert resultado == [(dia, dia)]


# ---------------------------------------------------------------------------
# ya_existe()
# ---------------------------------------------------------------------------

class TestYaExiste:
    """Pruebas para la función ya_existe() (idempotencia del pipeline)."""

    def test_archivo_no_existe_devuelve_false(self, tmp_path):
        """Si el parquet no existe, ya_existe debe devolver False."""
        import src.config as config
        original = config.DIR_BRONZE
        config.DIR_BRONZE = tmp_path
        try:
            assert ya_existe("metrica_inexistente", forzar=False) is False
        finally:
            config.DIR_BRONZE = original

    def test_archivo_existe_sin_forzar_devuelve_true(self, tmp_path):
        """Si el parquet existe y forzar=False, ya_existe devuelve True (se omite)."""
        import src.config as config
        original = config.DIR_BRONZE
        config.DIR_BRONZE = tmp_path
        (tmp_path / "mi_metrica.parquet").write_bytes(b"dummy")
        try:
            assert ya_existe("mi_metrica", forzar=False) is True
        finally:
            config.DIR_BRONZE = original

    def test_archivo_existe_con_forzar_devuelve_false(self, tmp_path):
        """Si el parquet existe pero forzar=True, ya_existe devuelve False (re-descarga)."""
        import src.config as config
        original = config.DIR_BRONZE
        config.DIR_BRONZE = tmp_path
        (tmp_path / "mi_metrica.parquet").write_bytes(b"dummy")
        try:
            assert ya_existe("mi_metrica", forzar=True) is False
        finally:
            config.DIR_BRONZE = original
