PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
export PYTHONPATH := src

.PHONY: test run

test:
	$(PYTHON) -m pytest -q

run:
	$(PYTHON) -m uvicorn sunny_devfix.app:app --host $${DEVFIX_HOST:-127.0.0.1} --port $${DEVFIX_PORT:-8000}
