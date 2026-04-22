"""Thin wrapper around the pure-Python gnmi_cli_lib formatter."""

from gnmi_cli_lib import (
    CommandParser,
    parse_and_convert as _parse_and_convert,
    __version__ as _version,
)


def format_cli_output(cli_command: str, data: dict) -> str:
    """Format gNMI JSON data as CLI table output.

    Args:
        cli_command: CLI command string (e.g., "show interfaces status").
        data: Parsed JSON data from gNMI response.

    Returns:
        CLI-formatted table string.
    """
    return _parse_and_convert(cli_command, data)


def list_supported_commands() -> dict:
    """List all supported CLI commands."""
    return CommandParser().list_commands()


def formatter_version() -> str:
    """Get the gnmi_cli_lib version."""
    return _version
