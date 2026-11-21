# Convierte el GTFS de TransMilenio en los tres CSV que lee el motor.
#
# Uso:
#   pip install pandas
#   python convertir_gtfs.py gtfs.zip datos
#
# Aquí sí se puede usar cualquier librería porque estamos fuera de motor/.
#
# Decisiones (también están en el README):
# - Nombres en mayúsculas y sin tildes.
# - Solo usamos el service_id con más viajes (un día hábil normal).
# - Cada recorrido distinto de una ruta es una ruta de un solo sentido:
#   B10-1, B10-2, ... (la -1 es la que tiene más viajes).
# - Horas como 25:10 son buses que pasan después de medianoche. Las
#   guardamos con la hora del reloj: 25:10 -> 01:10.

import sys
import unicodedata
import zipfile

import pandas as pd


def limpiar_nombre(texto):
    # "Calle 26 – Bogotá" -> "CALLE 26 - BOGOTA"
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.upper().split())


def hora_del_reloj(hora):
    # "25:10:00" -> "01:10"
    partes = hora.split(":")
    return f"{int(partes[0]) % 24:02d}:{partes[1]}"


def leer(archivo_zip, nombre):
    with zipfile.ZipFile(archivo_zip) as z:
        return pd.read_csv(z.open(nombre), dtype=str, keep_default_na=False)


def convertir(archivo_zip, carpeta):
    paradas = leer(archivo_zip, "stops.txt")
    rutas = leer(archivo_zip, "routes.txt")
    viajes = leer(archivo_zip, "trips.txt")
    tiempos = leer(archivo_zip, "stop_times.txt")

    # 1. Nombre de la estación de cada parada. Los vagones tienen una
    #    "parent_station": usamos el nombre de esa estación.
    nombre_de = {}
    for _, p in paradas.iterrows():
        nombre_de[p["stop_id"]] = limpiar_nombre(p["stop_name"])
    if "parent_station" in paradas.columns:
        for _, p in paradas.iterrows():
            if p["parent_station"] in nombre_de:
                nombre_de[p["stop_id"]] = nombre_de[p["parent_station"]]

    # 2. Quedarnos con un solo día de servicio.
    dia = viajes["service_id"].value_counts().idxmax()
    viajes = viajes[viajes["service_id"] == dia]
    nombre_ruta = dict(zip(rutas["route_id"], rutas["route_short_name"]))

    # 3. Estaciones y horas de cada viaje, en orden.
    tiempos["stop_sequence"] = tiempos["stop_sequence"].astype(int)
    tiempos = tiempos.sort_values(["trip_id", "stop_sequence"])
    paradas_de_viaje = {}   # viaje -> [(estacion, hora), ...]
    for _, t in tiempos.iterrows():
        lista = paradas_de_viaje.setdefault(t["trip_id"], [])
        estacion = nombre_de[t["stop_id"]]
        if len(lista) == 0 or lista[-1][0] != estacion:  # vagones seguidos = una parada
            lista.append((estacion, t["departure_time"] or t["arrival_time"]))

    # 4. Agrupar los viajes de cada ruta por recorrido.
    recorridos = {}  # (nombre de ruta, tupla de estaciones) -> lista de viajes
    for _, v in viajes.iterrows():
        lista = paradas_de_viaje.get(v["trip_id"], [])
        estaciones = tuple(e for e, h in lista)
        if len(estaciones) < 2 or len(set(estaciones)) != len(estaciones):
            continue  # recorridos de una parada o que repiten estación
        clave = (limpiar_nombre(nombre_ruta[v["route_id"]]), estaciones)
        recorridos.setdefault(clave, []).append(lista)

    # 5. Escribir los tres CSV.
    filas_rutas = []
    filas_horarios = []
    contador = {}  # cuántos recorridos lleva cada ruta
    for (corto, estaciones), lista_viajes in sorted(recorridos.items(),
                                                    key=lambda x: -len(x[1])):
        contador[corto] = contador.get(corto, 0) + 1
        ruta = f"{corto}-{contador[corto]}"
        for orden, estacion in enumerate(estaciones, start=1):
            filas_rutas.append([ruta, orden, estacion])
        for viaje in lista_viajes:
            for estacion, hora in viaje:
                if hora:
                    filas_horarios.append([ruta, estacion, hora_del_reloj(hora)])

    estaciones = sorted(set(f[2] for f in filas_rutas))
    pd.DataFrame({"nombre": estaciones}).to_csv(carpeta + "/estaciones.csv", index=False)
    pd.DataFrame(filas_rutas, columns=["ruta", "orden", "estacion"]).to_csv(
        carpeta + "/rutas.csv", index=False)
    pd.DataFrame(filas_horarios, columns=["ruta", "estacion", "hora"]).to_csv(
        carpeta + "/horarios.csv", index=False)
    print(len(estaciones), "estaciones,", len(set(f[0] for f in filas_rutas)), "rutas,",
          len(filas_horarios), "horarios")


if __name__ == "__main__":
    convertir(sys.argv[1], sys.argv[2])
