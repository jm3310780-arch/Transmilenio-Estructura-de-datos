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
#   self.buses      TablaHash  estación -> buses que paran ahí al día
#   self.ranking_ordenado  lista de (estación, buses), de más a menos buses
#   self.pila_deshacer / self.pila_rehacer   pilas de cambios (R9)

import csv

from .estructuras import TablaHash, ordenar, buscar_desde

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
        self.pila_deshacer = []
        self.pila_rehacer = []

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
            par[1] = ordenar(par[1])

        # Buses al día de cada estación: suma de los horarios de las rutas
        # que paran ahí (para el ranking, R6).
        self.buses = TablaHash(len(nombres))
        for nombre in nombres:
            total = 0
            for ruta in self.rutas_de.obtener(nombre):
                total += self._buses_de(ruta, nombre)
            self.buses.poner(nombre, total)
        self.ranking_ordenado = None  # None = hay que volver a ordenar

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
        resultado = []
        if prefijo is None or k is None or k <= 0:
            return resultado
        # Solo mayúsculas: NO se quitan los espacios del final, porque
        # "CALLE " (con espacio) no es lo mismo que "CALLE".
        prefijo = str(prefijo).upper()
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
        resultado = []
        if desde is None or hasta is None:
            return resultado
        desde = str(desde).upper()   # igual que en R2: sin quitar espacios
        hasta = str(hasta).upper()
        nombres = self.nombres
        i = buscar_desde(nombres, desde)
        while i < len(nombres) and nombres[i] <= hasta:
            if self._esta_abierta(nombres[i]):
                resultado.append(nombres[i])
            i += 1
        return resultado

    # -----------------------------------------------------------
    # R4. Próximo bus (Santiago Velásquez)   O(log h)
    # -----------------------------------------------------------
    def proximo_bus(self, estacion, ruta, hora):
        """Hora 'HH:MM' del siguiente bus (a esa hora o después), o None."""
        estacion = limpiar(estacion)
        ruta = limpiar_ruta(ruta)
        hora = hora_bonita(hora)
        if estacion is None or ruta is None or hora is None:
            return None
        clave = ruta + "|" + estacion
        veces = self.en_ruta.obtener(clave)
        if veces is None or veces == 0:
            return None  # la ruta no existe o no para en esa estación
        if not self._esta_abierta(estacion):
            return None  # cerrada: nadie sube ahí
        horas = self.horarios.obtener(clave)
        if horas is None:
            return None
        i = buscar_desde(horas, hora)
        if i == len(horas):
            return None  # ya no pasan más buses hoy
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
    # R6. Ranking de estaciones con más buses (Santiago Velásquez)   O(k + c)
    # -----------------------------------------------------------
    def ranking(self, k):
        """Las k estaciones abiertas con más buses al día: [(nombre, buses)]."""
        resultado = []
        if k is None or k <= 0:
            return resultado
        # Guardamos TODAS las estaciones ordenadas (también las cerradas).
        # Solo se vuelve a ordenar si una ruta cambió (R7): O(n log n).
        # Cerrar o reabrir NO obliga a reordenar: las cerradas se saltan.
        if self.ranking_ordenado is None:
            lista = []
            for nombre, buses in self.buses.pares():
                lista.append((nombre, buses))
            self.ranking_ordenado = ordenar(lista, primero_en_ranking)
        for nombre, buses in self.ranking_ordenado:
            if len(resultado) == k:
                break
            if self._esta_abierta(nombre):
                resultado.append((nombre, buses))
        return resultado

    # -----------------------------------------------------------
    # R7. Editar rutas (Santiago Wagner)   O(P)
    # -----------------------------------------------------------
    def agregar_parada(self, ruta, nueva, despues_de):
        """Pone 'nueva' justo después de 'despues_de' (None = al inicio)."""
        ruta = limpiar_ruta(ruta)
        nueva = limpiar(nueva)
        despues_de = limpiar(despues_de)
        if not self._agregar(ruta, nueva, despues_de):
            return False
        self._guardar_cambio(("agregar", ruta, nueva, despues_de))
        return True

    def quitar_parada(self, ruta, estacion):
        """Quita la estación de la ruta. False si no estaba."""
        ruta = limpiar_ruta(ruta)
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
        self._quitar(ruta, estacion, i)
        # Guardamos la anterior para poder deshacer y dejarla donde estaba.
        self._guardar_cambio(("quitar", ruta, estacion, anterior))
        return True

    def recorrido(self, ruta, al_reves=False):
        """Estaciones de la ruta en orden ([] si la ruta no existe)."""
        paradas = self.rutas.obtener(limpiar_ruta(ruta))
        if paradas is None:
            return []
        if al_reves:
            return paradas[::-1]
        return paradas[:]

    def _agregar(self, ruta, nueva, despues_de):
        if ruta is None or nueva is None:
            return False
        paradas = self.rutas.obtener(ruta)
        if paradas is None or self.abierta.obtener(nueva) is None:
            return False
        clave = ruta + "|" + nueva
        veces = self.en_ruta.obtener(clave)
        if veces is not None and veces > 0:
            return False  # ya está en la ruta
        if despues_de is None:
            posicion = 0
        else:
            i = posicion_de(paradas, despues_de)
            if i == -1:
                return False
            posicion = i + 1
        insertar_en(paradas, posicion, nueva)
        self.en_ruta.poner(clave, 1)
        self.rutas_de.obtener(nueva).append(ruta)
        self._sumar_buses(nueva, self._buses_de(ruta, nueva))
        return True

    def _quitar(self, ruta, estacion, i=-1):
        paradas = self.rutas.obtener(ruta)
        if i == -1:
            i = posicion_de(paradas, estacion)
        borrar_en(paradas, i)
        clave = ruta + "|" + estacion
        veces = self.en_ruta.obtener(clave) - 1
        self.en_ruta.poner(clave, veces)
        if veces == 0:
            rutas = self.rutas_de.obtener(estacion)
            borrar_en(rutas, posicion_de(rutas, ruta))
            self._sumar_buses(estacion, -self._buses_de(ruta, estacion))

    def _sumar_buses(self, estacion, cuantos):
        if cuantos != 0:
            self.buses.poner(estacion, self.buses.obtener(estacion) + cuantos)
            self.ranking_ordenado = None  # el ranking se vuelve a ordenar

    # -----------------------------------------------------------
    # R8. Cerrar y reabrir (Santiago Wagner)   O(1)
    # -----------------------------------------------------------
    def cerrar(self, nombre):
        nombre = limpiar(nombre)
        if self.abierta.obtener(nombre) is not True:
            return False  # no existe o ya estaba cerrada
        self.abierta.poner(nombre, False)
        self._guardar_cambio(("cerrar", nombre))
        return True

    def reabrir(self, nombre):
        nombre = limpiar(nombre)
        if self.abierta.obtener(nombre) is not False:
            return False  # no existe o ya estaba abierta
        self.abierta.poner(nombre, True)
        self._guardar_cambio(("reabrir", nombre))
        return True

    # -----------------------------------------------------------
    # R9. Deshacer y rehacer con dos pilas (Santiago Wagner)
    # -----------------------------------------------------------
    def _guardar_cambio(self, cambio):
        self.pila_deshacer.append(cambio)
        self.pila_rehacer = []  # un cambio nuevo borra lo que había para rehacer

    def deshacer(self):
        if len(self.pila_deshacer) == 0:
            return False
        cambio = self.pila_deshacer.pop()
        self._aplicar(cambio, al_contrario=True)
        self.pila_rehacer.append(cambio)
        return True

    def rehacer(self):
        if len(self.pila_rehacer) == 0:
            return False
        cambio = self.pila_rehacer.pop()
        self._aplicar(cambio, al_contrario=False)
        self.pila_deshacer.append(cambio)
        return True

    def _aplicar(self, cambio, al_contrario):
        """Aplica un cambio guardado. Si al_contrario es True, hace lo opuesto."""
        tipo = cambio[0]
        if tipo == "cerrar":
            # deshacer un cierre = reabrir; rehacerlo = cerrar
            self.abierta.poner(cambio[1], al_contrario)
        elif tipo == "reabrir":
            self.abierta.poner(cambio[1], not al_contrario)
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
# R10. Fila de abordaje (Santiago Wagner)   O(p + R)
# ---------------------------------------------------------------
# Los buses salen en los segundos frecuencia, 2*frecuencia, 3*frecuencia, ...
# Quien llega justo cuando sale un bus alcanza a subir. Si el bus se llena,
# los demás esperan el siguiente, en orden de llegada (si llegan en el mismo
# segundo, primero el que va antes en la lista).

