"""Pruebas de src/extract/trm.py con la red SIMULADA."""
from datetime import date

import pandas as pd

from src import config
from src.extract import trm


def test_consulta_filtra_por_fechas_en_el_servidor():
    q = trm.consulta_soql(date(2024, 1, 1), date(2026, 9, 30), 0)
    assert "2024-01-01T00:00:00" in q["$where"] and "2026-09-30T23:59:59" in q["$where"]
    assert q["$order"] == trm.CAMPO_FECHA and q["$offset"] == 0


def test_extraer_guarda_la_trm_en_bronce_y_omite_si_ya_existe(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DIR_BRONZE", tmp_path)
    llamadas = []

    def falso_http_json(metodo, url, params=None, **kwargs):
        llamadas.append(params["$offset"])
        return [{"valor": "3950.5", "vigenciadesde": "2024-01-01T00:00:00.000"}]

    monkeypatch.setattr(trm, "http_json", falso_http_json)
    trm.extraer(forzar=False)
    df = pd.read_parquet(tmp_path / "trm_diaria.parquet")
    assert df["valor"].iloc[0] == "3950.5" and df["_fuente"].iloc[0].startswith("TRM")
    trm.extraer(forzar=False)                    # segunda vez: idempotente
    assert len(llamadas) == 1
