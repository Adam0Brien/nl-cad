"""
Maze OpenSCAD Generator - Generates various types of mazes with walls, paths, and optional features
"""
import json
import re
import os
import random
from typing import Dict, List, Optional, Tuple
from .base_generator import BaseGenerator


class MazeGenerator(BaseGenerator):
    def __init__(self, 
                 system_prompt_path: str = "config/maze_system_prompt.txt",
                 user_prompt_path: str = "config/maze_user_prompt.txt"):
        """Initialize with prompt files for maze generation"""
        super().__init__(system_prompt_path, user_prompt_path)
        
        # Maze generation parameters
        self.default_wall_height = 20
        self.default_wall_thickness = 2
        self.default_path_width = 10
        self.default_maze_size = (10, 10)  # width x height in cells
    
    def _get_default_prompt(self, prompt_path: str) -> str:
        """Get default prompts if files don't exist"""
        if "system" in prompt_path:
            return """You are an expert OpenSCAD maze designer. Your job is to generate OpenSCAD code that creates various types of mazes.

MAZE DESIGN PRINCIPLES:
1. Use cube() primitives for walls
2. Use translate() to position wall segments
3. Use union() to combine all wall pieces
4. Use difference() to create openings and paths
5. Consider start and end points
6. Make paths wide enough for navigation

MAZE TYPES TO SUPPORT:
- Simple rectangular mazes
- Circular/radial mazes  
- Multi-level mazes
- Mazes with rooms
- Mazes with decorative elements

WALL CONSTRUCTION:
- Standard wall height: 20 units
- Wall thickness: 2 units
- Path width: 10 units
- Use consistent grid system

MAZE FEATURES:
- Clear start and end points
- Dead ends for challenge
- Multiple solution paths (optional)
- Decorative elements (pillars, arches)
- Optional roof or ceiling
- Optional base platform

EXAMPLE STRUCTURE:
```
// Maze with walls
union() {
    // Outer boundary walls
    translate([0, 0, 0]) cube([wall_thickness, maze_height, wall_height]);
    
    // Internal walls
    translate([x, y, 0]) cube([length, wall_thickness, wall_height]);
    
    // More walls...
}

// Optional: Subtract openings for doors/passages
difference() {
    // walls here
    // subtract door openings
    translate([door_x, door_y, door_z]) cube([door_width, door_depth, door_height]);
}
```

MAZE ALGORITHMS TO CONSIDER:
- Recursive backtracking
- Binary tree
- Eller's algorithm
- Wilson's algorithm

Return ONLY valid OpenSCAD code that creates a functional, interesting maze."""

        else:  # user prompt
            return """Create a maze design for: {description}

Requirements:
- Generate OpenSCAD code for a complete maze
- Include boundary walls and internal walls
- Create clear paths for navigation
- Add start and end points (openings in boundary)
- Make it challenging but solvable
- Use standard dimensions (wall height: 20, thickness: 2, path width: 10)

Maze specifications from description:
- Size: Extract or default to 10x10 cells
- Type: rectangular, circular, or multi-level as specified
- Difficulty: beginner, intermediate, or advanced
- Special features: rooms, dead ends, multiple levels, decorative elements

Additional considerations:
- Ensure there's at least one solution path
- Add visual interest with varying wall heights or decorative elements
- Consider adding a base platform
- Include comments explaining the maze layout

Return complete OpenSCAD code for the maze."""

    def generate(self, description: str) -> str:
        """Main function: turn description into maze OpenSCAD code"""
        print(f"🌀 Maze mode: Generating maze for '{description}'")
        
        # Parse description for maze parameters
        maze_params = self._parse_maze_description(description)
        print(f"📊 Parsed maze parameters: {maze_params}")
        
        # Always use algorithmic generation for reliability
        print("⚙️  Using algorithmic maze generation for consistent results")
        return self._generate_algorithmic_maze(maze_params)
    
    def _parse_maze_description(self, description: str) -> Dict:
        """Parse description to extract maze parameters"""
        params = {
            'size': self.default_maze_size,
            'type': 'rectangular',
            'difficulty': 'intermediate',
            'wall_height': self.default_wall_height,
            'wall_thickness': self.default_wall_thickness,
            'path_width': self.default_path_width,
            'features': []
        }
        
        description_lower = description.lower()
        
        # Extract size
        size_match = re.search(r'(\d+)\s*[x×]\s*(\d+)', description)
        if size_match:
            params['size'] = (int(size_match.group(1)), int(size_match.group(2)))
        
        # Extract maze type
        if any(word in description_lower for word in ['circular', 'round', 'radial']):
            params['type'] = 'circular'
        elif any(word in description_lower for word in ['multi-level', 'multilevel', '3d', 'layered']):
            params['type'] = 'multi-level'
        elif any(word in description_lower for word in ['room', 'chamber']):
            params['type'] = 'rooms'
        
        # Extract difficulty
        if any(word in description_lower for word in ['simple', 'easy', 'beginner']):
            params['difficulty'] = 'beginner'
        elif any(word in description_lower for word in ['hard', 'difficult', 'complex', 'advanced']):
            params['difficulty'] = 'advanced'
        
        # Extract features
        if any(word in description_lower for word in ['dead end', 'deadend']):
            params['features'].append('dead_ends')
        if any(word in description_lower for word in ['pillar', 'column']):
            params['features'].append('pillars')
        if any(word in description_lower for word in ['roof', 'ceiling', 'top']):
            params['features'].append('roof')
        if any(word in description_lower for word in ['base', 'platform', 'floor']):
            params['features'].append('base')
        
        return params
    
    def _generate_algorithmic_maze(self, params: Dict) -> str:
        """Generate a maze algorithmically using recursive backtracking"""
        print("🔧 Generating maze algorithmically...")
        
        width, height = params['size']
        wall_height = params['wall_height']
        wall_thickness = params['wall_thickness']
        path_width = params['path_width']
        
        # Generate maze grid using recursive backtracking
        maze_grid = self._create_maze_grid(width, height, params['difficulty'])
        
        # Convert maze grid to OpenSCAD code
        if params['type'] == 'circular':
            code = self._generate_circular_maze_code(maze_grid, params)
        elif params['type'] == 'multi-level':
            code = self._generate_multilevel_maze_code(maze_grid, params)
        else:
            code = self._generate_rectangular_maze_code(maze_grid, params)
        
        return code
    
    def _create_maze_grid(self, width: int, height: int, difficulty: str) -> List[List[Dict]]:
        """Create a maze grid using recursive backtracking algorithm"""
        # Initialize grid
        grid = []
        for y in range(height):
            row = []
            for x in range(width):
                row.append({
                    'visited': False,
                    'walls': {'top': True, 'right': True, 'bottom': True, 'left': True}
                })
            grid.append(row)
        
        # Recursive backtracking maze generation
        def carve_path(x, y):
            grid[y][x]['visited'] = True
            
            # Get neighbors in random order
            neighbors = [(x, y-1, 'top'), (x+1, y, 'right'), (x, y+1, 'bottom'), (x-1, y, 'left')]
            random.shuffle(neighbors)
            
            for nx, ny, direction in neighbors:
                if 0 <= nx < width and 0 <= ny < height and not grid[ny][nx]['visited']:
                    # Remove wall between current cell and neighbor
                    grid[y][x]['walls'][direction] = False
                    opposite = {'top': 'bottom', 'right': 'left', 'bottom': 'top', 'left': 'right'}
                    grid[ny][nx]['walls'][opposite[direction]] = False
                    
                    carve_path(nx, ny)
        
        # Start maze generation from random corner
        start_x, start_y = (0, 0) if difficulty != 'advanced' else (random.randint(0, width-1), random.randint(0, height-1))
        carve_path(start_x, start_y)
        
        # Add complexity based on difficulty
        if difficulty == 'advanced':
            # Remove some additional walls to create multiple paths
            for _ in range(width * height // 10):
                x, y = random.randint(0, width-1), random.randint(0, height-1)
                directions = ['top', 'right', 'bottom', 'left']
                direction = random.choice(directions)
                if grid[y][x]['walls'][direction]:
                    nx, ny = x, y
                    if direction == 'top' and y > 0: ny -= 1
                    elif direction == 'right' and x < width-1: nx += 1
                    elif direction == 'bottom' and y < height-1: ny += 1
                    elif direction == 'left' and x > 0: nx -= 1
                    else: continue
                    
                    grid[y][x]['walls'][direction] = False
                    opposite = {'top': 'bottom', 'right': 'left', 'bottom': 'top', 'left': 'right'}
                    grid[ny][nx]['walls'][opposite[direction]] = False
        
        return grid
    
    def _generate_rectangular_maze_code(self, maze_grid: List[List[Dict]], params: Dict) -> str:
        """Generate OpenSCAD code for a rectangular maze"""
        width, height = len(maze_grid[0]), len(maze_grid)
        wall_height = params['wall_height']
        wall_thickness = params['wall_thickness']
        path_width = params['path_width']
        
        cell_size = path_width + wall_thickness
        total_width = width * cell_size + wall_thickness
        total_height = height * cell_size + wall_thickness
        
        code_lines = [
            "// Algorithmically generated rectangular maze",
            f"// Grid size: {width}x{height}",
            f"// Wall height: {wall_height}, thickness: {wall_thickness}",
            f"// Path width: {path_width}",
            "",
            "union() {",
        ]
        
        # Add base platform if requested
        if 'base' in params['features']:
            code_lines.extend([
                "    // Base platform",
                f"    translate([0, 0, -2]) cube([{total_width}, {total_height}, 2]);",
                ""
            ])
        
        # Generate boundary walls
        code_lines.extend([
            "    // Boundary walls",
            f"    translate([0, 0, 0]) cube([{wall_thickness}, {total_height}, {wall_height}]); // Left wall",
            f"    translate([{total_width - wall_thickness}, 0, 0]) cube([{wall_thickness}, {total_height}, {wall_height}]); // Right wall",
            f"    translate([0, 0, 0]) cube([{total_width}, {wall_thickness}, {wall_height}]); // Bottom wall",
            f"    translate([0, {total_height - wall_thickness}, 0]) cube([{total_width}, {wall_thickness}, {wall_height}]); // Top wall",
            ""
        ])
        
        # Generate internal walls
        code_lines.append("    // Internal walls")
        for y in range(height):
            for x in range(width):
                cell = maze_grid[y][x]
                base_x = x * cell_size + wall_thickness
                base_y = y * cell_size + wall_thickness
                
                # Right wall
                if cell['walls']['right'] and x < width - 1:
                    wall_x = base_x + path_width
                    code_lines.append(f"    translate([{wall_x}, {base_y}, 0]) cube([{wall_thickness}, {path_width}, {wall_height}]);")
                
                # Top wall
                if cell['walls']['top'] and y < height - 1:
                    wall_y = base_y + path_width
                    code_lines.append(f"    translate([{base_x}, {wall_y}, 0]) cube([{path_width}, {wall_thickness}, {wall_height}]);")
        
        # Add decorative pillars if requested
        if 'pillars' in params['features']:
            code_lines.extend([
                "",
                "    // Decorative pillars at intersections"
            ])
            for y in range(height + 1):
                for x in range(width + 1):
                    pillar_x = x * cell_size
                    pillar_y = y * cell_size
                    code_lines.append(f"    translate([{pillar_x}, {pillar_y}, 0]) cube([{wall_thickness}, {wall_thickness}, {wall_height + 5}]);")
        
        code_lines.append("}")
        
        # Add entrance and exit
        entrance_x = wall_thickness
        entrance_y = 0
        exit_x = total_width - wall_thickness * 2
        exit_y = total_height - wall_thickness
        
        code_lines.extend([
            "",
            "// Create entrance and exit",
            "difference() {",
            "    union() { /* maze walls above */ }",
            "",
            "    // Entrance",
            f"    translate([{entrance_x}, {entrance_y - 1}, 0]) cube([{path_width}, {wall_thickness + 2}, {wall_height}]);",
            "",
            "    // Exit", 
            f"    translate([{exit_x}, {exit_y - 1}, 0]) cube([{path_width}, {wall_thickness + 2}, {wall_height}]);",
            "}"
        ])
        
        # Add roof if requested
        if 'roof' in params['features']:
            code_lines.extend([
                "",
                "// Optional roof",
                f"translate([0, 0, {wall_height}]) cube([{total_width}, {total_height}, 2]);"
            ])
        
        return '\n'.join(code_lines)
    
    def _generate_circular_maze_code(self, maze_grid: List[List[Dict]], params: Dict) -> str:
        """Generate OpenSCAD code for a circular maze"""
        # For now, generate a simplified circular maze
        # This would need more complex geometry calculations for a true circular maze
        return self._generate_rectangular_maze_code(maze_grid, params) + "\n\n// TODO: Implement true circular maze geometry"
    
    def _generate_multilevel_maze_code(self, maze_grid: List[List[Dict]], params: Dict) -> str:
        """Generate OpenSCAD code for a multi-level maze"""
        base_code = self._generate_rectangular_maze_code(maze_grid, params)
        
        # Add a second level
        wall_height = params['wall_height']
        second_level = base_code.replace("union() {", f"union() {{\n    // Level 1\n").replace(
            "translate([", f"translate(["
        ).replace("}", f"\n    // Level 2 (shifted)\n    translate([0, 0, {wall_height + 5}]) {{\n        // Simplified second level\n    }}\n}}")
        
        return second_level
    
    def _looks_like_openscad_code(self, text: str) -> bool:
        """Check if text looks like maze OpenSCAD code"""
        maze_indicators = ['cube(', 'translate(', 'union(', 'difference(', 'maze', 'wall']
        return any(indicator in text.lower() for indicator in maze_indicators)
    
    def _validate_and_clean_code(self, code: str) -> str:
        """Validate and clean the generated maze OpenSCAD code"""
        print("🧹 Starting maze code validation and cleaning...")
        
        # First do basic cleanup
        code = self._basic_code_cleanup(code)
        
        # Add maze-specific validation
        lines = code.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines at the start
            if not cleaned_lines and not stripped:
                continue
                
            cleaned_lines.append(line)
        
        cleaned_code = '\n'.join(cleaned_lines).strip()
        
        # Add a basic header comment if missing
        if not cleaned_code.startswith('//'):
            print("📝 Adding header comment...")
            cleaned_code = f"// Maze OpenSCAD code\n// Generated maze with walls and paths\n\n{cleaned_code}"
        
        # Ensure it ends properly
        if cleaned_code and not cleaned_code.rstrip().endswith((';', '}', ')')):
            print("🔧 Adding missing semicolon...")
            cleaned_code += ';'
        
        print(f"✅ Final maze code length: {len(cleaned_code)} characters")
        print("🎯 Maze code validation complete!")
        
        return cleaned_code
