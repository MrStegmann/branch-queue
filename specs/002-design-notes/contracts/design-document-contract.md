# Contract: Architectural Design Document (`DESIGN.md`)

**Feature Branch**: `002-design-notes`  
**Date**: 2026-11-08  
**Artifact Target**: `./DESIGN.md`  

---

## 1. Specification Overview

This contract establishes the structural, linguistic, and thematic requirements for the root-level architectural document `DESIGN.md`.

---

## 2. Document Schema & Mandatory Sections

`DESIGN.md` MUST follow the following hierarchical structure:

```markdown
# Notas de Diseño Arquitectónico: Sistema de Colas de Sucursal (`BranchQueueManager`)

## 1. Eficiencia Algorítmica: Cola por Servicio vs. Cola Única Compartida
- 1.1 Contexto y Modelado de Datos
- 1.2 Análisis de Complejidad Temporal: O(1) vs. O(N)
- 1.3 Eliminación de Elementos y Sobrecarga de Filtrado
- 1.4 Granularidad de Bloqueos y Contención (Lock Contention)

## 2. Concurrencia y Sincronización en `call_next`
- 2.1 Escenario de Colisión Concurrente (Dos Agentes en Paralelo)
- 2.2 Anatomía de la Condición de Carrera: Check-Then-Act (TOCTOU)
- 2.3 Visualización del Fallo de Concurrencia

## 3. Orden Crítico de Mutación de Estado
- 3.1 Respuesta a la Pregunta Central: Mutación Mandatoria Inicial
- 3.2 Justificación de la Extracción Atómica (`popleft`) dentro de la Sección Crítica
- 3.3 Comportamiento en Casos Borde (Cliente Único, Cola Vacía, Falla del Agente)

## 4. Alineación con los Principios de la Constitución
- 4.1 Principio II: Despacho Justo FIFO
- 4.2 Principio IV: Desacoplamiento de Agentes y Ventanillas
- 4.3 Principio V: Estructuras de Datos Canónicas en Python
```

---

## 3. Content Assertions & Validation Criteria

### Assertion 1: Language Compliance
- **Rule**: All headers, prose, analysis, and explanations MUST be written in Spanish.
- **Allowed Exceptions**: Standard technical code identifiers, keywords, and complexity indicators in backticks (e.g., `call_next`, `deque.popleft()`, `ServiceType`, `O(1)`, `O(N)`, `threading.Lock`, `WAITING`, `SERVING`).
- **Validation**:
  - Zero English prose sentences.
  - Consistent Spanish grammatical conventions and diacritics (acentos, signos de interrogación).

### Assertion 2: Efficiency Comparison
- **Rule**: The document MUST clearly contrast the time complexity of `call_next` in both models:
  - Per-service queue: $O(1)$ constant time lookup and extraction.
  - Single shared queue: $O(N)$ linear scan to find matching ticket + $O(N)$ list shift or filtering penalty.
- **Validation**: Both Big-O notations must be explicitly present, compared, and explained.

### Assertion 3: Concurrency Hazard & TOCTOU
- **Rule**: The document MUST describe the step-by-step failure mode when two agents call `call_next` simultaneously without synchronization.
- **Validation**: Must identify the hazard as a race condition / *Check-Then-Act* (or TOCTOU) where both agents read the same front ticket before either removes it.

### Assertion 4: State Mutation Ordering
- **Rule**: The document MUST answer: *"¿Qué mutación de estado debe ocurrir primero para garantizar que no se llame al mismo cliente dos veces?"*
- **Validation**:
  - The answer must explicitly designate the **atomic extraction and removal of the ticket from the waiting structure** (`popleft()`) inside the mutual exclusion critical section before returning the ticket reference to the agent.
  - It must explain why this mutation guarantees that the second agent immediately sees the next ticket or an empty queue.

