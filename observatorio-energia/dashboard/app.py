"""
Dashboard del Observatorio Energia y Clima, con Streamlit.

Responde las 6 preguntas de negocio del reto con las tablas de la capa oro.
Se ejecuta desde la raiz del proyecto con:
    streamlit run dashboard/app.py
y se abre en el navegador: http://localhost:8501
"""
# streamlit: convierte este programa de Python en una pagina web
import altair as alt
import streamlit as st

# Los datos y los calculos (dashboard/datos.py)
from datos import (ajuste_lineal, cargar, correlacion_por_rezago, correlacion_oni_matriz,
                   costos_de_compra, demanda_por, detalle_mensual, generacion_vs_oni,
                   intervalos_enso, matriz_por_fase, ventas_con_nombres)

# --- Configuracion de la pagina -------------------------------------------
# title = el titulo de la pestana; layout="wide" = usar todo el ancho de la pantalla
st.set_page_config(page_title="Observatorio Energía y Clima", layout="wide")


# @st.cache_data: lee los archivos UNA vez y los guarda en memoria.
# Sin esto, Streamlit los leeria otra vez con cada clic en un filtro
@st.cache_data
def leer_todo():
    return {
        "mensual": cargar("fact_mercado_mensual"),
        "horario": cargar("fact_mercado_horario"),
        "generacion": cargar("fact_generacion_mensual"),
        "ventas": ventas_con_nombres(),
    }


datos = leer_todo()
mensual = datos["mensual"].sort_values("mes")
# Los meses mas recientes aun no tienen ONI (NOAA lo publica despues):
# su fase queda como "Sin dato" para que no desaparezcan con el filtro
mensual["fase_enso"] = mensual["fase_enso"].fillna("Sin dato")

# --- Encabezado ------------------------------------------------------------
st.title("Observatorio Energía y Clima · EnerAndes")
st.caption("¿Nos vamos a apagar? Datos de XM, NOAA y EnerAndes, actualizados por GitHub Actions.")

# --- FILTROS, en la barra de la izquierda -----------------------------------
st.sidebar.header("Filtros")
# Filtro por FECHA: un rango de anos. min y max salen de los datos
anios = mensual["mes"].dt.year
desde, hasta = st.sidebar.slider("Años", int(anios.min()), int(anios.max()),
                                 (int(anios.min()), int(anios.max())))
# Filtro por FASE ENSO: El Nino, La Nina o Neutral. Por defecto, todas
opciones_fase = ["El Niño", "Neutral", "La Niña", "Sin dato"]
fases = st.sidebar.multiselect("Fase ENSO", opciones_fase, default=opciones_fase)
# Filtros del negocio (pregunta 5): municipio y segmento
ventas = datos["ventas"]
# placeholder = lo que dice el filtro cuando esta vacio (vacio = todos)
municipios = st.sidebar.multiselect("Municipio", sorted(ventas["municipio"].unique()), placeholder="Todos")
segmentos = st.sidebar.multiselect("Segmento", sorted(ventas["segmento"].unique()), placeholder="Todos")

# Se aplican los filtros de fecha y de fase a la tabla mensual
filtro = mensual[(anios >= desde) & (anios <= hasta) & mensual["fase_enso"].isin(fases)]

# --- KPIs: los numeros grandes de arriba ----------------------------------
ultimo = mensual.dropna(subset=["embalses_pct"]).iloc[-1]          # el ultimo mes con embalses
ultimo_oni = mensual.dropna(subset=["oni"]).iloc[-1]               # el ultimo mes con ONI
gen = datos["generacion"]
ultimo_gen = gen[gen["mes"] == gen["mes"].max()]
hidro = ultimo_gen.loc[ultimo_gen["tipo"] == "HIDRAULICA", "participacion_pct"].sum()

