# show_cli

End-to-end CLI tool for querying Azure-managed SONiC switches. Reads show commands from a file, retrieves data via the Azure REST API, and formats the output as familiar CLI tables using the Rust-based gnmi_cli_lib formatter.

## Requirements

- **Linux or macOS** (Windows is not supported)
- Python 3.8+
- pip
- [Azure CLI](https://aka.ms/install-azure-cli) (`az`) installed and on PATH
- Authenticated via `az login`

## Building the Wheel

```bash
git clone <repo-url>
cd GNMI-SHOW
make gnmi_show
```

This fetches the path converter from sonic-mgmt and creates a `.whl` file in `.build/`:

```
.build/gnmi_show-1.0.0-py3-none-any.whl
```

## Installing

```bash
pip install gnmi_show-1.0.0-py3-none-any.whl
```

No other setup required. The Rust formatter is pre-built and bundled in the wheel.

## Usage

Before using `show_cli`, authenticate with Azure:

```bash
az login
```

Create a file with one show command per line (e.g., `cli-input.txt`):

```
show interfaces status
show reboot-cause history
```

Then run:

```bash
show_cli -f cli-input.txt -n <switch_name> \
    -s <subscription-id> -g <resource-group> -r <resource-name>
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `-f, --file` | Yes | Path to a file containing one `show` command per line |
| `-n, --switch_name` | Yes | Switch name in Azure |
| `-s, --subscription_id` | Yes | Azure subscription ID |
| `-g, --resource_group` | Yes | Azure resource group name |
| `-r, --resource_name` | Yes | Azure resource name |

### How It Works

1. Reads show commands from the input file (one per line, blank lines skipped)
2. Converts each CLI command to a gNMI path (e.g., `show interfaces status` → `SHOW/interfaces/status`)
3. Automatically sets the Azure subscription (`az account set`)
4. Calls the Azure REST API to retrieve data from the specified switch
5. Polls the async operation until it completes
6. Formats the JSON response as a CLI table

## Project Structure

```
GNMI-SHOW/
  gnmi_show/                 # Python package
    cli.py                   #   CLI entry point (show_cli command)
    azure_api.py             #   Azure REST API client (subprocess + az rest)
    formatter.py             #   Wrapper around Rust formatter
    native/                  #   Pre-built Rust binaries
      gnmi_show_formatter.abi3.so   # Linux (PyO3 abi3, Python 3.8+)
  sonic-mgmt/                # Fetched at build time (git remote)
  pyproject.toml             # Package configuration
  Makefile                   # Build commands
```
