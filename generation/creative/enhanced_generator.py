"""
Enhanced OpenSCAD Generator with Multiple LLM Backends
Supports both local Ollama and OpenAI API for better results
"""
import json
import re
import os
import requests
from typing import Dict, List, Optional
from ..core.base_generator import BaseGenerator


class EnhancedGenerator(BaseGenerator):
    """Enhanced generator that can use both local and cloud LLMs"""
    
    def __init__(self, 
                 system_prompt_path: str = "config/creative/code/system_prompt.txt",
                 user_prompt_path: str = "config/creative/code/user_prompt.txt"):
        super().__init__(system_prompt_path, user_prompt_path)
        
        # Check if OpenAI API key is available
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.use_openai = self.openai_api_key is not None
        
        if self.use_openai:
            print("🌩️  Using OpenAI API for enhanced generation")
        else:
            print("🏠 Using local Ollama for generation")
    
    def _get_default_prompt(self, prompt_path: str) -> str:
        """Enhanced prompts with better examples"""
        if "system" in prompt_path:
            return """You are an expert OpenSCAD programmer. Generate precise, functional OpenSCAD code.

RULES:
1. ALWAYS include variable definitions at the top
2. Use proper OpenSCAD syntax only
3. Include meaningful comments
4. Generate complete, runnable code
5. Use unions/differences correctly
6. Define dimensions clearly

EXAMPLE OUTPUT:
```openscad
// Parametric box with lid
box_width = 50;
box_height = 30;
box_depth = 20;
wall_thickness = 2;

union() {
    // Main box body
    difference() {
        cube([box_width, box_height, box_depth]);
        translate([wall_thickness, wall_thickness, wall_thickness]) 
            cube([box_width-2*wall_thickness, box_height-2*wall_thickness, box_depth]);
    }
    
    // Lid
    translate([0, 0, box_depth]) 
        cube([box_width, box_height, wall_thickness]);
}
```

ALWAYS:
- Define ALL variables used
- Use proper OpenSCAD functions
- Include complete code blocks
- Add helpful comments"""

        else:  # user prompt
            return """Create OpenSCAD code for: {description}

Requirements:
- Generate complete, functional OpenSCAD code
- Define all variables at the top
- Include proper comments
- Use appropriate OpenSCAD functions
- Make it parametric when possible

Output ONLY the OpenSCAD code, no explanations."""

    def generate(self, description: str) -> str:
        """Generate OpenSCAD code using the best available method"""
        print(f"🔧 Enhanced mode: Generating '{description}'")
        
        if self.use_openai:
            return self._generate_with_openai(description)
        else:
            return self._generate_with_ollama(description, temperature=0.1, num_predict=1500)
    
    def _generate_with_openai(self, description: str) -> str:
        """Use OpenAI API for generation"""
        try:
            print("🌩️  Using OpenAI API...")
            
            user_prompt = self.user_prompt.replace("{description}", description)
            
            import openai
            openai.api_key = self.openai_api_key
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            content = response.choices[0].message.content
            print("✅ Received OpenAI response!")
            
            code = self._extract_openscad_code(content)
            if code:
                return self._validate_and_clean_code(code)
            else:
                print("❌ No valid code from OpenAI, falling back to algorithmic")
                return self._generate_fallback(description)
                
        except Exception as e:
            print(f"❌ OpenAI API failed: {e}")
            print("🔄 Falling back to local generation...")
            return self._generate_with_ollama(description)
    
    def _generate_fallback(self, description: str) -> str:
        """Generate a simple but functional OpenSCAD object"""
        # Parse description for basic shapes
        if any(word in description.lower() for word in ['box', 'cube', 'rectangular']):
            return self._generate_box_code(description)
        elif any(word in description.lower() for word in ['cylinder', 'tube', 'pipe']):
            return self._generate_cylinder_code(description)
        elif any(word in description.lower() for word in ['sphere', 'ball']):
            return self._generate_sphere_code(description)
        else:
            return self._generate_generic_code(description)
    
    def _generate_box_code(self, description: str) -> str:
        """Generate a parametric box"""
        return """// Parametric box
// Generated from: """ + description + """

// Dimensions
box_width = 30;
box_height = 20;
box_depth = 15;
wall_thickness = 2;

// Main object
difference() {
    // Outer box
    cube([box_width, box_height, box_depth]);
    
    // Inner cavity
    translate([wall_thickness, wall_thickness, wall_thickness])
        cube([box_width-2*wall_thickness, box_height-2*wall_thickness, box_depth-wall_thickness]);
}"""

    def _generate_cylinder_code(self, description: str) -> str:
        """Generate a parametric cylinder"""
        return """// Parametric cylinder
// Generated from: """ + description + """

// Dimensions
outer_diameter = 20;
inner_diameter = 15;
height = 30;

// Main object
difference() {
    // Outer cylinder
    cylinder(d=outer_diameter, h=height, $fn=50);
    
    // Inner hole
    translate([0, 0, -0.1])
        cylinder(d=inner_diameter, h=height+0.2, $fn=50);
}"""

    def _generate_sphere_code(self, description: str) -> str:
        """Generate a sphere"""
        return """// Parametric sphere
// Generated from: """ + description + """

// Dimensions
outer_diameter = 20;
wall_thickness = 2;

// Main object
difference() {
    // Outer sphere
    sphere(d=outer_diameter, $fn=50);
    
    // Inner cavity
    sphere(d=outer_diameter-2*wall_thickness, $fn=50);
}"""

    def _generate_generic_code(self, description: str) -> str:
        """Generate a generic object"""
        return """// Generic 3D object
// Generated from: """ + description + """

// Basic dimensions
width = 25;
height = 25;
depth = 25;

// Simple object
union() {
    cube([width, height, depth]);
    translate([width/2, height/2, depth])
        cylinder(d=width/2, h=10, $fn=30);
}"""

    def _validate_and_clean_code(self, code: str) -> str:
        """Enhanced validation for OpenSCAD code"""
        print("🧹 Starting enhanced code validation...")
        
        # Basic cleanup first
        code = self._basic_code_cleanup(code)
        
        # Check for essential elements
        has_variables = any(line.strip().endswith(';') and '=' in line for line in code.split('\n')[:10])
        has_geometry = any(func in code for func in ['cube(', 'cylinder(', 'sphere(', 'union(', 'difference('])
        
        if not has_variables:
            print("⚠️  Adding missing variable definitions...")
            code = "// Auto-generated variables\ndefault_size = 20;\n\n" + code
        
        if not has_geometry:
            print("❌ No geometry found, using fallback...")
            return self._generate_fallback("basic object")
        
        # Ensure proper ending
        if not code.strip().endswith((';', '}')):
            code += ';'
        
        print(f"✅ Enhanced validation complete: {len(code)} characters")
        return code
