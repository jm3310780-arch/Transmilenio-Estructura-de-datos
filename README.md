# Planeador de viajes TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos. Una app donde se busca
una estación, se planea un viaje y se ve a qué hora pasa el siguiente bus,
con la red real de TransMilenio.

## Cómo arrancar la app

Resumen: desde la carpeta del proyecto, se instalan las librerías una vez y
la app arranca con un solo comando.

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

### Paso a paso

**1. Tener Python 3.10 o más nuevo.** En una terminal escribe `python --version`
(en Windows también sirve `py --version`). Si no aparece una versión,
descárgalo de https://www.python.org/downloads/ (en Windows, marca la casilla
**"Add Python to PATH"** al instalarlo).

**2. Descargar el proyecto.** Con git:

```bash
git clone https://github.com/jm3310780-arch/Transmilenio-Estructura-de-datos.git
cd Transmilenio-Estructura-de-datos
```

O sin git: en GitHub, botón verde **Code → Download ZIP**, descomprimirlo
(clic derecho → Extraer todo) y entrar a la carpeta.

**3. Abrir una terminal en la carpeta del proyecto** (la que tiene `app/`,
`motor/` y `datos/`):

- Windows: en el Explorador de archivos, clic derecho en un espacio vacío
  de la carpeta → **Abrir en Terminal**.
- Mac: clic derecho sobre la carpeta → **Nuevo terminal en la carpeta**.

Para comprobar que estás en el lugar correcto, escribe `dir` (Windows) o
`ls` (Mac/Linux): deben aparecer `app`, `motor`, `datos` y `pruebas.py`.

**4. Instalar las librerías de la app** (solo la primera vez):

```bash
pip install -r requirements.txt
```

Si `pip` no se reconoce, usa `python -m pip install -r requirements.txt`
(en Windows: `py -m pip install -r requirements.txt`).

**5. (Opcional) Probar el motor:**

```bash
python pruebas.py
```

Debe decir `Todas las pruebas pasaron`.

**6. Abrir la app:**

```bash
streamlit run app/app.py
```

Si `streamlit` no se reconoce, usa `python -m streamlit run app/app.py`
(en Windows: `py -m streamlit run app/app.py`). La primera vez puede pedir un
correo: se deja vacío y se presiona Enter. Si Windows pregunta por el
firewall, se permite.

**7. Usarla.** Se abre sola en el navegador; si no, entra a
http://localhost:8501. Tiene una pestaña por requisito: Buscar (R1 y R2),
Rango (R3), Próximo bus (R4), Viaje (R5), Ranking (R6), Operar (R7, R8 y R9),
Fila (R10) y Rendimiento (R11).

**8. Cerrarla:** en la terminal, **Ctrl + C**. Mientras la app esté abierta no
hay que cerrar la terminal.

### Otros comandos

| Comando | Qué hace |
| --- | --- |
| `python pruebas.py` | Prueba el motor (R1 a R10, con casos borde) |
| `python app/rendimiento.py` | Panel de rendimiento (R11) en la consola, redes de 10.000 a 80.000 estaciones |
| `python app/rendimiento.py rapido` | Lo mismo con redes de 1.000 a 8.000 |
| `python convertir_gtfs.py gtfs.zip datos` | Convierte el GTFS a los tres CSV (necesita `pandas`) |

## Estructura del repositorio

| Archivo / carpeta | Qué tiene |
| --- | --- |
| `motor/` | **Todo** el motor. `from motor import Red, simular_fila` |
| `motor/estructuras.py` | Tabla hash, merge sort y búsqueda binaria, hechos por nosotros |
| `motor/red.py` | La clase `Red` (R1 a R9) y `simular_fila` (R10) |
| `app/app.py` | El front (Streamlit), en su propia carpeta. Solo llama al motor |
| `app/rendimiento.py` | Panel de rendimiento (R11): genera redes de tamaño n y mide cada operación |
| `convertir_gtfs.py` | GTFS → `estaciones.csv`, `rutas.csv`, `horarios.csv` |
| `datos/` | Los tres CSV ya generados |
| `pruebas.py` | Pruebas del motor |
| `integrantes.md` | Integrantes y qué requisito hizo cada uno |

