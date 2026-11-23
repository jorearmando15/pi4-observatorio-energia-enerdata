"""
Los DATOS y los CALCULOS del dashboard.

Lee las tablas de la capa oro (data/gold/*.parquet) y calcula lo que necesitan
las preguntas de negocio. Esta separado de app.py para poder PROBARLO con
pytest (tests/test_dashboard.py) sin abrir la pagina.
"""
# Path: para armar rutas de archivos que funcionan en Windows, Mac y Linux
from pathlib import Path

# pandas: tablas en memoria (DataFrames)
import pandas as pd

# La carpeta de la capa oro: dos niveles arriba de este archivo (la raiz) + data/gold
CARPETA_ORO = Path(__file__).resolve().parent.parent / "data" / "gold"


def cargar(tabla: str) -> pd.DataFrame:
    """Lee una tabla de la capa oro. Ejemplo: cargar("fact_mercado_mensual")."""
    # La ruta del archivo: data/gold/<tabla>.parquet
    df = pd.read_parquet(CARPETA_ORO / f"{tabla}.parquet")
    # Las columnas de fecha llegan como objetos 'date': se pasan a fechas de pandas
    # para poder filtrarlas y graficarlas (por ejemplo, mes >= '2023-01-01')
    for columna in ("mes", "fecha"):
        if columna in df.columns:
            df[columna] = pd.to_datetime(df[columna])
    return df


def ventas_con_nombres() -> pd.DataFrame:
    """Las ventas con el nombre del municipio y del segmento (une el hecho con sus dimensiones)."""
    # merge = join: une por la llave. Igual que un JOIN de SQL
    return (cargar("fact_ventas_mensual")
            .merge(cargar("dim_municipio"), on="municipio_id")
            .merge(cargar("dim_segmento"), on="segmento_id"))


def costos_de_compra(ventas: pd.DataFrame, mercado: pd.DataFrame) -> pd.DataFrame:
    """
    Pregunta 5: cuanto cuesta la energia de cada venta si se compra en BOLSA
    o por CONTRATO, con los precios reales de XM del mismo mes.

    ventas:  necesita mes_id, tipo_compra y energia_kwh
    mercado: necesita mes_id, precio_bolsa_cop_kwh y precio_contrato_cop_kwh
    Devuelve las ventas con 3 columnas nuevas, en pesos:
      costo_bolsa:    la energia x el precio de bolsa del mes
      costo_contrato: la energia x el precio de contrato del mes
      sobrecosto:     costo_bolsa - costo_contrato (positivo = la bolsa salio mas cara)
    """
    # Trae a cada venta los dos precios de su mes
    df = ventas.merge(mercado[["mes_id", "precio_bolsa_cop_kwh", "precio_contrato_cop_kwh"]],
                      on="mes_id", how="left")
    # kWh x COP/kWh = COP
    df["costo_bolsa"] = df["energia_kwh"] * df["precio_bolsa_cop_kwh"]
    df["costo_contrato"] = df["energia_kwh"] * df["precio_contrato_cop_kwh"]
    df["sobrecosto"] = df["costo_bolsa"] - df["costo_contrato"]
    return df


def correlacion_por_rezago(df: pd.DataFrame, causa: str, efecto: str, max_meses: int = 6) -> pd.DataFrame:
    """
    Pregunta 2: con cuantos meses de rezago se nota la CAUSA (por ejemplo, el ONI)
    en el EFECTO (por ejemplo, el precio de bolsa).

    Para cada rezago k = 0, 1, ..., max_meses compara la causa de hace k meses
    con el efecto de hoy. La correlacion va de -1 a 1: cerca de 1 = suben juntos.
    df debe estar ordenado por mes, una fila por mes.
    """
    filas = []
    for k in range(max_meses + 1):
        # shift(k): corre la columna k filas hacia abajo = el valor de hace k meses
        r = df[causa].shift(k).corr(df[efecto])
        filas.append({"rezago_meses": k, "correlacion": round(r, 2)})
    return pd.DataFrame(filas)


