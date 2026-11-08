# Notas de Diseño Arquitectónico: Sistema de Colas de Sucursal (`BranchQueueManager`)

## 1. Eficiencia Algorítmica: Cola por Servicio vs. Cola Única Compartida

### 1.1 Contexto y Modelado de Datos

En el sistema de atención de sucursales, los clientes ingresan a la oficina y obtienen un turno solicitando una categoría de servicio específica definida por la enumeración `ServiceType` (`deposit`, `withdrawal`, `account_management`). Los puestos de atención se configuran para atender una o más de estas categorías de manera especializada.

Frente a este requerimiento operativo, existen dos paradigmas arquitectónicos fundamentales para estructurar las colas de espera en memoria:

1. **Colas Aisladas por Servicio (`dict[ServiceType, collections.deque]`):**
   La clase `BranchQueueManager` mantiene un diccionario que mapea cada categoría de servicio a una estructura de cola de doble extremo (`collections.deque`) dedicada e independiente. Cada cliente que llega es encolado exclusivamente al final de la cola correspondiente a su trámite.

2. **Cola Única Compartida Intercalada (`list[Ticket]` o `deque[Ticket]`):**
   Todos los clientes, independientemente del tipo de servicio requerido, se insertan en una única estructura secuencial global en estricto orden cronológico de llegada.

A continuación se resume la comparación de características operativas entre ambos enfoques:

| Dimensión de Rendimiento | Colas Aisladas por Servicio (`dict[ServiceType, deque]`) | Cola Única Compartida (`list` o `deque`) |
| :--- | :--- | :--- |
| **Complejidad de `call_next(service)`** | **$O(1)$** (acceso directo por hash + extracción frontal) | **$O(N)$** (escaneo lineal buscando coincidencia de servicio) |
| **Extracción y Desencolado** | **$O(1)$** (desvinculación de punteros en bloque de cabeza) | **$O(N)$** (desplazamiento de elementos en memoria contigua) |
| **Sobrecarga de Filtrado** | **$0$** (cero asignación de memoria o recorridos) | **$O(N)$** (iteración y posible creación de listas temporales) |
| **Contención de Bloqueos (*Lock Contention*)** | Posibilidad de particionamiento granular de cerrojos por servicio | Un único punto de contención global para toda la sucursal |
| **Predecibilidad de Latencia** | Determinística y acotada en nanosegundos | Degenerativa en función del volumen total de clientes en espera |

### 1.2 Análisis de Complejidad Temporal: O(1) vs. O(N)

La operación más crítica y frecuente en la jornada operativa de la sucursal es el despacho de turnos mediante el método `call_next(service: ServiceType)`.

Bajo el modelo de **Colas Aisladas por Servicio**, la llamada a `call_next`:
1. Realiza una búsqueda directa por clave hash en el diccionario interno (`self._queues[service]`), cuya complejidad promedio y en el peor de los casos para un conjunto cerrado de claves es $O(1)$.
2. Si la cola contiene elementos, ejecuta `popleft()` sobre la instancia de `collections.deque`, extrayendo el elemento frontal en tiempo constante $O(1)$.
3. Por lo tanto, la complejidad temporal total del despacho es estrictamente **$O(1)$**. Este costo temporal es invariante: toma exactamente la misma cantidad de ciclos de procesador si hay 5 clientes esperando o si hay 50,000 en toda la sucursal.

Por el contrario, bajo el modelo de **Cola Única Compartida**:
1. Los turnos de depósitos, retiros y gestión de cuentas se encuentran intercalados cronológicamente.
2. Al invocar `call_next(service)`, el sistema debe realizar un escaneo lineal (*linear scan*) o búsqueda iterativa desde el inicio de la colección hasta encontrar el primer turno cuyo atributo `ticket.service` coincida con la categoría requerida.
3. En el peor escenario (por ejemplo, si no hay clientes esperando para ese servicio específico o el único cliente para ese servicio está al final de la cola), el algoritmo debe inspeccionar los $N$ elementos presentes en la cola.
4. Por lo tanto, la complejidad de localización es **$O(N)$**, penalizando drásticamente la latencia en momentos de alta afluencia en la sucursal.

