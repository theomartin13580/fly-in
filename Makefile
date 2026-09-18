VENV = .venv
PY = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip

.PHONY: install run debug clean lint lint-strict

install:
	python3 -m venv $(VENV)
	$(PIP) install flake8 mypy

run:
	$(PY) simulation.py

debug:
	$(PY) -m pdb simulation.py

clean:
	rm -rf __pycache__ .mypy_cache

lint:
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --strict