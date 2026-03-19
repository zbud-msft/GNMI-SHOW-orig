#!/usr/bin/env python3
"""
CLI entry point for the show_cli command.

Reads show commands from a file (one per line), converts each to a gNMI path,
retrieves data from an Azure-managed
SONiC switch via the ARM API, and formats the output as a CLI table using
the Rust-based gnmi_show_formatter.

Platform: Linux and macOS only (no Windows support).

Usage:
    show_cli -f cli-input.txt -n <switch_name> \
        -s <subscription-id> -g <resource-group> -r <resource-name>
"""

import argparse
import json
import shlex
import sys

from gnmi_show.azure_api import AzureApiError, AzureConfig, retrieve_data
from gnmi_show._sonic_path_converter import ShowCliToGnmiPathConverter, OptionException


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for show_cli."""
    parser = argparse.ArgumentParser(
        prog="show_cli",
        description="Retrieve and display gNMI data from Azure-managed SONiC switches",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run commands from a file (one 'show ...' command per line)
  show_cli -f cli-input.txt -n <switch_name> \\
      -s <subscription-id> -g <resource-group> -r <resource-name>
""",
    )

    parser.add_argument(
        "-f", "--file",
        required=True,
        help="Path to a file containing one 'show ...' command per line",
    )

    parser.add_argument(
        "--format",
        choices=["cli", "api"],
        default="cli",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "-n", "--switch_name",
        required=True,
        help="Switch name in Azure",
    )

    parser.add_argument(
        "-s", "--subscription_id",
        required=True,
        help="Azure subscription ID",
    )

    parser.add_argument(
        "-g", "--resource_group",
        required=True,
        help="Azure resource group name",
    )

    parser.add_argument(
        "-r", "--resource_name",
        required=True,
        help="Azure resource name",
    )

    parser.add_argument(
        "--api_version",
        default="2025-07-01-preview",
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help=argparse.SUPPRESS,
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help=argparse.SUPPRESS,
    )

    return parser


def write_output(content: str, output_path: str = None) -> None:
    """Write output to file or stdout."""
    if output_path:
        with open(output_path, "a") as f:
            f.write(content)
    else:
        print(content, end="")


def run_command(cli_path: str, config: AzureConfig, fmt: str, verbose: bool) -> str:
    """Run a single show command and return the formatted output."""
    tokens = shlex.split(cli_path)
    gnmi_path = ShowCliToGnmiPathConverter(tokens).convert()
    if verbose:
        print(f"Converted path: {gnmi_path}", file=sys.stderr)

    data = retrieve_data(config, gnmi_path)

    if fmt == "api":
        return json.dumps(data, indent=2) + "\n"
    else:
        from gnmi_show.formatter import format_cli_output
        cli_command = cli_path
        result = format_cli_output(cli_command, data)
        return result if result.endswith("\n") else result + "\n"


def main() -> int:
    """Main entry point for show_cli."""
    parser = create_parser()
    args = parser.parse_args()

    config = AzureConfig(
        subscription_id=args.subscription_id,
        resource_group=args.resource_group,
        resource_name=args.resource_name,
        switch=args.switch_name,
        api_version=args.api_version,
    )

    had_error = False

    try:
        with open(args.file, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.rstrip("\n")
                if not line.strip():
                    continue

                try:
                    output = run_command(line, config, args.format, args.verbose)
                    write_output(output, args.output)
                except OptionException as e:
                    print(f"{args.file}:{lineno}: Invalid path: {e}", file=sys.stderr)
                    had_error = True
                except AzureApiError as e:
                    print(f"{args.file}:{lineno}: Azure error: {e}", file=sys.stderr)
                    had_error = True
                except ValueError as e:
                    print(
                        f"{args.file}:{lineno}: No formatter found: {e}\n"
                        f"  Hint: Use --format api to see the raw JSON output.",
                        file=sys.stderr,
                    )
                    had_error = True
                except Exception as e:
                    if args.verbose:
                        import traceback
                        traceback.print_exc()
                    print(f"{args.file}:{lineno}: {e}", file=sys.stderr)
                    had_error = True

    except FileNotFoundError:
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"Error: Failed to read file '{args.file}': {e}", file=sys.stderr)
        return 2

    return 1 if had_error else 0


if __name__ == "__main__":
    sys.exit(main())