### 1.3 Eliminación de Elementos y Sobrecarga de Filtrado

Más allá de la fase de búsqueda, la remoción física del elemento de la estructura de datos expone una diferencia sustancial en la sobrecarga de memoria y ciclos de CPU:

- **Estructura Interna de `collections.deque`:**
  En la implementación canónica de CPython, `collections.deque` está construida como una lista doblemente enlazada de bloques de memoria de tamaño fijo (64 elementos por bloque). La operación `popleft()` simplemente decrementa el índice del bloque de cabeza o libera el puntero al bloque vacío cuando se agota. No requiere mover, desplazar ni reasignar ningún otro elemento en la memoria. Su costo de extracción es puramente $O(1)$.

- **Penalización por Desplazamiento en Listas Contiguas (`list.pop(i)`):**
  Si la cola compartida se almacena en una lista estándar de Python (`list[Ticket]`, que internamente es un arreglo dinámico de punteros contiguos), la eliminación de un turno en una posición intermedia arbitraria $i$ exige desplazar en memoria todos los $N - i$ elementos subsiguientes hacia la izquierda para cerrar el espacio vacío. Este desplazamiento en memoria (*array shifting*) tiene una complejidad temporal de $O(N)$ y genera una pesada carga en el subsistema de caché de la CPU.

- **Filtrado Dinámico en Vuelo:**
  Implementaciones ingenuas que intentan resolver el problema mediante comprensiones de listas o filtros en memoria (como `[t for t in shared_queue if t.service == target]`) no solo consumen $O(N)$ en tiempo, sino que asignan colecciones intermedias en cada invocación de `call_next`. Esto dispara la fragmentación de memoria y la presión sobre el recolector de basura (*garbage collector*), incrementando la variabilidad de la latencia.

### 1.4 Granularidad de Bloqueos y Contención (Lock Contention)

En un entorno bancario de producción concurrente, múltiples agentes de atención interactúan simultáneamente con el gestor de colas:

- **Contención en Cola Única Compartida:**
  Toda mutación o lectura de la estructura compartida debe estar protegida por un cerrojo de exclusión mutua (`threading.Lock`). Si existe una sola cola, **todas las ventanillas de todos los servicios compiten por el mismo cerrojo global**. Un agente de retiro no puede llamar a un cliente mientras un agente de plataforma comercial está consultando o modificando la cola. Esto genera un cuello de botella severo de serialización de hilos (*thread serialization*), donde los hilos pasan la mayor parte de su tiempo esperando en estado de bloqueo.

- **Aislamiento y Concurrencia Granular en Colas por Servicio:**
  Al particionar el estado en colas independientes por servicio, el sistema habilita un particionamiento de bloqueos (*lock striping* o cerrojos por servicio). Un agente llamando a un turno de `deposit` opera sobre una estructura completamente desacoplada de la cola de `withdrawal`, reduciendo la contención de bloqueos prácticamente a cero entre distintos servicios. Además, dado que cada operación en la sección crítica dura un tiempo constante infinitesimal $O(1)$, la probabilidad de colisión entre agentes del mismo servicio se minimiza drásticamente.

---

## 2. Concurrencia y Sincronización en `call_next`

### 2.1 Escenario de Colisión Concurrente (Dos Agentes en Paralelo)

Considere un escenario de alta concurrencia en la oficina principal del Banco Meridional:
- La **Ventanilla 1** (atendida por el **Agente A**) y la **Ventanilla 2** (atendida por el **Agente B**) están configuradas simultáneamente para atender trámites de `ServiceType.DEPOSIT`.
- En la cola de espera de depósitos aguardan varios clientes, encabezados por el cliente con el turno `DEP-010`, seguido por `DEP-011`.
- En el instante exacto $t_0$, tanto el Agente A como el Agente B terminan la atención de sus clientes previos y presionan simultáneamente la opción de llamar al siguiente turno en sus respectivas terminales, invocando concurrentemente el método `call_next(ServiceType.DEPOSIT)`.

