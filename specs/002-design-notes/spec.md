# Feature Specification: Design Notes (`DESIGN.md`)

**Feature Branch**: `002-design-notes`

**Created**: 2026-11-08

**Status**: Draft

**Input**: User description: "/speckit-specify # Docs: Design Notes (`DESIGN.md`)\n## Overview\nThe task is to create a design notes in the root of the project (`DESIGN.md`). This documents shall explain why using a separate queue for each service type makes `call_next` more efficient than using a single, shared queue; and describe what whould happen if two agents from the same service type calls `call_next` at the same time. In addition, we want to answer the questions \"What state mutation must occur first to ensure that the same client is not called twice?\".\n## What to do\n* Create a new file in the root directory of the project and call it `DESIGN.md`.\n* Explain why using a separate queue for each service type makes `call_next` more efficient than using a single, shared queue.\n* Describe what would happen if two agents handling the same service type were to call `call_next` simultaneously. What state mutation must occur first to ensure that the same client is not called twice?\n## Acceptance Criteria\n* The hole document MUST be in SPANISH.\n* The design note explains why a per-service structure is more efficient than a single shared list.\n* The design note addresses the scenario of concurrent `call_next` operations and identifies the correct order of mutation."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rationale for Per-Service Queue Efficiency (Priority: P1)

As a software engineer, system architect, or code reviewer, I want to consult an architectural design document (`DESIGN.md`) that explains why partitioning the queue by service type makes calling the next customer (`call_next`) significantly more efficient than maintaining a single shared queue, so that I can understand the underlying algorithmic and system performance trade-offs.

**Why this priority**: Understanding why the architecture uses separate queues for each service type is fundamental to the system's scalability and design integrity.

**Independent Test**: Can be validated by reading the "Eficiencia de Colas por Servicio vs. Cola Compartida" section of `DESIGN.md` and verifying that it clearly explains the computational complexity (O(1) direct retrieval vs. O(N) linear scanning/filtering) and operational efficiency gains of per-service queues.

**Acceptance Scenarios**:

1. **Given** a reader reviewing the system architecture, **When** they open `DESIGN.md` at the repository root, **Then** they find an analysis demonstrating why a per-service queue enables immediate O(1) customer retrieval for `call_next` without iterating or filtering through unrelated service requests.
2. **Given** a scenario comparing a single shared list against per-service queues, **When** `call_next` is invoked for a specific service type with $N$ pending tickets across all services, **Then** the document clearly contrasts the O(N) scanning penalty and overhead of the shared list with the direct O(1) access of dedicated queues.

---

### User Story 2 - Concurrency Hazards and State Mutation Ordering (Priority: P1)

As a backend engineer or systems designer, I want the design document to analyze what happens when two agents handling the same service type call `call_next` at the exact same moment, and to specify the exact state mutation order required to prevent the same customer from being called twice.

**Why this priority**: Concurrency safety is critical in customer service queuing systems; calling the same customer to two different counters creates immediate operational failure and customer friction.

**Independent Test**: Can be validated by inspecting the concurrency section of `DESIGN.md` and confirming it details the race condition scenario (read-then-act) and explicitly states which state mutation (atomic extraction/dequeuing or status change from `WAITING` to `SERVING`) must happen first.

**Acceptance Scenarios**:

1. **Given** two service agents attempting to serve the next customer simultaneously, **When** examining the concurrency section of `DESIGN.md`, **Then** the document details the step-by-step race condition that occurs without proper synchronization (both seeing the same top ticket and attempting to claim it).
2. **Given** the requirement to avoid duplicate ticket servicing, **When** reading the state mutation analysis, **Then** the document explicitly identifies and justifies the exact state mutation that must take place first (e.g., atomic dequeue / immediate removal from the pending queue before releasing locks or returning the customer to the agent).

---

### User Story 3 - Full Spanish Language and Document Standards Compliance (Priority: P2)

As a Spanish-speaking stakeholder, auditor, or engineer, I want the entire `DESIGN.md` file to be authored in Spanish with appropriate technical clarity and markdown structure, so that all project members have full comprehension of the architectural choices.

**Why this priority**: Compliance with the project documentation mandate ensures consistency, accessibility, and adheres strictly to the acceptance criteria.

