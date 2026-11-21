# Pruebas del motor con una red pequeña hecha a mano.
# Uso: python pruebas.py
# Si todo está bien, al final imprime "Todas las pruebas pasaron".

import os
import tempfile

from motor import Red, simular_fila


def crear_red_pequena():
    carpeta = tempfile.mkdtemp()
    with open(carpeta + "/estaciones.csv", "w") as f:
        f.write("nombre\nA\nB\nC\nD\nE\nCALLE 26\nCALLE 45\nCALLE 80\nCAN\n")
    with open(carpeta + "/rutas.csv", "w") as f:
        # R1: A -> B -> C -> D   R2: C -> E   R3: CALLE 26 -> CALLE 45 -> CALLE 80
        # (R1 va desordenada a propósito, para probar que se ordena por "orden")
        f.write("ruta,orden,estacion\n")
        f.write("R1,4,D\nR1,3,C\nR1,2,B\nR1,1,A\n")
        f.write("R2,1,C\nR2,2,E\n")
        f.write("R3,1,CALLE 26\nR3,2,CALLE 45\nR3,3,CALLE 80\n")
    with open(carpeta + "/horarios.csv", "w") as f:
        f.write("ruta,estacion,hora\n")
        f.write("R1,A,06:00\nR1,A,05:30\nR1,A,07:15\nR1,B,06:05\nR1,C,06:10\nR1,D,06:20\n")
        f.write("R2,C,06:30\nR2,C,06:40\nR2,E,06:50\n")
    return Red(carpeta)


# R1
red = crear_red_pequena()
assert red.estado("A") == "ABIERTA"
assert red.estado("a") == "ABIERTA"
assert red.estado("Z") == "NO EXISTE"

# R2
assert red.autocompletar("CA", 10) == ["CALLE 26", "CALLE 45", "CALLE 80", "CAN"]
assert red.autocompletar("CA", 2) == ["CALLE 26", "CALLE 45"]
assert red.autocompletar("X", 3) == []

# R3
assert red.rango("CALLE 26", "CALLE 80") == ["CALLE 26", "CALLE 45", "CALLE 80"]
assert red.rango("Z", "A") == []

# La red real carga bien
red = Red(os.path.dirname(os.path.abspath(__file__)) + "/datos")
assert red.estado("PORTAL NORTE") == "ABIERTA"
assert red.viaje("PORTAL NORTE", "PORTAL SUR") is not None

print("Todas las pruebas pasaron")
