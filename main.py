#!/usr/bin/env python3
"""
Multi-Generator CLI - Supports BOSL, Cube-only, Maze, Enhanced, and Two-Stage generators
"""
import click
from pathlib import Path
from generation.creative.hybrid_generator import HybridCADGenerator
from generation.catalog.bosl_generator import BOSLGenerator
from generation.catalog.cube_generator import CubeGenerator
from generation.catalog.maze_generator import MazeGenerator
from generation.creative.enhanced_generator import EnhancedGenerator
from generation.creative.two_stage_generator import TwoStageGenerator
from conversation.conversation_manager import ConversationManager
from speech.speech_recognizer import speech_to_text_with_confirmation, quick_speech_to_text


@click.command()
@click.option('-d', '--description', 
              help='What you want to generate (e.g., "M8 x 25 bolt")')
@click.option('-o', '--output', 
              help='Output file path (optional - will show code in terminal if not specified)')
@click.option('-m', '--mode', 
              type=click.Choice(['bosl', 'cube', 'maze', 'enhanced', 'two-stage', 'conversation'], case_sensitive=False),
              default='bosl',
              help='Generator mode: bosl (default), cube (voxel-style), maze, enhanced (auto-detect), two-stage (design→code), or conversation (interactive)')
@click.option('--test', is_flag=True, 
              help='Run built-in test cases to see examples')
@click.option('--speech', is_flag=True,
              help='Use speech input instead of typing description')
@click.option('--quick-speech', is_flag=True,
              help='Quick speech input (no confirmation)')
def main(description, output, mode, test, speech, quick_speech):
    """Generate OpenSCAD code from natural language descriptions"""
    
    if test:
        run_tests()
        return
    
    # Handle speech input
    if speech or quick_speech:
        if description:
            click.echo("Warning: Both description and speech specified. Using speech input.")
        
        try:
            if quick_speech:
                click.echo("🎤 Quick Speech Mode - Speak your CAD request:")
                description = quick_speech_to_text(timeout=30.0)
            else:
                click.echo("🎤 Speech Mode - Speak your CAD request:")
                description = speech_to_text_with_confirmation()
            
            if not description:
                click.echo("❌ No speech input received. Exiting.")
                return
                
        except ImportError:
            click.echo("❌ Speech recognition not available. Please install requirements:")
            click.echo("pip install SpeechRecognition pyaudio")
            return
        except Exception as e:
            click.echo(f"❌ Speech recognition error: {e}")
            return
    
    if not description:
        click.echo("Error: Please provide a description with -d, use --speech, or use --test to see examples")
        return
    
    # Create appropriate generator based on mode
    if mode.lower() == 'cube':
        generator = CubeGenerator()
        click.echo(f"🧊 Using Cube-only generator for voxel-style creation")
    elif mode.lower() == 'maze':
        generator = MazeGenerator()
        click.echo(f"🌀 Using Maze generator")
    elif mode.lower() == 'enhanced':
        generator = EnhancedGenerator()
        click.echo(f"⚡ Using Enhanced generator (auto-detects object type)")
    elif mode.lower() == 'two-stage':
        generator = TwoStageGenerator()
        click.echo(f"🎭 Using Two-stage generator (design → code)")
    elif mode.lower() == 'conversation':
        click.echo(f"💬 Starting Conversational Design Mode")
        run_conversational_mode(description or "interactive design session")
        return
    elif mode.lower() == 'bosl':
        generator = BOSLGenerator()
        click.echo(f"🔧 Using BOSL generator for mechanical parts")
    else:  # bosl or default
        generator = HybridCADGenerator()
        click.echo(f"🔧 Using BOSL generator for mechanical parts")
    
    # Generate code
    code = generator.generate(description)
    
    if output:
        # Save to file
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(code)
        click.echo(f"Generated OpenSCAD code saved to: {output_path}")
    else:
        # Show in terminal
        click.echo("\nGenerated OpenSCAD Code:")
        click.echo("=" * 40)
        click.echo(code)
        click.echo("=" * 40)


