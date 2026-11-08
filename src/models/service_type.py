"""ServiceType domain enumeration and normalization logic."""

from enum import Enum
from typing import Union
from src.exceptions.errors import InvalidServiceTypeError


class ServiceType(str, Enum):
    """Enumeration of supported banking service categories."""

    DEPOSIT = "deposito"
    WITHDRAWAL = "retiro"
    ACCOUNT_MANAGEMENT = "gestion_cuenta"

    # Spanish aliases for attribute access
    DEPOSITO = "deposito"
    RETIRO = "retiro"
    GESTION_CUENTA = "gestion_cuenta"

    @classmethod
    def from_string(cls, value: Union[str, "ServiceType"]) -> "ServiceType":
        """
        Parses and normalizes a string or ServiceType instance into a valid ServiceType enum.

        Supports:
        - Direct enum instances
        - Canonical Spanish values ('deposito', 'retiro', 'gestion_cuenta')
        - Spanish accented variants ('depósito', 'gestión_cuenta', 'gestión de cuenta')
        - English aliases ('deposit', 'withdrawal', 'account_management', 'account management')
        - Space/underscore normalization
        - Numeric shortcuts ('1' -> DEPOSIT, '2' -> WITHDRAWAL, '3' -> ACCOUNT_MANAGEMENT)

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

        # Check direct value match against canonical values
        for member in cls:
            if cleaned == member.value:
                return member

        # Check aliases map (English, Spanish accents, shortcuts)
        aliases_map = {
            # English aliases
            "deposit": cls.DEPOSIT,
            "withdrawal": cls.WITHDRAWAL,
            "account_management": cls.ACCOUNT_MANAGEMENT,
            # Spanish aliases / accents
            "deposito": cls.DEPOSIT,
            "depósito": cls.DEPOSIT,
            "retiro": cls.WITHDRAWAL,
            "gestion_cuenta": cls.ACCOUNT_MANAGEMENT,
            "gestión_cuenta": cls.ACCOUNT_MANAGEMENT,
            "gestion_de_cuenta": cls.ACCOUNT_MANAGEMENT,
            "gestión_de_cuenta": cls.ACCOUNT_MANAGEMENT,
            "gestion": cls.ACCOUNT_MANAGEMENT,
            "gestión": cls.ACCOUNT_MANAGEMENT,
            # Numeric shortcuts
            "1": cls.DEPOSIT,
            "2": cls.WITHDRAWAL,
            "3": cls.ACCOUNT_MANAGEMENT,
        }
        if cleaned in aliases_map:
            return aliases_map[cleaned]

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
