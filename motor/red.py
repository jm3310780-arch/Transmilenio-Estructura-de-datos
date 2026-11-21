# La clase Red tiene toda la lógica del planeador (R1 a R9).
# simular_fila (R10) está al final, como una función suelta.
#
# Qué guardamos (n = número de estaciones):
#   self.abierta    TablaHash  estación -> True (abierta) / False (cerrada)
#   self.nombres    lista de todas las estaciones en orden alfabético
#   self.rutas      TablaHash  ruta -> lista de estaciones en orden
#   self.rutas_de   TablaHash  estación -> lista de rutas que paran ahí
#   self.en_ruta    TablaHash  "ruta|estación" -> cuántas veces está en la ruta
#   self.horarios   TablaHash  "ruta|estación" -> lista ordenada de horas "HH:MM"
#   self.buses      TablaHash  estación -> buses al día (para el ranking)
#   self.deshacer_lista / self.rehacer_lista   pilas de cambios (R9)

import csv

from .estructuras import TablaHash, ordenar, buscar_desde, esta_ordenada

ABIERTA = "ABIERTA"
CERRADA = "CERRADA"
NO_EXISTE = "NO EXISTE"


def limpiar(nombre):
    """Quita espacios de los lados y pasa a mayúsculas: ' calle 26' -> 'CALLE 26'."""
    if nombre is None:
        return None
    return str(nombre).strip().upper()


def limpiar_ruta(ruta):
    if ruta is None:
        return None
    return str(ruta).strip()


def hora_bonita(hora):
    """'7:5' -> '07:05'. Con dos dígitos, las horas se comparan bien como texto.

    Devuelve None si el texto no es una hora.
    """
    try:
        partes = str(hora).strip().split(":")
        return "%02d:%02d" % (int(partes[0]), int(partes[1]))
    except (ValueError, IndexError):
        return None


def leer_csv(archivo):
    """Devuelve las filas del archivo, sin la fila de títulos."""
    filas = []
    with open(archivo, encoding="utf-8-sig", newline="") as f:
        lector = csv.reader(f)
        primera = True
        for fila in lector:
            if primera:
                primera = False  # saltar los títulos
                continue
            if len(fila) > 0 and fila[0].strip() != "":
                filas.append(fila)
    return filas


def esta_en(lista, valor):
    """Reemplaza a 'valor in lista' (prohibido): recorre la lista. O(len)."""
    for x in lista:
        if x == valor:
            return True
    return False


def posicion_de(lista, valor):
    """Reemplaza a lista.index(valor) (prohibido). -1 si no está. O(len)."""
    for i in range(len(lista)):
        if lista[i] == valor:
            return i
    return -1


def insertar_en(lista, posicion, valor):
    """Mete valor en la posición, corriendo los demás a la derecha. O(len)."""
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
    # Más buses va primero. Si empatan, en orden alfabético.
    if a[1] != b[1]:
        return a[1] > b[1]
    return a[0] < b[0]


