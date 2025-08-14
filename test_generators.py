#!/usr/bin/env python3
"""
Test all generators - Demonstrates the maze generator and other modes
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from generation.maze_generator import MazeGenerator
from generation.cube_generator import CubeGenerator
from generation.bosl_generator import BOSLGenerator


def test_maze_generator():
    """Test the maze generator with various descriptions"""
    print("🌀 Testing Maze Generator")
    print("=" * 50)
    
    generator = MazeGenerator()
    
    test_cases = [
        "simple 5x5 maze",
        "complex 10x10 maze with dead ends and pillars", 
        "beginner 6x6 maze with base platform",
        "advanced 8x8 maze with roof and rooms",
        "circular maze with decorative elements"
    ]
    
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    for i, description in enumerate(test_cases, 1):
        print(f"\nTest {i}: {description}")
        print("-" * 30)
        
        try:
            code = generator.generate(description)
            
            if code:
                print("✅ Generated successfully!")
                
                # Save to file
                filename = f"maze_test_{i}.scad"
                output_file = output_dir / filename
                output_file.write_text(code)
                print(f"📁 Saved to: {output_file}")
                
                # Show preview
                preview = code[:300].replace('\n', ' ')
                print(f"📄 Preview: {preview}...")
                
            else:
                print("❌ Generation failed!")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def test_cube_generator():
    """Test the cube generator"""
    print("\n🧊 Testing Cube Generator")
    print("=" * 50)
    
    generator = CubeGenerator()
    
    test_cases = [
        "simple house",
        "castle tower",
        "robot figure"
    ]
    
    output_dir = Path("output")
    
    for i, description in enumerate(test_cases, 1):
        print(f"\nTest {i}: {description}")
        print("-" * 30)
        
        try:
            code = generator.generate(description)
            
            if code:
                print("✅ Generated successfully!")
                
                # Save to file
                filename = f"cube_test_{i}.scad"
                output_file = output_dir / filename
                output_file.write_text(code)
                print(f"📁 Saved to: {output_file}")
                
            else:
                print("❌ Generation failed!")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def test_bosl_generator():
    """Test the BOSL generator"""
    print("\n🔧 Testing BOSL Generator")
    print("=" * 50)
    
    generator = BOSLGenerator()
    
    test_cases = [
        "M8 x 25 bolt",
        "20mm cube with 3mm fillet"
    ]
    
    output_dir = Path("output")
    
    for i, description in enumerate(test_cases, 1):
        print(f"\nTest {i}: {description}")
        print("-" * 30)
        
        try:
            code = generator.generate(description)
            
            if code:
                print("✅ Generated successfully!")
                
                # Save to file
                filename = f"bosl_test_{i}.scad"
                output_file = output_dir / filename
                output_file.write_text(code)
                print(f"📁 Saved to: {output_file}")
                
            else:
                print("❌ Generation failed!")
                
        except Exception as e:
            print(f"❌ Error: {e}")


def demonstrate_algorithmic_maze():
    """Demonstrate the algorithmic maze generation fallback"""
    print("\n⚙️  Testing Algorithmic Maze Generation")
    print("=" * 50)
    
    generator = MazeGenerator()
    
    # Test the algorithmic generation directly
    params = {
        'size': (5, 5),
        'type': 'rectangular',
        'difficulty': 'intermediate',
        'wall_height': 20,
        'wall_thickness': 2,
        'path_width': 10,
        'features': ['base', 'pillars']
    }
    
    try:
        code = generator._generate_algorithmic_maze(params)
        
        if code:
            print("✅ Algorithmic generation successful!")
            
            # Save to file
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / "algorithmic_maze.scad"
            output_file.write_text(code)
            print(f"📁 Saved to: {output_file}")
            
            # Show structure info
            lines = code.split('\n')
            print(f"📊 Generated {len(lines)} lines of code")
            print(f"🔧 Features: {params['features']}")
            
        else:
            print("❌ Algorithmic generation failed!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 NL-CAD Generator Testing Suite")
    print("=" * 60)
    
    # Test all generators
    test_maze_generator()
    test_cube_generator() 
    test_bosl_generator()
    demonstrate_algorithmic_maze()
    
    print("\n🏁 Testing complete!")
    print("Check the 'output/' directory for generated .scad files")
