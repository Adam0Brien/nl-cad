"""
Cube-Only OpenSCAD Generator - Generates objects using only cubes for voxel-style creations
"""
import json
import re
import os
import requests
from typing import Dict, List, Optional
from ..core.base_generator import BaseGenerator


class CubeGenerator(BaseGenerator):
    def __init__(self, 
                 system_prompt_path: str = "config/catalog/cube/system_prompt.txt",
                 user_prompt_path: str = "config/catalog/cube/user_prompt.txt"):
        """Initialize with prompt files for cube-only generation"""
        super().__init__(system_prompt_path, user_prompt_path)
    
    def _get_default_prompt(self, prompt_path: str) -> str:
        """Get default prompts if files don't exist"""
        if "system" in prompt_path:
            return """You are an expert OpenSCAD voxel artist. Your job is to generate OpenSCAD code that creates objects using ONLY cubes.

STRICT RULES - CUBES ONLY:
1. Use ONLY cube() primitives - no cylinders, spheres, or other shapes
2. Use translate() to position cubes in 3D space
3. Use union() to combine cubes
4. Use difference() to subtract cubes (for hollow areas)
5. Think in terms of voxels/blocks like Minecraft
6. Create recognizable shapes through clever cube placement

APPROACH:
- Break objects into layers (bottom to top)
- Use a consistent cube size (like 10x10x10 units)
- Position cubes on a grid system
- Create outlines first, then fill in details
- Use subtraction for windows, doors, openings

EXAMPLE STRUCTURE:
```
// Object made of cubes only
union() {
    // Base layer
    translate([0, 0, 0]) cube([10, 10, 10]);
    translate([10, 0, 0]) cube([10, 10, 10]);
    
    // Second layer
    translate([0, 0, 10]) cube([10, 10, 10]);
    
    // Continue building up...
}
```

For complex objects like towers, buildings, or sculptures:
- Start with the base/foundation cubes
- Build up layer by layer
- Add details with smaller cubes
- Use subtraction for openings

Return ONLY valid OpenSCAD code using cubes."""

        else:  # user prompt
            return """Create a voxel/cube-based version of: {description}

Requirements:
- Use ONLY cube() primitives
- Position cubes with translate()
- Build the object layer by layer
- Make it recognizable despite the blocky style
- Use a consistent cube size (suggest 10x10x10 units)

Think like you're building with LEGO blocks or in Minecraft.

Return complete OpenSCAD code using only cubes."""

    def generate(self, description: str) -> str:
        """Main function: turn description into cube-only OpenSCAD code"""
        print(f"🧊 Cube mode: Generating voxel version of '{description}'")
        
        # Use Ollama to generate the cube-only OpenSCAD code
        code = self._generate_with_ollama(description)
        
        if code:
            print("✅ Generated cube-only OpenSCAD code")
            return code
        else:
            print("❌ Failed to generate cube code")
            return ""
    
    def _looks_like_openscad_code(self, text: str) -> bool:
        """Check if text looks like cube-only OpenSCAD code"""
        cube_indicators = ['cube(', 'translate(', 'union(', 'difference(']
        invalid_indicators = ['cylinder(', 'sphere(', 'polygon(']
        
        has_cubes = any(indicator in text for indicator in cube_indicators)
        has_invalid = any(indicator in text for indicator in invalid_indicators)
        
        return has_cubes and not has_invalid
    
    def _validate_and_clean_code(self, code: str) -> str:
        """Validate and clean the generated cube-only OpenSCAD code"""
        print("🧹 Starting code validation and cleaning...")
        
        # First do basic cleanup
        code = self._basic_code_cleanup(code)
        
        lines = code.split('\n')
        cleaned_lines = []
        skipped_lines = 0
        invalid_primitives_found = []
        needs_union_wrapper = True
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines at the start
            if not cleaned_lines and not stripped:
                continue
            
            # Check if code already has proper union structure
            if stripped.startswith('union()') or 'union {' in stripped:
                needs_union_wrapper = False
            
            # Validate cube-only constraint
            invalid_found = [invalid for invalid in ['cylinder(', 'sphere(', 'polygon(', 'circle('] if invalid in stripped.lower()]
            if invalid_found:
                print(f"❌ Skipping line with non-cube primitive ({invalid_found[0]}): {stripped}")
                invalid_primitives_found.extend(invalid_found)
                skipped_lines += 1
                continue
                
            cleaned_lines.append(line)
        
        print(f"📊 Cube validation complete:")
        print(f"   • Original lines: {len(lines)}")
        print(f"   • Cleaned lines: {len(cleaned_lines)}")
        print(f"   • Skipped lines: {skipped_lines}")
        if invalid_primitives_found:
            print(f"   • Invalid primitives found: {set(invalid_primitives_found)}")
        
        cleaned_code = '\n'.join(cleaned_lines).strip()
        
        # Wrap individual translate/cube statements in union if needed
        if needs_union_wrapper and cleaned_code:
            print("🔧 Wrapping individual cubes in union()...")
            # Check if we have multiple individual cube statements
            cube_statements = [line for line in cleaned_lines if 'translate(' in line and 'cube(' in line]
            if len(cube_statements) > 1:
                # Wrap in union
                indented_code = '\n'.join('    ' + line for line in cleaned_lines if line.strip())
                cleaned_code = f"union() {{\n{indented_code}\n}}"
        
        # Add a basic header comment if missing
        if not cleaned_code.startswith('//'):
            print("📝 Adding header comment...")
            cleaned_code = f"// Cube-only OpenSCAD code\n// Voxel-style creation\n\n{cleaned_code}"
        
        # Ensure it ends properly
        if cleaned_code and not cleaned_code.rstrip().endswith((';', '}', ')')):
            print("🔧 Adding missing semicolon...")
            cleaned_code += ';'
        
        print(f"✅ Final code length: {len(cleaned_code)} characters")
        print("🎯 Code validation complete!")
        
        return cleaned_code
