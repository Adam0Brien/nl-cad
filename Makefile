# Load optional environment overrides from parent or local
-include ../.env
-include .env

# Defaults
OLLAMA_BASE_URL ?= http://localhost:11434
OLLAMA_MODEL ?= mistral:7b-instruct
OLLAMA_CONNECT_TIMEOUT ?= 5
OLLAMA_READ_TIMEOUT ?= 120
OLLAMA_NUM_PREDICT ?= 128

export OLLAMA_BASE_URL
export OLLAMA_MODEL
export OLLAMA_CONNECT_TIMEOUT
export OLLAMA_READ_TIMEOUT
export OLLAMA_NUM_PREDICT

PY ?= python3

help:
	@echo "Usage (from nl-cad/):"
	@echo "  make run DESCRIPTION='M6 x 20 bolt' [OUTPUT=output/file.scad]"
	@echo "  make run-long DESCRIPTION='...' [OUTPUT=output/file.scad]   # longer timeout"
	@echo "  make test                                             # built-in tests"
	@echo "  make pull-model                                       # ollama pull $(OLLAMA_MODEL)"

# Usage:
# make run DESCRIPTION="M6 x 20 bolt" [OUTPUT=output/file.scad]
run:
	$(PY) main.py -d "$(DESCRIPTION)" $(if $(OUTPUT),-o "$(OUTPUT)",)

# Same as run, but with a longer read timeout
run-long:
	OLLAMA_READ_TIMEOUT=300 $(PY) main.py -d "$(DESCRIPTION)" $(if $(OUTPUT),-o "$(OUTPUT)",)

# Built-in tests
test:
	$(PY) main.py --test

# Pull current model
pull-model:
	ollama pull $(OLLAMA_MODEL)

.PHONY: help run run-long test pull-model
