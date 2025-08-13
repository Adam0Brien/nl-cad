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
	@echo "NL-CAD - Natural Language CAD Generator"
	@echo ""
	@echo "🌐 WEB UI MODE:"
	@echo "  make ui                                               # Start web interface at http://127.0.0.1:5000"
	@echo "  make ui-dev                                           # Start web UI in debug mode"
	@echo "  make ui-port PORT=8080                                # Start web UI on custom port"
	@echo ""
	@echo "💻 COMMAND LINE MODE (no UI):"
	@echo "  make run DESCRIPTION='M6 x 20 bolt' [OUTPUT=output/file.scad]"
	@echo "  make run-long DESCRIPTION='...' [OUTPUT=output/file.scad]   # longer timeout"
	@echo "  make speech [OUTPUT=output/file.scad]                      # speech input with confirmation"
	@echo "  make quick-speech [OUTPUT=output/file.scad]                # quick speech input"
	@echo "  make test                                             # built-in tests"
	@echo ""
	@echo "🛠️  DEVELOPMENT & SETUP:"
	@echo "  make install                                          # Install Python dependencies"
	@echo "  make pull-model                                       # ollama pull $(OLLAMA_MODEL)"
	@echo "  make clean                                            # Clean output directory"
	@echo "  make status                                           # Show configuration status"

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

# Speech input with confirmation
speech:
	$(PY) main.py --speech $(if $(OUTPUT),-o "$(OUTPUT)",)

# Quick speech input (no confirmation)
quick-speech:
	$(PY) main.py --quick-speech $(if $(OUTPUT),-o "$(OUTPUT)",)

# Web UI Commands
ui:
	@echo "🌐 Starting NL-CAD Web Interface..."
	@echo "📍 Access at: http://127.0.0.1:5000"
	@echo "🎤 Features: Voice input, 3D preview, STL download"
	@echo "⏹️  Press Ctrl+C to stop"
	@echo ""
	$(PY) web_app.py

ui-dev:
	@echo "🌐 Starting NL-CAD Web Interface (Debug Mode)..."
	@echo "📍 Access at: http://127.0.0.1:5000"
	@echo "🔄 Auto-reloads on file changes"
	@echo ""
	FLASK_DEBUG=1 $(PY) web_app.py

ui-port:
	@echo "🌐 Starting NL-CAD Web Interface on port $(PORT)..."
	@echo "📍 Access at: http://127.0.0.1:$(PORT)"
	@echo ""
	$(PY) -c "from web_app import app; app.run(host='127.0.0.1', port=$(PORT))"

# Development & Setup Commands
install:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed!"

clean:
	@echo "🧹 Cleaning output directory..."
	rm -f output/*.scad output/*.stl
	@echo "✅ Output directory cleaned!"

status:
	@echo "🔧 NL-CAD Configuration Status:"
	@echo "  OLLAMA_BASE_URL: $(OLLAMA_BASE_URL)"
	@echo "  OLLAMA_MODEL: $(OLLAMA_MODEL)"
	@echo "  OLLAMA_CONNECT_TIMEOUT: $(OLLAMA_CONNECT_TIMEOUT)s"
	@echo "  OLLAMA_READ_TIMEOUT: $(OLLAMA_READ_TIMEOUT)s"
	@echo "  OLLAMA_NUM_PREDICT: $(OLLAMA_NUM_PREDICT)"
	@echo "  Python: $(shell $(PY) --version 2>&1)"
	@echo ""
	@echo "🧪 Testing Ollama connection..."
	@curl -s $(OLLAMA_BASE_URL)/api/tags > /dev/null && echo "✅ Ollama is running" || echo "❌ Ollama not accessible"

# Pull current model
pull-model:
	@echo "📥 Pulling Ollama model: $(OLLAMA_MODEL)"
	ollama pull $(OLLAMA_MODEL)

# Generate STL directly (CLI shortcut)
stl:
	@echo "🔧 Generating STL from: $(DESCRIPTION)"
	$(PY) main.py -d "$(DESCRIPTION)" -o "output/model.scad"
	@echo "🎯 Converting to STL..."
	openscad --export-format stl -o "output/model.stl" "output/model.scad"
	@echo "✅ STL generated: output/model.stl"

.PHONY: help run run-long speech quick-speech test pull-model ui ui-dev ui-port install clean status stl