# st.columns(4): cuatro columnas, una para cada KPI
k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Embalses ({ultimo['mes']:%Y-%m})", f"{ultimo['embalses_pct']:.1f} %")
k2.metric("Precio de bolsa (último mes)", f"{mensual['precio_bolsa_cop_kwh'].dropna().iloc[-1]:,.0f} COP/kWh")
k3.metric(f"ONI ({ultimo_oni['mes']:%Y-%m})", f"{ultimo_oni['oni']:+.2f}", ultimo_oni["fase_enso"])
k4.metric("Generación hidráulica", f"{hidro:.1f} %")

# --- Una PESTANA por pregunta ---------------------------------------------
p1, p2, p3, p4, p5, p6 = st.tabs(["1 · Riesgo hídrico", "2 · Clima → precio", "3 · Generación",
                                  "4 · Demanda", "5 · Impacto en el negocio", "6 · Pregunta propia"])

with p1:
    st.subheader("¿Cómo han evolucionado los embalses y en qué se parece 2026 a los Niños anteriores?")
    # Grafico de linea: el mes en el eje X y el % de los embalses en el eje Y
    # x_label y y_label: los nombres de los ejes
    st.line_chart(filtro, x="mes", y="embalses_pct", x_label="Mes", y_label="Embalses (%)")
    # Comparacion: el promedio de los embalses en cada episodio de El Nino
    episodios = {"El Niño 2015-2016": ("2015-09", "2016-04"),
                 "El Niño 2023-2024": ("2023-10", "2024-04"),
                 "2026 (actual)": ("2026-01", "2026-12")}
    tabla = []
    for nombre, (ini, fin) in episodios.items():
        # Las filas cuyo mes esta entre ini y fin
        tramo = mensual[(mensual["mes"] >= ini) & (mensual["mes"] <= fin + "-28")]
        tabla.append({"Episodio": nombre,
                      "Embalses promedio (%)": round(tramo["embalses_pct"].mean(), 1),
                      "Embalses mínimo (%)": round(tramo["embalses_pct"].min(), 1)})
    st.dataframe(tabla, hide_index=True)

with p2:
    st.subheader("¿Qué relación hay entre el ONI, los aportes hídricos y el precio de bolsa?")
    con_precio = filtro.dropna(subset=["precio_bolsa_cop_kwh"])
    c1, c2 = st.columns(2)
    c1.line_chart(con_precio, x="mes", y="oni", height=250, x_label="Mes", y_label="ONI")
    c2.line_chart(con_precio, x="mes", y="precio_bolsa_cop_kwh", height=250,
                  x_label="Mes", y_label="Precio de bolsa (COP/kWh)")
    st.line_chart(con_precio, x="mes", y="aportes_pct", height=200,
                  x_label="Mes", y_label="Aportes (% de lo normal)")
    # Con cuantos meses de rezago se nota cada causa en el precio
    con_datos = mensual.dropna(subset=["precio_bolsa_cop_kwh"]).reset_index(drop=True)
    oni = correlacion_por_rezago(con_datos, "oni", "precio_bolsa_cop_kwh")
    aportes = correlacion_por_rezago(con_datos, "aportes_pct", "precio_bolsa_cop_kwh")
    # Una tabla con las dos correlaciones, una columna por causa
    rezagos = oni.rename(columns={"correlacion": "ONI"}).merge(
        aportes.rename(columns={"correlacion": "Aportes"}), on="rezago_meses")
    st.bar_chart(rezagos, x="rezago_meses", y=["ONI", "Aportes"], stack=False, height=240,
                 x_label="Meses de rezago", y_label="Correlación con el precio")
    mejor = oni.loc[oni["correlacion"].idxmax()]
    meses = int(mejor["rezago_meses"])
    st.info(f"El ONI se nota en el precio con {meses} {'mes' if meses == 1 else 'meses'} de rezago "
            f"(correlación {mejor['correlacion']:.2f}). Los aportes pesan más y de inmediato: "
            f"correlación {aportes.loc[0, 'correlacion']:.2f} en el mismo mes (menos agua, precio más alto).")

