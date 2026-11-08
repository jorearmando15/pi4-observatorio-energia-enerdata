"""Pruebas del orquestador de las capas plata y oro."""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src import config, transformar


def test_main_ejecuta_plata_antes_de_dbt(monkeypatch):
    orden = []
    ejecutable = Path("dbt")
    ejecutar_plata = Mock(side_effect=lambda: orden.append("plata"))

    def ejecutar_dbt(*args, **kwargs):
        orden.append("dbt")
        return SimpleNamespace(returncode=0)

    ejecutar_dbt_mock = Mock(side_effect=ejecutar_dbt)
    monkeypatch.setattr(transformar.pipeline_plata, "main", ejecutar_plata)
    monkeypatch.setattr(transformar, "_buscar_ejecutable_dbt", lambda: ejecutable)
    monkeypatch.setattr(transformar.subprocess, "run", ejecutar_dbt_mock)

    assert transformar.main() == 0

    assert orden == ["plata", "dbt"]
    ejecutar_dbt_mock.assert_called_once_with(
        [
            str(ejecutable),
            "build",
            "--project-dir",
            str(config.RAIZ / "dbt"),
            "--profiles-dir",
            str(config.RAIZ / "dbt"),
        ],
        cwd=config.RAIZ,
        check=False,
    )


def test_main_no_ejecuta_dbt_si_falla_plata(monkeypatch):
    error = ValueError("falló la validación Pandera")
    ejecutar_dbt = Mock()
    monkeypatch.setattr(
        transformar.pipeline_plata,
        "main",
        Mock(side_effect=error),
    )
    monkeypatch.setattr(transformar.subprocess, "run", ejecutar_dbt)

    with pytest.raises(ValueError, match="falló la validación Pandera"):
        transformar.main()

    ejecutar_dbt.assert_not_called()


def test_main_devuelve_el_codigo_de_error_de_dbt(monkeypatch):
    monkeypatch.setattr(transformar.pipeline_plata, "main", Mock())
    monkeypatch.setattr(transformar, "_buscar_ejecutable_dbt", lambda: Path("dbt"))
    monkeypatch.setattr(
        transformar.subprocess,
        "run",
        Mock(return_value=Mock(returncode=1)),
    )

    assert transformar.main() == 1


def test_main_reporta_si_no_encuentra_dbt(monkeypatch):
    monkeypatch.setattr(transformar.pipeline_plata, "main", Mock())
    monkeypatch.setattr(
        transformar,
        "_buscar_ejecutable_dbt",
        Mock(side_effect=FileNotFoundError("dbt no encontrado")),
    )

    with pytest.raises(FileNotFoundError, match="dbt no encontrado"):
        transformar.main()