Si el gestor de colas no implementa una política estricta de exclusión mutua y un orden correcto de mutación de estado, los dos hilos de ejecución colisionarán inevitablemente.

### 2.2 Anatomía de la Condición de Carrera: Check-Then-Act (TOCTOU)

El riesgo crítico en este escenario es una condición de carrera del tipo **Comprobación y Acción Posterior** (*Check-Then-Act*, conocida formalmente en seguridad informática como *Time-of-Check to Time-of-Use* o **TOCTOU**).

El fallo se desglosa en la siguiente secuencia temporal sin sincronización:
1. **Comprobación Simultánea (*Time of Check*):** El hilo del Agente A inspecciona la cabeza de la cola de depósitos y comprueba que hay un turno disponible: observa el turno `DEP-010`. Casi de forma idéntica, antes de que el Agente A altere la estructura de datos, el hilo del Agente B inspecciona exactamente la misma cabeza de cola y comprueba que `DEP-010` sigue allí.
2. **Ventana de Vulnerabilidad (*Race Window*):** Entre el momento en que se inspecciona el turno y el momento en que se remueve o se asigna a la ventanilla, existe una brecha temporal donde el estado visualizado por ambos hilos es idéntico pero obsoleto (*stale state*).
3. **Acción Duplicada (*Time of Use*):**
   - El Agente A actualiza su terminal y convoca por megafonía al turno `DEP-010` hacia la Ventanilla 1.
   - El Agente B actualiza su terminal y convoca por megafonía al turno `DEP-010` hacia la Ventanilla 2.
4. **Impacto en el Negocio y la Sucursal:**
   - **Confusión y Caos:** El cliente titular de `DEP-010` escucha su número asignado a dos ventanillas diferentes simultáneamente, sin saber a cuál dirigirse.
   - **Pérdida de Invariantes del Sistema:** Dos ventanillas operan sobre la misma transacción, violando el Principio IV de la Constitución (Desacoplamiento de Agentes y Ventanillas).
   - **Salto de Turno (*Starvation*):** El cliente con el turno `DEP-011` que debió ser atendido por el segundo agente permanece injustamente en espera.

### 2.3 Visualización del Fallo de Concurrencia

A continuación se compara el flujo temporal de colisión sin sincronización frente al flujo protegido mediante sección crítica:

```text
========================================================================================
ESCENARIO 1: COLISIÓN CONCURRENTE NO PROTEGIDA (FALLO TOCTOU)
========================================================================================
Tiempo   Agente A (Ventanilla 1)                Agente B (Ventanilla 2)
------   -----------------------                -----------------------
 t0      call_next(DEPOSIT)                     call_next(DEPOSIT)
 t1      Lee cabeza de cola -> DEP-010          .
 t2      .                                      Lee cabeza de cola -> DEP-010 (Visto doble!)
 t3      Asigna DEP-010 a Ventanilla 1          .
 t4      .                                      Asigna DEP-010 a Ventanilla 2
 t5      Extrae DEP-010                         Extrae DEP-011 (o corrompe punteros)
         💥 RESULTADO: ¡DEP-010 fue llamado a dos ventanillas al mismo tiempo!

========================================================================================
ESCENARIO 2: FLUJO PROTEGIDO CON EXCLUSIÓN MUTUA Y EXTRACCIÓN INMEDIATA (DISEÑO CORRECTO)
========================================================================================
Tiempo   Agente A (Ventanilla 1)                Agente B (Ventanilla 2)
------   -----------------------                -----------------------
 t0      call_next(DEPOSIT)                     call_next(DEPOSIT)
 t1      [Adquiere self._lock]                  [Espera en bloqueo de cerrojo...]
 t2      MUTACIÓN 1: q.popleft() -> DEP-010     [Espera...]
         (DEP-010 removido instantáneamente)    .
 t3      [Libera self._lock y retorna DEP-010]  .
 t4      .                                      [Adquiere self._lock]
 t5      .                                      MUTACIÓN 2: q.popleft() -> DEP-011
 t6      .                                      [Libera self._lock y retorna DEP-011]
         ✅ RESULTADO: Agente A atiende DEP-010 y Agente B atiende DEP-011. Despacho justo.
```

