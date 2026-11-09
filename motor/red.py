import csv
import os

class Red:
    def __init__(self, carpeta: str):
        # Listas paralelas (no podemos usar diccionarios ni sets dentro del motor)
        self.estaciones = []
        self.estado_estaciones = []  # True = abierta, False = cerrada
        self.cargared(carpeta)

    def cargared(self, carpeta: str):
        """Carga estaciones.csv y evita duplicados usando listas básicas."""
        ruta_estaciones = os.path.join(carpeta, "estaciones.csv")
        
        with open(ruta_estaciones, mode="r", encoding="utf-8") as f:
            lector = csv.reader(f)
            next(lector, None)  # Saltar encabezado
            for fila in lector:
                if fila:
                    nombre = fila[0].strip().upper()
                    # Evitamos duplicados manualmente sin usar set
                    encontrado = False
                    for est in self.estaciones:
                        if est == nombre:
                            encontrado = True
                            break
                    if not encontrado:
                        self.estaciones.append(nombre)
                        self.estado_estaciones.append(True)
        
        # Ordenar alfabéticamente sin usar sort() ni sorted() (Ordenamiento burbuja manual)
        self._ordenar_estaciones()

    def _ordenar_estaciones(self):
        n = len(self.estaciones)
        for i in range(n):
            for j in range(0, n - i - 1):
                if self.estaciones[j] > self.estaciones[j + 1]:
                    # Intercambiar nombre
                    temp_est = self.estaciones[j]
                    self.estaciones[j] = self.estaciones[j + 1]
                    self.estaciones[j + 1] = temp_est
                    
                    # Intercambiar estado paralelo
                    temp_estado = self.estado_estaciones[j]
                    self.estado_estaciones[j] = self.estado_estaciones[j + 1]
                    self.estado_estaciones[j + 1] = temp_estado

    def _buscar_indice(self, nombre: str) -> int:
        nombre_buscado = nombre.strip().upper()
        for i in range(len(self.estaciones)):
            if self.estaciones[i] == nombre_buscado:
                return i
        return -1

    def estado(self, nombre: str) -> bool:
        """R1: Verifica si una estación existe y está abierta."""
        idx = self._buscar_indice(nombre)
        if idx != -1:
            return self.estado_estaciones[idx]
        return False

    def autocompletar(self, prefijo: str, k: int) -> list:
        """R2: Devuelve hasta k estaciones abiertas que empiezan por prefijo, en orden alfabético."""
        prefijo_m = prefijo.strip().upper()
        resultado = []
        
        for i in range(len(self.estaciones)):
            if self.estado_estaciones[i]:
                nombre = self.estaciones[i]
                # Validar prefijo manualmente sin métodos prohibidos
                coincide = True
                if len(nombre) < len(prefijo_m):
                    coincide = False
                else:
                    for p in range(len(prefijo_m)):
                        if nombre[p] != prefijo_m[p]:
                            coincide = False
                            break
                if coincide:
                    resultado.append(nombre)
                    if len(resultado) == k:
                        break
        return resultado

    def rango(self, desde: str, hasta: str) -> list:
        """R3: Todas las estaciones abiertas entre dos nombres, en orden alfabético."""
        desde_m = desde.strip().upper()
        hasta_m = hasta.strip().upper()
        resultado = []
        
        agregando = False
        for i in range(len(self.estaciones)):
            nombre = self.estaciones[i]
            if nombre == desde_m:
                agregando = True
            
            if agregando and self.estado_estaciones[i]:
                resultado.append(nombre)
                
            if nombre == hasta_m:
                break
                
        return resultado
