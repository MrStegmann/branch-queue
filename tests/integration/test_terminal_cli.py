"""Integration tests for terminal CLI menu options, input guards, and exit handling."""

import io
from datetime import datetime, timezone
import pytest

from src.cli.terminal import run_cli
from src.services.queue_manager import BranchQueueManager


def test_cli_exit_option(monkeypatch, capsys):
    """Option 6 exits cleanly."""
    monkeypatch.setattr("builtins.input", lambda prompt="": "6")
    manager = BranchQueueManager()

    exit_code = run_cli(manager=manager)
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "Exiting Banco Meridional Queue Manager. Goodbye!" in captured


def test_cli_invalid_menu_choice(monkeypatch, capsys):
    """Entering an invalid menu option displays error and continues until exit."""
    inputs = iter(["foo", "99", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    manager = BranchQueueManager()

    exit_code = run_cli(manager=manager)
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "[ERROR] Invalid option 'foo'. Please enter a number between 1 and 6." in captured
    assert "[ERROR] Invalid option '99'. Please enter a number between 1 and 6." in captured


def test_cli_issue_ticket_and_view_stats(monkeypatch, capsys):
    """Issue a ticket via Option 1 and inspect via Option 5."""
    fixed_time = datetime(2026, 10, 27, 10, 15, 30, tzinfo=timezone.utc)
    manager = BranchQueueManager(time_provider=lambda: fixed_time)

    # 1 (Issue), Alice Smith, 1 (Deposit), 5 (View stats), 6 (Exit)
    inputs = iter(["1", "Alice Smith", "1", "5", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    exit_code = run_cli(manager=manager)
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "[SUCCESS] Ticket Issued Successfully!" in captured
    assert "Ticket Number : #1" in captured
    assert "Client Name   : Alice Smith" in captured
    assert "Deposit Queue Depth            : 1" in captured
    assert "Total Waiting Clients          : 1" in captured


def test_cli_issue_ticket_blank_name_guard(monkeypatch, capsys):
    """Option 1 guards against blank or whitespace-only client names."""
    inputs = iter(["1", "   ", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    manager = BranchQueueManager()

    run_cli(manager=manager)
    captured = capsys.readouterr().out
    assert "[ERROR] Client name cannot be blank. Please try again." in captured


def test_cli_call_and_peek_workflows(monkeypatch, capsys):
    """Peek and call next client via options 3 and 2."""
    fixed_time = datetime(2026, 10, 27, 10, 18, 45, tzinfo=timezone.utc)
    manager = BranchQueueManager(time_provider=lambda: fixed_time)
    manager.issue_ticket("Charlie Brown", "deposit")

    # 3 (Peek), 1 (Deposit), 2 (Call Next), 1 (Deposit), 2 (Call Next again), 1 (Deposit), 6 (Exit)
    inputs = iter(["3", "1", "2", "1", "2", "1", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    exit_code = run_cli(manager=manager)
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "[PEEK] Next in line for Deposit:" in captured
    assert "Charlie Brown" in captured
    assert "[DISPATCH] NOW SERVING:" in captured
    assert "[INFO] No clients are currently waiting for 'Deposit'." in captured


def test_cli_list_waiting_empty_and_populated(monkeypatch, capsys):
    """Option 4 displays empty queue info and formatted queue list."""
    manager = BranchQueueManager()

    # 4 (List when empty), 1 (Issue), "Bob Jones", "withdrawal", 4 (List populated), 6 (Exit)
    inputs = iter(["4", "1", "Bob Jones", "withdrawal", "4", "6"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    exit_code = run_cli(manager=manager)
    assert exit_code == 0
    captured = capsys.readouterr().out
    assert "[INFO] All branch queues are currently empty." in captured
    assert "CURRENT BRANCH QUEUES" in captured
    assert "[WITHDRAWAL] (1 waiting)" in captured
    assert "Bob Jones" in captured


def test_cli_handles_eof_and_interrupt(monkeypatch, capsys):
    """EOF and KeyboardInterrupt are handled gracefully without uncaught exceptions."""
    manager = BranchQueueManager()

    def raise_eof(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    assert run_cli(manager=manager) == 0
    assert "EOF encountered" in capsys.readouterr().out

    def raise_interrupt(prompt=""):
        raise KeyboardInterrupt

    monkeypatch.setattr("builtins.input", raise_interrupt)
    assert run_cli(manager=manager) == 130
    assert "Interrupted by user" in capsys.readouterr().out
