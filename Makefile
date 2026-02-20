.PHONY: install test lint fmt run clean

install:  ## Install the package with dev tools (editable)
	python -m pip install -e ".[dev]"

test:  ## Run the test suite
	pytest

lint:  ## Static checks
	ruff check .

fmt:  ## Auto-fix lint issues
	ruff check --fix .

run:  ## Evaluate the bundled two_sum example
	codejudge run examples/two_sum --max-prefs 5

clean:  ## Remove caches and build artifacts
	rm -rf build dist *.egg-info src/*.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
