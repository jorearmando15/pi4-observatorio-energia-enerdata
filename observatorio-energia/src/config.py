"""
Configuracion central del pipeline.
Todo lo que puede cambiar (fechas, URLs, rutas) vive AQUI y no regado en el codigo.
Si hay que cambiar una fecha o una URL, se cambia en este archivo y en ningun otro.
"""
# ---------------------------------------------------------------------------
# IMPORTS (traer codigo que ya existe)
# ---------------------------------------------------------------------------
from datetime import date   # datetime: libreria de Python para fechas y horas.
                            # date sirve para escribir una fecha: date(2026, 1, 1)
from pathlib import Path    # pathlib: libreria de Python para manejar rutas de
                            # carpetas y archivos sin preocuparse por / o \

# --- Rango de fechas a extraer --------------------------------------------
# Para la clase usamos 2026 (rapido). Para el proyecto, amplien a 2023-01-01.
FECHA_INICIO = date(2024, 1, 1)     # primer dia que se descarga
FECHA_FIN = date(2026, 9, 30)       # ultimo dia que se descarga

# --- Rutas (relativas a la raiz del proyecto) ------------------------------
# __file__ es la ruta de ESTE archivo (src/config.py).
# .resolve() la vuelve ruta completa; .parent sube una carpeta.
# Dos veces .parent: de src/config.py sube a src/ y luego a la raiz del proyecto.
RAIZ = Path(__file__).resolve().parent.parent
DIR_INSUMOS = RAIZ / "data" / "insumos"     # el operador / une partes de una ruta
DIR_BRONZE = RAIZ / "data" / "bronze"       # aqui se guardan los datos descargados

# --- Fuente 1: API de XM (mercado electrico) -------------------------------
XM_URL = "https://servapibi.xm.com.co/{periodo}"   # periodo: hourly | daily | lists
XM_MAX_DIAS = 30                                    # la API no acepta rangos mas largos
XM_METRICAS = [
    # Lista de tuplas. Cada tupla es una metrica a descargar:
    # (MetricId, Entity, periodo, nombre del archivo en bronce)
    ("PrecBolsNaci", "Sistema", "hourly", "xm_precio_bolsa"),   # precio de bolsa por hora
    ("DemaReal", "Sistema", "hourly", "xm_demanda"),            # demanda real por hora
    ("PorcVoluUtilDiar", "Sistema", "daily", "xm_embalses"),    # % de embalses por dia
    ("Gene", "Recurso", "hourly", "xm_generacion"),             # generacion por planta
    ("AporEner", "Sistema", "daily", "xm_aportes"),             # aportes hidricos
]

# Catalogos: endpoint "lists", sin ventana de fechas y con otra estructura (ListEntities).
# (MetricId, Entity, nombre del archivo en bronce)
XM_LISTADOS = [
    ("ListadoRecursos", "Sistema", "xm_listado_recursos"),
]

# --- Fuente 2: IDEAM en datos.gov.co (API Socrata / SoQL) ------------------
IDEAM_URL = "https://www.datos.gov.co/resource/s54a-sgyg.json"   # precipitacion
IDEAM_DEPARTAMENTO = "ANTIOQUIA"
IDEAM_DIAS_VENTANA = 7          # pedir de a una semana evita timeouts del servidor
# El IDEAM es la fuente MAS LENTA (5 a 30 s por semana). Para la clase pedimos
# solo jun-sep 2026. Para el proyecto, usen el mismo rango de las demas fuentes.
IDEAM_FECHA_INICIO = date(2026, 6, 1)

# --- Fuente 3: NOAA, indice de El Nino (archivo de texto) ------------------
NOAA_ONI_URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

# --- Fuente 4: archivo interno de EnerAndes (Excel) ------------------------
ENERANDES_EXCEL = DIR_INSUMOS / "ventas_enerandes_2023_2026.xlsx"

# --- Comportamiento HTTP ---------------------------------------------------
HTTP_TIMEOUT = 120      # segundos que se espera una respuesta antes de rendirse
HTTP_REINTENTOS = 4     # intentos ante fallas de red o del servidor
