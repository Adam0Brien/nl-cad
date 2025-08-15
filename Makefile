# Load optional environment overrides from parent or local
-include ../.env
-include .env

# Defaults
OLLAMA_BASE_URL ?= http://localhost:11434
OLLAMA_MODEL ?= mistral:7b-instruct
OLLAMA_CONNECT_TIMEOUT ?= 5
OLLAMA_READ_TIMEOUT ?= 120
OLLAMA_NUM_PREDICT ?= 128

# Two-stage generator model configuration
DESIGN_MODEL ?= llama3.2:3b
CODE_MODEL ?= codegemma:7b

export OLLAMA_BASE_URL
export OLLAMA_MODEL
export OLLAMA_CONNECT_TIMEOUT
export OLLAMA_READ_TIMEOUT
export OLLAMA_NUM_PREDICT
export DESIGN_MODEL
export CODE_MODEL

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
	@echo "🎯 GENERATOR MODES:"
	@echo "  make bosl DESCRIPTION='M6 x 20 bolt' [OUTPUT=output/file.scad]     # BOSL mechanical parts (default)"
	@echo "  make cube DESCRIPTION='simple house' [OUTPUT=output/file.scad]     # Cube-only voxel objects"
	@echo "  make maze DESCRIPTION='10x10 maze' [OUTPUT=output/file.scad]       # Maze generation"
	@echo "  make enhanced DESCRIPTION='storage box' [OUTPUT=output/file.scad]  # Enhanced auto-detect generator"
	@echo "  make two-stage DESCRIPTION='coffee mug' [OUTPUT=output/file.scad]  # Two-stage design→code generator"
	@echo "  make maze-direct DESCRIPTION='test maze'                           # Direct algorithmic maze (reliable)"
	@echo "  make cube-speech [OUTPUT=output/file.scad]                         # Cube mode with speech input"
	@echo "  make maze-speech [OUTPUT=output/file.scad]                         # Maze mode with speech input"
	@echo "  make enhanced-speech [OUTPUT=output/file.scad]                     # Enhanced mode with speech input"
	@echo "  make two-stage-speech [OUTPUT=output/file.scad]                    # Two-stage mode with speech input"
	@echo "  make test-maze                                                     # Test maze generation algorithms"
	@echo ""
	@echo "🛠️  DEVELOPMENT & SETUP:"
	@echo "  make install                                          # Install Python dependencies"
	@echo "  make pull-model                                       # ollama pull $(OLLAMA_MODEL)"
	@echo "  make pull-two-stage-models                            # Pull optimized models for two-stage generation"
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

# Generator Mode Commands
# BOSL Generator (mechanical parts) - default mode
bosl:
	$(PY) main.py -m bosl -d "$(DESCRIPTION)" $(if $(OUTPUT),-o "$(OUTPUT)",)

# Cube Generator (voxel-style objects)
cube:
	$(PY) main.py -m cube -d "$(DESCRIPTION)" $(if $(OUTPUT),-o "$(OUTPUT)",)

# Maze Generator
maze:
	$(PY) main.py -m maze -d "$(DESCRIPTION)" $(if $(OUTPUT),-o "$(OUTPUT)",)

# Enhanced Generator (auto-detects object type)
enhanced:
	$(PY) main.py -m enhanced -d "$(DESCRIPTION)" $(if $(OUTPUT),-o "$(OUTPUT)",)

# Two-Stage Generator (design → code)
two-stage:
	$(PY) main.py -m two-stage -d "$(DESCRIPTION)" $(if $(OUTPUT),-o "$(OUTPUT)",)

# Generator modes with speech input
cube-speech:
	$(PY) main.py -m cube --speech $(if $(OUTPUT),-o "$(OUTPUT)",)

maze-speech:
	$(PY) main.py -m maze --speech $(if $(OUTPUT),-o "$(OUTPUT)",)

enhanced-speech:
	$(PY) main.py -m enhanced --speech $(if $(OUTPUT),-o "$(OUTPUT)",)

two-stage-speech:
	$(PY) main.py -m two-stage --speech $(if $(OUTPUT),-o "$(OUTPUT)",)

# Test maze generation algorithms (no dependencies required)
test-maze:
	@echo "🌀 Testing Maze Generation Algorithms..."
	$(PY) simple_maze_test.py