---

## 3. Orden Crítico de Mutación de Estado

### 3.1 Respuesta a la Pregunta Central: Mutación Mandatoria Inicial

Ante la interrogante de diseño:

> **¿Qué mutación de estado debe ocurrir primero para garantizar que no se llame al mismo cliente dos veces?**

La respuesta arquitectónica y formal es:

> **La mutación de estado que debe ocurrir primero, de manera inmediata e indivisible, es la extracción atómica y desvinculación física del turno de la colección de espera activa (`popleft()` sobre `self._queues[service]`) bajo exclusión mutua (`threading.Lock`), ANTES de propagar o retornar la referencia del turno al agente o ventanilla invocante.**

Cualquier arquitectura alternativa que intente primero marcar el turno en memoria (por ejemplo, transicionar una bandera `ticket.status = SERVING`) manteniendo el turno dentro de la lista de espera expone una ventana de vulnerabilidad si la colección es iterable por otros hilos. Al remover físicamente el objeto de la cola mediante `popleft()`, el turno deja de existir de inmediato para cualquier otro hilo que adquiera el cerrojo una fracción de microsegundo después.

### 3.2 Justificación de la Extracción Atómica (`popleft`) dentro de la Sección Crítica

La extracción mediante `popleft()` en la sección crítica asegura tres garantías esenciales de integridad:

1. **Transferencia Exclusiva de Propiedad (*Single Ownership Transfer*):**
   Al ejecutarse `popleft()`, la referencia al objeto `Ticket` se extrae de la estructura de datos compartida y pasa a estar contenida únicamente en la variable local del hilo en ejecución. Ningún otro hilo o agente puede obtener una referencia a dicho turno a través de la cola.
2. **Invariante de Estado del Turno:**
   Dentro de la misma sección protegida por el cerrojo, el turno experimenta la mutación de su ciclo de vida desde `TicketStatus.WAITING` hacia `TicketStatus.SERVING`, registrando el identificador del agente y la ventanilla asignada. Esta atomicidad evita estados inconsistentes donde un turno figure como "en atención" pero continúe dentro de la cola de espera.
3. **Determinismo para Invocaciones Concurrentes Subsiguientes:**
   Cuando el segundo hilo (Agente B) obtiene el control del cerrojo, el estado interno de la cola ya refleja fielmente la extracción previa: la nueva cabeza es indiscutiblemente el siguiente cliente en estricto orden FIFO (`DEP-011`).

### 3.3 Comportamiento en Casos Borde (Cliente Único, Cola Vacía, Falla del Agente)

El diseño del método `call_next` garantiza estabilidad ante todas las condiciones de borde operativas:

- **Escenario de Cliente Único en Cola:**
  Si únicamente existe un cliente esperando en la sucursal (`DEP-010`) y dos agentes invocan `call_next(DEPOSIT)` simultáneamente:
  1. El Agente A adquiere el cerrojo, extrae `DEP-010` mediante `popleft()`, dejando la longitud de la cola en $0$, y libera el cerrojo.
  2. El Agente B adquiere el cerrojo a continuación, evalúa `len(self._queues[service]) == 0`, y lanza inmediatamente la excepción tipificada `EmptyQueueError`.
  3. No se produce doble llamada ni estados corrompidos: el Agente A recibe al cliente y el Agente B es informado limpiamente de que no restan clientes por atender.

- **Escenario de Cola Vacía (*Fail-Fast*):**
  Si no hay clientes en la cola al momento de la invocación, la verificación de longitud se realiza bajo el cerrojo y se lanza de inmediato `EmptyQueueError` sin alterar ningún contador, timestamp ni lista de historial. Esta comprobación es puramente libre de efectos colaterales (*fail-fast* sin mutaciones residuales).

- **Falla del Agente o Excepción no Controlada (*Agent Crash*):**
  La gestión del cerrojo se implementa mediante administradores de contexto idiomáticos (`with self._lock:`). Si el hilo del agente experimenta un fallo de memoria, interrupción o excepción imprevista durante el despacho:
  - El administrador de contexto garantiza que el cerrojo siempre sea liberado en el bloque de salida (`__exit__`), previniendo condiciones de bloqueo mutuo (*deadlock*) en la sucursal.
  - Dado que la extracción atómica ya retiró el turno defectuoso, las demás ventanillas de la sucursal continúan atendiendo a los clientes siguientes con total normalidad, preservando la continuidad del negocio exigida por el Principio IV de la Constitución.