def demanda_por(df: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Pregunta 4: la demanda promedio por hora, por dia de la semana o por mes, en MWh."""
    # groupby: agrupa por la columna y saca el promedio de la demanda en cada grupo
    resultado = df.groupby(columna, as_index=False)["demanda_kwh"].mean()
    # kWh -> MWh, para que los numeros sean mas cortos
    resultado["demanda_mwh"] = (resultado["demanda_kwh"] / 1000).round(0)
    return resultado[[columna, "demanda_mwh"]]


def generacion_vs_oni(generacion: pd.DataFrame, mercado: pd.DataFrame) -> pd.DataFrame:
    """
    Pregunta propia: la matriz de generacion mes a mes junto al ONI.

    generacion: fact_generacion_mensual (mes, tipo, participacion_pct)
    mercado:    fact_mercado_mensual (mes, oni, fase_enso)
    Devuelve una fila por mes con una columna por tipo de planta
    (hidraulica_pct, termica_pct, ...) mas el ONI y la fase ENSO.
    """
    # pivot: los tipos pasan de filas a columnas (una columna por tipo)
    ancho = (generacion.pivot_table(index="mes", columns="tipo",
                                    values="participacion_pct", aggfunc="sum")
             .fillna(0.0)
             .reset_index())
    # 'HIDRAULICA' -> 'hidraulica_pct', para nombres comodos en el dashboard
    ancho = ancho.rename(columns={c: f"{c.lower()}_pct" for c in ancho.columns if c != "mes"})

    # Trae el ONI y la fase del mismo mes. Si un mes no tiene ONI, queda "Sin dato"
    df = ancho.merge(mercado[["mes", "oni", "fase_enso"]], on="mes", how="left")
    df["fase_enso"] = df["fase_enso"].fillna("Sin dato")
    return df.sort_values("mes").reset_index(drop=True)


def matriz_por_fase(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pregunta propia: participacion promedio de cada tipo de planta en cada fase ENSO.

    df: la salida de generacion_vs_oni.
    Devuelve una fila por fase, ordenada El Nino -> Neutral -> La Nina.
    """
    tipos = [c for c in df.columns if c.endswith("_pct")]
    # "Sin dato" no es una fase: se excluye del promedio
    datos = df[df["fase_enso"] != "Sin dato"]
    resumen = (datos.groupby("fase_enso", as_index=False)
               .agg(meses=("mes", "count"),
                    **{t: (t, "mean") for t in tipos}))
    # La etiqueta lleva el numero de meses: un promedio de 3 meses pesa distinto
    # que uno de 21, y el lector debe verlo.
    unidad = resumen["meses"].map(lambda n: "mes" if n == 1 else "meses")
    resumen["etiqueta"] = (resumen["fase_enso"] + " ("
                           + resumen["meses"].astype(str) + " " + unidad + ")")

    # Orden fijo de las fases, para que las barras no cambien de lugar
    orden = ["El Niño", "Neutral", "La Niña"]
    posicion = {fase: i for i, fase in enumerate(orden)}
    resumen["_orden"] = resumen["fase_enso"].map(posicion).fillna(len(orden))
    resumen = resumen.sort_values("_orden").drop(columns="_orden").reset_index(drop=True)
    for t in tipos:
        resumen[t] = resumen[t].round(1)
    return resumen


def correlacion_oni_matriz(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pregunta propia: correlacion entre el ONI y la participacion de cada tipo.

    Va de -1 a 1. Cerca de 1 = cuando sube el ONI, sube esa fuente;
    cerca de -1 = cuando sube el ONI, baja.
    """
    tipos = [c for c in df.columns if c.endswith("_pct")]
    datos = df.dropna(subset=["oni"])
    filas = [{"tipo": c.replace("_pct", ""),
              "correlacion": round(datos["oni"].corr(datos[c]), 2)}
             for c in tipos]
    return (pd.DataFrame(filas)
            .sort_values("correlacion", ascending=False)
            .reset_index(drop=True))


def intervalos_enso(df: pd.DataFrame) -> pd.DataFrame:
    """
    Inicio y fin de cada mes, para sombrear la fase ENSO en la serie de tiempo.

    df: la salida de generacion_vs_oni.
    Devuelve mes, mes_fin y fase_enso. Cada franja cubre exactamente un mes.
    """
    out = df[["mes", "fase_enso"]].copy()
    out["mes_fin"] = out["mes"] + pd.offsets.MonthBegin(1)
    return out


def detalle_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabla mensual lista para mostrar: una fila por mes y columnas en espanol.

    Es la evidencia detras de los promedios por fase.
    """
    columnas = {
        "mes": "Mes",
        "oni": "ONI",
        "fase_enso": "Fase ENSO",
        "hidraulica_pct": "Hidráulica (%)",
        "termica_pct": "Térmica (%)",
        "solar_pct": "Solar (%)",
        "eolica_pct": "Eólica (%)",
        "cogenerador_pct": "Cogenerador (%)",
    }
    tabla = (df.sort_values("mes")[[c for c in columnas if c in df.columns]]
             .rename(columns=columnas)
             .copy())
    tabla["Mes"] = pd.to_datetime(tabla["Mes"]).dt.strftime("%Y-%m")
    if "ONI" in tabla.columns:
        tabla["ONI"] = tabla["ONI"].round(2)
    for c in tabla.columns:
        if c.endswith("(%)"):
            tabla[c] = tabla[c].round(1)
    return tabla.reset_index(drop=True)


def ajuste_lineal(df: pd.DataFrame, x: str, y: str) -> dict:
    """
    Recta de minimos cuadrados y R^2 entre dos columnas.

    Sirve para dibujar la tendencia del scatter y explicar cuanta variacion
    del efecto (y) queda explicada por la causa (x).
    """
    datos = df[[x, y]].dropna()
    if len(datos) < 2 or datos[x].var() == 0:
        return {"pendiente": None, "intercepto": None, "r2": None, "n": int(len(datos))}
    pendiente = datos[x].cov(datos[y]) / datos[x].var()
    intercepto = datos[y].mean() - pendiente * datos[x].mean()
    r2 = datos[x].corr(datos[y]) ** 2
    return {"pendiente": float(pendiente), "intercepto": float(intercepto),
            "r2": float(r2), "n": int(len(datos))}