**Independent Test**: Can be verified by performing a language audit on `DESIGN.md` to ensure that 100% of the narrative, analysis, headings, and explanations are written in Spanish.

**Acceptance Scenarios**:

1. **Given** the generated `DESIGN.md` file in the root of the repository, **When** reviewing the text content, **Then** the entire document is written in Spanish while accurately preserving technical identifiers (such as `call_next`, `DESIGN.md`, O(1), O(N)).
2. **Given** the document formatting requirements, **When** viewing `DESIGN.md`, **Then** it follows clean markdown conventions with clear headings, lists, and conceptual diagrams or code-agnostic flow representations.

---

### Edge Cases

- **Single Pending Customer**: What happens when only one customer is waiting in the queue and two agents invoke `call_next` simultaneously? The document must explain how the first agent acquires the ticket and the second agent receives an empty/none indicator safely.
- **Empty Service Queue**: How does the system handle concurrent calls when the queue for that service type has zero tickets? The document must confirm both agents receive an empty response without blocking or generating spurious state mutations.
- **Agent Failure After Mutation**: If an agent crashes or disconnects immediately after mutating the state to claim the ticket, what happens to the ticket lifecycle? The document should briefly touch upon how state transition boundaries isolate customer states.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A file named `DESIGN.md` MUST be created in the root directory of the project repository.
- **FR-002**: The entire content of `DESIGN.md` (all sections, explanations, headers, and descriptions) MUST be written in Spanish.
- **FR-003**: `DESIGN.md` MUST explain why using an independent queue for each service type (`deposit`, `withdrawal`, `account_management`) makes `call_next` more efficient than using a single shared queue.
- **FR-004**: `DESIGN.md` MUST detail the computational and operational differences between per-service queues (O(1) access) and a single shared queue (O(N) search and filtering).
- **FR-005**: `DESIGN.md` MUST describe the concurrency failure mode (race condition / *check-then-act*) that occurs if two agents of the same service type invoke `call_next` simultaneously without mutual exclusion.
- **FR-006**: `DESIGN.md` MUST answer the question: *"¿Qué mutación de estado debe ocurrir primero para garantizar que no se llame al mismo cliente dos veces?"* ("What state mutation must occur first to ensure that the same client is not called twice?") by identifying the initial mandatory mutation (removing the ticket from the waiting structure / atomically changing status from `WAITING` to `SERVING`).
- **FR-007**: `DESIGN.md` MUST maintain consistency with the architectural principles established in the Branch Queue Constitution (fair FIFO dispatch, agent decoupling, thread and execution safety).

### Key Entities

- **Documento de Diseño (`DESIGN.md`)**: The root markdown artifact documenting queue architecture rationale and concurrency synchronization principles.
- **Cola por Tipo de Servicio (`ServiceQueue`)**: Independent sequential FIFO queues partitioned by transaction category (`deposit`, `withdrawal`, `account_management`).
- **Operación de Despacho (`call_next`)**: The interface operation by which an available service counter/agent requests and claims the next customer in waiting order.
- **Transición de Estado del Ticket (`TicketStateMutation`)**: The atomic state transformation (from `WAITING` to `SERVING`, accompanied by removal from the waiting collection) that claims exclusivity over the customer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the narrative, explanations, and structure in `DESIGN.md` are written in Spanish.
- **SC-002**: A reader can verify within 1 minute of reading that the efficiency comparison articulates why per-service queues achieve O(1) dequeue time versus O(N) scan time for a shared queue.
- **SC-003**: A reader can verify within 1 minute of reading that the concurrency analysis clearly describes the simultaneous invocation scenario and explicitly designates the first required state mutation to prevent duplicate calls.
- **SC-004**: The file `DESIGN.md` exists directly at the project root (`./DESIGN.md`) and passes markdown linting and structure checks.

## Assumptions

- The project's existing domain model supports three primary service categories: `deposit`, `withdrawal`, and `account_management`.
- The target audience for `DESIGN.md` includes software architects, technical leads, and evaluators who expect rigorous conceptual rigor and clean markdown presentation.
- Function/method names like `call_next` and file names like `DESIGN.md` remain in English as standard code/system identifiers within the Spanish documentation.