# Generate a working maze directly (algorithmic fallback)
maze-direct:
	@echo "🌀 Generating maze algorithmically: $(DESCRIPTION)"
	@echo "// Direct algorithmic maze generation" > "output/direct_maze.scad"
	@echo "// $(DESCRIPTION)" >> "output/direct_maze.scad"
	@echo "" >> "output/direct_maze.scad"
	@echo "wall_height = 20;" >> "output/direct_maze.scad"
	@echo "wall_thickness = 2;" >> "output/direct_maze.scad"
	@echo "path_width = 10;" >> "output/direct_maze.scad"
	@echo "" >> "output/direct_maze.scad"
	@echo "union() {" >> "output/direct_maze.scad"
	@echo "    // Simple 5x5 maze example" >> "output/direct_maze.scad"
	@echo "    translate([0, 0, 0]) cube([2, 62, 20]); // Left wall" >> "output/direct_maze.scad"
	@echo "    translate([60, 0, 0]) cube([2, 62, 20]); // Right wall" >> "output/direct_maze.scad"
	@echo "    translate([0, 0, 0]) cube([62, 2, 20]); // Bottom wall" >> "output/direct_maze.scad"
	@echo "    translate([0, 60, 0]) cube([62, 2, 20]); // Top wall" >> "output/direct_maze.scad"
	@echo "    // Internal walls for maze paths" >> "output/direct_maze.scad"
	@echo "    translate([12, 2, 0]) cube([2, 20, 20]);" >> "output/direct_maze.scad"
	@echo "    translate([24, 14, 0]) cube([20, 2, 20]);" >> "output/direct_maze.scad"
	@echo "    translate([36, 26, 0]) cube([2, 20, 20]);" >> "output/direct_maze.scad"
	@echo "    translate([14, 48, 0]) cube([20, 2, 20]);" >> "output/direct_maze.scad"
	@echo "}" >> "output/direct_maze.scad"
	@echo "✅ Working maze generated: output/direct_maze.scad"

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
	@echo "  DESIGN_MODEL: $(DESIGN_MODEL)"
	@echo "  CODE_MODEL: $(CODE_MODEL)"
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

# Pull two-stage specialized models
pull-two-stage-models:
	@echo "📥 Pulling two-stage models..."
	@echo "🎨 Pulling design model: $(DESIGN_MODEL)"
	ollama pull $(DESIGN_MODEL)
	@echo "🔧 Pulling code model: $(CODE_MODEL)"
	ollama pull $(CODE_MODEL)
	@echo "✅ Two-stage models ready!"

# Generate STL directly (CLI shortcut)
stl:
	@echo "🔧 Generating STL from: $(DESCRIPTION)"
	$(PY) main.py -d "$(DESCRIPTION)" -o "output/model.scad"
	@echo "🎯 Converting to STL..."
	openscad --export-format stl -o "output/model.stl" "output/model.scad"
	@echo "✅ STL generated: output/model.stl"

# Generate STL with specific generator modes
enhanced-stl:
	@echo "⚡ Generating Enhanced STL from: $(DESCRIPTION)"
	$(PY) main.py -m enhanced -d "$(DESCRIPTION)" -o "output/enhanced_model.scad"
	@echo "🎯 Converting to STL..."
	openscad --export-format stl -o "output/enhanced_model.stl" "output/enhanced_model.scad"
	@echo "✅ Enhanced STL generated: output/enhanced_model.stl"

cube-stl:
	@echo "🧊 Generating Cube STL from: $(DESCRIPTION)"
	$(PY) main.py -m cube -d "$(DESCRIPTION)" -o "output/cube_model.scad"
	@echo "🎯 Converting to STL..."
	openscad --export-format stl -o "output/cube_model.stl" "output/cube_model.scad"
	@echo "✅ Cube STL generated: output/cube_model.stl"

maze-stl:
	@echo "🌀 Generating Maze STL from: $(DESCRIPTION)"
	$(PY) main.py -m maze -d "$(DESCRIPTION)" -o "output/maze_model.scad"
	@echo "🎯 Converting to STL..."
	openscad --export-format stl -o "output/maze_model.stl" "output/maze_model.scad"
	@echo "✅ Maze STL generated: output/maze_model.stl"

.PHONY: help run run-long speech quick-speech test pull-model ui ui-dev ui-port install clean status stl bosl cube maze enhanced cube-speech maze-speech enhanced-speech test-maze maze-direct enhanced-stl cube-stl maze-stl
