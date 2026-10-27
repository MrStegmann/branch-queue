"""Interactive terminal command-line interface for Banco Meridional Queue Manager."""

import sys
from typing import Optional

from src.exceptions.errors import EmptyClientNameError, InvalidServiceTypeError
from src.models.service_type import ServiceType
from src.services.queue_manager import BranchQueueManager

BANNER = """============================================================
           BANCO MERIDIONAL - QUEUE MANAGER v1.0
============================================================
1. Issue New Ticket (Client Arrival)
2. Call Next Client (Service Counter Dispatch)
3. Peek Next Client (Non-Mutating Inspection)
4. List All Waiting Clients
5. View Branch Statistics & Queue Depth
6. Exit System
============================================================"""

SERVICES_MENU = """Available Services:
  1. deposit
  2. withdrawal
  3. account_management
Select service type (enter number or name): """

DISPATCH_MENU = """Select service line to dispatch:
  1. deposit
  2. withdrawal
  3. account_management
Select service (number or name): """

PEEK_MENU = """Select service line to peek:
  1. deposit
  2. withdrawal
  3. account_management
Select service (number or name): """


def prompt_service_selection(prompt_text: str) -> ServiceType:
    """Prompts the user for a service selection and parses it into a ServiceType."""
    raw = input(prompt_text).strip()
    try:
        return ServiceType.from_string(raw)
    except InvalidServiceTypeError:
        raise InvalidServiceTypeError(
            f"Invalid service type '{raw}'. Must be 'deposit', 'withdrawal', or 'account_management'."
        )


def handle_issue_ticket(manager: BranchQueueManager) -> None:
    """Workflow 1: Issue New Ticket."""
    name_input = input("Enter client name: ")
    trimmed_name = name_input.strip()
    if not trimmed_name:
        print("[ERROR] Client name cannot be blank. Please try again.")
        return

    try:
        service = prompt_service_selection(SERVICES_MENU)
    except InvalidServiceTypeError as e:
        print(f"[ERROR] {e}")
        return

    try:
        ticket = manager.issue_ticket(trimmed_name, service)
        print("------------------------------------------------------------")
        print("[SUCCESS] Ticket Issued Successfully!")
        print(f"  Ticket Number : #{ticket.number}")
        print(f"  Client Name   : {ticket.client_name}")
        print(f"  Service Type  : {ticket.service_type.display_name()}")
        print(f"  Issued At     : {ticket.issued_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("------------------------------------------------------------")
    except EmptyClientNameError as e:
        print(f"[ERROR] {e}")


def handle_call_next(manager: BranchQueueManager) -> None:
    """Workflow 2: Call Next Client."""
    try:
        service = prompt_service_selection(DISPATCH_MENU)
    except InvalidServiceTypeError as e:
        print(f"[ERROR] {e}")
        return

    ticket = manager.call_next(service)
    print("------------------------------------------------------------")
    if ticket is None:
        print(f"[INFO] No clients are currently waiting for '{service.display_name()}'.")
    else:
        print("[DISPATCH] NOW SERVING:")
        print(f"  Ticket Number : #{ticket.number}")
        print(f"  Client Name   : {ticket.client_name}")
        print(f"  Service Line  : {ticket.service_type.display_name()}")
        print(f"  Waiting Since : {ticket.issued_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print("------------------------------------------------------------")


def handle_peek_next(manager: BranchQueueManager) -> None:
    """Workflow 3: Peek Next Client."""
    try:
        service = prompt_service_selection(PEEK_MENU)
    except InvalidServiceTypeError as e:
        print(f"[ERROR] {e}")
        return

    ticket = manager.peek_next(service)
    print("------------------------------------------------------------")
    if ticket is None:
        print(f"[INFO] No clients are currently waiting for '{service.display_name()}'.")
    else:
        print(f"[PEEK] Next in line for {service.display_name()}:")
        print(f"  Ticket Number : #{ticket.number}")
        print(f"  Client Name   : {ticket.client_name}")
        print(f"  Waiting Since : {ticket.issued_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("(Note: Ticket remains in queue at position #1)")
    print("------------------------------------------------------------")


def handle_list_waiting(manager: BranchQueueManager) -> None:
    """Workflow 4: List All Waiting Clients."""
    stats = manager.get_stats()
    if stats.total_waiting == 0:
        print("[INFO] All branch queues are currently empty.")
        return

    print("============================================================")
    print("                   CURRENT BRANCH QUEUES")
    print("============================================================")

    service_order = [ServiceType.DEPOSIT, ServiceType.WITHDRAWAL, ServiceType.ACCOUNT_MANAGEMENT]
    for s in service_order:
        queue_items = manager.list_waiting(s)
        service_label = s.display_name().upper()
        print(f"[{service_label}] ({len(queue_items)} waiting)")
        if queue_items:
            for t in queue_items:
                print(f"  #{t.number} - {t.client_name} (arrived {t.issued_at.strftime('%H:%M:%S')})")
        else:
            print("  -- No clients waiting --")
        print()

    print("============================================================")
    print(f"Total Active Waiting Clients: {stats.total_waiting}")
    print("============================================================")


def handle_view_stats(manager: BranchQueueManager) -> None:
    """Workflow 5: View Branch Statistics."""
    stats = manager.get_stats()
    print("============================================================")
    print("                  BRANCH QUEUE STATISTICS")
    print("============================================================")
    print(f"  Deposit Queue Depth            : {stats.counts_by_service[ServiceType.DEPOSIT]}")
    print(f"  Withdrawal Queue Depth         : {stats.counts_by_service[ServiceType.WITHDRAWAL]}")
    print(f"  Account Management Queue Depth : {stats.counts_by_service[ServiceType.ACCOUNT_MANAGEMENT]}")
    print("------------------------------------------------------------")
    print(f"  Total Waiting Clients          : {stats.total_waiting}")
    print(f"  Snapshot Time                  : {stats.snapshot_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("============================================================")


def run_cli(manager: Optional[BranchQueueManager] = None) -> int:
    """
    Main loop for the terminal CLI.

    Returns:
        int: Process exit code (0 for clean exit, 130 for keyboard interrupt, 1 for fatal error).
    """
    if manager is None:
        manager = BranchQueueManager()

    while True:
        try:
            print(BANNER)
            choice = input("Select an option [1-6]: ").strip()

            if choice == "1":
                handle_issue_ticket(manager)
            elif choice == "2":
                handle_call_next(manager)
            elif choice == "3":
                handle_peek_next(manager)
            elif choice == "4":
                handle_list_waiting(manager)
            elif choice == "5":
                handle_view_stats(manager)
            elif choice == "6":
                print("Exiting Banco Meridional Queue Manager. Goodbye!")
                return 0
            else:
                print(f"[ERROR] Invalid option '{choice}'. Please enter a number between 1 and 6.")

        except EOFError:
            print("\n[INFO] EOF encountered. Exiting Banco Meridional Queue Manager.")
            return 0
        except KeyboardInterrupt:
            print("\n[INFO] Interrupted by user. Exiting Banco Meridional Queue Manager.")
            return 130
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")


def main() -> None:
    """Entrypoint function for CLI execution."""
    code = run_cli()
    sys.exit(code)


if __name__ == "__main__":
    main()
