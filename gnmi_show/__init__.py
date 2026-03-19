"""
gnmi_show - End-to-end CLI tool for querying Azure-managed SONiC switches.

Converts CLI show commands to gNMI paths, retrieves data via the Azure ARM API,
and formats output as CLI tables using the Rust-based gnmi_show_formatter.

Platform: Linux and macOS only (no Windows support).
Requires: Azure CLI (`az login`) for authentication.
"""

__version__ = "1.0.0"

from gnmi_show._sonic_path_converter import ShowCliToGnmiPathConverter, OptionException
from gnmi_show.azure_api import AzureConfig, AzureApiError, retrieve_data

__all__ = [
    "__version__",
    "ShowCliToGnmiPathConverter",
    "OptionException",
    "AzureConfig",
    "AzureApiError",
    "retrieve_data",
    "format_cli_output",
]


def format_cli_output(cli_command: str, data: dict) -> str:
    """Lazy import wrapper — only loads the native module when actually called."""
    from gnmi_show.formatter import format_cli_output as _fmt
    return _fmt(cli_command, data)
