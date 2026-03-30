PYTHON ?= python3
BUILD_DIR = .build

.PHONY: gnmi_show clean test help sync-converter

sync-converter: ## Pull latest path converter from sonic-mgmt
	git submodule update --init --depth=1 sonic-mgmt
	cp sonic-mgmt/tests/telemetry/show_cli_to_gnmi_path.py gnmi_show/_sonic_path_converter.py
	@echo "Updated _sonic_path_converter.py from sonic-mgmt submodule."

gnmi_show: clean sync-converter ## Build the gnmi_show wheel
	@echo "Building gnmi_show wheel..."
	@mkdir -p $(BUILD_DIR)
	$(PYTHON) -m pip install --quiet build
	$(PYTHON) -m build --wheel --outdir $(BUILD_DIR)
	@echo ""
	@echo "Build complete. Wheel is in $(BUILD_DIR)/:"
	@ls -1 $(BUILD_DIR)/*.whl
	@echo ""
	@echo "Install with:"
	@echo "  pip install $(BUILD_DIR)/gnmi_show-*.whl"

clean: ## Remove build artifacts
	rm -rf $(BUILD_DIR) build dist *.egg-info gnmi_show.egg-info

test: ## Run tests
	$(PYTHON) -m pytest tests/ -v

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'