with p3:
    st.subheader("¿De qué fuente viene la energía y cómo cambia en época seca?")
    # pivot: una columna por tipo de planta -> barras apiladas
    mezcla = gen.pivot_table(index="mes", columns="tipo", values="participacion_pct").reset_index()
    # El mes como texto ('2026-01'): asi sale una barra ancha por mes
    mezcla["mes"] = mezcla["mes"].dt.strftime("%Y-%m")
    st.bar_chart(mezcla, x="mes", y=[c for c in mezcla.columns if c != "mes"], height=320,
                 x_label="Mes", y_label="Participación (%)")
    st.caption("Participación de cada tipo de planta en la generación del mes (%).")

with p4:
    st.subheader("¿Cuáles son los patrones de demanda? ¿Cuál es la hora pico?")
    horario = datos["horario"]
    por_hora = demanda_por(horario, "hora")
    pico = por_hora.loc[por_hora["demanda_mwh"].idxmax()]
    st.metric("Hora pico", f"{int(pico['hora'])}:00", f"{pico['demanda_mwh']:,.0f} MWh en promedio")
    c1, c2 = st.columns(2)
    c1.bar_chart(por_hora, x="hora", y="demanda_mwh", height=260, x_label="Hora", y_label="Demanda (MWh)")
    por_dia = demanda_por(horario, "dia_semana").merge(
        horario[["dia_semana", "dia_nombre"]].drop_duplicates(), on="dia_semana")
    c2.bar_chart(por_dia, x="dia_nombre", y="demanda_mwh", height=260, sort=False,
                 x_label="Día", y_label="Demanda (MWh)")

with p5:
    st.subheader("¿Cuánto habría costado comprar en bolsa en lugar de por contrato?")
    v = ventas
    # Si se eligio algun municipio o segmento, se filtra; si no, quedan todos
    if municipios:
        v = v[v["municipio"].isin(municipios)]
    if segmentos:
        v = v[v["segmento"].isin(segmentos)]
    costos = costos_de_compra(v, mensual)
    contrato = costos[costos["tipo_compra"] == "Contrato"]
    # Por mes: lo que costo por contrato frente a lo que habria costado en bolsa (millones)
    por_mes = contrato.groupby("mes_id", as_index=False)[["costo_contrato", "costo_bolsa"]].sum()
    # rename: nombres claros para la leyenda del grafico; / 1e6 = en millones
    por_mes = por_mes.rename(columns={"costo_contrato": "Por contrato", "costo_bolsa": "En bolsa"})
    por_mes[["Por contrato", "En bolsa"]] = (por_mes[["Por contrato", "En bolsa"]] / 1e6).round(0)
    por_mes["mes"] = por_mes["mes_id"].astype(str)
    st.bar_chart(por_mes, x="mes", y=["Por contrato", "En bolsa"], stack=False, height=300,
                 x_label="Mes", y_label="Millones de pesos")
    total = (contrato["costo_bolsa"] - contrato["costo_contrato"]).sum() / 1e6
    st.info(f"Comprar en bolsa la energía que se compró por contrato habría costado "
            f"{total:,.0f} millones de pesos {'más' if total > 0 else 'menos'}.")
    # El riesgo: la energia que SI se compro en bolsa, por municipio y segmento
    bolsa = costos[costos["tipo_compra"] == "Bolsa"]
    riesgo = (bolsa.groupby(["municipio", "segmento"], as_index=False)
              .agg(energia_bolsa_mwh=("energia_kwh", "sum"), sobrecosto=("sobrecosto", "sum")))
    riesgo["Energía en bolsa (MWh)"] = (riesgo["energia_bolsa_mwh"] / 1000).round(0)
    riesgo["Sobrecosto (millones)"] = (riesgo["sobrecosto"] / 1e6).round(1)
    riesgo = riesgo.rename(columns={"municipio": "Municipio", "segmento": "Segmento"})
    st.write("Dónde se concentra el riesgo: la energía comprada en bolsa y lo que costó de más frente al contrato.")
    st.dataframe(riesgo[["Municipio", "Segmento", "Energía en bolsa (MWh)", "Sobrecosto (millones)"]]
                 .sort_values("Sobrecosto (millones)", ascending=False), hide_index=True)

