# App del planeador. Solo muestra cosas y llama al motor:
# todas las reglas del sistema están en motor/.
#
# Uso:
#   pip install streamlit
#   streamlit run app.py
#
# Streamlit vuelve a correr este archivo de arriba a abajo cada vez que el
# usuario toca algo. Por eso la red se guarda en st.session_state: así no se
# vuelve a cargar y no se pierden los cambios (cierres, ediciones, etc.).

import random

import streamlit as st

from motor import Red, simular_fila
import rendimiento

st.set_page_config(page_title="Planeador TransMilenio")
st.title("Planeador TransMilenio")

if "red" not in st.session_state:
    st.session_state.red = Red("datos")
red = st.session_state.red

pestanas = st.tabs(["Buscar", "Rango", "Próximo bus", "Viaje", "Ranking",
                    "Operar", "Fila", "Rendimiento"])

# ---------- R1 y R2 ----------
with pestanas[0]:
    texto = st.text_input("Escribe una estación", "CAL")
    sugerencias = red.autocompletar(texto, 8)
    if len(sugerencias) > 0:
        st.write("Sugerencias: " + ", ".join(sugerencias))
    estado = red.estado(texto)
    if estado == "NO EXISTE":
        st.info(f"{texto.upper()} no es el nombre exacto de una estación.")
    elif estado == "ABIERTA":
        st.success(f"{texto.upper()} existe y está abierta.")
    else:
        st.warning(f"{texto.upper()} existe pero está cerrada.")

# ---------- R3 ----------
with pestanas[1]:
    desde = st.text_input("Desde", "CALLE 26")
    hasta = st.text_input("Hasta", "CALLE 80")
    st.write(red.rango(desde, hasta))

# ---------- R4 ----------
with pestanas[2]:
    estacion = st.selectbox("Estación", red.nombres, key="bus_estacion")
    rutas = [r for r in red.lista_rutas if estacion in red.recorrido(r)]
    ruta = st.selectbox("Ruta", rutas)
    hora = st.text_input("Hora (HH:MM)", "07:00")
    if ruta is not None:
        siguiente = red.proximo_bus(estacion, ruta, hora)
        if siguiente is None:
            st.warning("No pasan más buses de esa ruta hoy, o la estación está cerrada.")
        else:
            st.success(f"El próximo bus de la ruta {ruta} pasa a las {siguiente}.")

# ---------- R5 ----------
with pestanas[3]:
    origen = st.selectbox("Origen", red.nombres, index=red.nombres.index("PORTAL NORTE"))
    destino = st.selectbox("Destino", red.nombres, index=red.nombres.index("PORTAL SUR"))
    tramos = red.viaje(origen, destino)
    if tramos is None:
        st.warning("No hay viaje directo ni con un solo transbordo.")
    elif len(tramos) == 0:
        st.info("Ya estás en el destino.")
    else:
        for ruta, sube, baja in tramos:
            parada = red.recorrido(ruta)
            i = parada.index(sube)
            cuantas = parada.index(baja, i + 1) - i
            st.write(f"Toma la ruta **{ruta}** en {sube} y bájate en {baja} ({cuantas} paradas).")
        if len(tramos) == 2:
            st.caption(f"Transbordo en {tramos[0][2]}.")

# ---------- R6 ----------
with pestanas[4]:
    k = st.number_input("¿Cuántas estaciones?", 1, 50, 10)
    tabla = []
    for nombre, buses in red.ranking(k):
        tabla.append({"Estación": nombre, "Buses al día": buses})
    st.table(tabla)

