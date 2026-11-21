# Estructuras y algoritmos hechos por nosotros.
#
# Dentro de motor/ el enunciado NO deja usar dict, set, sorted, .sort(),
# min, max, "x in lista", .index(), .count(), bisect, heapq, collections
# ni functools. Por eso aquí están:

#   1. TablaHash          -> reemplaza a dict
#   2. ordenar            -> merge sort, reemplaza a sorted
#   3. buscar_desde       -> búsqueda binaria


# ---------------------------------------------------------------
# 1. Tabla hash con encadenamiento
# ---------------------------------------------------------------
# Es una lista de "cubetas". Cada cubeta es una lista de pares [clave, valor].
# La función hash() de Python convierte la clave en un número y el residuo
# con el número de cubetas dice en qué cubeta va. hash() no está prohibida:
# lo prohibido es dict. Cuando hay más claves que cubetas, se duplican las
# cubetas, así cada cubeta tiene en promedio menos de 1 par -> O(1) promedio.

class TablaHash:
    def __init__(self, capacidad=64):
        tam = 64
        while tam < capacidad:
            tam *= 2
        self.cubetas = [None] * tam
        for i in range(tam):
            self.cubetas[i] = []
        self.cantidad = 0

    def obtener(self, clave):
        """Devuelve el valor guardado con esa clave, o None si no está."""
        for par in self.cubetas[hash(clave) % len(self.cubetas)]:
            if par[0] == clave:
                return par[1]
        return None

    def poner(self, clave, valor):
        """Guarda el valor. Si la clave ya estaba, lo reemplaza."""
        cubeta = self.cubetas[hash(clave) % len(self.cubetas)]
        for par in cubeta:
            if par[0] == clave:
                par[1] = valor
                return
        cubeta.append([clave, valor])
        self.cantidad += 1
        if self.cantidad > len(self.cubetas):
            self._agrandar()

    def _agrandar(self):
        viejas = self.cubetas
        tam = len(viejas) * 2
        self.cubetas = [None] * tam
        for i in range(tam):
            self.cubetas[i] = []
        for cubeta in viejas:
            for par in cubeta:
                self.cubetas[hash(par[0]) % tam].append(par)

    def pares(self):
        """Lista de todos los pares [clave, valor] (sin orden)."""
        todos = []
        for cubeta in self.cubetas:
            for par in cubeta:
                todos.append(par)
        return todos


# ---------------------------------------------------------------
# 2. Merge sort (estable)
# ---------------------------------------------------------------
# Parte la lista en dos mitades, ordena cada una y las mezcla. O(n log n).
# "va_antes(a, b)" dice si a debe ir antes que b. Si no se da, se usa <.
# Es estable: si dos elementos empatan, quedan en el orden en que venían.

def esta_ordenada(lista, va_antes=None):
    """True si la lista ya está en orden. O(n)."""
    for i in range(1, len(lista)):
        if va_antes is None:
            if lista[i] < lista[i - 1]:
                return False
        elif va_antes(lista[i], lista[i - 1]):
            return False
    return True


def ordenar(lista, va_antes=None):
    """Devuelve una lista nueva ordenada (merge sort de abajo hacia arriba)."""
    n = len(lista)
    actual = lista[:]
    if n <= 1 or esta_ordenada(actual, va_antes):
        return actual
    otra = [None] * n
    ancho = 1
    while ancho < n:
        inicio = 0
        while inicio < n:
            medio = inicio + ancho
            if medio > n:
                medio = n
            fin = inicio + 2 * ancho
            if fin > n:
                fin = n
            _mezclar(actual, otra, inicio, medio, fin, va_antes)
            inicio = fin
        actual, otra = otra, actual
        ancho *= 2
    return actual


def _mezclar(origen, destino, inicio, medio, fin, va_antes):
    i = inicio
    j = medio
    k = inicio
    if va_antes is None:
        while i < medio and j < fin:
            if origen[j] < origen[i]:
                destino[k] = origen[j]
                j += 1
            else:
                destino[k] = origen[i]
                i += 1
            k += 1
    else:
        while i < medio and j < fin:
            if va_antes(origen[j], origen[i]):
                destino[k] = origen[j]
                j += 1
            else:
                destino[k] = origen[i]
                i += 1
            k += 1
    # Lo que sobró de una de las dos mitades ya está en orden.
    while i < medio:
        destino[k] = origen[i]
        i += 1
        k += 1
    while j < fin:
        destino[k] = origen[j]
        j += 1
        k += 1


# ---------------------------------------------------------------
# 3. Búsqueda binaria
# ---------------------------------------------------------------
# En una lista ORDENADA, devuelve la primera posición cuyo valor es >= x.
# Si ninguno lo es, devuelve len(lista). O(log n).

def buscar_desde(lista, x):
    inicio = 0
    fin = len(lista)
    while inicio < fin:
        medio = (inicio + fin) // 2
        if lista[medio] < x:
            inicio = medio + 1
        else:
            fin = medio
    return inicio
