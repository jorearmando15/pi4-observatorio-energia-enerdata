"""
Tests de la Evidencia 3: el workflow de GitHub Actions y la seguridad.
Leen .github/workflows/pipeline.yml y comprueban que cumple lo pedido.
"""
from pathlib import Path

import pytest
import yaml

# tests/ -> observatorio-energia/ -> raiz del repositorio
RAIZ_PROYECTO = Path(_file_).resolve().parents[1]
RAIZ_REPO = RAIZ_PROYECTO.parent
WORKFLOW = RAIZ_REPO / ".github" / "workflows" / "pipeline.yml"

pytestmark = pytest.mark.skipif(not WORKFLOW.exists(), reason="no se encontro pipeline.yml")


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))


def _disparadores(workflow: dict) -> dict:
    # PyYAML lee la clave "on" como el booleano True
    return workflow.get("on") or workflow.get(True)


def _pasos(workflow: dict) -> list:
    return workflow["jobs"]["pipeline"]["steps"]


def test_workflow_corre_a_diario_y_a_mano(workflow):
    disparadores = _disparadores(workflow)
    assert "workflow_dispatch" in disparadores
    campos = disparadores["schedule"][0]["cron"].split()
    assert len(campos) == 5
    # dia del mes, mes y dia de la semana en "*" = todos los dias
    assert campos[2:] == ["", "", "*"]


def test_workflow_ejecuta_el_pipeline_completo_en_orden(workflow):
    comandos = [p["run"] for p in _pasos(workflow) if "run" in p]
    esperado = ["src.pipeline", "src.silver.enerandes", "dbt build", "pytest", "src.exportar_oro"]
    posiciones = []
    for fragmento in esperado:
        indices = [i for i, c in enumerate(comandos) if fragmento in c]
        assert indices, f"falta el paso que ejecuta {fragmento}"
        posiciones.append(indices[0])
    # bronce -> plata -> oro -> pruebas -> exportar
    assert posiciones == sorted(posiciones)


def test_workflow_publica_la_capa_oro_como_artefacto(workflow):
    publicar = [p for p in _pasos(workflow)
                if str(p.get("uses", "")).startswith("actions/upload-artifact")]
    assert publicar, "falta el paso con actions/upload-artifact"
    assert publicar[0]["with"]["path"].rstrip("/").endswith("data/gold")


def test_env_ignorado_y_workflow_sin_claves():
    ignorados = (RAIZ_PROYECTO / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert ".env" in [linea.strip() for linea in ignorados]
    texto = WORKFLOW.read_text(encoding="utf-8").lower()
    for palabra in ("password:", "api_key:", "token:"):
        assert palabra not in texto