## Reglas del motor

Dentro de `motor/` no usamos `dict`, `set`, `sorted`, `.sort()`, `min`, `max`,
`x in lista`, `.index()`, `.count()`, `bisect`, `heapq`, `collections`,
`functools` ni librerías externas. Solo listas, `str`, tuplas y el módulo
`csv`. Lo que hacía falta lo programamos en `motor/estructuras.py`. El motor
devuelve listas, tuplas, textos, números, booleanos o `None`; nunca
diccionarios ni conjuntos.

## Contrato del motor

| Llamada | Req. | Devuelve |
| --- | --- | --- |
| `Red(carpeta)` | carga | La red de los tres CSV, todas las estaciones abiertas |
| `red.estado(nombre)` | R1 | `"ABIERTA"`, `"CERRADA"` o `"NO EXISTE"` |
| `red.autocompletar(prefijo, k)` | R2 | Hasta k estaciones abiertas que empiezan por el prefijo, en orden alfabético (`[]` si no hay) |
| `red.rango(desde, hasta)` | R3 | Estaciones abiertas entre los dos nombres (inclusive), en orden alfabético |
| `red.proximo_bus(estacion, ruta, hora)` | R4 | `"HH:MM"` del siguiente bus de esa ruta en esa estación (a esa hora o después), o `None` si no hay más ese día |
| `red.viaje(origen, destino)` | R5 | Lista de tramos `(ruta, sube_en, baja_en)`: 1 si es directo, 2 si hay transbordo; el de menos paradas. `None` si no hay viaje |
| `red.ranking(k)` | R6 | Lista de `(nombre, buses_por_dia)` de las k estaciones abiertas con más buses, de mayor a menor (empates: orden alfabético) |
| `red.agregar_parada(ruta, nueva, despues_de)` | R7 | `True` si la agregó justo después de `despues_de`, `False` si no se pudo |
| `red.quitar_parada(ruta, estacion)` | R7 | `True` si la quitó, `False` si no estaba |
| `red.recorrido(ruta, al_reves=False)` | R7 | Lista de nombres en orden (`[]` si la ruta no existe) |
| `red.cerrar(nombre)` / `red.reabrir(nombre)` | R8 | `True` si cambió el estado, `False` si no existe o ya estaba así |
| `red.deshacer()` / `red.rehacer()` | R9 | `True` si deshizo o rehízo algo, `False` si no había nada |
| `simular_fila(llegadas, frecuencia, capacidad)` | R10 | En el mismo orden de `llegadas`, el segundo en que sale el bus de cada persona |

Casos borde que decidimos:

- Los nombres se comparan sin espacios a los lados y en mayúsculas
  (`" calle 26"` = `"CALLE 26"`).
- `proximo_bus` devuelve `None` si la ruta no existe, la estación no existe,
  la ruta no para ahí, la estación está cerrada o ya no hay más buses.
  Si la hora pedida coincide con un bus, ese bus cuenta.
- `viaje` devuelve `None` si el origen o el destino no existen o están
  cerrados, o si no se llega con máximo un transbordo; `[]` si origen y
  destino son la misma estación (no hay que tomar ningún bus).
- `agregar_parada` devuelve `False` si la ruta o la estación no existen, si
  `despues_de` no está en la ruta o si la estación ya estaba en la ruta.
  Con `despues_de=None` la pone al inicio.
- `ranking(k)` con k ≤ 0 devuelve `[]`; si hay menos de k abiertas,
  devuelve todas.
- `simular_fila`: como dice el enunciado, los buses salen en los segundos
  f, 2f, 3f… (f = frecuencia; no hay bus en el segundo 0). Quien llega justo cuando sale un bus alcanza a subir.
  Si dos llegan en el mismo segundo, sube primero el que va antes en la
  lista. Ejemplo del enunciado:
  `simular_fila([30, 5, 5, 70], 60, 2)` → `[120, 60, 60, 120]`.

