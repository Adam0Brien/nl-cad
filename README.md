# NL-CAD: Natural Language CAD Generator

A multi-mode OpenSCAD code generator that converts natural language descriptions into 3D models. Supports multiple generation modes including mechanical parts, voxel-style objects, and mazes.

## 🎯 Features

### Generator Modes

1. **🔧 BOSL Generator** - Mechanical parts using BOSL2 library
   - Bolts, nuts, washers, screws
   - Mechanical components with precise dimensions
   - Threading and standard hardware

2. **🧊 Cube Generator** - Voxel-style objects using only cubes
   - Minecraft-like blocky creations
   - Buildings, characters, objects made from cubes
   - Pixel art in 3D

3. **🌀 Maze Generator** - Generate various types of mazes
   - Rectangular and circular mazes
   - Configurable difficulty levels
   - Multi-level mazes with decorative elements
   - Algorithmic generation with recursive backtracking

4. **🎭 Two-Stage Generator** - Advanced AI-powered generation
   - Design stage: Creative conceptualization using optimized model
   - Code stage: Technical implementation with specialized model
   - Improved code quality and variable validation

5. **💬 Conversational Generator** - Interactive design sessions
   - Ask clarifying questions about your design needs
   - Iterative refinement through conversation
   - Progressive design development with feedback
   - Handles timeouts gracefully with intelligent fallbacks

### Interfaces

- **Command Line Interface** - Simple CLI with speech recognition and conversational mode
- **Web Interface** - Browser-based UI with STL generation and interactive conversations
- **Direct API** - Python module for integration

## 🚀 Quick Start

### Installation

```bash
git clone <repository>
cd nl-cad
pip install -r requirements.txt
```

### Basic Usage

#### Command Line

```bash
# BOSL mode (default) - mechanical parts
python main.py -d "M8 x 25 bolt"

# Generate using speech input 🎤
python3 main.py --speech

# Quick speech input (no confirmation)
python3 main.py --quick-speech

# Using make commands
make speech                    # Speech with confirmation
make quick-speech              # Quick speech mode
make run DESCRIPTION="M6 bolt" # Text input

# Run test cases to see examples
python3 main.py --test
```

**What You Can Generate:**
- **Fasteners:** "M8 x 25 bolt", "M10 nut", "3/8 inch washer"
- **Shapes:** "cuboid 20mm 30mm 40mm", "cyl length 40mm diameter 25mm"
- **🎤 Speech Input:** Just speak naturally: "Create an M8 bolt 25 millimeters long"

**How It Works:**
1. You type: "M8 x 25 bolt"
2. AI figures out: size=8, length=25, coarse=true  
3. Output: Minimal OpenSCAD code with BOSL includes

**Examples:**
| What you want | Type this | Gets this |
|---------------|-----------|-----------|
| M6 bolt, 20mm long | `"M6 x 20 bolt"` | `metric_bolt(size=6, l=20, coarse=true)` |
| 3/8 inch washer | `"3/8 inch washer"` | `metric_washer(size=9.525)` |
| 20x30x40 cube | `"cuboid 20mm 30mm 40mm"` | `cuboid(size=[20,30,40])` |

**Abstract Examples (AI-Powered):**
- `"i need a bolt the width of a king-sized bed and is 200 long"` → AI interprets as ~152mm diameter and 200mm length
- `"box roughly the size of a smartphone"` → AI interprets as ~70x140mm

**Advanced Features:**
- **🎤 Speech Recognition**: Speak your CAD requests naturally
- **AI Integration**: Uses Ollama for complex, abstract descriptions
- **Dual Input Modes**: Type or speak - your choice!

**Limits:**
- Simple shapes (no complex assemblies)

**Troubleshooting:**
- **"No component found"** → Try simpler words: "bolt" instead of "hex head fastener"
- **Missing length** → Include it: "M6 x 25 bolt" not just "M6 bolt"
- **AI not working** → Check if Ollama is running: `ollama list`
- **🎤 Speech not working** → Install audio dependencies: `pip install SpeechRecognition pyaudio`
- **Microphone issues** → Test with: `python3 speech/speech_recognizer.py`

