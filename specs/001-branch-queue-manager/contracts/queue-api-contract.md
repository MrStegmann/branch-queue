# Programmatic API Contract: BranchQueueManager

**Feature Branch**: `001-branch-queue-manager`  
**Date**: 2026-10-27  
**Module**: `src.services.queue_manager`  

---

## 1. Overview

The `BranchQueueManager` provides the authoritative programmatic interface for all Banco Meridional queue operations. It enforces the Constitution principles of strict sequential issuance, $O(1)$ FIFO dispatch, side-effect-free inspection, and thread safety.

---

## 2. Type Signatures & API Specification

### 2.1 Initialization

```python
class BranchQueueManager:
    def __init__(self, time_provider: Optional[Callable[[], datetime]] = None) -> None:
        """
        Initializes the BranchQueueManager with isolated queues for each ServiceType.
        
        Args:
            time_provider: Optional factory returning datetime instances.
                           Defaults to lambda: datetime.now(timezone.utc) or system local time.
                           Enables deterministic time injection in tests.
        """
```

---

### 2.2 `issue_ticket`

```python
def issue_ticket(self, client_name: str, service: Union[str, ServiceType]) -> Ticket:
    """
    Issues a new sequential ticket for a validated client and service type.
    
    Preconditions:
        - client_name is non-empty and contains non-whitespace characters.
        - service matches a valid ServiceType enum value or string representation.
        
    Postconditions:
        - Returned Ticket has a monotonic number incremented by exactly 1 from previous.
        - Ticket is appended to the corresponding ServiceType FIFO queue.
        - Counter is incremented only AFTER validation passes.
        
    Raises:
        EmptyClientNameError: If client_name is empty or whitespace only.
        InvalidServiceTypeError: If service is not a recognized ServiceType.
        
    Returns:
        Ticket: The newly created immutable Ticket instance.
    """
```

---

### 2.3 `call_next`

```python
def call_next(self, service: Union[str, ServiceType]) -> Optional[Ticket]:
    """
    Dispatches the longest-waiting client from the specified service queue.
    
    Preconditions:
        - service matches a valid ServiceType.
        
    Postconditions:
        - If queue is non-empty: The oldest ticket is removed from the queue and returned.
        - If queue is empty: Returns None without error or state change.
        - Queue depth for the service decrements by 1 (if non-empty).
        - Other service queues remain completely unaffected.
        
    Raises:
        InvalidServiceTypeError: If service is invalid.
        
    Returns:
        Optional[Ticket]: The dispatched ticket, or None if the queue is empty.
    """
```

---

### 2.4 `peek_next`

```python
def peek_next(self, service: Union[str, ServiceType]) -> Optional[Ticket]:
    """
    Inspects the next waiting client for the specified service WITHOUT mutating the queue.
    
    Preconditions:
        - service matches a valid ServiceType.
        
    Postconditions:
        - Queue order, depth, and contents remain 100% identical before and after the call.
        - Idempotent and thread-safe.
        
    Raises:
        InvalidServiceTypeError: If service is invalid.
        
    Returns:
        Optional[Ticket]: The next ticket to be served, or None if the queue is empty.
    """
```

---

### 2.5 `list_waiting`

```python
def list_waiting(
    self, 
    service: Optional[Union[str, ServiceType]] = None
) -> list[Ticket]:
    """
    Returns an ordered snapshot list of all currently waiting tickets.
    
    Args:
        service: If specified, returns tickets only for that service category.
                 If None, returns all waiting tickets across all services in arrival order.
                 
    Postconditions:
        - Queue state is never mutated.
        - Returned list is a copy; mutating the returned list does not alter internal queues.
        
    Raises:
        InvalidServiceTypeError: If service is provided but invalid.
        
    Returns:
        list[Ticket]: Chronologically ordered list of waiting tickets.
    """
```

---

### 2.6 `get_stats`

```python
def get_stats(self) -> QueueStats:
    """
    Computes real-time queue depth metrics across all service lines.
    
    Postconditions:
        - Computes instantaneous counts in O(1) time.
        - Queue state is untouched.
        
    Returns:
        QueueStats: Object containing counts_by_service and total_waiting.
    """
```

---

### 2.7 `reset`

```python
def reset(self) -> None:
    """
    Clears all queues and resets the global ticket sequence number to 1.
    Thread-safe. Used primarily during morning branch initialization and test teardown.
    """
```
