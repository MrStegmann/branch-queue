"""Unit tests for domain models (ServiceType, Ticket, TicketStatus)."""

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import pytest

from src.models.service_type import ServiceType
from src.exceptions.errors import EmptyClientNameError, InvalidServiceTypeError, ValidationError


def test_service_type_enum_values():
    assert ServiceType.DEPOSIT == "deposit"
    assert ServiceType.WITHDRAWAL == "withdrawal"
    assert ServiceType.ACCOUNT_MANAGEMENT == "account_management"


def test_service_type_from_string_success():
    assert ServiceType.from_string("deposit") == ServiceType.DEPOSIT
    assert ServiceType.from_string("DEPOSIT") == ServiceType.DEPOSIT
    assert ServiceType.from_string("  Withdrawal  ") == ServiceType.WITHDRAWAL
    assert ServiceType.from_string("account_management") == ServiceType.ACCOUNT_MANAGEMENT
    assert ServiceType.from_string("account management") == ServiceType.ACCOUNT_MANAGEMENT
    assert ServiceType.from_string("Account Management") == ServiceType.ACCOUNT_MANAGEMENT
    # Numeric shortcuts
    assert ServiceType.from_string("1") == ServiceType.DEPOSIT
    assert ServiceType.from_string("2") == ServiceType.WITHDRAWAL
    assert ServiceType.from_string("3") == ServiceType.ACCOUNT_MANAGEMENT
    # Direct enum pass-through
    assert ServiceType.from_string(ServiceType.DEPOSIT) == ServiceType.DEPOSIT


def test_service_type_from_string_invalid():
    with pytest.raises(InvalidServiceTypeError) as exc_info:
        ServiceType.from_string("invalid_service")
    assert "Invalid service type" in str(exc_info.value)

    with pytest.raises(InvalidServiceTypeError):
        ServiceType.from_string(123)  # type: ignore


def test_service_type_display_name():
    assert ServiceType.DEPOSIT.display_name() == "Deposit"
    assert ServiceType.WITHDRAWAL.display_name() == "Withdrawal"
    assert ServiceType.ACCOUNT_MANAGEMENT.display_name() == "Account Management"


def test_ticket_model_creation_and_immutability(fixed_now: datetime):
    from src.models.ticket import Ticket, TicketStatus

    ticket = Ticket(
        number=1,
        client_name="Alice Smith",
        service_type=ServiceType.DEPOSIT,
        issued_at=fixed_now,
    )

    assert ticket.number == 1
    assert ticket.client_name == "Alice Smith"
    assert ticket.service_type == ServiceType.DEPOSIT
    assert ticket.issued_at == fixed_now

    # Verify frozen immutability
    with pytest.raises(FrozenInstanceError):
        ticket.client_name = "Bob"  # type: ignore

    with pytest.raises(FrozenInstanceError):
        ticket.number = 2  # type: ignore


def test_ticket_model_whitespace_trimming(fixed_now: datetime):
    from src.models.ticket import Ticket

    ticket = Ticket(
        number=1,
        client_name="  Bob Jones  ",
        service_type=ServiceType.WITHDRAWAL,
        issued_at=fixed_now,
    )
    assert ticket.client_name == "Bob Jones"


def test_ticket_model_validation_empty_client_name(fixed_now: datetime):
    from src.models.ticket import Ticket

    with pytest.raises(EmptyClientNameError):
        Ticket(
            number=1,
            client_name="",
            service_type=ServiceType.DEPOSIT,
            issued_at=fixed_now,
        )

    with pytest.raises(EmptyClientNameError):
        Ticket(
            number=1,
            client_name="   ",
            service_type=ServiceType.DEPOSIT,
            issued_at=fixed_now,
        )


def test_ticket_model_validation_invalid_number(fixed_now: datetime):
    from src.models.ticket import Ticket

    with pytest.raises(ValidationError):
        Ticket(
            number=0,
            client_name="Alice",
            service_type=ServiceType.DEPOSIT,
            issued_at=fixed_now,
        )

    with pytest.raises(ValidationError):
        Ticket(
            number=-5,
            client_name="Alice",
            service_type=ServiceType.DEPOSIT,
            issued_at=fixed_now,
        )


def test_ticket_status_enum():
    from src.models.ticket import TicketStatus

    assert TicketStatus.ISSUED.value == "ISSUED"
    assert TicketStatus.WAITING.value == "WAITING"
    assert TicketStatus.SERVING.value == "SERVING"
    assert TicketStatus.COMPLETED.value == "COMPLETED"
    assert TicketStatus.CANCELLED.value == "CANCELLED"
