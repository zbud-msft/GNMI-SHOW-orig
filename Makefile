PYTHON ?= python3
VENV = .venv

.PHONY: install sync-converter test help clean

install: sync-converter ## Set up the venv, init submodules, and symlink show_cli
	git submodule update --init --depth=1 GNMI-CLI-Converter
	@$(PYTHON) -m venv --help >/dev/null 2>&1 || { \
		echo "ERROR: $(PYTHON) -m venv is not available."; \
		echo "On Debian/Ubuntu, install: sudo apt install python3-venv"; \
		exit 1; \
	}
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/pip install --quiet --upgrade pip
	$(VENV)/bin/pip install --quiet tabulate natsort
	chmod +x show_cli
	mkdir -p $(HOME)/.local/bin
	ln -sf $(CURDIR)/show_cli $(HOME)/.local/bin/show_cli
	@echo ""
	@echo "Installed. Make sure $(HOME)/.local/bin is on your PATH."
	@echo "Then run: show_cli --help"

sync-converter: ## Pull latest path converter from sonic-mgmt
	git submodule update --init --depth=1 sonic-mgmt
	cp sonic-mgmt/tests/telemetry/show_cli_to_gnmi_path.py gnmi_show/_sonic_path_converter.py
	@echo "Updated _sonic_path_converter.py from sonic-mgmt submodule."

test: ## Run tests against the local wrapper
	PYTHONPATH=.:GNMI-CLI-Converter/python $(VENV)/bin/python -m pytest tests/ -v

clean: ## Remove venv and the global symlink
	rm -rf $(VENV)
	rm -f $(HOME)/.local/bin/show_cli

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
