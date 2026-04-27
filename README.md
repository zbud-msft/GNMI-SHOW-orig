# show_cli

End-to-end CLI tool for querying Azure-managed SONiC switches. Reads show commands from a file, retrieves data via the Azure REST API, and formats the output as familiar CLI tables using the pure-Python `gnmi_cli_lib` formatter (pulled in as a git submodule).

## Requirements

- Linux or macOS (Windows is not supported)
- `python3` 3.8+ (with `python3-venv` on Debian/Ubuntu — see prerequisites below)
- `git`
- `make`
- [Azure CLI](https://aka.ms/install-azure-cli) (`az`), authenticated via `az login`

### Install prerequisites

**Ubuntu / Debian:**

```bash
sudo apt update
sudo apt install -y python3 git make \
    "python$(python3 -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')-venv"
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

Per-tool install pages: [python](https://www.python.org/downloads/), [git](https://git-scm.com/download/linux), [make](https://www.gnu.org/software/make/), [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli-linux).

**macOS** (with [Homebrew](https://brew.sh)):

```bash
brew install python git make azure-cli
```

Per-tool install pages: [python](https://www.python.org/downloads/macos/), [git](https://git-scm.com/download/mac), [make](https://formulae.brew.sh/formula/make), [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli-macos).

## Install

```bash
git clone --recurse-submodules https://github.com/Azure/GNMI-SHOW.git
cd GNMI-SHOW
make install
```

`make install` initializes the submodules, creates a local `.venv` with `tabulate` and `natsort`, and symlinks `show_cli` into `~/.local/bin`. Make sure `~/.local/bin` is on your `PATH`:

```bash
echo $PATH | tr ':' '\n' | grep -q "$HOME/.local/bin" || \
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

## Usage

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
    cli.py                   #   CLI entry point
    azure_api.py             #   Azure REST API client (subprocess + az rest)
    formatter.py             #   Thin wrapper over gnmi_cli_lib
  show_cli                   # Bash wrapper (sets PYTHONPATH, runs gnmi_show.cli)
  GNMI-CLI-Converter/        # Submodule — pure-Python gnmi_cli_lib formatter
    python/gnmi_cli_lib/
  sonic-mgmt/                # Submodule — path converter source
  Makefile                   # install / sync-converter / test targets
  .venv/                     # Created by `make install`; gitignored
```

## Updating

```bash
git pull
git submodule update --remote --merge
make install     # refreshes the venv
```

## Uninstall

```bash
make clean       # removes the .venv and the ~/.local/bin/show_cli symlink
```

## Troubleshooting

**`E: Package 'pythonX.Y-venv' has no installation candidate`**
The `universe` repository isn't enabled. Run:
```bash
sudo add-apt-repository universe
sudo apt update
```
then re-run the install command.

**`UnsupportedMediaTypeException` / `JToken` errors from Azure**
Your shell is invoking the Windows `az.cmd` rather than a Linux-native `az`
(common on WSL when Azure CLI is only installed on the Windows side). Check:
```bash
which az
```
If the path starts with `/mnt/c/` or ends in `.cmd`/`.exe`, install the Linux
Azure CLI inside your distro so it takes precedence:
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

**`show_cli: command not found` after `make install`**
`~/.local/bin` isn't on your PATH. Add it (see the [Install](#install) section)
and restart your shell.