**Project Structure:**
```
Hackathon/
├── main.py                    # Main program (just run this)
├── generation/
│   └── bosl_generator.py     # The AI logic and parameter extraction
├── speech/                    # 🎤 Speech recognition module
│   ├── __init__.py
│   └── speech_recognizer.py  # Speech-to-text functionality
├── data/
│   ├── bosl_catalog.json     # BOSL component definitions
│   └── openscad_catalog.json # Basic OpenSCAD primitives
├── config/
│   ├── creative/             # Creative AI generation prompts
│   │   ├── system_prompt.txt # Spatial reasoning & OpenSCAD rules
│   │   └── user_prompt.txt   # Creative generation instructions
│   ├── catalog/              # Catalog-based generation prompts
│   │   ├── system_prompt.txt # Parameter extraction rules
│   │   └── user_prompt.txt   # Catalog matching instructions
│   ├── system_prompt.txt     # BOSL generation instructions
│   └── user_prompt.txt       # BOSL user prompts
├── output/                   # Generated .scad files
```

**Testing:**

# Test basic functionality
python3 main.py --test
```

**For Developers:**
- **Adding Components**: Edit `data/bosl_catalog.json`
- **Adjusting AI Behavior**: 
  - Creative generation: Modify `config/creative/system_prompt.txt` and `config/creative/user_prompt.txt`
  - Catalog generation: Modify `config/catalog/system_prompt.txt` and `config/catalog/user_prompt.txt`
  - BOSL generation: Modify `config/system_prompt.txt` and `config/user_prompt.txt`
- **Extending Logic**: Modify `generation/bosl_generator.py`
# Cube mode - voxel objects  
python main.py -m cube -d "simple house"

# Maze mode - generate mazes
python main.py -m maze -d "10x10 maze with dead ends"

# Two-stage mode - enhanced AI generation  
python main.py -m two-stage -d "modern coffee mug with handle"

# Conversational mode - interactive design
python main.py -m conversation -d "I want to create something special"

# Save to file
python main.py -m maze -d "circular maze" -o output/my_maze.scad

# Voice input
python main.py --speech -m cube
```

#### Web Interface

```bash
python web_app.py
# Open http://localhost:5000
```

### Testing

```bash
# Test all generators
python main.py --test

# Test maze generation specifically
python simple_maze_test.py
```

## 📝 Usage Examples

### BOSL Generator Examples

```bash
python main.py -d "M8 x 25 bolt"
python main.py -d "cuboid 20mm 30mm 40mm"  
python main.py -d "cylinder diameter 25mm height 40mm"
python main.py -d "M10 nut"
python main.py -d "3/8 inch washer"
```

### Cube Generator Examples

```bash
python main.py -m cube -d "simple house"
python main.py -m cube -d "castle tower"
python main.py -m cube -d "robot figure"
python main.py -m cube -d "tree"
python main.py -m cube -d "car"
```

### Maze Generator Examples

```bash
python main.py -m maze -d "simple 5x5 maze"
python main.py -m maze -d "complex 10x10 maze with dead ends"
python main.py -m maze -d "beginner maze with base platform"
python main.py -m maze -d "advanced maze with pillars and roof"
python main.py -m maze -d "circular maze"
python main.py -m maze -d "multi-level maze"
```

### Two-Stage Generator Examples

```bash
python main.py -m two-stage -d "modern coffee mug with handle"
python main.py -m two-stage -d "decorative vase with Greek patterns"
python main.py -m two-stage -d "desk organizer with compartments"
python main.py -m two-stage -d "phone charging stand"
python main.py -m two-stage -d "storage box with hinged lid"
```

### Conversational Mode Examples

```bash
# Start interactive design session
python main.py -m conversation -d "I want to design a treasure chest"
python main.py -m conversation -d "help me create a custom container"
python main.py -m conversation -d "I need something decorative"

# The system will ask clarifying questions like:
# - What dimensions do you need?
# - What style preferences do you have?
# - Any specific functional requirements?
# - Materials and appearance preferences?
```

## 🔧 Technical Details

### Architecture

The system uses a base class architecture:

