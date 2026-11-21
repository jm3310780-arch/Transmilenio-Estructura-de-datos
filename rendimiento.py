# R11. Panel de rendimiento: mide cuánto tarda cada operación con redes cada
# vez más grandes y lo compara con la O grande que esperábamos.
#
# Igual que el script del profesor: redes de 10.000, 20.000, 40.000 y 80.000
# estaciones, el tiempo de cada operación es la MEDIANA de varias
# repeticiones, y se calcula la PENDIENTE de log(tiempo) contra log(n):
#   pendiente ~ 0  -> constante u O(log n)  (línea plana)
#   pendiente ~ 1  -> lineal (se duplica cuando n se duplica)
#   pendiente > 1  -> peor que lineal
#
# n = número de estaciones. La red de prueba tiene n/10 rutas de 12 paradas
# y 8 buses por parada (mismo formato de los tres CSV). Las rutas no se
# alargan al crecer n, así que P (paradas de una ruta) y h (buses de una
# ruta en una estación) quedan fijos y solo crece n.
#
# Uso: python rendimiento.py          (la app usa medir() en su pestaña)
#      python rendimiento.py rapido   (redes de 1.000 a 8.000, para probar)

import math
import os
import random
import sys
import tempfile
import time

from motor import Red, simular_fila

TAMANOS = [10000, 20000, 40000, 80000]
TAMANOS_RAPIDO = [1000, 2000, 4000, 8000]
VECES = 300          # llamadas por repetición
REPETICIONES = 5     # se toma la mediana de estas repeticiones
PARADAS_POR_RUTA = 12
BUSES_POR_PARADA = 8

# operación -> (O grande esperada, pendiente esperada)
ESPERADO = {
    "R1 estado": ("O(1)", 0),
    "R2 autocompletar": ("O(log n + k)", 0),
    "R3 rango": ("O(log n + m)", 0),
    "R4 proximo_bus": ("O(log h)", 0),
    "R6 ranking": ("O(k + c)", 0),
    "R7 agregar y quitar": ("O(P)", 0),
    "R7 recorrido": ("O(P)", 0),
    "R8 cerrar y reabrir": ("O(1)", 0),
    "R9 deshacer y rehacer": ("O(P)", 0),
    "R10 simular_fila (p = 5n)": ("O(p)", 1),
    "Carga Red(carpeta)": ("O(n log n + H)", 1),
}


# Qué explica la medición cuando no es una línea perfecta.
EXPLICACION = {
    "R2 autocompletar": "Crece un poco por el log n de la búsqueda binaria y porque "
                        "una lista más grande cabe peor en la caché del procesador.",
    "R3 rango": "Igual que R2: log n de la búsqueda binaria + m resultados (m fijo aquí).",
    "R6 ranking": "No depende de n: la lista ya está ordenada y solo se leen las k "
                  "primeras abiertas más las c cerradas que se saltan (aquí c = 5). "
                  "Solo después de editar una ruta se reordena una vez: O(n log n).",
    "R7 agregar y quitar": "O(P) por buscar y correr las paradas de la ruta. No toca el "
                           "ranking: solo lo marca para reordenarlo en la próxima consulta.",
    "R10 simular_fila (p = 5n)": "Los pasajeros crecen con n (p = 5n), así que debe ser "
                                 "lineal. Si sale algo más de 1 es la caché: listas de "
                                 "cientos de miles de elementos ya no caben en ella.",
    "Carga Red(carpeta)": "Leer los CSV es lineal en el tamaño de los archivos (H filas "
                          "de horarios) y ordenar los nombres es n log n.",
}


def nombre(i):
    return "EST " + str(i).zfill(6)


