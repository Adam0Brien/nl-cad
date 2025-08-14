#!/usr/bin/env python3
"""
Simple Maze Test - Tests maze generation without external dependencies
"""
import random
from pathlib import Path


def create_simple_maze_grid(width, height):
    """Create a simple maze grid using recursive backtracking"""
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
    
    # Start maze generation from (0,0)
    carve_path(0, 0)
    return grid


def generate_maze_openscad(maze_grid, wall_height=20, wall_thickness=2, path_width=10):
    """Generate OpenSCAD code for a maze"""
    width, height = len(maze_grid[0]), len(maze_grid)
    cell_size = path_width + wall_thickness
    total_width = width * cell_size + wall_thickness
    total_height = height * cell_size + wall_thickness
    
    code_lines = [
        "// Simple algorithmically generated maze",
        f"// Grid size: {width}x{height}",
        f"// Wall height: {wall_height}, thickness: {wall_thickness}",
        f"// Path width: {path_width}",
        "",
        "union() {",
    ]
    
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
    
    code_lines.append("}")
    
    # Add entrance and exit
    entrance_x = wall_thickness
    entrance_y = 0
    exit_x = total_width - wall_thickness - path_width
    exit_y = total_height - wall_thickness
    
    code_lines.extend([
        "",
        "// Create entrance and exit openings",
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
    
    return '\n'.join(code_lines)


def test_maze_generation():
    """Test the maze generation"""
    print("🌀 Testing Simple Maze Generation")
    print("=" * 50)
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    test_cases = [
        {"size": (5, 5), "name": "5x5_simple"},
        {"size": (8, 8), "name": "8x8_medium"},
        {"size": (10, 6), "name": "10x6_rectangular"}
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        width, height = test_case["size"]
        name = test_case["name"]
        
        print(f"\nTest {i}: Generating {width}x{height} maze ({name})")
        print("-" * 40)
        
        try:
            # Generate maze grid
            maze_grid = create_simple_maze_grid(width, height)
            print(f"✅ Created maze grid: {width}x{height}")
            
            # Generate OpenSCAD code
            code = generate_maze_openscad(maze_grid)
            print(f"✅ Generated OpenSCAD code ({len(code)} characters)")
            
            # Save to file
            filename = f"maze_{name}.scad"
            output_file = output_dir / filename
            output_file.write_text(code)
            print(f"📁 Saved to: {output_file}")
            
            # Show preview
            preview_lines = code.split('\n')[:10]
            print(f"📄 Preview (first 10 lines):")
            for line in preview_lines:
                print(f"    {line}")
            print("    ...")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Simple Maze Generator Test")
    print("=" * 60)
    
    test_maze_generation()
    
    print("\n🏁 Testing complete!")
    print("Check the 'output/' directory for generated .scad files")
    print("\nTo test in OpenSCAD:")
    print("1. Open one of the generated .scad files in OpenSCAD")
    print("2. Press F5 to preview or F6 to render")
    print("3. You should see a 3D maze with walls and paths!")
