# Two-Stage Generator Architecture

## Overview
The two-stage generator uses separate, optimized models for different aspects of OpenSCAD code generation:

**Stage 1: Creative Design** → **Stage 2: Technical Implementation**

## Model Specialization

### Stage 1: Design Generation
- **Model**: `llama3.2:3b` (default, configurable via `DESIGN_MODEL`)
- **Purpose**: Creative design specification generation
- **Temperature**: 0.8 (higher creativity)
- **Focus**: Understanding user intent, creating detailed design specs

### Stage 2: Code Generation  
- **Model**: `codegemma:7b` (default, configurable via `CODE_MODEL`)
- **Purpose**: Converting design specs to precise OpenSCAD code
- **Temperature**: 0.2 (lower for precision)
- **Focus**: Technical accuracy, proper syntax, variable definitions

## Configuration

Set environment variables to customize models:
```bash
export DESIGN_MODEL="llama3.2:3b"    # Creative design model
export CODE_MODEL="codegemma:7b"     # Code generation model
```

## Usage

```bash
# Install specialized models
make pull-two-stage-models

# Generate with two-stage approach
make two-stage DESCRIPTION="coffee mug with handle"

# Check configuration
make status
```

## Benefits

1. **Better Quality**: Each model optimized for its specific task
2. **Fewer Errors**: Code model focused on syntax accuracy  
3. **More Creative**: Design model can be more creative without breaking code
4. **Configurable**: Easy to swap models based on available resources
5. **Separation of Concerns**: Design creativity separate from technical implementation

## Model Recommendations

### For Design Stage:
- `llama3.2:3b` - Good creativity/speed balance
- `llama3.1:8b` - Higher quality, slower
- `mistral:7b-instruct` - General purpose fallback

### For Code Stage:
- `codegemma:7b` - Google's code-specialized model
- `deepseek-coder:6.7b` - Strong code generation
- `codellama:7b-instruct` - Meta's code model
