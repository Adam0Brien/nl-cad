"""
Two-Stage Generator Architecture
Stage 1: Creative Design Generation
Stage 2: OpenSCAD Code Generation
"""
import json
import re
import os
import requests
from typing import Dict, List, Optional, Tuple
from .base_generator import BaseGenerator


class TwoStageGenerator(BaseGenerator):
    """Two-stage generator: Design → Code with separate optimized models"""
    
    def __init__(self, 
                 design_system_prompt_path: str = "config/design_system_prompt.txt",
                 design_user_prompt_path: str = "config/design_user_prompt.txt",
                 code_system_prompt_path: str = "config/code_system_prompt.txt",
                 code_user_prompt_path: str = "config/code_user_prompt.txt",
                 design_model: str = None,
                 code_model: str = None):
        # Initialize with design prompts first
        super().__init__(design_system_prompt_path, design_user_prompt_path)
        
        # Load code generation prompts separately
        self.code_system_prompt = self._load_prompt(code_system_prompt_path)
        self.code_user_prompt = self._load_prompt(code_user_prompt_path)
        
        # Store model preferences for each stage (with environment variable fallbacks)
        self.design_model = design_model or os.getenv("DESIGN_MODEL", "llama3.2:3b")
        self.code_model = code_model or os.getenv("CODE_MODEL", "codegemma:7b")
        
        print("🎭 Two-stage generator initialized:")
        print(f"   Stage 1: Creative design generation ({self.design_model})")
        print(f"   Stage 2: Technical OpenSCAD implementation ({self.code_model})")
    
    def _get_default_prompt(self, prompt_path: str) -> str:
        """Get default prompts for design stage"""
        if "design" in prompt_path and "system" in prompt_path:
            return """You are a creative industrial designer and 3D modeling expert. Your job is to take natural language descriptions and create detailed, technical design specifications.

YOUR ROLE:
- Think like a professional product designer
- Consider functionality, aesthetics, and manufacturability
- Break down objects into geometric components
- Specify dimensions, materials, and construction details

OUTPUT FORMAT:
Create a detailed design specification with:

1. OBJECT OVERVIEW
   - Purpose and function
   - Overall dimensions (length × width × height)
   - Main geometric shapes involved

2. DETAILED COMPONENTS
   - List each major part/component
   - Dimensions for each component
   - Position and orientation
   - How components connect/relate

3. CONSTRUCTION APPROACH
   - Primary shapes to use (cubes, cylinders, spheres)
   - Boolean operations needed (union, difference, intersection)
   - Key measurements and proportions

4. SPECIAL FEATURES
   - Holes, cutouts, or openings
   - Decorative elements
   - Functional details (handles, lids, etc.)

EXAMPLE OUTPUT:
For "coffee mug":

OBJECT OVERVIEW:
- Purpose: Drinking vessel for hot beverages
- Overall dimensions: 90mm diameter × 100mm height
- Main shapes: Cylinder (body), torus handle, optional saucer

DETAILED COMPONENTS:
1. Main body: Hollow cylinder, outer diameter 90mm, inner diameter 80mm, height 100mm
2. Handle: Torus-based shape, major radius 15mm, minor radius 8mm, positioned at side
3. Base: Slight taper for stability, bottom diameter 85mm

CONSTRUCTION APPROACH:
- Start with cylinder(d=90, h=100) for outer body
- Subtract cylinder(d=80, h=95) for interior cavity (leaving 5mm at bottom)
- Add handle using rotated/translated torus
- Union all positive shapes, difference negative spaces

SPECIAL FEATURES:
- Slight outward flare at rim for comfortable drinking
- Comfortable handle positioned for right-hand use
- Stable base with slight inward taper

Be creative but practical. Think about how someone would actually make this object."""

        elif "design" in prompt_path and "user" in prompt_path:
            return """Create a detailed technical design specification for: {description}

Think like a professional product designer. Consider:
- How would this object actually be used?
- What are the key functional requirements?
- What geometric shapes would work best?
- What are reasonable dimensions?
- How would the parts fit together?

Provide a complete design specification following the format:
1. OBJECT OVERVIEW
2. DETAILED COMPONENTS  
3. CONSTRUCTION APPROACH
4. SPECIAL FEATURES

Be specific about dimensions and construction methods."""

        else:
            # Default fallback
            return "You are a helpful assistant."
    
    def _get_code_prompts(self) -> Tuple[str, str]:
        """Get prompts for code generation stage"""
        code_system = """You are an expert OpenSCAD programmer. Your job is to convert detailed design specifications into clean, functional OpenSCAD code.

STRICT REQUIREMENTS:
1. ALWAYS define variables at the top for all dimensions
2. Use proper OpenSCAD syntax only - no other languages
3. Include helpful comments explaining each section
4. Use meaningful variable names
5. Structure code logically (variables → main object → details)
6. Use union(), difference(), intersection() correctly
7. Ensure all dimensions are realistic and proportional

CODE STRUCTURE:
```
// Object name and description
// Variable definitions
width = 50;
height = 30;
depth = 20;

// Main construction
union() {
    // Primary shapes
    translate([0, 0, 0]) cube([width, height, depth]);
    
    // Additional components
    translate([width/2, height/2, depth]) cylinder(d=10, h=5);
}
```

BEST PRACTICES:
- Use descriptive variable names (not just x, y, z)
- Add comments for each major section
- Use translate() and rotate() for positioning
- Group related operations logically
- Test that all parentheses and brackets are balanced
- Ensure code will actually render in OpenSCAD

AVOID:
- Undefined variables
- Syntax from other programming languages
- Overly complex nested operations
- Missing semicolons or brackets
- Unrealistic dimensions (too big or too small)"""

        code_user = """Convert this design specification into OpenSCAD code:

{design_spec}

Requirements:
- Generate complete, functional OpenSCAD code
- Define ALL dimensions as variables at the top
- Include clear comments for each section
- Use proper OpenSCAD functions and syntax
- Make the code clean and well-structured
- Ensure all measurements are reasonable

Output ONLY the OpenSCAD code, nothing else."""

        return code_system, code_user
    
    def generate(self, description: str) -> str:
        """Two-stage generation: Design → Code"""
        print(f"🎭 Two-stage generation for: '{description}'")
        print("")
        
        # Stage 1: Generate creative design specification
        print("🎨 Stage 1: Generating creative design specification...")
        design_spec = self._generate_design_specification(description)
        
        if not design_spec:
            print("❌ Stage 1 failed, using fallback design")
            design_spec = self._generate_fallback_design(description)
        
        print(f"✅ Stage 1 complete: {len(design_spec)} characters")
        print(f"📄 Design preview: {design_spec[:200]}...")
        print("")
        
        # Stage 2: Convert design to OpenSCAD code
        print("🔧 Stage 2: Converting design to OpenSCAD code...")
        openscad_code = self._generate_openscad_from_design(design_spec)
        
        if not openscad_code:
            print("❌ Stage 2 failed, using algorithmic fallback")
            openscad_code = self._generate_code_fallback(description, design_spec)
        
        print(f"✅ Stage 2 complete: {len(openscad_code)} characters")
        print("🎯 Two-stage generation complete!")
        
        return openscad_code
    
    def _generate_design_specification(self, description: str) -> str:
        """Stage 1: Generate design specification using creative model"""
        try:
            user_prompt = self.user_prompt.replace("{description}", description)
            
            # Use creative model for design generation
            result = self._generate_with_ollama_custom(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                temperature=0.8,  # Higher creativity for design
                num_predict=1000,
                model=self.design_model  # Use design-optimized model
            )
            
            if result and len(result) > 100:  # Ensure we got a substantial response
                return result
            else:
                return ""
                
        except Exception as e:
            print(f"⚠️  Design generation error: {e}")
            return ""
    
    def _generate_openscad_from_design(self, design_spec: str) -> str:
        """Stage 2: Convert design spec to OpenSCAD using code-specialized model"""
        try:
            code_system, code_user_template = self._get_code_prompts()
            code_user = code_user_template.replace("{design_spec}", design_spec)
            
            # Use code-specialized model for technical implementation
            result = self._generate_with_ollama_custom(
                system_prompt=code_system,
                user_prompt=code_user,
                temperature=0.2,  # Lower temperature for precise code
                num_predict=800,
                model=self.code_model  # Use code-optimized model
            )
            
            if result:
                # Extract and validate OpenSCAD code
                code = self._extract_openscad_code(result)
                if code:
                    return self._validate_and_clean_code(code)
            
            return ""
            
        except Exception as e:
            print(f"⚠️  Code generation error: {e}")
            return ""
    
    def _generate_with_ollama_custom(self, system_prompt: str, user_prompt: str, 
                                   temperature: float, num_predict: int, 
                                   model: str = None) -> str:
        """Custom Ollama generation with specific prompts and optional model selection"""
        try:
            # Use specified model or fall back to environment/default
            if not model:
                model = os.getenv("OLLAMA_MODEL", "deepseek-coder:6.7b")
            
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            
            print(f"🤖 Using model: {model}")
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": num_predict,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=(10, 300)
            )
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "")
            return content.strip()
            
        except Exception as e:
            print(f"Ollama generation failed: {e}")
            return ""
    
    def _generate_fallback_design(self, description: str) -> str:
        """Fallback design specification if Stage 1 fails"""
        return f"""OBJECT OVERVIEW:
- Purpose: {description}
- Overall dimensions: 50mm × 50mm × 30mm (estimated)
- Main shapes: Rectangular base with functional elements

DETAILED COMPONENTS:
1. Main body: Rectangular base, 50mm × 50mm × 30mm
2. Functional elements: Based on object purpose
3. Details: Simple geometric additions as needed

CONSTRUCTION APPROACH:
- Start with cube([50, 50, 30]) as main body
- Add cylinders or other shapes for functionality
- Use difference() for any necessary cutouts
- Keep proportions reasonable and functional

SPECIAL FEATURES:
- Simplified design for reliable generation
- Focus on core functionality
- Standard proportions for stability"""
    
    def _generate_code_fallback(self, description: str, design_spec: str) -> str:
        """Fallback code generation if Stage 2 fails - generates complete working code"""
        # Extract key dimensions from design spec if possible
        size_match = re.search(r'(\d+)mm.*?(\d+)mm.*?(\d+)mm', design_spec)
        if size_match:
            w, h, d = size_match.groups()
            width, height, depth = int(w), int(h), int(d)
        else:
            # Use reasonable default dimensions
            width, height, depth = 60, 40, 30
        
        return f"""// Fallback OpenSCAD code for: {description}
// Generated from design specification

// Object dimensions
width = {width};
height = {height};
depth = {depth};
wall_thickness = 3;
feature_size = width / 4;

// Main object construction
union() {{
    // Primary body
    cube([width, height, depth]);
    
    // Secondary feature (generic geometric element)
    translate([width/2, height/2, depth])
        cylinder(d=feature_size, h=depth/2, $fn=24);
}}"""
    
    def _validate_and_clean_code(self, code: str) -> str:
        """Enhanced validation for two-stage generated code with undefined variable fixing"""
        print("🧹 Validating and cleaning generated code...")
        
        # Basic cleanup
        code = self._basic_code_cleanup(code)
        
        # Find all variable references in the code (excluding comments)
        variable_references = set()
        import re
        
        # Remove comments temporarily to avoid false positives
        code_without_comments = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        
        # Look for variables in actual code contexts (inside function calls, arrays, etc.)
        # Match patterns like: cube([variable_name, other_var]), translate([x, y, z])
        for match in re.finditer(r'(?:cube|cylinder|sphere|translate|rotate)\s*\(\s*\[([^\]]+)\]', code_without_comments):
            params = match.group(1)
            # Extract variable names from parameter lists
            for param in re.finditer(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', params):
                var_name = param.group(1)
                # Skip OpenSCAD keywords and numeric literals
                if (var_name not in ['cube', 'cylinder', 'sphere', 'translate', 'rotate', 'union', 'difference', 
                                   'intersection', 'linear_extrude', 'rotate_extrude', 'hull', 'minkowski',
                                   'color', 'echo', 'module', 'function', 'if', 'else', 'for', 'true', 'false',
                                   'undef', 'PI', 'use', 'include', '$fn', '$fa', '$fs', 'd', 'h', 'r'] 
                    and not var_name.isdigit()):
                    variable_references.add(var_name)
        
        # Also look for variables in direct assignment contexts like diameter=var_name
        for match in re.finditer(r'(?:d|h|r)\s*=\s*([a-zA-Z_][a-zA-Z0-9_]*)', code_without_comments):
            var_name = match.group(1)
            if not var_name.isdigit():
                variable_references.add(var_name)
        
        # Find all variable definitions in the code
        defined_variables = set()
        for match in re.finditer(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*[^;]+;', code, re.MULTILINE):
            defined_variables.add(match.group(1))
        
        # Find undefined variables
        undefined_vars = variable_references - defined_variables
        
        if undefined_vars:
            print(f"⚠️  Found undefined variables: {list(undefined_vars)}")
            
            # Add missing variable definitions at the top
            missing_definitions = []
            for var in sorted(undefined_vars):
                # Guess reasonable default values based on variable names
                if 'width' in var.lower() or 'length' in var.lower():
                    default_val = 100
                elif 'height' in var.lower():
                    default_val = 75
                elif 'depth' in var.lower():
                    default_val = 60
                elif 'thickness' in var.lower():
                    default_val = 5
                elif 'radius' in var.lower():
                    default_val = 15
                elif 'diameter' in var.lower():
                    default_val = 30
                elif 'leg' in var.lower():
                    default_val = 40
                elif 'top' in var.lower():
                    default_val = 120
                else:
                    default_val = 20
                
                missing_definitions.append(f"{var} = {default_val};")
            
            if missing_definitions:
                # Insert at the beginning after any initial comments
                lines = code.split('\n')
                insert_point = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('//') or line.strip() == '':
                        insert_point = i + 1
                    else:
                        break
                
                print(f"✅ Adding {len(missing_definitions)} missing variable definitions")
                for definition in reversed(missing_definitions):  # Insert in reverse order
                    lines.insert(insert_point, definition)
                
                code = '\n'.join(lines)
        
        # Remove obviously wrong variable definitions (like comment words)
        lines = code.split('\n')
        filtered_lines = []
        for line in lines:
            # Skip variable definitions that look like they came from comments
            if re.match(r'^(Apron|Century|Dimensions|Legs|Mid|Modern|Stretcher|Table|Top|Basic|fallback|shape|i|in)\s*=', line):
                print(f"🗑️  Removing bogus variable definition: {line.strip()}")
                continue
            filtered_lines.append(line)
        code = '\n'.join(filtered_lines)
        
        # Check for essential elements
        lines = code.split('\n')
        has_variables = any('=' in line and line.strip().endswith(';') for line in lines[:20])
        has_geometry = any(func in code for func in ['cube(', 'cylinder(', 'sphere(', 'union(', 'difference('])
        
        if not has_variables:
            print("⚠️  No variables found, adding default dimensions...")
            code = "// Default dimensions\nsize = 30;\n\n" + code
        
        if not has_geometry:
            print("❌ No geometry found, adding basic shape...")
            code += "\n\n// Basic fallback shape\ncube([size, size, size]);"
        
        # Remove empty braces and incomplete constructs
        code = re.sub(r'translate\([^)]*\)\s*{\s*}', '', code)  # Remove empty translate blocks
        code = re.sub(r'for\s*\([^)]*\)\s*{\s*}', '', code)     # Remove empty for loops
        
        # Ensure proper ending
        if not code.strip().endswith((';', '}')):
            code += ';'
        
        print(f"✅ Code validation complete: {len(code)} characters")
        return code
