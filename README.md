# Planeador de viajes TransMilenio

Proyecto final de Estructuras de Datos y Algoritmos. Una app donde se busca
una estación, se planea un viaje y se ve a qué hora pasa el siguiente bus,
con la red real de TransMilenio.

## Cómo arrancar la app

```bash
pip install -r requirements.txt
streamlit run app.py
```

Se abre sola en el navegador (http://localhost:8501). Otros comandos:

| Comando | Qué hace |
| --- | --- |
| `python pruebas.py` | Prueba el motor (R1 a R10, con casos borde) |
| `python rendimiento.py` | Panel de rendimiento (R11) en la consola, redes de 10.000 a 80.000 estaciones |
| `python rendimiento.py rapido` | Lo mismo con redes de 1.000 a 8.000 |
| `python convertir_gtfs.py gtfs.zip datos` | Convierte el GTFS a los tres CSV |

## Estructura del repositorio

| Archivo / carpeta | Qué tiene |
| --- | --- |
| `motor/` | **Todo** el motor. `from motor import Red, simular_fila` |
| `motor/estructuras.py` | Tabla hash, merge sort, conteo (counting sort), búsqueda binaria, montículo y montículo indexado, hechos por nosotros |
| `motor/red.py` | La clase `Red` (R1 a R9) y `simular_fila` (R10) |
| `app.py` | El front (Streamlit). Solo llama al motor |
| `rendimiento.py` | Genera redes de tamaño n y mide cada operación (R11) |
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
y cada grupo se ordena (si ya viene ordenado, solo se revisa en O(h)). Al
final se arma el montículo del ranking en O(n) (heapify).

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

### R6. Ranking — montículo indexado, O((k + c) log(k + c))

**Estructura:** `MonticuloIndexado` con pares `[estación, buses al día]`
(más buses arriba; empate, orden alfabético) más una `TablaHash`
estación → posición en el montículo.
**Consulta:** recorremos el montículo desde la raíz con un montículo
auxiliar de candidatos (empieza con la raíz; se saca el mejor y se meten sus
dos hijos). Así salen en orden sin desarmar el montículo principal. Las
cerradas se saltan. Se visitan k + c nodos → O((k + c) log(k + c)),
**no depende de n**.
**Cómo se mantiene al día:**
- Cerrar o reabrir (R8) **no toca** el montículo: la consulta pregunta a la
  tabla hash si cada estación está abierta. O(1).
- Editar una ruta (R7) cambia los buses de una sola estación: se busca su
  posición en la tabla hash y se sube o baja en el montículo. O(log n).

**Descartamos:** ordenar todas las estaciones en cada consulta
(O(n log n)); guardar la lista ordenada y reordenar después de cada cambio
(la primera consulta después de un cierre costaría O(n log n)); y una lista
ordenada donde se reubica la estación al editar (O(n) por correr elementos).

### R7. Editar rutas — lista (arreglo) por ruta, O(P + log n)

**Estructura:** cada ruta es una lista de estaciones en orden.
- `agregar_parada`: se busca `despues_de` recorriendo la ruta (O(P)) y se
  corren las siguientes una casilla (O(P)). Se actualiza el montículo del
  ranking (O(log n)).
- `quitar_parada`: igual, corriendo al otro lado. O(P + log n).
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
Costo: O(1) para cierres y O(P + log n) para ediciones de ruta.
**Descartamos:** guardar una copia de toda la red en cada cambio (O(n) por
cambio y mucha memoria).

### R10. Fila de abordaje — counting sort + cola, O(p + R)

1. **Ordenar las llegadas** (la gente sube en orden de llegada):
   - si ya vienen en orden, solo se revisa: O(p);
   - si son segundos enteros (lo normal): counting sort, O(p + R). Se cuenta
     cuántas personas llegan en cada segundo y con eso se arma la lista
     ordenada sin comparar;
   - si no (decimales o un rango enorme): merge sort estable, O(p log p).
2. **Simular con una cola** (FIFO): una lista donde se agrega al final y un
   índice `frente` marca quién sigue. Cada bus sube hasta `capacidad`
   personas del frente. Si la fila está vacía, saltamos directo al primer
   bus que le sirve al siguiente pasajero (no se simulan buses vacíos).
   O(p + buses con gente) = O(p).
3. **Devolver en el orden original:** las personas que llegaron en el segundo
   v ocupan posiciones seguidas en la lista ordenada, así que se reparten en
   un solo recorrido. O(p + R).

**Descartamos:** `fila.pop(0)`, que corre a todos los de la fila y deja todo
en O(p²); y un montículo para ordenar por llegada, que da O(p log p).

## Panel de rendimiento (R11)

Pestaña **Rendimiento** de la app (o `python rendimiento.py`). Igual que el
script del curso: genera redes con el formato de los CSV de 10.000, 20.000,
40.000 y 80.000 estaciones, toma la **mediana** de varias repeticiones de cada
operación y calcula la **pendiente** de log(tiempo) contra log(n)
(0 = constante u O(log n), 1 = lineal). Muestra lo medido junto a la curva
esperada y explica las diferencias. En la red de prueba las rutas no se
alargan con n (P y h fijos) y en R10 hay p = 5n pasajeros.

Una corrida (microsegundos por llamada):

| Operación | Esperado | n=10.000 | n=80.000 | Pendiente |
| --- | --- | --- | --- | --- |
| R1 estado | O(1) | 0.3 | 0.3 | 0.03 |
| R2 autocompletar | O(log n + k) | 2.6 | 3.5 | 0.15 |
| R3 rango | O(log n + m) | 4.0 | 3.9 | -0.01 |
| R4 proximo_bus | O(log h) | 1.9 | 1.9 | -0.02 |
| R6 ranking | O((k + c) log(k + c)) | 23.3 | 21.7 | -0.04 |
| R7 agregar y quitar | O(P + log n) | 7.7 | 7.6 | 0.03 |
| R7 recorrido | O(P) | 0.3 | 0.4 | 0.12 |
| R8 cerrar y reabrir | O(1) | 1.5 | 1.2 | -0.10 |
| R9 deshacer y rehacer | O(P + log n) | 0.5 | 0.6 | 0.00 |
| R10 simular_fila (p = 5n) | O(p) | 13 921 | 115 786 | 1.02 |
| Carga `Red(carpeta)` | O(n log n + H) | 280 879 | 3 478 139 | 1.24 |

Todas las operaciones salen planas (pendiente ≈ 0) menos R10, que es lineal
porque p crece con n, y la carga. Las pequeñas subidas de R2 y R3 son el
log n de la búsqueda binaria y la caché del procesador; los saltos entre una
corrida y otra son ruido del computador.

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
