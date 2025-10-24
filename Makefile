.PHONY: install test lint fmt run clean

install:  ## Install the package with dev tools (editable)
	python -m pip install -e ".[dev]"

test:  ## Run the test suite
	pytest

