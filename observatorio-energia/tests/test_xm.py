"""
Tests para src/extract/xm.py.

Cubre:
  - aplanar(): convierte JSON anidado de XM en lista de filas planas
  - aplanar_listado(): aplana respuestas del endpoint "lists" (catalogos)
"""

from src.extract.xm import aplanar, aplanar_listado


# ---------------------------------------------------------------------------
# aplanar()  — datos hourly
# ---------------------------------------------------------------------------

class TestAplanarHourly:
    """Pruebas de aplanar() con periodo='hourly'."""

    def _respuesta_hourly(self):
        """Respuesta mínima válida de la API XM (hourly)."""
        return {
            "Items": [
                {
                    "Date": "2026-01-01",
                    "HourlyEntities": [
                        {
                            "Id": "Sistema",
                            "Values": {
                                "Hour01": 100.0,
                                "Hour02": 110.0,
                            },
                        }
                    ],
                }
            ]
        }

    def test_devuelve_lista_no_vacia(self):
        """aplanar() con datos hourly debe devolver al menos una fila."""
        filas = aplanar(self._respuesta_hourly(), "hourly")
        assert isinstance(filas, list)
        assert len(filas) > 0

    def test_fila_contiene_date_e_id(self):
        """Cada fila debe tener las claves 'Date' e 'Id'."""
        filas = aplanar(self._respuesta_hourly(), "hourly")
        for fila in filas:
            assert "Date" in fila
            assert "Id" in fila

    def test_fila_contiene_valores_de_horas(self):
        """Las horas (Hour01, Hour02, ...) deben aparecer en la fila."""
        filas = aplanar(self._respuesta_hourly(), "hourly")
        assert "Hour01" in filas[0]
        assert "Hour02" in filas[0]

    def test_date_e_id_correctos(self):
        """Los valores de Date e Id deben coincidir con el JSON de entrada."""
        filas = aplanar(self._respuesta_hourly(), "hourly")
        assert filas[0]["Date"] == "2026-01-01"
        assert filas[0]["Id"] == "Sistema"


# ---------------------------------------------------------------------------
# aplanar()  — datos daily
# ---------------------------------------------------------------------------

class TestAplanarDaily:
    """Pruebas de aplanar() con periodo='daily'."""

    def _respuesta_daily(self):
        """Respuesta mínima válida de la API XM (daily)."""
        return {
            "Items": [
                {
                    "Date": "2026-01-01",
                    "DailyEntities": [
                        {"Id": "Sistema", "Value": 75.5}
                    ],
                }
            ]
        }

    def test_devuelve_lista_no_vacia(self):
        """aplanar() con datos daily debe devolver al menos una fila."""
        filas = aplanar(self._respuesta_daily(), "daily")
        assert len(filas) > 0

    def test_fila_tiene_date_id_value(self):
        """Cada fila daily debe tener exactamente Date, Id y Value."""
        filas = aplanar(self._respuesta_daily(), "daily")
        assert filas[0]["Date"] == "2026-01-01"
        assert filas[0]["Id"] == "Sistema"
        assert filas[0]["Value"] == 75.5

    def test_multiples_entidades(self):
        """Con varias entidades en un mismo día, se generan múltiples filas."""
        respuesta = {
            "Items": [
                {
                    "Date": "2026-01-01",
                    "DailyEntities": [
                        {"Id": "A", "Value": 10.0},
                        {"Id": "B", "Value": 20.0},
                        {"Id": "C", "Value": 30.0},
                    ],
                }
            ]
        }
        filas = aplanar(respuesta, "daily")
        assert len(filas) == 3
        ids = [f["Id"] for f in filas]
        assert ids == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# aplanar()  — respuesta vacía
# ---------------------------------------------------------------------------

class TestAplanarVacia:
    """aplanar() debe manejar respuestas vacías sin errores."""

    def test_items_vacio(self):
        """Si 'Items' está vacío, devuelve lista vacía."""
        filas = aplanar({"Items": []}, "hourly")
        assert filas == []

    def test_sin_clave_items(self):
        """Si la respuesta no trae 'Items', devuelve lista vacía (sin excepción)."""
        filas = aplanar({}, "hourly")
        assert filas == []


# ---------------------------------------------------------------------------
# aplanar_listado()  — nuevo endpoint "lists"
# ---------------------------------------------------------------------------

class TestAplanarListado:
    """Pruebas para la nueva función aplanar_listado() (catálogos de XM)."""

    def _respuesta_listado(self):
        """Respuesta mínima válida del endpoint lists de XM."""
        return {
            "Items": [
                {
                    "Date": "2026-09-30",
                    "ListEntities": [
                        {"Id": "BETANIA", "Values": {"Tipo": "Hidro", "Capacidad": 540.0}},
                        {"Id": "CHIVOR",  "Values": {"Tipo": "Hidro", "Capacidad": 1000.0}},
                    ],
                }
            ]
        }

    def test_devuelve_lista_no_vacia(self):
        """aplanar_listado() debe devolver al menos una fila con datos reales."""
        filas = aplanar_listado(self._respuesta_listado())
        assert isinstance(filas, list)
        assert len(filas) > 0

    def test_fila_contiene_id_y_values(self):
        """Cada fila debe incluir 'Id' y los campos de 'Values' desempacados."""
        filas = aplanar_listado(self._respuesta_listado())
        assert filas[0]["Id"] == "BETANIA"
        assert filas[0]["Tipo"] == "Hidro"
        assert filas[0]["Capacidad"] == 540.0

    def test_numero_de_filas_correcto(self):
        """Con 2 entidades en un item, se generan 2 filas."""
        filas = aplanar_listado(self._respuesta_listado())
        assert len(filas) == 2

    def test_sin_items_devuelve_lista_vacia(self):
        """Si no hay 'Items', devuelve lista vacía sin lanzar excepción."""
        assert aplanar_listado({}) == []

    def test_item_sin_date_no_falla(self):
        """Si el item no trae 'Date', la función igual produce la fila sin ese campo."""
        respuesta = {
            "Items": [
                {
                    # Sin clave "Date"
                    "ListEntities": [
                        {"Id": "GUATRON", "Values": {"Tipo": "Termica"}}
                    ]
                }
            ]
        }
        filas = aplanar_listado(respuesta)
        assert len(filas) == 1
        assert "Date" not in filas[0]
        assert filas[0]["Id"] == "GUATRON"
