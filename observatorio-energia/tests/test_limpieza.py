"""
Pruebas automaticas de la capa plata (reglas de limpieza de EnerAndes).

Cada prueba es una funcion que empieza por test_. Prepara unos datos de
ejemplo pequenos, ejecuta una funcion del proyecto y comprueba con assert
que el resultado es el esperado. No necesitan internet ni los archivos de
data/: se ejecutan en segundos.

Uso:
    python -m pytest -v
"""
# ---------------------------------------------------------------------------
# IMPORTS
# ---------------------------------------------------------------------------
import pandas as pd     # pandas: para armar una tabla de ejemplo
import pandera.errors   # los errores que lanza pandera cuando una regla falla
import pytest           # pytest: la libreria que encuentra y ejecuta las pruebas

from src.quality.esquemas import ESQUEMA_VENTAS               # el esquema de la capa plata
from src.silver.enerandes import clave_municipio, limpiar, sin_tildes   # lo que se prueba


# ---------------------------------------------------------------------------
# DATOS DE EJEMPLO
# ---------------------------------------------------------------------------
def hoja_de_ejemplo() -> pd.DataFrame:
    """Una hoja 2023 en miniatura, como queda en bronce: encabezado como fila,
    una fila repetida, una energia negativa y la fila TOTAL."""
    # Una lista de listas: cada lista de adentro es una fila de la hoja.
    # Todo va entre comillas (texto), como llega del Excel; None es una celda vacia
    filas = [
        ["Fecha", "Municipio", "Segmento", "Tipo_Compra", "Energia_kWh", "Valor_COP", "Clientes"],
        ["2023-01", "Medellín", "Residencial", "Contrato", "1000", "900000", "10"],
        ["2023-01", "Medellín", "Residencial", "Contrato", "1000", "900000", "10"],   # repetida
        ["2023-01", "ITAGUI", "RESID.", "bolsa", "500", "450000", "5"],
        ["2023-02", "Rio Negro", "IND", "CONTRATOS", "-300", "270000", "2"],         # negativa
        ["TOTAL", None, None, None, "1200", "1620000", "17"],                        # total
    ]
    # pd.DataFrame(filas, columns=...) convierte la lista en una tabla.
    # [f"col_{i}" for i in range(7)] arma los nombres col_0 ... col_6, igual que en bronce
    return pd.DataFrame(filas, columns=[f"col_{i}" for i in range(7)])


# ---------------------------------------------------------------------------
# PRUEBAS
# ---------------------------------------------------------------------------
def test_sin_tildes_quita_tildes_mayusculas_y_espacios():
    # assert A == B: si A es igual a B, sigue; si no, la prueba falla.
    # Con espacios, mayusculas y tildes -> todo limpio
    assert sin_tildes(" ITAGÜÍ ") == "itagui"
    # Con una sola tilde -> sin tilde y en minuscula
    assert sin_tildes("Medellín") == "medellin"


def test_clave_municipio_resuelve_los_alias():
    # Un alias de la lista ALIAS_MUNICIPIO -> su clave
    assert clave_municipio("Rio Negro") == "rionegro"
    # Otro alias, con tilde y mayusculas -> su clave
    assert clave_municipio("Medellín D.E.") == "medellin"
    # Celda vacia -> None. "is None" pregunta si no tiene valor
    assert clave_municipio(None) is None


def test_limpiar_quita_encabezado_total_y_duplicados():
    # Ejecuta la limpieza completa sobre la hoja en miniatura;
    # limpiar() devuelve tres cosas y se reciben en tres variables
    limpias, cuarentena, metricas = limpiar(hoja_de_ejemplo())
    # len(limpias) es el numero de filas.
    # 5 filas de datos - 1 TOTAL - 1 repetida - 1 negativa = 2 limpias
    assert len(limpias) == 2
    # .values son los valores de la columna periodo; "not in" pregunta que NO este
    assert "TOTAL" not in limpias["periodo"].values


def test_limpiar_unifica_valores_y_pone_divipola():
    # El _ recibe lo que esta prueba no necesita (cuarentena y metricas)
    limpias, _, _ = limpiar(hoja_de_ejemplo())
    # limpias["municipio"] == "Itagüí" da True en las filas de Itagui;
    # limpias[...] deja solo esas filas; .iloc[0] toma la primera (posicion 0)
    itagui = limpias[limpias["municipio"] == "Itagüí"].iloc[0]
    # 'ITAGUI' recibio su codigo DIVIPOLA
    assert itagui["divipola"] == "05360"
    # 'RESID.' quedo como 'Residencial'
    assert itagui["segmento"] == "Residencial"
    # 'bolsa' quedo como 'Bolsa'
    assert itagui["tipo_compra"] == "Bolsa"


def test_energia_negativa_va_a_cuarentena():
    # Esta prueba solo necesita la cuarentena: lo demas va a _
    _, cuarentena, _ = limpiar(hoja_de_ejemplo())
    # Solo una fila tenia energia negativa
    assert len(cuarentena) == 1
    # .iloc[0] es la primera fila de la cuarentena; su energia es -300
    assert cuarentena.iloc[0]["energia_kwh"] == -300


def test_pandera_rechaza_un_tipo_de_compra_invalido():
    limpias, _, _ = limpiar(hoja_de_ejemplo())
    # .loc[0, "tipo_compra"] es la celda de la fila 0, columna tipo_compra;
    # se le pone a proposito un valor que no esta permitido
    limpias.loc[0, "tipo_compra"] = "CONTRATOS"
    # with pytest.raises(...): la prueba ESPERA ese error dentro del bloque.
    # Si pandera lanza SchemaErrors, la prueba pasa; si no lo lanza, falla
    with pytest.raises(pandera.errors.SchemaErrors):
        # Revisa la tabla danada con las reglas de pandera
        ESQUEMA_VENTAS.validate(limpias, lazy=True)