def simular_fila(llegadas, frecuencia, capacidad):
    """Segundo en que sale el bus de cada persona, en el orden de 'llegadas'.

    Ejemplo: simular_fila([30, 5, 5, 70], 60, 2) -> [120, 60, 60, 120]
    """
    p = len(llegadas)
    salida = [None] * p
    if p == 0 or frecuencia <= 0 or capacidad <= 0:
        return salida

    conteo = contar_por_segundo(llegadas)
    if conteo is not None:
        # --- Camino normal: los segundos son enteros. Counting sort, O(p + R).
        primero = conteo[0]
        cuantos = conteo[1]          # cuantos[v] = personas que llegan en primero + v
        # 1. Lista de llegadas ya en orden, sin comparar: se lee el conteo.
        tiempos = []
        for v in range(len(cuantos)):
            for vez in range(cuantos[v]):
                tiempos.append(primero + v)
        # 2. Simular la fila con las llegadas en orden.
        sale = subir_a_buses(tiempos, frecuencia, capacidad)
        # 3. Devolver en el orden original. Los que llegaron en el segundo v
        #    ocupan, en orden, los puestos inicio[v], inicio[v] + 1, ...
        inicio = []
        acumulado = 0
        for v in range(len(cuantos)):
            inicio.append(acumulado)
            acumulado += cuantos[v]
        for i in range(p):
            v = llegadas[i] - primero
            salida[i] = sale[inicio[v]]
            inicio[v] += 1
        return salida

    # --- Camino de respaldo (segundos con decimales): merge sort, O(p log p).
    def llega_antes(a, b):
        return llegadas[a] < llegadas[b]
    orden = ordenar(list(range(p)), llega_antes)   # posiciones en orden de llegada
    tiempos = []
    for i in orden:
        tiempos.append(llegadas[i])
    sale = subir_a_buses(tiempos, frecuencia, capacidad)
    for j in range(p):
        salida[orden[j]] = sale[j]
    return salida