def run_tests():
    """Run built-in test cases"""
    generator = HybridCADGenerator()
    
    test_cases = [
        # Catalog-based tests (should use fast path)
        "M8 x 25 bolt",
        "M6 x 20 fine thread bolt", 
        "cuboid 20mm 30mm 40mm",
        "cuboid 25mm with fillet 5mm",
        "cyl length 40mm diameter 25mm",
        "M10 nut",
        
        # Hybrid tests (should trigger AI completion or creative generation)
        "storage box for screws",  # Should infer tray with reasonable dimensions
        "hexagonal container 50mm wide",  # Should trigger creative AI generation
        "small gear for robot project"  # Should infer reasonable gear parameters
    ]
    
    # Enhanced Generator tests
    click.echo("\n⚡ Enhanced Generator Tests:")
    click.echo("=" * 50)
    enhanced_generator = EnhancedGenerator()
    
    enhanced_test_cases = [
        "storage box with lid",
        "decorative vase", 
        "phone stand",
        "desk organizer",
        "lamp shade"
    ]
    
    for test in enhanced_test_cases:
        click.echo(f"Input: {test}")
        code = enhanced_generator.generate(test)
        click.echo(f"Output:\n{code}")
        click.echo("-" * 30)
    
    # Cube Generator tests
    click.echo("\n🧊 Cube Generator Tests:")
    click.echo("=" * 50)
    cube_generator = CubeGenerator()
    
    cube_test_cases = [
        "simple house",
        "castle tower", 
        "tree",
        "robot figure",
        "car"
    ]
    
    for test in cube_test_cases:
        click.echo(f"Input: {test}")
        code = cube_generator.generate(test)
        click.echo(f"Output:\n{code}")
        click.echo("-" * 30)
    
    
    # Maze Generator tests
    click.echo("\n🌀 Maze Generator Tests:")
    click.echo("=" * 50)
    maze_generator = MazeGenerator()
    
    maze_test_cases = [
        "simple 5x5 maze",
        "complex 10x10 maze with dead ends",
        "circular maze", 
        "beginner maze with rooms",
        "advanced multi-level maze"
    ]
    
    for test in maze_test_cases:
        click.echo(f"Input: {test}")
        code = maze_generator.generate(test)
        click.echo(f"Output:\n{code}")
        click.echo("-" * 30)
    
    # Two-Stage Generator tests
    click.echo("\n🎭 Two-Stage Generator Tests:")
    click.echo("=" * 50)
    two_stage_generator = TwoStageGenerator()
    
    two_stage_test_cases = [
        "coffee mug with handle",
        "modern desk lamp",
        "storage box with compartments",
        "decorative flower vase",
        "phone charging stand"
    ]
    
    for test in two_stage_test_cases:
        click.echo(f"Input: {test}")
        code = two_stage_generator.generate(test)
        click.echo(f"Output:\n{code}")
        click.echo("-" * 30)


def run_conversational_mode(initial_description: str):
    """Run interactive conversational design mode"""
    click.echo("💬 Welcome to Conversational Design Mode!")
    click.echo("I'll ask questions to help design exactly what you need.")
    click.echo("Type 'quit' or 'exit' at any time to stop.")
    click.echo("Type 'reset' to start a fresh conversation.\n")
    
    conversation_manager = ConversationManager()
    
    # Start conversation
    if initial_description and initial_description != "interactive design session":
        initial_request = initial_description
    else:
        initial_request = click.prompt("What would you like to design?")
    
    try:
        # Start conversation
        response = conversation_manager.start_conversation(initial_request)
        
        while True:
            # Display assistant message
            click.echo(f"\n🤖 Assistant: {response['message']}")
            
            # Show progress
            if response.get('progress'):
                progress_bar = "█" * (response['progress'] // 5) + "░" * (20 - response['progress'] // 5)
                click.echo(f"Progress: [{progress_bar}] {response['progress']}%")
            
            # Show questions
            if response.get('questions'):
                click.echo("\nQuestions to help me understand better:")
                for i, question in enumerate(response['questions'], 1):
                    click.echo(f"  {i}. {question}")
            
            # Show current code if available
            if response.get('code'):
                click.echo(f"\n📄 Current Design Preview:")
                code_preview = response['code'][:200] + "..." if len(response['code']) > 200 else response['code']
                click.echo(code_preview)
            
            # Check if complete
            if response.get('stage') == 'complete':
                click.echo("\n✅ Design complete!")
                if click.confirm("Would you like to save the OpenSCAD code?"):
                    save_path = click.prompt("Save as", default="conversational_design.scad")
                    with open(save_path, 'w') as f:
                        f.write(response.get('code', ''))
                    click.echo(f"Saved to {save_path}")
                break
            
            # Get user input
            user_input = click.prompt("\n💭 Your response").strip()
            
            if user_input.lower() in ['quit', 'exit', 'stop']:
                click.echo("👋 Thanks for using Conversational Design!")
                break
            elif user_input.lower() == 'reset':
                click.echo("🔄 Starting fresh conversation...")
                new_request = click.prompt("What would you like to design?")
                response = conversation_manager.start_fresh_conversation(new_request)
                continue
            
            # Continue conversation
            response = conversation_manager.continue_conversation(user_input)
            
    except KeyboardInterrupt:
        click.echo("\n👋 Conversation ended. Thanks for using Conversational Design!")
    except Exception as e:
        click.echo(f"\n❌ Error in conversation: {e}")


if __name__ == '__main__':
    main()
