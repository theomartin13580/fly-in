VENV = .venv
PY = $(VENV)/bin/python3
PIP = $(VENV)/bin/pip
MAP ?= 03_ultimate_challenge.txt

MYPY_FLAGS = --warn-return-any --warn-unused-ignores --ignore-missing-imports \
	--disallow-untyped-defs --check-untyped-defs

.PHONY: install run debug clean lint lint-strict

install:
	python3 -m venv $(VENV)
	$(PIP) install flake8 mypy

run:
	$(PY) main.py $(MAP) --visual

debug:
	$(PY) -m pdb main.py $(MAP)

clean:
	rm -rf __pycache__ .mypy_cache

lint:
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . $(MYPY_FLAGS)

lint-strict:
	$(VENV)/bin/flake8 .
	$(VENV)/bin/mypy . --strict