# ---------- R7, R8 y R9 ----------
with pestanas[5]:
    st.subheader("Recorrido de una ruta")
    ruta = st.selectbox("Ruta", red.lista_rutas, key="op_ruta")
    al_reves = st.checkbox("Ver al revés")
    st.write(" → ".join(red.recorrido(ruta, al_reves)))

    st.subheader("Editar la ruta")
    parada = st.selectbox("Estación", red.nombres, key="op_parada")
    despues = st.selectbox("Después de", ["(al inicio)"] + red.recorrido(ruta))
    if despues == "(al inicio)":
        despues = None
    col1, col2 = st.columns(2)
    if col1.button("Agregar parada"):
        st.write("Listo." if red.agregar_parada(ruta, parada, despues) else "No se pudo.")
    if col2.button("Quitar parada"):
        st.write("Listo." if red.quitar_parada(ruta, parada) else "Esa estación no está en la ruta.")

    st.subheader("Cerrar o reabrir")
    cual = st.selectbox("Estación", red.nombres, key="op_cerrar")
    col1, col2 = st.columns(2)
    if col1.button("Cerrar"):
        st.write("Cerrada." if red.cerrar(cual) else "Ya estaba cerrada.")
    if col2.button("Reabrir"):
        st.write("Reabierta." if red.reabrir(cual) else "Ya estaba abierta.")

    st.subheader("Historial")
    col1, col2 = st.columns(2)
    if col1.button("Deshacer"):
        st.write("Se deshizo el último cambio." if red.deshacer() else "No hay nada para deshacer.")
    if col2.button("Rehacer"):
        st.write("Se rehízo." if red.rehacer() else "No hay nada para rehacer.")

# ---------- R10 ----------
with pestanas[6]:
    st.write("Cada persona llega en un segundo; los buses salen cada *frecuencia* "
             "segundos con un cupo, y la gente sube en orden de llegada.")
    pasajeros = st.number_input("Pasajeros", 1, 1000000, 200000)
    segundos = st.number_input("Llegan entre el segundo 0 y el", 1, 86400, 3600)
    frecuencia = st.number_input("Sale un bus cada (segundos)", 1, 3600, 60)
    capacidad = st.number_input("Cupo de cada bus", 1, 500, 150)
    if st.button("Simular"):
        llegadas = [random.randrange(segundos) for i in range(pasajeros)]
        salidas = simular_fila(llegadas, frecuencia, capacidad)
        esperas = [salidas[i] - llegadas[i] for i in range(pasajeros)]
        st.write(f"Espera promedio: {sum(esperas) / pasajeros:.1f} segundos")
        st.write(f"Espera máxima: {max(esperas)} segundos")
        st.write(f"Último bus: segundo {max(salidas)}")

# ---------- R11 ----------
with pestanas[7]:
    st.write("Corre cada operación del motor en redes de tamaño creciente "
             "(n = número de estaciones), toma la mediana de varias repeticiones "
             "y calcula la **pendiente** de log(tiempo) contra log(n): "
             "0 = constante u O(log n), 1 = lineal. La línea *esperado* es la "
             "curva que daría la complejidad que calculamos (ver README).")
    rapido = st.checkbox("Modo rápido (n = 1.000 a 8.000)", value=False)
    tamanos = rendimiento.TAMANOS_RAPIDO if rapido else rendimiento.TAMANOS
    if st.button("Medir"):
        barra = st.empty()
        resultados = rendimiento.medir(tamanos, lambda n: barra.write(f"Midiendo n = {n:,} ..."))
        barra.empty()
        resumen = []
        for op, (o_grande, esperada) in rendimiento.ESPERADO.items():
            medido = [r[op] for r in resultados]
            m = rendimiento.pendiente(tamanos, medido)
            resumen.append({"Operación": op, "Esperado": o_grande,
                            "Pendiente esperada": esperada,
                            "Pendiente medida": round(m, 2),
                            "Veredicto": rendimiento.veredicto(m, esperada)})
        st.subheader("Resumen")
        st.table(resumen)
        for op, (o_grande, esperada) in rendimiento.ESPERADO.items():
            medido = [r[op] for r in resultados]
            st.subheader(f"{op}  (esperado {o_grande})")
            datos = {"n": tamanos,
                     "medido (µs)": medido,
                     "esperado (µs)": rendimiento.curva_esperada(tamanos, esperada, medido[0])}
            st.line_chart(datos, x="n", y=["medido (µs)", "esperado (µs)"])
            nota = rendimiento.EXPLICACION.get(op)
            if nota:
                st.caption(nota)
