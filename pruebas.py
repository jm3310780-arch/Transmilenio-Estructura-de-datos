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

# R4
assert red.proximo_bus("A", "R1", "05:00") == "05:30"
assert red.proximo_bus("A", "R1", "06:00") == "06:00"
assert red.proximo_bus("A", "R1", "6:01") == "07:15"
assert red.proximo_bus("A", "R1", "08:00") is None
assert red.proximo_bus("E", "R1", "05:00") is None

# R5
assert red.viaje("A", "C") == [("R1", "A", "C")]
assert red.viaje("A", "E") == [("R1", "A", "C"), ("R2", "C", "E")]
assert red.viaje("D", "A") is None          # las rutas van en un solo sentido
assert red.viaje("A", "A") == []

# R6
assert red.ranking(2) == [("A", 3), ("C", 3)]
assert red.ranking(0) == []
assert len(red.ranking(100)) == 9     # todas las abiertas

# R7
assert red.agregar_parada("R1", "E", "B") is True
assert red.recorrido("R1") == ["A", "B", "E", "C", "D"]
assert red.recorrido("R1", al_reves=True) == ["D", "C", "E", "B", "A"]
assert red.agregar_parada("R1", "E", "A") is False   # ya está en la ruta
assert red.agregar_parada("R1", "Z", "A") is False   # no existe
assert red.agregar_parada("R1", "CAN", None) is True # al inicio
assert red.recorrido("R1")[0] == "CAN"
assert red.quitar_parada("R1", "D") is True
assert red.quitar_parada("R1", "D") is False
assert red.recorrido("NO EXISTE") == []

# R8: una estación cerrada desaparece de todo
red = crear_red_pequena()
assert red.cerrar("C") is True
assert red.cerrar("C") is False
assert red.estado("C") == "CERRADA"
assert red.rango("B", "C") == ["B"]
assert red.proximo_bus("C", "R1", "05:00") is None
assert red.viaje("A", "E") is None                 # no se transborda en C
assert red.viaje("A", "D") == [("R1", "A", "D")] # pero el bus sí pasa
assert red.ranking(1) == [("A", 3)]
assert red.autocompletar("C", 10) == ["CALLE 26", "CALLE 45", "CALLE 80", "CAN"]
assert red.reabrir("C") is True
assert red.ranking(2) == [("A", 3), ("C", 3)]
assert red.cerrar("NO EXISTE") is False
assert red.reabrir("NO EXISTE") is False
assert red.reabrir("C") is False

# R9
red = crear_red_pequena()
assert red.deshacer() is False
red.cerrar("A")
red.quitar_parada("R1", "B")
red.agregar_parada("R2", "D", None)
assert red.deshacer() is True
assert red.recorrido("R2") == ["C", "E"]
assert red.deshacer() is True
assert red.recorrido("R1") == ["A", "B", "C", "D"]
assert red.deshacer() is True
assert red.estado("A") == "ABIERTA"
assert red.deshacer() is False
assert red.rehacer() is True
assert red.estado("A") == "CERRADA"
assert red.deshacer() is True
red.quitar_parada("R2", "C")    # C deja de tener los 2 buses de R2
assert red.ranking(1) == [("A", 3)]
assert red.proximo_bus("C", "R2", "05:00") is None
assert red.deshacer() is True
assert red.ranking(2) == [("A", 3), ("C", 3)]
assert red.proximo_bus("C", "R2", "05:00") == "06:30"
red.cerrar("C")                 # un cambio nuevo borra lo que había para rehacer
assert red.rehacer() is False

# R10
assert simular_fila([30, 5, 5, 70], 60, 2) == [120, 60, 60, 120]  # ejemplo del enunciado
assert simular_fila([0, 0, 1, 2, 3, 10, 11], 5, 2) == [5, 5, 10, 10, 15, 15, 20]  # no hay bus en el 0
assert simular_fila([5, 6], 5, 1) == [5, 10]   # llegar justo cuando sale: alcanza
assert simular_fila([], 5, 2) == []
assert simular_fila([7, 1], 5, 10) == [10, 5]       # se devuelve en el orden de entrada
assert simular_fila([3, 3, 3], 5, 1) == [5, 10, 15]  # empate: primero el que va antes

# La red real carga bien
red = Red(os.path.dirname(os.path.abspath(__file__)) + "/datos")
assert red.estado("PORTAL NORTE") == "ABIERTA"
assert red.viaje("PORTAL NORTE", "PORTAL SUR") is not None

print("Todas las pruebas pasaron")