- `BaseGenerator` - Abstract base class for all generators
- `BOSLGenerator` - Inherits from BaseGenerator, handles mechanical parts
- `CubeGenerator` - Inherits from BaseGenerator, cube-only objects
- `MazeGenerator` - Inherits from BaseGenerator, maze generation

### Maze Generation Features

#### Algorithmic Generation
- **Recursive Backtracking Algorithm** - Creates perfect mazes with single solution paths
- **Configurable Difficulty** - Beginner, intermediate, and advanced modes
- **Multiple Maze Types** - Rectangular, circular, and multi-level mazes

#### Maze Parameters
- **Size**: Grid dimensions (e.g., 5x5, 10x10, 15x8)
- **Wall Properties**: Height (20 units), thickness (2 units), path width (10 units)
- **Features**: Base platforms, decorative pillars, roofs, rooms

#### Maze Types
1. **Rectangular Mazes** - Standard grid-based mazes
2. **Circular Mazes** - Radial maze layouts (planned)
3. **Multi-level Mazes** - Stacked maze levels with connections

### Output Files

Generated files are saved to the `output/` directory:
- `.scad` files - OpenSCAD source code
- `.stl` files - 3D printable models (via web interface)

## 🎛️ Configuration

### Environment Variables

```bash
# Ollama Configuration (for LLM-based generation)
export OLLAMA_MODEL="deepseek-coder:6.7b"
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_NUM_PREDICT="2500"
export OLLAMA_CONNECT_TIMEOUT="10"
export OLLAMA_READ_TIMEOUT="600"
```

### Prompt Customization

Each generator uses customizable prompt files in the `config/` directory:

- `system_prompt.txt` / `user_prompt.txt` - BOSL generator
- `cube_system_prompt.txt` / `cube_user_prompt.txt` - Cube generator  
- `maze_system_prompt.txt` / `maze_user_prompt.txt` - Maze generator

## 🔬 Testing

### Automated Tests

```bash
# Run all generator tests
python main.py --test

# Test specific maze generation
python simple_maze_test.py
```

### Manual Testing

1. Generate a maze: `python main.py -m maze -d "5x5 simple maze" -o test.scad`
2. Open `test.scad` in OpenSCAD
3. Press F5 to preview or F6 to render
4. You should see a 3D maze with walls and paths

### Expected Output

A successful maze generation will create:
- Boundary walls forming the maze perimeter
- Internal walls creating the maze paths
- Entrance and exit openings
- Optional features (base, pillars, roof) if requested

## 🛠️ Development

### Adding New Generators

1. Create a new generator class inheriting from `BaseGenerator`
2. Implement required abstract methods:
   - `_get_default_prompt()`
   - `generate()`
   - `_validate_and_clean_code()`
3. Add the generator to `main.py` and `web_app.py`
4. Create prompt files in `config/`

### Maze Algorithm Improvements

The maze generator supports multiple algorithms:
- ✅ Recursive Backtracking (implemented)
- 🔄 Binary Tree (planned)
- 🔄 Eller's Algorithm (planned)
- 🔄 Wilson's Algorithm (planned)

## 🐛 Troubleshooting

### Common Issues

1. **"Module not found" errors** - Install requirements: `pip install -r requirements.txt`
2. **Empty maze output** - Check that the algorithmic fallback is working
3. **OpenSCAD errors** - Verify the generated code syntax in OpenSCAD
4. **Speech recognition fails** - Install additional dependencies: `pip install SpeechRecognition pyaudio`

### Debugging

Enable verbose output by running with Python's `-v` flag:
```bash
python -v main.py -m maze -d "test maze"
```

## 📊 Example Output

A typical 5x5 maze generates approximately:
- 45 lines of OpenSCAD code  
- 1500+ characters
- Boundary walls (4 pieces)
- Internal walls (15-25 pieces depending on maze complexity)
- Entrance and exit openings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new generators
4. Submit a pull request

## 📄 License

[License information here]

## 🔗 Related Projects

- [BOSL2](https://github.com/revarbat/BOSL2) - Advanced OpenSCAD library
- [OpenSCAD](https://openscad.org/) - The OpenSCAD application
