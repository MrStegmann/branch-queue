"""ServiceType domain enumeration and normalization logic."""

from enum import Enum
from typing import Union
from src.exceptions.errors import InvalidServiceTypeError


class ServiceType(str, Enum):
    """Enumeration of supported banking service categories."""

    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ACCOUNT_MANAGEMENT = "account_management"

    @classmethod
    def from_string(cls, value: Union[str, "ServiceType"]) -> "ServiceType":
        """
        Parses and normalizes a string or ServiceType instance into a valid ServiceType enum.

        Supports:
        - Direct enum instances
        - Case-insensitive string matching ('deposit', 'DEPOSIT', 'Deposit')
        - Space/underscore normalization ('account management', 'account_management')
        - Numeric shortcuts ('1' -> deposit, '2' -> withdrawal, '3' -> account_management)

        Raises:
            InvalidServiceTypeError: If the value cannot be resolved to a valid ServiceType.
        """
        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise InvalidServiceTypeError(
                f"Invalid service type '{value}'. Expected string or ServiceType, got {type(value).__name__}."
            )

        cleaned = value.strip().lower().replace(" ", "_")

        # Check direct value match
        for member in cls:
            if cleaned == member.value:
                return member

        # Check numeric shortcuts
        numeric_map = {
            "1": cls.DEPOSIT,
            "2": cls.WITHDRAWAL,
            "3": cls.ACCOUNT_MANAGEMENT,
        }
        if cleaned in numeric_map:
            return numeric_map[cleaned]

        valid_options = ", ".join(f"'{m.value}'" for m in cls)
        raise InvalidServiceTypeError(
            f"Invalid service type '{value}'. Must be one of: {valid_options} (or numbers 1-3)."
        )

    def display_name(self) -> str:
        """Returns a user-friendly display name for the service."""
        display_map = {
            ServiceType.DEPOSIT: "Deposit",
            ServiceType.WITHDRAWAL: "Withdrawal",
            ServiceType.ACCOUNT_MANAGEMENT: "Account Management",
        }
        return display_map.get(self, self.value.replace("_", " ").title())