---

## 4. Alineación con los Principios de la Constitución

### 4.1 Principio II: Despacho Justo FIFO

El **Principio II de la Constitución de Branch Queue** mandata que la distribución del trabajo debe adherirse estrictamente a una disciplina de cola transparente, priorizando al cliente con mayor tiempo de espera (*Longest-Waiting Priority*) bajo el orden cronológico de llegada (FIFO).

La arquitectura basada en colas independientes por servicio satisface este mandato de manera natural e inviolable:
- Cada estructura `collections.deque` añade los turnos emitidos exclusivamente por el extremo derecho (`append()`), sellando su marca temporal inmutable de creación.
- El método `call_next` extrae invariablemente por el extremo izquierdo (`popleft()`), garantizando matemáticamente que el cliente con mayor tiempo de permanencia en la sucursal bancaria para ese servicio sea el primero en ser llamado.
- Se elimina por diseño cualquier posibilidad de inanición (*starvation*) o alteración arbitraria de prioridades dentro de la categoría, garantizando una experiencia de usuario equitativa y auditable.

### 4.2 Principio IV: Desacoplamiento de Agentes y Ventanillas

El **Principio IV** exige que los puestos de atención y los agentes operen con total autonomía e independencia, de modo que la operativa de una ventanilla no bloquee ni comprometa el procesamiento en paralelo de las demás ventanillas de la sucursal.

El diseño del gestor de colas materializa este desacoplamiento en tres frentes:
1. **Aislamiento de Estado:** Las ventanillas no comparten variables de sesión ni estados transitorios entre sí. La interacción con el núcleo de colas se limita a llamadas puntuales, atómicas y de duración infinitesimal a `call_next`.
2. **Resiliencia ante Pausas o Interrupciones:** Si un cajero en la Ventanilla 1 debe suspender temporalmente su atención, salir a receso o si su terminal sufre una desconexión abrupta, la cola general de la sucursal no sufre impacto alguno. Los cajeros en las Ventanillas 2, 3 y 4 continúan llamando y atendiendo turnos sin interrupciones.
3. **Secciones Críticas Mínimas:** La protección por cerrojo (`threading.Lock`) se mantiene activa únicamente durante el instante de extracción del turno (`popleft()`), liberándose inmediatamente. El tiempo durante el cual el agente realmente atiende al cliente en mostrador transcurre completamente por fuera del cerrojo, permitiendo concurrencia masiva y simultánea en la oficina.

### 4.3 Principio V: Estructuras de Datos Canónicas en Python

El **Principio V** establece que toda la lógica de dominio debe implementarse en Python moderno e idiomático, empleando exclusivamente tipos y estructuras canónicas de la biblioteca estándar, sin incurrir en dependencias externas innecesarias.

La arquitectura implementada en `BranchQueueManager` honra plenamente este principio:
- **`collections.deque`**: Provee la semántica FIFO con garantías formales de complejidad temporal $O(1)$ para inserción y extracción en extremos, implementada a nivel de lenguaje en C sin sobrecarga.
- **`dict[ServiceType, deque]`**: Ofrece indexación directa y tipada para la segregación de colas sin necesidad de motores de búsqueda ni bases de datos intermedias en memoria.
- **`enum.Enum`**: Proporciona seguridad de tipos estricta para `ServiceType` y `TicketStatus`, evitando cadenas de texto mágicas y facilitando el análisis estático con herramientas como `mypy`.
- **`threading.Lock`**: Otorga primitivas de sincronización nativas y directas del sistema operativo para salvaguardar la concurrencia con cero sobrecarga externa.
- **Cero Dependencias Externas:** El núcleo del motor de colas preserva una portabilidad total, ejecución ligera y alta fiabilidad en cualquier entorno estándar de Python 3.11+.
