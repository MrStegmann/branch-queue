# Research & Architectural Findings: Design Notes (`DESIGN.md`)

**Feature Branch**: `002-design-notes`  
**Date**: 2026-11-08  
**Status**: Completed  

---

## 1. Algorithmic Efficiency: Per-Service Queue vs. Single Shared Queue

### Context
In a branch queue management system like Banco Meridional, clients arrive requesting specific service categories (`deposit`, `withdrawal`, `account_management`). Service counters/agents are assigned to specific services (or request tickets for a specific service when ready). We evaluated two architectural models for managing waiting clients:
1. **Per-Service Isolated Queues** (`dict[ServiceType, collections.deque]`): Separate FIFO queue for each service category.
2. **Single Shared Queue** (`list[Ticket]` or `deque[Ticket]`): All tickets regardless of service type placed into a single shared chronological line.

### Comparison Matrix

| Dimension | Per-Service Queue (`dict[ServiceType, deque]`) | Single Shared Queue (`list` or `deque`) |
| :--- | :--- | :--- |
| **`call_next(service)` Complexity** | **$O(1)$** direct hash lookup + $O(1)$ `popleft()` | **$O(N)$** linear scan to search for the next matching service ticket |
| **Ticket Deletion/Extraction** | **$O(1)$** head removal from doubly linked block | **$O(N)$** removal from intermediate list index (shifting elements) |
| **Filtering Overhead** | **$0$** (No traversal or temporary allocations) | **$O(N)$** iteration and potential filtering allocations |
| **Lock Granularity & Contention** | Capable of per-queue lock partitioning ($L_{\text{deposit}}, L_{\text{withdrawal}}, \dots$) | Single global lock contention across all service agents and counters |
| **Memory Allocation** | Dedicated small bounded deques, cache-friendly blocks | Single large dynamic array; fragmented or high-turnover memory churn |

### Decisions
- **Decision**: Adopt and document the **Per-Service Isolated Queue** model as the primary operational architecture.
- **Rationale**: `call_next` is the highest-frequency operational dispatch method in a busy branch. An $O(1)$ guarantee ensures deterministic, constant-time performance regardless of whether there are 10 or 100,000 waiting clients across the branch.
- **Alternatives Considered**: 
  - *Single Shared Queue with On-the-Fly Filtering*: Rejected due to $O(N)$ search penalty and $O(N)$ list mutation overhead upon popping intermediate elements.
  - *Indexed In-Memory Multi-Map*: Rejected because standard library `collections.deque` mapped by enum keys (`dict[ServiceType, deque]`) already provides strictly $O(1)$ append and popleft without third-party indexing overhead.

---

## 2. Concurrency Hazards & State Mutation Ordering

### Context
When multiple counters handle the same service category (e.g., Counter 1 and Counter 2 both serving `deposit`), both agents can invoke `call_next(ServiceType.DEPOSIT)` simultaneously. Without correct concurrency controls and state mutation ordering, race conditions arise.

### Concurrency Hazard: "Check-Then-Act" (Time-of-Check to Time-of-Use / TOCTOU)
1. **Unsynchronized Scenario**:
   - Agent A reads the front of the queue: sees Ticket #10.
   - Agent B reads the front of the queue: also sees Ticket #10 (before Agent A removes it).
   - Agent A calls Customer #10 to Counter 1.
   - Agent B calls Customer #10 to Counter 2.
   - **Result**: Dual dispatch failure, counter conflict, customer confusion, and state corruption.

2. **Analysis of State Mutation Ordering**:
   - *Question*: **¿Qué mutación de estado debe ocurrir primero para garantizar que no se llame al mismo cliente dos veces?**
   - *Resolution*: The state mutation that **MUST occur first** is the **atomic extraction and removal of the ticket from the active waiting collection** (`q.popleft()`, or transitioning state from `WAITING` to `SERVING` within a mutual exclusion critical section) **prior to yielding control or returning the ticket reference to the calling agent**.
   - By executing this extraction atomically under mutual exclusion (`threading.Lock` or atomic test-and-set):
     - The first thread to acquire the lock pops Ticket #10 and immediately removes it from the queue.
     - When the second thread acquires the lock, Ticket #10 is no longer present; it pops Ticket #11 (or receives `EmptyQueueError` if the queue is now empty).
     - It is physically impossible for Ticket #10 to be returned to more than one agent.

### Decisions
- **Decision**: Explicitly document the "Check-Then-Act" failure mode and formulate the definitive answer emphasizing that **atomic extraction (`popleft` / removal from waiting collection) within the critical section must precede ticket assignment and counter presentation**.
- **Rationale**: Any delay between reading the next ticket and modifying the waiting collection exposes a race window where concurrent workers read stale state.
- **Alternatives Considered**:
  - *Two-Phase Locking with Status Flags (`WAITING` -> `RESERVED` -> `SERVING`)*: Evaluated. While useful in distributed databases with long transactions, for an in-memory queue coordinator, atomic `popleft()` under a thread lock is strictly superior, simpler, and free of deadlock risk.

---

## 3. Linguistic & Document Quality Guidelines

### Context
Acceptance Criteria mandate that the entire document `DESIGN.md` must be written in **Spanish**, while preserving standard technical identifiers.

### Guidelines
1. **Language**: 100% Spanish prose, section headers, technical rationale, and explanations.
2. **Technical Identifiers**: Preserve canonical code symbols verbatim in backticks:
   - Methods: `call_next`, `issue_ticket`, `peek_next`
   - Data structures: `collections.deque`, `popleft()`, `dict`
   - Complexity notation: $O(1)$, $O(N)$
   - Status enums: `WAITING`, `SERVING`, `COMPLETED`
   - File names: `DESIGN.md`, `branch_queue.py`, `queue_manager.py`
3. **Clarity**: Use standard Spanish computer science and software architecture terminology:
   - "Condición de carrera" (Race condition)
   - "Exclusión mutua" (Mutual exclusion)
   - "Complejidad algorítmica temporal" (Time algorithmic complexity)
   - "Mutación atómica de estado" (Atomic state mutation)
   - "Despacho FIFO" (FIFO dispatch)

---

## 4. Document Structure for `DESIGN.md`

### Proposed Outline
1. **Título y Propósito**: Visión general del documento de diseño arquitectónico.
2. **1. Análisis de Eficiencia: Cola por Servicio vs. Cola Única Compartida**:
   - Justificación de la estructura `dict[ServiceType, deque]`.
   - Comparación matemática de complejidad ($O(1)$ vs. $O(N)$).
   - Impacto en contención de bloqueos (*lock contention*) y asignación de memoria.
3. **2. Concurrencia y Sincronización en `call_next`**:
   - El escenario de dos agentes simultáneos para el mismo servicio.
   - Explicación de la condición de carrera (*Check-Then-Act* / TOCTOU).
   - Diagrama de flujo temporal (secuencia de colisión sin sincronización vs. sincronizada).
4. **3. Orden Crítico de Mutación de Estado**:
   - Respuesta directa y destacada a la pregunta central: *¿Qué mutación de estado debe ocurrir primero?*
   - Demostración de por qué la extracción atómica (`popleft`) previa al retorno del ticket previene el doble llamado.
   - Manejo de casos borde (un solo cliente en cola, cola vacía, desconexión de agente).
5. **4. Conclusiones y Alineación con la Constitución**:
   - Resumen de garantías de equidad FIFO, desacoplamiento de agentes y seguridad de hilos (*thread safety*).