## Decisiones por requisito (R12)

Qué es cada letra:

| Letra | Significa |
| --- | --- |
| **n** | número de estaciones de la red |
| **k** | cuántos resultados se piden (R2, R6) |
| **m** | cuántas estaciones caen en el rango (R3) |
| **c** | estaciones cerradas que hay que saltarse |
| **P** | paradas de una ruta |
| **h** | buses de una ruta en una estación (horarios de ese par) |
| **H** | filas de `horarios.csv` |
| **p** | pasajeros (R10); **R** = segundos entre la primera y la última llegada |

### Carga: `Red(carpeta)` — O(n log n + H)

Se leen los tres CSV una vez. Las estaciones se guardan en una tabla hash y en
una lista ordenada con merge sort (O(n log n)). Las paradas de cada ruta se
ordenan por la columna `orden`. Los horarios se agrupan por `"ruta|estación"`
y cada grupo se ordena con merge sort. Al final se cuentan los buses al día
de cada estación (para el ranking).

### R1. Buscar una estación — tabla hash, O(1) promedio

**Estructura:** `TablaHash` nombre → `True`/`False` (abierta/cerrada),
implementada por nosotros con encadenamiento: una lista de cubetas y cada
cubeta una lista de pares. Cuando hay más claves que cubetas, se duplica el
número de cubetas (rehash), así cada cubeta tiene en promedio menos de un
elemento.
**Por qué:** es la consulta más usada y la tabla hash la responde en O(1)
promedio sin importar cuántas estaciones haya.
**Descartamos:** recorrer la lista de estaciones, O(n); búsqueda binaria en la
lista ordenada, O(log n), que también serviría pero es más lenta que la hash.

### R2. Autocompletar — lista ordenada + búsqueda binaria, O(log n + k + c)

**Estructura:** lista de todos los nombres en orden alfabético (se ordena una
sola vez al cargar). **Algoritmo:** búsqueda binaria del primer nombre
≥ prefijo; desde ahí se avanza mientras el nombre empiece por el prefijo,
saltando las cerradas (se pregunta a la tabla hash en O(1)), hasta tener k.
**Descartamos:** recorrer todas las estaciones (O(n)); un trie, que también
da O(largo del prefijo + k) pero gasta mucha más memoria y para el orden
alfabético hay que recorrerlo igual. Pensamos en un árbol AVL, pero las
estaciones nunca se agregan ni se borran (solo se cierran), así que una lista
ordenada es más sencilla y da la misma O grande.

### R3. Listar un rango — misma lista ordenada, O(log n + m + c)

Búsqueda binaria hasta `desde` y se avanza hasta pasar `hasta`, guardando las
abiertas. Si `desde > hasta` el resultado es `[]`.
**Descartamos:** filtrar toda la lista, O(n).

### R4. Próximo bus — tabla hash + búsqueda binaria, O(log h)

**Estructura:** `TablaHash` `"ruta|estación"` → lista ordenada de horas
`"HH:MM"`. Otra `TablaHash` `"ruta|estación"` dice si la ruta para ahí (se
actualiza con R7), así no hay que recorrer la ruta.
**Algoritmo:** búsqueda binaria de la primera hora ≥ la pedida. Las horas van
siempre con dos dígitos (`07:05`), así que compararlas como texto da el mismo
orden que compararlas como horas.
**Descartamos:** recorrer todos los horarios del par (O(h)): las troncales
tienen cientos de buses al día por estación.

### R5. Planear un viaje — dos barridos con tabla hash

1. Desde el origen se avanza por cada ruta que pasa por ahí y se anota en una
   `TablaHash` cuántas paradas toma llegar a cada estación y con qué ruta. Si
   se llega al destino, es un viaje directo.
