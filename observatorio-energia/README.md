# Observatorio Energía y Clima – Equipo <nombre>

> Proyecto Integrado IV – Integración de Información · IU Digital de Antioquia · 2026-2

## 👥 Integrante

| Nombre | Usuario GitHub | Rol |
|---|---|---|
| Jorge Rodriguez | @jorgerodriguezdev | Líder técnico / Data Engineer |
| Yusep Ruiz | @yusepruiz | Data Quality Analyst | 
| Lina Johana Seguro | LinaSeguro | Analytics Engineer |
| Raul Niño | Buclex | BI Analyst / Storyteller |


## 🎯 Objetivo

Integrar datos del mercado eléctrico (XM), del clima (IDEAM y NOAA) y de ventas internas (EnerAndes) para analizar el riesgo energético de Colombia ante El Niño 2026.

## 📦 Fuentes de datos (capa bronce)

| Fuente | Tipo | Archivo en data/bronze/ |
|---|---|---|
| XM – API Sinergox | API REST (POST, JSON) | xm_precio_bolsa, xm_demanda, xm_embalses, xm_generacion, xm_aportes, xm_listado_recursos |
| IDEAM – datos.gov.co | API Socrata (SoQL) | ideam_precipitacion_diaria, ideam_temperatura_diaria |
| NOAA – índice ONI | Archivo de texto | noaa_oni |
| EnerAndes | Excel interno | enerandes_ventas_2023 … enerandes_ventas_2026 |
| *TRM – Banco de la República (fuente propia)* | API Socrata (SoQL) | trm_diaria |

### Fuente propia: TRM (Tasa de Cambio Representativa del Mercado)

- *Qué es:* el valor oficial diario del dólar en pesos colombianos (USD/COP).
- *De dónde viene:* portal de datos abiertos datos.gov.co, dataset "TRM – Banco de la República, tasa de cambio diaria" (32sa-8pi3), consultado con SoQL y filtrado por fechas en el servidor.
- *Para qué la usamos:* en un año de El Niño baja la generación hidráulica y el sistema recurre más a plantas térmicas, cuyos combustibles se cotizan en dólares. Cruzaremos la TRM con el precio de bolsa de XM para analizar cuánto del costo de la energía se explica por el tipo de cambio.


## ⚙️ Cómo ejecutar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# copiar ventas_enerandes_2023_2026.xlsx en data/insumos/
python -m src.pipeline          # descarga las 4 fuentes a data/bronze/ (unos 3 minutos)
python -m src.consultar         # consultas SQL de BI con DuckDB
```

Para volver a descargar todo: `python -m src.pipeline --forzar`. El rango de fechas se cambia en `src/config.py`.

## 🏗️ Arquitectura

```
Fuentes -> BRONCE (dato tal cual + linaje) -> PLATA (limpio) -> ORO (modelo estrella) -> Dashboard
```

## 🤖 Uso de IA

(Declarar aquí qué herramientas de IA se usaron y para qué.)
