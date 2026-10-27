# Feature Specification: Banco Meridional Queue Manager

**Feature Branch**: `001-branch-queue-manager`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "Feature: Banco Meridional Queue Manager - Terminal-based queue management system for Banco Meridional to automate client flow, eliminate agent idle time, and optimize service-specific waiting queues prior to touchscreen kiosk integration."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Client Arrival & Sequential Ticket Issuance (Priority: P1)

When a client arrives at the branch, a branch receptionist or triage kiosk registers the client's name and requested service type (`deposit`, `withdrawal`, or `account_management`). The system issues an official ticket with an immutable timestamp and a unique, globally sequential ticket number that increases monotonically across all services.

**Why this priority**: Ticket issuance is the foundational entry point for the entire branch workflow. Without reliable, ordered ticket generation, no downstream service dispatch can occur.

**Independent Test**: Can be tested independently by issuing tickets across alternating service types and verifying that ticket numbers increment sequentially from 1 upwards without duplicates, gaps, or resets between categories.

**Acceptance Scenarios**:

1. **Given** an empty branch queue, **When** a client "Alice" arrives requesting "deposit", **Then** the system issues ticket #1 with client name "Alice", service type "deposit", and a recorded arrival timestamp.
2. **Given** ticket #1 was issued for "deposit", **When** client "Bob" requests "withdrawal", **Then** the system issues ticket #2 for "Bob" under "withdrawal".
3. **Given** ticket #2 was issued for "withdrawal", **When** client "Charlie" requests "deposit", **Then** the system issues ticket #3 for "Charlie" under "deposit".
4. **Given** any queue state, **When** a client provides an unsupported service type or empty name, **Then** the system rejects issuance with a clear validation error without incrementing the global counter.

---

### User Story 2 - Dedicated Service Agent Dispatch (Priority: P1)

A dedicated teller or service agent assigned to a specific service line (`deposit`, `withdrawal`, or `account_management`) requests the next client waiting for their specific service. The system instantly selects and dequeues the client who has been waiting the longest for that specific service (FIFO order), removing them from the waiting line.

**Why this priority**: Eliminating agent idle time and servicing clients strictly in order of arrival is the core business objective of Banco Meridional.

**Independent Test**: Can be tested independently by enqueuing multiple clients across distinct service categories, requesting "call next" for one category, and verifying that only the earliest arrival for that specific category is dequeued while other queues remain untouched.

**Acceptance Scenarios**:

1. **Given** clients Alice (arrival T1) and Charlie (arrival T3) are waiting for "deposit", **When** the deposit agent calls next, **Then** Alice is returned and dequeued, leaving Charlie as the sole waiting deposit client.
2. **Given** Charlie is waiting for "deposit" and Bob is waiting for "withdrawal", **When** the withdrawal agent calls next, **Then** Bob is returned and dequeued, leaving Charlie unaffected in the deposit queue.
3. **Given** no clients are waiting for "account_management", **When** an account manager calls next, **Then** the system notifies the agent with a meaningful, non-crashing status message indicating the queue is empty.

---

### User Story 3 - Queue Oversight & Non-Mutating Inspection (Priority: P2)

Branch supervisors or counter agents need to view upcoming clients or examine the full state of branch queues without altering client positions or dispatching tickets prematurely.

**Why this priority**: State inspection provides operational visibility for floor managers to balance workloads and answer customer inquiries without disrupting line order.

**Independent Test**: Can be tested independently by issuing tickets, calling "peek next" and "list waiting", and confirming the queue depth, ordering, and ticket sequence remain 100% identical before and after inspection.

**Acceptance Scenarios**:

1. **Given** clients are waiting in a service queue, **When** an agent peeks at the next client, **Then** the system displays the next waiting client's ticket details without removing them from the queue.
2. **Given** a service queue is empty, **When** an agent peeks at the next client, **Then** the system returns a safe, descriptive indication that no clients are waiting without throwing an unhandled exception.
3. **Given** clients waiting across multiple service lines, **When** a supervisor requests the full waiting list, **Then** the system presents all active clients grouped by service type in strict order of their arrival.

---

### User Story 4 - Branch Real-Time Statistics & Load Monitoring (Priority: P2)

Floor managers and monitoring screens require an instant snapshot of waiting volume across all service lines to gauge branch congestion and identify bottlenecks.

**Why this priority**: Real-time metrics allow management to reassign teller staff dynamically based on queue depth before wait times escalate.

**Independent Test**: Can be tested independently by querying queue statistics across various branch states (empty, partially populated, and after dispatches) and verifying exact counts per service category and accurate total counts.

**Acceptance Scenarios**:

1. **Given** an empty branch system, **When** statistics are requested, **Then** each service count is reported as 0 and the overall total count is 0.
2. **Given** 2 clients in "deposit", 3 in "withdrawal", and 1 in "account_management", **When** statistics are requested, **Then** the system reports `deposit: 2`, `withdrawal: 3`, `account_management: 1`, and `total: 6`.
3. **Given** active waiting counts, **When** a client is called and dequeued, **Then** the corresponding service count and total count decrement immediately.

---

### User Story 5 - Interactive Terminal Operations Interface (Priority: P3)

Branch staff interact with the queue manager through a resilient text-based terminal menu loop that supports all operational workflows (issuing tickets, calling next, viewing queues, viewing stats, exiting) with clear prompts and input guards.