with p6:
    st.subheader("Cuando hay El Niño, ¿una mayor parte de la electricidad se produce quemando gas o carbón (térmica) en vez de usando agua (hidráulica)?")
    st.caption("Pregunta propia: integra NOAA (ONI y fase ENSO) con XM (generación por tipo de planta). "
               "Cada punto es un mes entre 2024 y 2026.")

    # Une la generacion mensual con el ONI del mismo mes
    gen_oni = generacion_vs_oni(datos["generacion"], mensual)
    # Respeta los filtros de anos y de fase de la barra lateral
    gen_oni = gen_oni[(gen_oni["mes"].dt.year >= desde) & (gen_oni["mes"].dt.year <= hasta)
                      & gen_oni["fase_enso"].isin(fases)]

    if gen_oni.empty:
        st.warning("No hay meses de generación para los filtros elegidos.")
    else:
        resumen = matriz_por_fase(gen_oni)
        if resumen.empty:
            st.warning("Los meses filtrados no tienen fase ENSO (ONI) disponible.")
        else:
            con_fase = resumen.set_index("fase_enso")
            # El resto agrupa Neutral y La Nina: asi la comparacion no depende de 3 meses
            fuera_nino = gen_oni[~gen_oni["fase_enso"].isin(["El Niño", "Sin dato"])]
            if "El Niño" in con_fase.index and not fuera_nino.empty:
                termica_nino = con_fase.loc["El Niño", "termica_pct"]
                termica_resto = fuera_nino["termica_pct"].mean()
                hidro_nino = con_fase.loc["El Niño", "hidraulica_pct"]
                hidro_resto = fuera_nino["hidraulica_pct"].mean()
                k1, k2, k3 = st.columns(3)
                k1.metric("Térmica en El Niño", f"{termica_nino:.1f} %")
                k2.metric("Térmica fuera de El Niño", f"{termica_resto:.1f} %")
                k3.metric("Diferencia", f"{termica_nino - termica_resto:+.1f} pp",
                          help="Puntos porcentuales de participación térmica: El Niño menos el resto. "
                               "La Niña solo aporta 3 meses, por eso se agrupa con Neutral.")

            # Colores y etiquetas compartidos por las graficas
            colores = {"El Niño": "#d62728", "Neutral": "#8c8c8c",
                       "La Niña": "#1f77b4", "Sin dato": "#d9d9d9"}
            fases_presentes = [f for f in ["El Niño", "Neutral", "La Niña", "Sin dato"]
                               if f in set(gen_oni["fase_enso"])]
            escala_fase = alt.Scale(domain=fases_presentes,
                                    range=[colores[f] for f in fases_presentes])
            orden = resumen["etiqueta"].tolist()
            etiquetas = dict(zip(resumen["fase_enso"], resumen["etiqueta"]))
            puntos = gen_oni.assign(etiqueta=gen_oni["fase_enso"].map(etiquetas))
            limite_termica = max(50, int(gen_oni["termica_pct"].max()) + 5)

            # 1) Serie mensual con las fases ENSO sombreadas
            st.write("**1. La serie mensual y las fases ENSO (El Niño, Neutral, La Niña)**")
            series = gen_oni.melt(
                id_vars=["mes"],
                value_vars=["hidraulica_pct", "termica_pct"],
                var_name="tecnologia", value_name="pct")
            series["tecnologia"] = series["tecnologia"].map(
                {"hidraulica_pct": "Hidráulica", "termica_pct": "Térmica"})
            fondo = alt.Chart(intervalos_enso(gen_oni)).mark_rect(opacity=0.14).encode(
                x=alt.X("mes:T", title="Mes", axis=alt.Axis(format="%Y-%m", labelAngle=-45)),
                x2=alt.X2("mes_fin:T"),
                color=alt.Color("fase_enso:N", scale=escala_fase, title="Fase ENSO"),
                tooltip=[alt.Tooltip("fase_enso:N", title="Fase")],
            )
            lineas = alt.Chart(series).mark_line(strokeWidth=2.5).encode(
                x=alt.X("mes:T", title="Mes", axis=alt.Axis(format="%Y-%m", labelAngle=-45)),
                y=alt.Y("pct:Q", scale=alt.Scale(domain=[0, 100]),
                        title="Participación (%)"),
                color=alt.Color("tecnologia:N",
                                scale=alt.Scale(domain=["Hidráulica", "Térmica"],
                                                range=["#2e7d32", "#c62828"]),
                                title="Tecnología"),
                tooltip=[alt.Tooltip("mes:T", title="Mes", format="%Y-%m"),
                         alt.Tooltip("tecnologia:N", title="Tecnología"),
                         alt.Tooltip("pct:Q", title="Participación (%)", format=".1f")],
            )
            st.altair_chart((fondo + lineas).resolve_scale(color="independent")
                            .properties(height=320), width="stretch")
            st.caption("El fondo rojo marca los meses de El Niño; el azul, los de La Niña. "
                       "La térmica sube cuando el fondo es rojo.")

            # 2) Promedio por fase y distribucion mensual
            c1, c2 = st.columns(2)
            with c1:
                st.write("**2. Promedio por fase (con el número de meses)**")
                barras = resumen.melt(
                    id_vars=["fase_enso", "etiqueta", "meses"],
                    value_vars=["hidraulica_pct", "termica_pct"],
                    var_name="tecnologia", value_name="pct")
                barras["tecnologia"] = barras["tecnologia"].map(
                    {"hidraulica_pct": "Hidráulica", "termica_pct": "Térmica"})
                grafico_barras = alt.Chart(barras).mark_bar().encode(
                    x=alt.X("etiqueta:N", sort=orden, title=None,
                            axis=alt.Axis(labelAngle=0)),
                    xOffset=alt.XOffset("tecnologia:N", sort=["Hidráulica", "Térmica"]),
                    y=alt.Y("pct:Q", scale=alt.Scale(domain=[0, 100]),
                            title="Participación promedio (%)"),
                    color=alt.Color("tecnologia:N",
                                    scale=alt.Scale(domain=["Hidráulica", "Térmica"],
                                                    range=["#2e7d32", "#c62828"]),
                                    title=None),
                    tooltip=[alt.Tooltip("fase_enso:N", title="Fase"),
                             alt.Tooltip("meses:Q", title="Meses"),
                             alt.Tooltip("tecnologia:N", title="Tecnología"),
                             alt.Tooltip("pct:Q", title="Promedio (%)", format=".1f")],
                ).properties(height=300)
                st.altair_chart(grafico_barras, width="stretch")

            with c2:
                st.write("**3. Cada mes, no solo el promedio**")
                base = alt.Chart(puntos).encode(
                    x=alt.X("etiqueta:N", sort=orden, title=None,
                            axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("termica_pct:Q",
                            scale=alt.Scale(domain=[0, limite_termica]),
                            title="Participación térmica (%)"),
                    color=alt.Color("fase_enso:N", scale=escala_fase, legend=None),
                )
                caja = base.mark_boxplot(extent="min-max", size=38, opacity=0.30)
                nube = base.mark_circle(size=45, opacity=0.55).encode(
                    tooltip=[alt.Tooltip("mes:T", title="Mes", format="%Y-%m"),
                             alt.Tooltip("oni:Q", title="ONI", format=".2f"),
                             alt.Tooltip("termica_pct:Q", title="Térmica (%)", format=".1f")])
                st.altair_chart((caja + nube).properties(height=300), width="stretch")

            # 3) Dispersion ONI vs termica, con recta de tendencia
            st.write("**4. ¿Cuánto se relaciona el ONI con la térmica?**")
            col_izq, col_der = st.columns([2, 1])
            with col_izq:
                dispersion = gen_oni.dropna(subset=["oni"])
                base = alt.Chart(dispersion).encode(
                    x=alt.X("oni:Q", title="ONI (positivo = El Niño)"),
                    y=alt.Y("termica_pct:Q",
                            scale=alt.Scale(domain=[0, limite_termica]),
                            title="Participación térmica (%)"),
                )
                nube = base.mark_circle(size=70, opacity=0.8).encode(
                    color=alt.Color("fase_enso:N", scale=escala_fase, title="Fase ENSO"),
                    tooltip=[alt.Tooltip("mes:T", title="Mes", format="%Y-%m"),
                             alt.Tooltip("oni:Q", title="ONI", format=".2f"),
                             alt.Tooltip("termica_pct:Q", title="Térmica (%)", format=".1f")])
                tendencia = (alt.Chart(dispersion)
                             .transform_regression("oni", "termica_pct", method="linear")
                             .mark_line(color="#333333", strokeDash=[6, 4], strokeWidth=2)
                             .encode(x=alt.X("oni:Q"), y=alt.Y("termica_pct:Q")))
                st.altair_chart((nube + tendencia).properties(height=320), width="stretch")
                ajuste = ajuste_lineal(gen_oni, "oni", "termica_pct")
                if ajuste["r2"] is not None:
                    st.caption(f"Recta de mínimos cuadrados: R² = {ajuste['r2']:.2f}. "
                               f"El ONI explica cerca del {ajuste['r2'] * 100:.0f} % de la "
                               "variación mensual de la térmica; el resto son otros factores "
                               "(estacionalidad, disponibilidad de plantas, mantenimientos...).")
            with col_der:
                st.write("Correlación con el ONI")
                corr = correlacion_oni_matriz(gen_oni)
                nombres = {"hidraulica": "Hidráulica", "termica": "Térmica",
                           "solar": "Solar", "eolica": "Eólica",
                           "cogenerador": "Cogenerador", "otro": "Otro"}
                tabla_corr = corr.assign(
                    Tipo=corr["tipo"].map(nombres).fillna(corr["tipo"]),
                    Correlación=corr["correlacion"].map(lambda v: f"{v:+.2f}"))
                st.dataframe(tabla_corr[["Tipo", "Correlación"]], hide_index=True)

            # 4) Tabla mensual: la evidencia detras de los promedios
            with st.expander("Ver los meses uno por uno (la evidencia detrás de los promedios)"):
                st.dataframe(detalle_mensual(gen_oni), hide_index=True)

            if "El Niño" in con_fase.index and not fuera_nino.empty:
                corr_termica = corr.loc[corr["tipo"] == "termica", "correlacion"].iloc[0]
                max_resto = fuera_nino["termica_pct"].max()
                st.info(f"En El Niño la térmica promedia {termica_nino:.1f} % y fuera de El Niño "
                        f"{termica_resto:.1f} % ({termica_nino - termica_resto:+.1f} pp). "
                        f"La hidráulica hace lo contrario: {hidro_resto:.1f} % fuera de El Niño "
                        f"y {hidro_nino:.1f} % en El Niño. "
                        f"Correlación ONI–térmica: {corr_termica:+.2f}.")
                st.caption(f"La relación no es perfecta: hay meses fuera de El Niño con térmica "
                           f"de hasta {max_resto:.0f} %, sobre todo a finales de 2024, así que la "
                           "estacionalidad también influye. La Niña solo tiene 3 meses; la comparación "
                           "más estable es El Niño contra Neutral. La generación disponible empieza en 2024.")
