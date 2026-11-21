# Estructuras y algoritmos hechos por nosotros.
#
# Dentro de motor/ el enunciado NO deja usar dict, set, sorted, .sort(),
# min, max, "x in lista", .index(), .count(), bisect, heapq, collections
# ni functools. Por eso aquí están:
#   1. TablaHash     -> reemplaza a dict
#   2. ordenar       -> merge sort, reemplaza a sorted
#   3. buscar_desde  -> búsqueda binaria


# ---------------------------------------------------------------
# 1. Tabla hash
# ---------------------------------------------------------------
# Es una lista de "cubetas" (como los casilleros de un gimnasio). Cada cubeta
# es una lista de pares [clave, valor].
# hash(clave) convierte la clave en un número; el residuo de dividirlo por el
# número de cubetas dice en qué cubeta va. (hash() sí se puede usar: lo
# prohibido es dict.)
# Cuando hay más claves que cubetas, duplicamos las cubetas para que cada una
# tenga muy pocos pares. Así buscar es O(1) en promedio.

class TablaHash:
    def __init__(self, capacidad=64):
        tam = 64
        while tam < capacidad:
            tam = tam * 2
        self.cubetas = []
        for i in range(tam):
            self.cubetas.append([])
        self.cantidad = 0

    def obtener(self, clave):
        """Devuelve el valor guardado con esa clave, o None si no está."""
        cubeta = self.cubetas[hash(clave) % len(self.cubetas)]
        for par in cubeta:
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
        """Duplica las cubetas y vuelve a repartir los pares."""
        viejas = self.cubetas
        self.cubetas = []
        for i in range(len(viejas) * 2):
            self.cubetas.append([])
        for cubeta in viejas:
            for par in cubeta:
                self.cubetas[hash(par[0]) % len(self.cubetas)].append(par)

    def pares(self):
        """Lista de todos los pares [clave, valor] (sin orden)."""
        todos = []
        for cubeta in self.cubetas:
            for par in cubeta:
                todos.append(par)
        return todos


# ---------------------------------------------------------------
# 2. Merge sort
# ---------------------------------------------------------------
# Parte la lista en dos mitades, ordena cada mitad (llamándose a sí misma) y
# después mezcla las dos mitades ya ordenadas. O(n log n).
# "va_antes(a, b)" dice si a debe ir antes que b. Si no se da, se usa a < b.
# Es estable: si dos elementos empatan, quedan en el orden en que venían.

def menor(a, b):
    return a < b


def ordenar(lista, va_antes=menor):
    """Devuelve una lista nueva con los elementos de lista en orden."""
    if len(lista) <= 1:
        return lista[:]
    mitad = len(lista) // 2
    izquierda = ordenar(lista[:mitad], va_antes)
    derecha = ordenar(lista[mitad:], va_antes)
    return mezclar(izquierda, derecha, va_antes)


def mezclar(izquierda, derecha, va_antes):
    """Junta dos listas ordenadas en una sola lista ordenada."""
    resultado = []
    i = 0
    j = 0
    while i < len(izquierda) and j < len(derecha):
        # Si empatan, va primero el de la izquierda (por eso es estable).
        if va_antes(derecha[j], izquierda[i]):
            resultado.append(derecha[j])
            j += 1
        else:
            resultado.append(izquierda[i])
            i += 1
    # Lo que sobró de alguna de las dos ya está en orden.
    while i < len(izquierda):
        resultado.append(izquierda[i])
        i += 1
    while j < len(derecha):
        resultado.append(derecha[j])
        j += 1
    return resultado


# ---------------------------------------------------------------
# 3. Búsqueda binaria
# ---------------------------------------------------------------
# En una lista ORDENADA, devuelve la primera posición cuyo valor es >= x.
# Si ninguno lo es, devuelve len(lista).
# En cada vuelta mira el del medio y descarta la mitad. O(log n).

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