def contar_por_segundo(llegadas):
    """Cuenta cuántas personas llegan en cada segundo.

    Devuelve (primero, cuantos): cuantos[v] = personas que llegan en el
    segundo primero + v. Devuelve None si hay segundos con decimales o si el
    rango es demasiado grande (ahí conviene más merge sort).
    """
    primero = llegadas[0]
    ultimo = llegadas[0]
    for x in llegadas:
        if type(x) is not int:
            return None
        if x < primero:
            primero = x
        if x > ultimo:
            ultimo = x
    if ultimo - primero > 4 * len(llegadas) + 100000:
        return None
    cuantos = [0] * (ultimo - primero + 1)
    for x in llegadas:
        cuantos[x - primero] += 1
    return (primero, cuantos)


def subir_a_buses(tiempos, frecuencia, capacidad):
    """tiempos: llegadas YA ORDENADAS. Devuelve el bus de cada una. O(p).

    La fila es una COLA: una lista a la que se agrega al final, y "frente"
    dice quién es el primero. (No usamos fila.pop(0) porque corre a todos
    los de la fila cada vez y con muchos pasajeros sería O(p^2).)
    """
    p = len(tiempos)
    sale = [0] * p
    fila = []
    frente = 0
    siguiente = 0           # siguiente persona que todavía no ha llegado
    bus = frecuencia        # el primer bus sale en el segundo "frecuencia"
    while siguiente < p or frente < len(fila):
        # Si no hay nadie esperando, saltamos al primer bus que le sirve
        # al siguiente que llega (no tiene sentido simular buses vacíos).
        if frente == len(fila) and tiempos[siguiente] > bus:
            bus = -(-tiempos[siguiente] // frecuencia) * frecuencia  # múltiplo >= llegada
        # Entran a la fila todos los que llegan antes de que salga el bus.
        while siguiente < p and tiempos[siguiente] <= bus:
            fila.append(siguiente)
            siguiente += 1
        # Suben en orden de llegada hasta llenar el bus.
        subidos = 0
        while subidos < capacidad and frente < len(fila):
            sale[fila[frente]] = bus
            frente += 1
            subidos += 1
        bus += frecuencia
    return sale
