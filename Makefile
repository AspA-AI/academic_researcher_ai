# Makefile for ai_researcher backend (FastAPI)

.PHONY: help venv install run test

VENV ?= .venv
# Prefer a Python version that can install torch wheels reliably (3.11/3.12).
# Falls back to python3 if those aren't available.
HOST_PYTHON := $(shell command -v python3.12 >/dev/null 2>&1 && echo python3.12 || (command -v python3.11 >/dev/null 2>&1 && echo python3.11 || echo python3))
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

help:
	@echo "Targets:"
	@echo "  make venv     - create local venv at $(VENV)"
	@echo "  make install  - install backend deps (api/requirements.txt)"
	@echo "  make run      - run FastAPI backend on http://localhost:8000"
	@echo "  make test     - run unit tests (JSON agent shape tests)"

venv:
	@if [ ! -x "$(PYTHON)" ]; then \
		echo "Creating venv with: $(HOST_PYTHON)"; \
		$(HOST_PYTHON) -m venv $(VENV); \
		$(PIP) install --upgrade pip; \
	else \
		echo "Using existing venv: $(VENV)"; \
	fi

install: venv
	$(PIP) install -r api/requirements.txt

run: install
	$(UVICORN) api.app:app --reload --host 0.0.0.0 --port 8000

test: venv
	@echo "Running tests (expects deps already installed in $(VENV))."
	$(PYTHON) -m unittest -q api.tests.test_agents_json