2. Desde el destino se retrocede por cada ruta que llega ahí. Si una estación
   abierta también se alcanzó en el paso 1 con otra ruta, se puede
   transbordar en ella: paradas = (origen→cambio) + (cambio→destino).

Se queda el viaje (directo o con un transbordo) de menos paradas.
Costo: O(suma de P de las rutas que pasan por el origen y por el destino).
El bus sí pasa por una estación cerrada (y cuenta como parada), pero ahí
nadie sube, baja ni transborda.
**Descartamos:** probar todas las parejas de rutas (O(rutas² · P)), y un BFS
sobre todo el grafo, que encuentra el camino de menos paradas pero no
controla bien "máximo un transbordo".

### R6. Ranking — lista ordenada guardada, O(k + c)

**Estructura:** una `TablaHash` estación → buses al día, y una lista de
**todas** las estaciones (abiertas y cerradas) ordenada con merge sort de más
a menos buses (empate: orden alfabético). La lista se guarda y se reutiliza.
**Consulta:** se recorre la lista guardada desde el principio, saltando las
cerradas, hasta tener k. O(k + c), **no depende de n**.
**Cómo se mantiene al día:**
- Cerrar o reabrir (R8) **no obliga a reordenar**: las cerradas siguen en la
  lista y la consulta se las salta (pregunta a la tabla hash, O(1)).
- Editar una ruta (R7) cambia los buses de una estación: se marca la lista
  como desactualizada y se vuelve a ordenar **una sola vez**, en la siguiente
  consulta (O(n log n)). Como dice el enunciado, el ranking se consulta mucho
  y cambia poco, así que casi todas las consultas cuestan O(k + c).

**Descartamos:** ordenar todas las estaciones en cada consulta
(O(n log n) siempre); quitar las cerradas de la lista al cerrar (habría que
reordenar o correr elementos al reabrir); y un montículo (heap), que
actualiza en O(log n) pero es más difícil y para este uso no hace falta.

### R7. Editar rutas — lista (arreglo) por ruta, O(P)

**Estructura:** cada ruta es una lista de estaciones en orden.
- `agregar_parada`: se busca `despues_de` recorriendo la ruta (O(P)) y se
  corren las siguientes una casilla (O(P)). Se suman los buses de la
  estación y se marca el ranking para reordenar.
- `quitar_parada`: igual, corriendo al otro lado. O(P).
- `recorrido`: copia la lista, al derecho o al revés. O(P).

**Descartamos:** una lista doblemente enlazada, que inserta en O(1) pero
igual hay que encontrar `despues_de` (O(P)), así que no mejora la O grande y
recorrer al revés es lo mismo. Las rutas son cortas (máximo 33 paradas en los
datos reales).

### R8. Cerrar y reabrir — tabla hash, O(1)

Se cambia el `True`/`False` en la tabla hash. Todas las demás operaciones lo
consultan en O(1), así que la estación cerrada desaparece de búsquedas,
autocompletado, rangos, ranking, próximo bus y viajes sin recalcular nada.

### R9. Deshacer y rehacer — dos pilas

Dos listas usadas como pilas (`append` y `pop` al final, O(1)). Cada cambio
se guarda como una tupla, por ejemplo `("cerrar", "CALLE 26")` o
`("quitar", ruta, estación, la_que_estaba_antes)`. Deshacer saca el último de
la pila de deshacer, hace lo contrario y lo pasa a la pila de rehacer; rehacer
hace lo opuesto. Un cambio nuevo vacía la pila de rehacer.
Costo: O(1) para cierres y O(P) para ediciones de ruta.
**Descartamos:** guardar una copia de toda la red en cada cambio (O(n) por
cambio y mucha memoria).

### R10. Fila de abordaje — counting sort + cola, O(p + R)

