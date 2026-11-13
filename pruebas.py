cat << 'EOF' > pruebas.py
import os
import tempfile
from motor import Red, simular_fila

def crear_red_pequena():
    carpeta = tempfile.mkdtemp()
    with open(carpeta + "/estaciones.csv", "w", encoding="utf-8") as f:
        f.write("nombre\n")
        for est in ["A", "B", "C", "D", "E", "CALLE 26", "CALLE 45", "CALLE 80", "CAN"]:
            f.write(est + "\n")
            
    with open(carpeta + "/rutas.csv", "w", encoding="utf-8") as f:
        f.write("ruta,orden,estacion\n")
        f.write("R1,4,D\nR1,3,C\nR1,2,B\nR1,1,A\n")
        f.write("R2,1,C\nR2,2,E\n")
        f.write("R3,1,CALLE 26\nR3,2,CALLE 45\nR3,3,CALLE 80\n")
        
    with open(carpeta + "/horarios.csv", "w", encoding="utf-8") as f:
        f.write("ruta,estacion,hora\n")
        f.write("R1,A,06:00\nR1,A,05:30\nR1,A,07:15\nR1,B,06:05\nR1,C,06:10\nR1,D,06:20\n")
        f.write("R2,C,06:30\nR2,C,06:40\nR2,E,06:50\n")
        
    return Red(carpeta)

red = crear_red_pequena()
assert red.estado("A") == (True, True)
assert red.estado("a") == (True, True)
assert red.estado("Z") == (False, False)

assert red.autocompletar("CA", 2) == ["CALLE 26", "CALLE 45"]
assert red.rango("CALLE 26", "CALLE 80") == ["CALLE 26", "CALLE 45", "CALLE 80"]

assert red.proximo_bus("A", "R1", "05:00") == "05:30"
assert red.viaje("A", "E") == [("R1", "A", "C", 2), ("R2", "C", "E", 1)]
assert red.ranking(2) == [("A", 3), ("C", 3)]

assert simular_fila([0, 0, 1, 2, 3, 10, 11], 5, 2) == [0, 0, 5, 5, 10, 10, 15]

print("Todas las pruebas pasaron")
EOF

