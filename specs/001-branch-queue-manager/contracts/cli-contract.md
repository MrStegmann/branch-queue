# Terminal CLI Contract: Banco Meridional Queue Manager

**Feature Branch**: `001-branch-queue-manager`  
**Date**: 2026-10-27  
**Module**: `src.cli.terminal`  

---

## 1. Overview

The terminal command-line interface provides branch staff and receptionists with a keyboard-driven management console. It exposes all domain workflows while guaranteeing resilient input handling and zero unhandled crash terminations.

---

## 2. Command Invocation

```bash
python -m src.cli.terminal
# or
python main.py
```

### Exit Codes
- `0`: Clean exit chosen by user via menu option 6 or EOF (`Ctrl+D`).
- `130`: Clean shutdown via keyboard interrupt (`Ctrl+C`).
- `1`: Unexpected fatal error.

---

## 3. Main Menu Layout

Upon startup or after completing any workflow, the console displays:

```text
============================================================
           BANCO MERIDIONAL - QUEUE MANAGER v1.0
============================================================
1. Issue New Ticket (Client Arrival)
2. Call Next Client (Service Counter Dispatch)
3. Peek Next Client (Non-Mutating Inspection)
4. List All Waiting Clients
5. View Branch Statistics & Queue Depth
6. Exit System
============================================================
Select an option [1-6]: 
```

---

## 4. Option Workflows & Prompt Contracts

### Option 1: Issue New Ticket

1. **Prompt**: `Enter client name: `
   - If empty/whitespace: Outputs `[ERROR] Client name cannot be blank. Please try again.` and returns to menu.
2. **Prompt**:
   ```text
   Available Services:
     1. deposit
     2. withdrawal
     3. account_management
   Select service type (enter number or name): 
   ```
   - If invalid input: Outputs `[ERROR] Invalid service type '<input>'. Must be 'deposit', 'withdrawal', or 'account_management'.` and returns to menu without incrementing ticket sequence.
3. **Success Output**:
   ```text
   ------------------------------------------------------------
   [SUCCESS] Ticket Issued Successfully!
     Ticket Number : #1
     Client Name   : Alice Smith
     Service Type  : Deposit
     Issued At     : 2026-10-27 10:15:30
   ------------------------------------------------------------
   ```

---

### Option 2: Call Next Client

1. **Prompt**:
   ```text
   Select service line to dispatch:
     1. deposit
     2. withdrawal
     3. account_management
   Select service (number or name): 
   ```
2. **Outcome A (Client waiting)**:
   ```text
   ------------------------------------------------------------
   [DISPATCH] NOW SERVING:
     Ticket Number : #1
     Client Name   : Alice Smith
     Service Line  : Deposit
     Waiting Since : 2026-10-27 10:15:30
   ------------------------------------------------------------
   ```
3. **Outcome B (Empty queue)**:
   ```text
   ------------------------------------------------------------
   [INFO] No clients are currently waiting for 'Deposit'.
   ------------------------------------------------------------
   ```

---

### Option 3: Peek Next Client

1. **Prompt**:
   ```text
   Select service line to peek:
     1. deposit
     2. withdrawal
     3. account_management
   Select service (number or name): 
   ```
2. **Outcome A (Client waiting)**:
   ```text
   ------------------------------------------------------------
   [PEEK] Next in line for Deposit:
     Ticket Number : #3
     Client Name   : Charlie Brown
     Waiting Since : 2026-10-27 10:18:45
   (Note: Ticket remains in queue at position #1)
   ------------------------------------------------------------
   ```
3. **Outcome B (Empty queue)**:
   ```text
   ------------------------------------------------------------
   [INFO] No clients are currently waiting for 'Deposit'.
   ------------------------------------------------------------
   ```

---

### Option 4: List All Waiting Clients

- **Output (When clients waiting)**:
   ```text
   ============================================================
                      CURRENT BRANCH QUEUES
   ============================================================
   [DEPOSIT] (2 waiting)
     #3 - Charlie Brown (arrived 10:18:45)
     #5 - Daniel White (arrived 10:22:10)

   [WITHDRAWAL] (1 waiting)
     #2 - Bob Jones (arrived 10:16:12)

   [ACCOUNT MANAGEMENT] (0 waiting)
     -- No clients waiting --
   ============================================================
   Total Active Waiting Clients: 3
   ============================================================
   ```
- **Output (All empty)**:
   ```text
   [INFO] All branch queues are currently empty.
   ```

---

### Option 5: View Branch Statistics

- **Output**:
   ```text
   ============================================================
                     BRANCH QUEUE STATISTICS
   ============================================================
     Deposit Queue Depth            : 2
     Withdrawal Queue Depth         : 1
     Account Management Queue Depth : 0
   ------------------------------------------------------------
     Total Waiting Clients          : 3
     Snapshot Time                  : 2026-10-27 10:25:00
   ============================================================
   ```

---

### Option 6: Exit System

- **Output**:
   ```text
   Exiting Banco Meridional Queue Manager. Goodbye!
   ```
- Terminates process cleanly with exit code 0.

---

## 5. Input Resilience Contract

1. **Unrecognized Menu Choice**:
   - Input: `"foo"`, `"99"`, `""`
   - Output: `[ERROR] Invalid option 'foo'. Please enter a number between 1 and 6.`
   - Behavior: Redisplays menu without crashing or throwing exceptions.
2. **Whitespace Trimming**:
   - Input `"  Alice  "` -> stored as `"Alice"`.
   - Input `" 1 "` -> parsed as option 1.
3. **Service Input Flexibility**:
   - Number selection (`1`, `2`, `3`) or string names (`deposit`, `Deposit`, `DEPOSIT`) are all accepted.
