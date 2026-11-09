# La clase Red tiene toda la lógica del planeador (R1 a R9).
import csv

from .estructuras import TablaHash, ordenar, buscar_desde


def limpiar(nombre):
    """Quita espacios de los lados y pasa a mayúsculas."""
    if nombre is None:
        return None
    return nombre.strip().upper()


def hora_bonita(hora):
    """'7:5' -> '07:05'."""
    partes = hora.strip().split(":")
    return f"{int(partes[0]):02d}:{int(partes[1]):02d}"


def leer_csv(archivo):
    filas = []
    with open(archivo, encoding="utf-8-sig") as f:
        lector = csv.reader(f)
        next(lector)
        for fila in lector:
            if len(fila) > 0:
                filas.append(fila)
    return filas


def esta_en(lista, valor):
    for x in lista:
        if x == valor:
            return True
    return False


def posicion_de(lista, valor):
    for i in range(len(lista)):
        if lista[i] == valor:
            return i
    return -1


def primero_por_orden(a, b):
    return a[0] < b[0]


def primero_en_ranking(a, b):
    if a[1] != b[1]:
        return a[1] > b[1]
    return a[0] < b[0]


class Red:
    def __init__(self, carpeta):
        self.abierta = TablaHash()
        self.rutas = TablaHash()
        self.rutas_de = TablaHash()
        self.horarios = TablaHash()
        self.buses = TablaHash()
        self.deshacer_lista = []
        self.rehacer_lista = []
        self.ranking_guardado = None

        # Estaciones
        nombres = []
        for fila in leer_csv(carpeta + "/estaciones.csv"):
            nombre = limpiar(fila[0])
            if self.abierta.obtener(nombre) is None:
                self.abierta.poner(nombre, True)
                self.rutas_de.poner(nombre, [])
                self.buses.poner(nombre, 0)
                nombres.append(nombre)
        self.nombres = ordenar(nombres)

        # Rutas
        filas_por_ruta = TablaHash()
        for fila in leer_csv(carpeta + "/rutas.csv"):
            ruta = fila[0].strip()
            if filas_por_ruta.obtener(ruta) is None:
                filas_por_ruta.poner(ruta, [])
            filas_por_ruta.obtener(ruta).append((int(fila[1]), limpiar(fila[2])))
        for ruta, filas in filas_por_ruta.pares():
            paradas = []
            for orden, estacion in ordenar(filas, primero_por_orden):
                paradas.append(estacion)
                self.rutas_de.obtener(estacion).append(ruta)
            self.rutas.poner(ruta, paradas)

        # Horarios
        for fila in leer_csv(carpeta + "/horarios.csv"):
            clave = fila[0].strip() + "|" + limpiar(fila[1])
            if self.horarios.obtener(clave) is None:
                self.horarios.poner(clave, [])
            self.horarios.obtener(clave).append(hora_bonita(fila[2]))
        for par in self.horarios.pares():
            par[1] = ordenar(par[1])

        # Buses al día
        for ruta, paradas in self.rutas.pares():
            for estacion in paradas:
                self._sumar_buses(ruta, estacion, 1)

    def _sumar_buses(self, ruta, estacion, signo):
        horas = self.horarios.obtener(ruta + "|" + estacion)
        if horas is not None:
            total = self.buses.obtener(estacion) + signo * len(horas)
            self.buses.poner(estacion, total)

    def _esta_abierta(self, nombre):
        return self.abierta.obtener(nombre) is True

    # R1. Estado
    def estado(self, nombre):
        valor = self.abierta.obtener(limpiar(nombre))
        if valor is None:
            return (False, False)
        return (True, valor)

    # R2. Autocompletar
    def autocompletar(self, prefijo, k):
        prefijo = limpiar(prefijo)
        resultado = []
        i = buscar_desde(self.nombres, prefijo)
        while i < len(self.nombres) and len(resultado) < k:
            nombre = self.nombres[i]
            if not nombre.startswith(prefijo):
                break
            if self._esta_abierta(nombre):
                resultado.append(nombre)
            i += 1
        return resultado

    # R3. Rango
    def rango(self, desde, hasta):
        desde = limpiar(desde)
        hasta = limpiar(hasta)
        resultado = []
        i = buscar_desde(self.nombres, desde)
        while i < len(self.nombres) and self.nombres[i] <= hasta:
            if self._esta_abierta(self.nombres[i]):
                resultado.append(self.nombres[i])
            i += 1
        return resultado

    # R4. Próximo bus (Parte de Santiago Wagner)
    def proximo_bus(self, estacion, ruta, hora):
        """Hora 'HH:MM' del siguiente bus (a esa hora o después), o None."""
        estacion = limpiar(estacion)
        paradas = self.rutas.obtener(ruta)
        if paradas is None or not esta_en(paradas, estacion):
            return None
        if not self._esta_abierta(estacion):
            return None
        horas = self.horarios.obtener(ruta + "|" + estacion)
        if horas is None:
            return None
        i = buscar_desde(horas, hora_bonita(hora))
        if i == len(horas):
            return None
        return horas[i]

    # R6. Ranking de estaciones con más buses (Parte de Santiago Wagner)
    def ranking(self, k):
        """Las k estaciones abiertas con más buses al día: [(nombre, buses)]."""
        if self.ranking_guardado is None:
            lista = []
            for nombre, buses in self.buses.pares():
                if self._esta_abierta(nombre):
                    lista.append((nombre, buses))
            self.ranking_guardado = ordenar(lista, primero_en_ranking)
        return self.ranking_guardado[:k]
        # -----------------------------------------------------------
    # R5. Planear un viaje (directo o con un transbordo)
    # -----------------------------------------------------------
    def viaje(self, origen, destino):
        """Lista de tramos (ruta, sube_en, baja_en, paradas).

        [] si origen y destino son la misma estación, None si no hay viaje.
        """
        origen = limpiar(origen)
        destino = limpiar(destino)
        if not self._esta_abierta(origen) or not self._esta_abierta(destino):
            return None
        if origen == destino:
            return []

        mejor = None
        mejor_total = 0

        # Paso 1: desde el origen, avanzar por cada ruta que pasa por ahí.
        alcanzadas = TablaHash()
        for ruta in self.rutas_de.obtener(origen):
            paradas = self.rutas.obtener(ruta)
            i = posicion_de(paradas, origen)
            for j in range(i + 1, len(paradas)):
                estacion = paradas[j]
                cuantas = j - i
                if estacion == destino:
                    if mejor is None or cuantas < mejor_total:
                        mejor = [(ruta, origen, destino, cuantas)]
                        mejor_total = cuantas
                    break
                antes = alcanzadas.obtener(estacion)
                if antes is None or cuantas < antes[0]:
                    alcanzadas.poner(estacion, (cuantas, ruta))

        # Paso 2: desde el destino, retroceder por cada ruta que llega ahí.
        for ruta in self.rutas_de.obtener(destino):
            paradas = self.rutas.obtener(ruta)
            s = posicion_de(paradas, destino)
            for q in range(s - 1, -1, -1):
                cambio = paradas[q]
                if cambio == origen:
                    break
                llegada = alcanzadas.obtener(cambio)
                if llegada is None or llegada[1] == ruta:
                    continue
                if not self._esta_abierta(cambio):
                    continue
                total = llegada[0] + (s - q)
                if mejor is None or total < mejor_total:
                    mejor = [(llegada[1], origen, cambio, llegada[0]),
                             (ruta, cambio, destino, s - q)]
                    mejor_total = total
        return mejor