def generar_red(n, carpeta):
    """Escribe los tres CSV de una red al azar con n estaciones."""
    rnd = random.Random(n)
    with open(os.path.join(carpeta, "estaciones.csv"), "w") as f:
        f.write("nombre\n")
        for i in range(n):
            f.write(nombre(i) + "\n")
    with open(os.path.join(carpeta, "rutas.csv"), "w") as f_rut, \
            open(os.path.join(carpeta, "horarios.csv"), "w") as f_hor:
        f_rut.write("ruta,orden,estacion\n")
        f_hor.write("ruta,estacion,hora\n")
        for r in range(n // 10):
            paradas = rnd.sample(range(n), PARADAS_POR_RUTA)
            salida = rnd.randrange(5 * 60, 7 * 60)
            for orden in range(PARADAS_POR_RUTA):
                est = nombre(paradas[orden])
                f_rut.write(f"R{r},{orden + 1},{est}\n")
                for b in range(BUSES_POR_PARADA):
                    m = salida + b * 90 + orden * 3
                    f_hor.write(f"R{r},{est},{m // 60:02d}:{m % 60:02d}\n")


def mediana(valores):
    valores = sorted(valores)  # aquí sí se puede: estamos fuera de motor/
    return valores[len(valores) // 2]


def cronometrar(funcion):
    """Microsegundos por llamada: mediana de REPETICIONES tandas de VECES."""
    tiempos = []
    for rep in range(REPETICIONES):
        inicio = time.perf_counter()
        for i in range(VECES):
            funcion(i)
        tiempos.append((time.perf_counter() - inicio) / VECES * 1e6)
    return mediana(tiempos)


def medir_una_red(n):
    carpeta = tempfile.mkdtemp()
    generar_red(n, carpeta)

    inicio = time.perf_counter()
    red = Red(carpeta)
    carga = (time.perf_counter() - inicio) * 1e6

    rnd = random.Random(1)
    al_azar = [nombre(rnd.randrange(n)) for i in range(VECES)]
    rutas = ["R" + str(rnd.randrange(n // 10)) for i in range(VECES)]
    paradas = [red.recorrido(r) for r in rutas]
    # Cerramos las 5 estaciones con más buses: ranking tiene que saltarlas.
    for est, buses in red.ranking(5):
        red.cerrar(est)

    def editar(i):
        red.agregar_parada(rutas[i], al_azar[i], paradas[i][5])
        red.quitar_parada(rutas[i], al_azar[i])

    def cerrar_y_reabrir(i):
        red.cerrar(al_azar[i])
        red.reabrir(al_azar[i])

    red.agregar_parada(rutas[0], al_azar[0], paradas[0][5])
    red.quitar_parada(rutas[0], paradas[0][3])

    def deshacer_y_rehacer(i):
        red.deshacer()
        red.rehacer()

    rnd_fila = random.Random(n)
    llegadas = [rnd_fila.randrange(3600) for i in range(5 * n)]
    tiempos_fila = []
    for rep in range(3):
        inicio = time.perf_counter()
        simular_fila(llegadas, 60, 150)
        tiempos_fila.append((time.perf_counter() - inicio) * 1e6)

    return {
        "R1 estado": cronometrar(lambda i: red.estado(al_azar[i])),
        "R2 autocompletar": cronometrar(lambda i: red.autocompletar(al_azar[i][:8], 5)),
        "R3 rango": cronometrar(lambda i: red.rango(al_azar[i], al_azar[i][:-1] + "9")),
        "R4 proximo_bus": cronometrar(lambda i: red.proximo_bus(paradas[i][2], rutas[i], "06:30")),
        "R6 ranking": cronometrar(lambda i: red.ranking(10)),
        "R7 agregar y quitar": cronometrar(editar),
        "R7 recorrido": cronometrar(lambda i: red.recorrido(rutas[i], i % 2 == 0)),
        "R8 cerrar y reabrir": cronometrar(cerrar_y_reabrir),
        "R9 deshacer y rehacer": cronometrar(deshacer_y_rehacer),
        "R10 simular_fila (p = 5n)": mediana(tiempos_fila),
        "Carga Red(carpeta)": carga,
    }


def pendiente(tamanos, tiempos):
    """Pendiente de la recta de mínimos cuadrados de log(t) contra log(n)."""
    xs = [math.log(n) for n in tamanos]
    ys = [math.log(t) for t in tiempos]
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    arriba = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    abajo = sum((x - mx) ** 2 for x in xs)
    return arriba / abajo


def veredicto(medida, esperada):
    if abs(medida - esperada) <= 0.3:
        return "como se esperaba"
    if medida > esperada:
        return "crece más de lo esperado"
    return "crece menos de lo esperado"


def curva_esperada(tamanos, esperada, primer_tiempo):
    """Tiempo que daría la pendiente esperada, empezando en el primer punto."""
    return [primer_tiempo * (n / tamanos[0]) ** esperada for n in tamanos]


def medir(tamanos=TAMANOS, avisar=None):
    """Lista de resultados (un diccionario por cada tamaño de red)."""
    resultados = []
    for n in tamanos:
        if avisar is not None:
            avisar(n)
        resultados.append(medir_una_red(n))
    return resultados


if __name__ == "__main__":
    tamanos = TAMANOS_RAPIDO if "rapido" in sys.argv else TAMANOS
    resultados = medir(tamanos, lambda n: print(f"midiendo n = {n} ...", flush=True))
    print("\nMicrosegundos por llamada (mediana)")
    print("operación".ljust(28) + "esperado".ljust(24)
          + "".join(str(n).rjust(10) for n in tamanos) + "  pendiente (esperada)")
    for op, (o_grande, esperada) in ESPERADO.items():
        tiempos = [r[op] for r in resultados]
        m = pendiente(tamanos, tiempos)
        print(op.ljust(28) + o_grande.ljust(24)
              + "".join(f"{t:10.1f}" for t in tiempos)
              + f"  {m:5.2f} ({esperada})  {veredicto(m, esperada)}")