class Red:
    # -----------------------------------------------------------
    # Cargar los tres CSV (José)
    # -----------------------------------------------------------
    def __init__(self, carpeta):
        carpeta = str(carpeta).rstrip("/\\")
        self.deshacer_lista = []
        self.rehacer_lista = []

        # Estaciones (todas abiertas al cargar).
        filas_est = leer_csv(carpeta + "/estaciones.csv")
        self.abierta = TablaHash(len(filas_est))
        self.rutas_de = TablaHash(len(filas_est))
        nombres = []
        for fila in filas_est:
            nombre = limpiar(fila[0])
            if self.abierta.obtener(nombre) is None:
                self.abierta.poner(nombre, True)
                self.rutas_de.poner(nombre, [])
                nombres.append(nombre)
        self.nombres = ordenar(nombres)

        # Rutas: juntamos las filas de cada ruta y las ordenamos por "orden".
        filas_rut = leer_csv(carpeta + "/rutas.csv")
        filas_por_ruta = TablaHash()
        nombres_rutas = []
        for fila in filas_rut:
            ruta = limpiar_ruta(fila[0])
            lista = filas_por_ruta.obtener(ruta)
            if lista is None:
                lista = []
                filas_por_ruta.poner(ruta, lista)
                nombres_rutas.append(ruta)
            lista.append((int(fila[1]), limpiar(fila[2])))
        self.rutas = TablaHash(len(nombres_rutas))
        self.en_ruta = TablaHash(len(filas_rut))
        for ruta in nombres_rutas:
            paradas = []
            for orden, estacion in ordenar(filas_por_ruta.obtener(ruta), primero_por_orden):
                if self.abierta.obtener(estacion) is None:
                    continue  # una parada que no está en estaciones.csv
                paradas.append(estacion)
                clave = ruta + "|" + estacion
                veces = self.en_ruta.obtener(clave)
                if veces is None:
                    self.en_ruta.poner(clave, 1)
                    self.rutas_de.obtener(estacion).append(ruta)
                else:
                    self.en_ruta.poner(clave, veces + 1)
            self.rutas.poner(ruta, paradas)
        self.lista_rutas = ordenar(nombres_rutas)

        # Horarios: una lista de horas por cada (ruta, estación), ordenada.
        self.horarios = TablaHash(len(filas_rut))
        for fila in leer_csv(carpeta + "/horarios.csv"):
            clave = limpiar_ruta(fila[0]) + "|" + limpiar(fila[1])
            hora = hora_bonita(fila[2])
            if hora is None:
                continue
            horas = self.horarios.obtener(clave)
            if horas is None:
                horas = []
                self.horarios.poner(clave, horas)
            horas.append(hora)
        for par in self.horarios.pares():
            if not esta_ordenada(par[1]):
                par[1] = ordenar(par[1])

        # Buses al día de cada estación: suma de los horarios de las rutas
        # que paran ahí (para el ranking).
        self.buses = TablaHash(len(nombres))
        for nombre in nombres:
            total = 0
            for ruta in self.rutas_de.obtener(nombre):
                total += self._buses_de(ruta, nombre)
            self.buses.poner(nombre, total)
        self.ranking_guardado = None  # None = hay que volver a calcularlo

    def _buses_de(self, ruta, estacion):
        horas = self.horarios.obtener(ruta + "|" + estacion)
        if horas is None:
            return 0
        return len(horas)

    def _esta_abierta(self, nombre):
        return self.abierta.obtener(nombre) is True

    # -----------------------------------------------------------
    # R1. ¿Existe la estación y está abierta? (José)   O(1) promedio
    # -----------------------------------------------------------
    def estado(self, nombre):
        """'ABIERTA', 'CERRADA' o 'NO EXISTE'."""
        valor = self.abierta.obtener(limpiar(nombre))
        if valor is None:
            return NO_EXISTE
        if valor:
            return ABIERTA
        return CERRADA

    # -----------------------------------------------------------
    # R2. Autocompletar (José)   O(log n + k)
    # -----------------------------------------------------------
    def autocompletar(self, prefijo, k):
        """Hasta k estaciones abiertas que empiezan por prefijo, en orden."""
        prefijo = limpiar(prefijo)
        resultado = []
        if prefijo is None or k is None or k <= 0:
            return resultado
        nombres = self.nombres
        # Con búsqueda binaria saltamos al primer nombre >= prefijo.
        i = buscar_desde(nombres, prefijo)
        while i < len(nombres) and len(resultado) < k:
            nombre = nombres[i]
            if not nombre.startswith(prefijo):
                break  # ya pasamos todos los que empiezan así
            if self._esta_abierta(nombre):
                resultado.append(nombre)
            i += 1
        return resultado

    # -----------------------------------------------------------
    # R3. Rango de nombres (José)   O(log n + m)
    # -----------------------------------------------------------
    def rango(self, desde, hasta):
        """Estaciones abiertas entre desde y hasta (incluidas), en orden."""
        desde = limpiar(desde)
        hasta = limpiar(hasta)
        resultado = []
        if desde is None or hasta is None:
            return resultado
        nombres = self.nombres
        i = buscar_desde(nombres, desde)
        while i < len(nombres) and nombres[i] <= hasta:
            if self._esta_abierta(nombres[i]):
                resultado.append(nombres[i])
            i += 1
        return resultado

    # -----------------------------------------------------------
    # R4. Próximo bus (Santiago Wagner)
    # -----------------------------------------------------------
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

    # -----------------------------------------------------------
    # R5. Planear un viaje, directo o con un transbordo (Santiago Serrano)
    # -----------------------------------------------------------
    def viaje(self, origen, destino):
        """Lista de tramos (ruta, sube_en, baja_en) con menos paradas.

        1 tramo si es directo, 2 si hay transbordo. None si no hay viaje
        (estación inexistente o cerrada, o no se llega con un transbordo).
        [] si origen y destino son la misma estación (no hay que viajar).
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
        # "alcanzadas" guarda, para cada estación, (paradas, ruta) del
        # camino directo más corto que encontramos para llegar a ella.
        alcanzadas = TablaHash()
        for ruta in self.rutas_de.obtener(origen):
            paradas = self.rutas.obtener(ruta)
            i = posicion_de(paradas, origen)
            for j in range(i + 1, len(paradas)):
                estacion = paradas[j]
                cuantas = j - i
                if estacion == destino:
                    if mejor is None or cuantas < mejor_total:
                        mejor = [(ruta, origen, destino)]
                        mejor_total = cuantas
                    break
                antes = alcanzadas.obtener(estacion)
                if antes is None or cuantas < antes[0]:
                    alcanzadas.poner(estacion, (cuantas, ruta))

        # Paso 2: desde el destino, retroceder por cada ruta que llega ahí.
        # Si una estación abierta también se alcanzó en el paso 1 con otra
        # ruta, se puede transbordar en ella.
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
                    mejor = [(llegada[1], origen, cambio), (ruta, cambio, destino)]
                    mejor_total = total
        return mejor

    # -----------------------------------------------------------
    # R6. Ranking de estaciones con más buses (Santiago Wagner)
    # -----------------------------------------------------------
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
    # R7. Editar rutas (Santiago Velásquez)
    # -----------------------------------------------------------
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


# ---------------------------------------------------------------
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

