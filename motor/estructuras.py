# Estructuras y algoritmos hechos por nosotros.
#
# Dentro de motor/ el enunciado NO deja usar dict, set, sorted, .sort(),
# min, max, "x in lista", .index(), .count(), bisect, heapq, collections
# ni functools. Por eso aquí están:
#   1. TablaHash          -> reemplaza a dict
#   2. ordenar            -> merge sort, reemplaza a sorted
#      contar_valores     -> counting sort para enteros en un rango chico
#   3. buscar_desde       -> búsqueda binaria
#   4. Monticulo          -> montículo binario (cola de prioridad)
#   5. MonticuloIndexado  -> montículo que deja cambiar la prioridad de una
#                            clave en O(log n) (lo usa el ranking, R6)


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
# 2b. Conteo de valores (base del counting sort)
# ---------------------------------------------------------------
# Para claves enteras en un rango pequeño (por ejemplo, segundos del día):
# conteo[v] = cuántas claves valen menor + v. Con esos conteos se arma la
# lista ordenada sin comparar nada: O(p + R), R = mayor - menor + 1.
# Devuelve (menor, conteo), o None si las claves no son enteras o el rango
# es tan grande que no conviene (ahí se usa merge sort).

def contar_valores(claves):
    p = len(claves)
    if p == 0:
        return None
    menor_v = claves[0]
    mayor_v = claves[0]
    for x in claves:
        if type(x) is not int:
            return None
        if x < menor_v:
            menor_v = x
        elif x > mayor_v:
            mayor_v = x
    rango = mayor_v - menor_v + 1
    if rango > 4 * p + 100000:
        return None
    conteo = [0] * rango
    for x in claves:
        conteo[x - menor_v] += 1
    return (menor_v, conteo)


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


# ---------------------------------------------------------------
# 4. Montículo binario
# ---------------------------------------------------------------
# Árbol completo guardado en una lista: los hijos de la posición i están en
# 2i+1 y 2i+2. El que "va_antes" de todos queda en la posición 0.
# agregar y sacar: O(log n).

class Monticulo:
    def __init__(self, va_antes):
        self.datos = []
        self.va_antes = va_antes

    def __len__(self):
        return len(self.datos)

    def agregar(self, x):
        datos = self.datos
        datos.append(x)
        i = len(datos) - 1
        while i > 0:
            padre = (i - 1) // 2
            if not self.va_antes(datos[i], datos[padre]):
                break
            datos[i], datos[padre] = datos[padre], datos[i]
            i = padre

    def sacar(self):
        datos = self.datos
        primero = datos[0]
        ultimo = datos.pop()
        if len(datos) > 0:
            datos[0] = ultimo
            i = 0
            n = len(datos)
            while True:
                mejor = i
                izq = 2 * i + 1
                der = izq + 1
                if izq < n and self.va_antes(datos[izq], datos[mejor]):
                    mejor = izq
                if der < n and self.va_antes(datos[der], datos[mejor]):
                    mejor = der
                if mejor == i:
                    break
                datos[i], datos[mejor] = datos[mejor], datos[i]
                i = mejor
        return primero


# ---------------------------------------------------------------
# 5. Montículo indexado
# ---------------------------------------------------------------
# Guarda pares [clave, valor]. Además tiene una TablaHash clave -> posición
# en la lista, para poder encontrar una clave en O(1) y cambiarle el valor
# en O(log n) (se sube o se baja hasta su lugar).
#
# mejores(k, sirve) devuelve los k mejores pares que cumplen sirve(clave)
# SIN sacarlos del montículo: recorre el árbol desde la raíz usando un
# montículo auxiliar con los candidatos (las "fronteras"). Cada par
# visitado mete a lo sumo 2 hijos, así que cuesta O((k + c) log(k + c)),
# donde c es cuántos pares que no sirven se saltaron por el camino.

class MonticuloIndexado:
    def __init__(self, pares, va_antes):
        """pares: lista de [clave, valor]. Se arma en O(n) (heapify)."""
        self.datos = pares
        self.va_antes = va_antes
        n = len(pares)
        i = n // 2 - 1
        while i >= 0:
            self._bajar_sin_indice(i)
            i -= 1
        self.posicion = TablaHash(n)
        for i in range(n):
            self.posicion.poner(pares[i][0], i)

    def _bajar_sin_indice(self, i):
        datos = self.datos
        n = len(datos)
        while True:
            mejor = i
            izq = 2 * i + 1
            der = izq + 1
            if izq < n and self.va_antes(datos[izq], datos[mejor]):
                mejor = izq
            if der < n and self.va_antes(datos[der], datos[mejor]):
                mejor = der
            if mejor == i:
                return
            datos[i], datos[mejor] = datos[mejor], datos[i]
            i = mejor

    def _cambiar_lugar(self, i, j):
        datos = self.datos
        datos[i], datos[j] = datos[j], datos[i]
        self.posicion.poner(datos[i][0], i)
        self.posicion.poner(datos[j][0], j)

    def valor(self, clave):
        i = self.posicion.obtener(clave)
        if i is None:
            return None
        return self.datos[i][1]

    def cambiar(self, clave, valor):
        """Le pone un valor nuevo a la clave y la deja en su lugar. O(log n)."""
        i = self.posicion.obtener(clave)
        if i is None:
            return
        datos = self.datos
        datos[i][1] = valor
        # Subir mientras vaya antes que su padre.
        while i > 0:
            padre = (i - 1) // 2
            if not self.va_antes(datos[i], datos[padre]):
                break
            self._cambiar_lugar(i, padre)
            i = padre
        # Bajar mientras un hijo vaya antes que él.
        n = len(datos)
        while True:
            mejor = i
            izq = 2 * i + 1
            der = izq + 1
            if izq < n and self.va_antes(datos[izq], datos[mejor]):
                mejor = izq
            if der < n and self.va_antes(datos[der], datos[mejor]):
                mejor = der
            if mejor == i:
                return
            self._cambiar_lugar(i, mejor)
            i = mejor

    def mejores(self, k, sirve):
        """Los k mejores pares (clave, valor) cuya clave cumple sirve(clave)."""
        datos = self.datos
        resultado = []
        if k <= 0 or len(datos) == 0:
            return resultado
        va_antes = self.va_antes
        frontera = Monticulo(lambda a, b: va_antes(datos[a], datos[b]))
        frontera.agregar(0)
        n = len(datos)
        while len(frontera) > 0 and len(resultado) < k:
            i = frontera.sacar()
            if sirve(datos[i][0]):
                resultado.append((datos[i][0], datos[i][1]))
            if 2 * i + 1 < n:
                frontera.agregar(2 * i + 1)
            if 2 * i + 2 < n:
                frontera.agregar(2 * i + 2)
        return resultado
