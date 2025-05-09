.DEFAULT_GOAL := help

venv:
	@curl -LsSf https://astral.sh/uv/install.sh | sh
	@uv venv --python '3.12'


.PHONY: install
install: venv ## Install a virtual environment
	@uv pip install --upgrade pip
	@uv sync --all-extras --dev --frozen


.PHONY: fmt
fmt: venv ## Run autoformatting and linting
	@uv pip install pre-commit
	@uv run pre-commit install --config src/py/.pre-commit-config.yaml
	@uv run pre-commit run --config src/py/.pre-commit-config.yaml --all-files


.PHONY: help
help:  ## Display this help screen
	@echo -e "\033[1mAvailable commands:\033[0m"
	@grep -E '^[a-z.A-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' | sort
