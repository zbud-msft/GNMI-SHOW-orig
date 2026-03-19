"""Thin wrapper around the Rust-based gnmi_show_formatter native module."""

import json
from gnmi_show.native.gnmi_show_formatter import (
    parse_and_convert as _parse_and_convert,
    convert as _convert,
    list_commands as _list_commands,
    version as _version,
)


def format_cli_output(cli_command: str, data: dict) -> str:
    """Format gNMI JSON data as CLI table output using the Rust formatter.

    Args:
        cli_command: CLI command string (e.g., "show interfaces status").
        data: Parsed JSON data from gNMI response.

    Returns:
        CLI-formatted table string.
    """
    json_str = json.dumps(data)
    return _parse_and_convert(cli_command, json_str)


def convert(command_name: str, data: dict) -> str:
    """Convert using an internal command key.

    Args:
        command_name: Internal command key (e.g., "interfaces_status").
        data: Parsed JSON data from gNMI response.

    Returns:
        CLI-formatted table string.
    """
    json_str = json.dumps(data)
    return _convert(command_name, json_str)


def list_supported_commands() -> dict:
    """List all supported CLI commands.

    Returns:
        Dict mapping command names to their subcommands.
    """
    return _list_commands()


def formatter_version() -> str:
    """Get the gnmi_cli_lib version."""
    return _version()
