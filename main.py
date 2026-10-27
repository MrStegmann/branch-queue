"""Application entry point for Banco Meridional Queue Manager."""

import sys
from src.cli.terminal import run_cli


def main() -> None:
    """Run the Banco Meridional Queue Manager terminal interface."""
    exit_code = run_cli()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
