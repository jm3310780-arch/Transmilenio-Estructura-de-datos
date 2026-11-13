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


def insertar_en(lista, posicion, valor):
    """Mete valor en la posición, corriendo los demás a la derecha."""
    lista.append(None)
    i = len(lista) - 1
    while i > posicion:
        lista[i] = lista[i - 1]
        i -= 1
    lista[posicion] = valor


def borrar_en(lista, posicion):
    """Saca el elemento de la posición, corriendo los demás a la izquierda."""
    for i in range(posicion, len(lista) - 1):
        lista[i] = lista[i + 1]
    lista.pop()


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

    # R4. Próximo bus (Santiago Wagner)
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

    # R6. Ranking de estaciones con más buses (Santiago Wagner)
    def ranking(self, k):
        """Las k estaciones abiertas con más buses al día: [(nombre, buses)]."""
        if self.ranking_guardado is None:
            lista = []
            for nombre, buses in self.buses.pares():
                if self._esta_abierta(nombre):
                    lista.append((nombre, buses))
            self.ranking_guardado = ordenar(lista, primero_en_ranking)
        return self.ranking_guardado[:k]

    # R5. Planear un viaje (Santiago Serrano)
    def viaje(self, origen, destino):
        """Lista de tramos (ruta, sube_en, baja_en, paradas)."""
        origen = limpiar(origen)
        destino = limpiar(destino)
        if not self._esta_abierta(origen) or not self._esta_abierta(destino):
            return None
        if origen == destino:
            return []

        mejor = None
        mejor_total = 0

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

    # R7. Editar rutas (Santiago Velásquez)
    def agregar_parada(self, ruta, nueva, despues_de):
        nueva = limpiar(nueva)
        despues_de = limpiar(despues_de)
        if not self._agregar(ruta, nueva, despues_de):
            return False
        self._guardar_cambio(("agregar", ruta, nueva, despues_de))
        return True

    def quitar_parada(self, ruta, estacion):
        estacion = limpiar(estacion)
        paradas = self.rutas.obtener(ruta)
        if paradas is None:
            return False
        i = posicion_de(paradas, estacion)
        if i == -1:
            return False
        anterior = None
        if i > 0:
            anterior = paradas[i - 1]
        self._quitar(ruta, estacion)
        self._guardar_cambio(("quitar", ruta, estacion, anterior))
        return True

    def recorrido(self, ruta, al_reves=False):
        paradas = self.rutas.obtener(ruta)
        if paradas is None:
            return []
        if al_reves:
            return paradas[::-1]
        return paradas[:]

    def _agregar(self, ruta, nueva, despues_de):
        paradas = self.rutas.obtener(ruta)
        if paradas is None or self.abierta.obtener(nueva) is None:
            return False
        if esta_en(paradas, nueva):
            return False
        if despues_de is None:
            posicion = 0
        else:
            i = posicion_de(paradas, despues_de)
            if i == -1:
                return False
            posicion = i + 1
        insertar_en(paradas, posicion, nueva)
        self.rutas_de.obtener(nueva).append(ruta)
        self._sumar_buses(ruta, nueva, 1)
        self.ranking_guardado = None
        return True

    def _quitar(self, ruta, estacion):
        paradas = self.rutas.obtener(ruta)
        borrar_en(paradas, posicion_de(paradas, estacion))
        rutas = self.rutas_de.obtener(estacion)
        borrar_en(rutas, posicion_de(rutas, ruta))
        self._sumar_buses(ruta, estacion, -1)
        self.ranking_guardado = None

    # R8. Cerrar y reabrir (Santiago Velásquez)
    def cerrar(self, nombre):
        nombre = limpiar(nombre)
        if self.abierta.obtener(nombre) is not True:
            return False
        self._poner_abierta(nombre, False)
        self._guardar_cambio(("cerrar", nombre))
        return True

    def reabrir(self, nombre):
        nombre = limpiar(nombre)
        if self.abierta.obtener(nombre) is not False:
            return False
        self._poner_abierta(nombre, True)
        self._guardar_cambio(("reabrir", nombre))
        return True

    def _poner_abierta(self, nombre, valor):
        self.abierta.poner(nombre, valor)
        self.ranking_guardado = None

    # R9. Deshacer y rehacer (Santiago Velásquez)
    def _guardar_cambio(self, cambio):
        self.deshacer_lista.append(cambio)
        self.rehacer_lista = []

    def deshacer(self):
        if len(self.deshacer_lista) == 0:
            return False
        cambio = self.deshacer_lista.pop()
        self._aplicar(cambio, al_contrario=True)
        self.rehacer_lista.append(cambio)
        return True

    def rehacer(self):
        if len(self.rehacer_lista) == 0:
            return False
        cambio = self.rehacer_lista.pop()
        self._aplicar(cambio, al_contrario=False)
        self.deshacer_lista.append(cambio)
        return True

    def _aplicar(self, cambio, al_contrario):
        tipo = cambio[0]
        if tipo == "cerrar":
            self._poner_abierta(cambio[1], al_contrario)
        elif tipo == "reabrir":
            self._poner_abierta(cambio[1], not al_contrario)
        elif tipo == "agregar":
            ruta, estacion, despues_de = cambio[1], cambio[2], cambio[3]
            if al_contrario:
                self._quitar(ruta, estacion)
            else:
                self._agregar(ruta, estacion, despues_de)
        elif tipo == "quitar":
            ruta, estacion, anterior = cambio[1], cambio[2], cambio[3]
            if al_contrario:
                self._agregar(ruta, estacion, anterior)
            else:
                self._quitar(ruta, estacion)


# R10. Fila de abordaje (Santiago Velásquez)
def simular_fila(llegadas, frecuencia, capacidad):
    """Los buses salen en el minuto 0, frecuencia, 2*frecuencia, ..."""
    for i in range(1, len(llegadas)):
        if llegadas[i] < llegadas[i - 1]:
            llegadas = ordenar(llegadas)
            break
    n = len(llegadas)
    salida = [0] * n

    fila = []
    frente = 0
    siguiente = 0
    bus = 0

    while siguiente < n or frente < len(fila):
        if frente == len(fila) and llegadas[siguiente] > bus:
            bus = (llegadas[siguiente] + frecuencia - 1) // frecuencia * frecuencia
        while siguiente < n and llegadas[siguiente] <= bus:
            fila.append(siguiente)
            siguiente += 1
        subidos = 0
        while subidos < capacidad and frente < len(fila):
            salida[fila[frente]] = bus
            frente += 1
            subidos += 1
        bus += frecuencia
    return salida