**Why this priority**: Provides the immediate operational user interface for staff before physical kiosk hardware is installed.

**Independent Test**: Can be tested independently by navigating through menu options, entering invalid menu choices or invalid service inputs, and confirming the application prompts gracefully without terminating unexpectedly.

**Acceptance Scenarios**:

1. **Given** the terminal application is running, **When** a user enters menu option 1, **Then** the system prompts for client name and service type, issues the ticket, and displays the confirmation before returning to the main menu.
2. **Given** the terminal menu is displayed, **When** an invalid or unrecognized menu option is entered, **Then** the system reports an invalid choice message and redisplays the menu without crashing.
3. **Given** any menu prompt, **When** the user selects the exit option, **Then** the system cleanly shuts down.

---

### Edge Cases

- **Empty Queue Access**: Calling or peeking next on an empty service category must return a clear informative status rather than crashing or raising unhandled exceptions.
- **Service Name Normalization & Validation**: Case differences or whitespace (e.g. `" Deposit "` vs `"deposit"`) must either be cleanly normalized or validated, and invalid service inputs (e.g. `"loan"`) must be rejected at issuance.
- **Empty or Whitespace Client Name**: Registering a ticket with a blank or whitespace-only name must be rejected with an appropriate error message.
- **Service Isolation**: Dispatches or state changes in one service category must never modify, reorder, or alter the queue state of any other service category.
- **Concurrent Dispatch Protection**: If multiple agents for the same service invoke dispatch simultaneously, state transition (removal from queue) must precede any presentation or service assignment to prevent duplicate calls of the same client.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST assign a strictly sequential, monotonic integer ticket number starting at 1 that increases globally across all service categories.
- **FR-002**: System MUST validate and record client name, valid service type (`deposit`, `withdrawal`, `account_management`), and arrival timestamp upon ticket creation.
- **FR-003**: System MUST reject ticket issuance requests with invalid service types or blank client names, providing descriptive feedback without advancing the global ticket counter.
- **FR-004**: System MUST maintain separate, independent first-in-first-out (FIFO) waiting lines for each supported service category to guarantee fair dispatch based on arrival order.
- **FR-005**: System MUST dequeue and return the longest-waiting client for a specified service category when called by an agent.
- **FR-006**: System MUST handle "call next" and "peek next" requests on empty queues gracefully without crashing or causing application instability.
- **FR-007**: System MUST provide a non-mutating peek capability that reveals the next waiting client for a specified service without altering queue ordering or membership.
- **FR-008**: System MUST provide a non-mutating overview of all currently waiting clients grouped by service type in order of arrival.
- **FR-009**: System MUST report real-time waiting counts per service type alongside an aggregate total count across the entire branch.
- **FR-010**: System MUST provide an interactive terminal menu loop enabling branch staff to issue tickets, call next, inspect queues, view statistics, and exit safely.
- **FR-011**: System MUST document the architectural justification for independent service queues over a monolithic list, detailing algorithmic complexity advantages for dispatch and inspection.
- **FR-012**: System MUST document the concurrent dispatch race condition scenario and specify the necessary state mutation ordering to prevent duplicate ticket servicing.

### Key Entities

- **Ticket**: An immutable domain record representing an enqueued client. Attributes:
  - `number`: Unique, globally sequential integer (1, 2, 3, ...).
  - `client_name`: Validated non-empty string representing the client.
  - `service_type`: Standardized service category (`deposit`, `withdrawal`, or `account_management`).
  - `issued_at`: Timestamp recording the exact moment of ticket creation.
- **Branch Queue System**: The core coordinator maintaining isolated service waiting lines, the global sequence counter, and operational interfaces for enqueueing, dispatching, and reporting.
- **Service Category**: The defined banking operations supported by the branch (`deposit`, `withdrawal`, `account_management`).
- **Branch Statistics**: A structured summary of active client counts per service category and total waiting volume.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Dispatch ("call next") and inspection ("peek next") operations execute with immediate $O(1)$ efficiency regardless of total branch volume or queue depth.
- **SC-002**: 100% of issued tickets possess globally unique, contiguous, and strictly ascending ticket numbers.
- **SC-003**: 100% of client calls within any given service queue adhere strictly to first-come, first-served (FIFO) arrival order.
- **SC-004**: Zero application crashes or unhandled exceptions when querying or dispatching from empty service queues or receiving invalid menu selections.
- **SC-005**: Queue inspection operations (`peek_next`, `list_waiting`, `stats`) are 100% side-effect-free, never mutating queue order, timestamps, or client counts.
- **SC-006**: Branch staff can complete any primary workflow (issuing a ticket, dispatching next, or viewing stats) within 3 menu interactions in the terminal interface.

## Assumptions

- **Service Categories**: The initial deployment supports exactly three fixed service types: `deposit`, `withdrawal`, and `account_management`. Dynamic service registration is out of scope for v1.
- **Data Persistence**: The queue manager operates in-memory for the duration of the branch session. Persistent database storage across application restarts is out of scope for this version.
- **Concurrency Environment**: The system is designed for single-process terminal execution, but its core data structures and architectural design explicitly define thread-safety and atomic mutation rules for future multi-agent kiosk integration.
- **Time Source**: System timestamps rely on standard local branch system time.
- **Dependencies**: The implementation relies strictly on the Python standard library with zero external runtime dependencies.
