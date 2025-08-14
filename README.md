# Natural language to OpenSCAD Code Generator

Uses the BOSL OpenSCAD Library for a wider selection of shapes.

**What This Does:**
Turn natural language into OpenSCAD code

**The Goal:** If you can describe what you want, you can generate OpenSCAD - no need to understand the language, then convert your OpenSCAD code into STL for 3D Printing.

**Quick Start:**
```bash
# Install dependencies
pip install -r requirements.txt

# Generate a bolt (text input)
python3 main.py -d "M6 x 20 bolt"

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