1. **Ordenar las llegadas** (la gente sube en orden de llegada) con
   **counting sort**: se cuenta cuántas personas llegan en cada segundo
   (`contar_por_segundo`) y con esos conteos se arma la lista de llegadas
   en orden, sin comparar. O(p + R). Si hubiera segundos con decimales, se
   usa merge sort, O(p log p). Los dos son estables: si dos llegan en el
   mismo segundo, sube primero el que va antes en la lista.
2. **Simular con una cola** (`subir_a_buses`): una lista donde se agrega al
   final y un índice `frente` marca quién sigue. Cada bus sube hasta
   `capacidad` personas del frente. Si la fila está vacía, saltamos al primer
   bus que le sirve al siguiente pasajero (no se simulan buses vacíos). O(p).
3. **Devolver en el orden original:** los que llegaron en el segundo v ocupan
   puestos seguidos en la lista ordenada (desde `inicio[v]`), así que se
   reparten en un solo recorrido. O(p + R).

**Descartamos:** `fila.pop(0)`, que corre a todos los de la fila y deja todo
en O(p²); y ordenar siempre con merge sort, que da O(p log p).

## Panel de rendimiento (R11)

Pestaña **Rendimiento** de la app (o `python app/rendimiento.py`). Igual que el
script del curso: genera redes con el formato de los CSV de 10.000, 20.000,
40.000 y 80.000 estaciones, toma la **mediana** de varias repeticiones de cada
operación y calcula la **pendiente** de log(tiempo) contra log(n)
(0 = constante u O(log n), 1 = lineal). Muestra lo medido junto a la curva
esperada y explica las diferencias. En la red de prueba las rutas no se
alargan con n (P y h fijos) y en R10 hay p = 5n pasajeros.

Una corrida (microsegundos por llamada; varía un poco en cada computador):

| Operación | Esperado | n=10.000 | n=80.000 | Pendiente |
| --- | --- | --- | --- | --- |
| R1 estado | O(1) | 0.4 | 0.4 | ≈ 0 |
| R2 autocompletar | O(log n + k) | 3.6 | 4.2 | ≈ 0 |
| R3 rango | O(log n + m) | 4.2 | 4.3 | ≈ 0 |
| R4 proximo_bus | O(log h) | 2.3 | 2.4 | ≈ 0 |
| R6 ranking | O(k + c) | 3.9 | 4–7 | ≈ 0.2 |
| R7 agregar y quitar | O(P) | 8.4 | 8–12 | ≈ 0.1 |
| R7 recorrido | O(P) | 0.5 | 0.5–0.9 | ≈ 0.2 |
| R8 cerrar y reabrir | O(1) | 1.5 | 1.2–2.6 | ≈ 0.1 |
| R9 deshacer y rehacer | O(P) | 0.7 | 0.6–1.4 | ≈ 0.1 |
| R10 simular_fila (p = 5n) | O(p) | 18 904 | 163 212 | 0.98 |
| Carga `Red(carpeta)` | O(n log n + H) | 360 124 | 4 257 414 | 1.19 |

Todas las operaciones salen planas (pendiente cerca de 0) menos R10, que es
lineal porque p crece con n, y la carga. Las diferencias pequeñas entre una
corrida y otra son ruido del computador (otros programas usando el
procesador en ese momento).

## Los datos

`datos/` tiene 147 estaciones, 181 rutas y unos 140.000 horarios, generados
con `convertir_gtfs.py` desde el GTFS de julio de 2021. Cada ruta va en un
solo sentido (por ejemplo `B10-1` y `B10-2`). Decisiones de la conversión:

- Nombres en mayúsculas y sin tildes. Los vagones se juntan en su estación.
- Se usa un solo día de servicio (el `service_id` con más viajes).
- Cada recorrido distinto de una ruta es una ruta aparte (`-1` es el de más
  viajes). Se descartan recorridos de una sola parada o que repiten estación.
- **Horas después de medianoche:** el GTFS trae horas como `25:10`. Las
  guardamos con la hora del reloj: `25:10` → `01:10`, porque el contrato pide
  `HH:MM` y así se comparan bien como texto. Esos buses quedan al principio
  de la lista del día.
