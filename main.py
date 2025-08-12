#!/usr/bin/env python3
"""
Simple BOSL Generator CLI - Easy to use and understand
"""
import click
from pathlib import Path
from generation.bosl_generator import BOSLGenerator
from speech.speech_recognizer import speech_to_text_with_confirmation, quick_speech_to_text


@click.command()
@click.option('-d', '--description', 
              help='What you want to generate (e.g., "M8 x 25 bolt")')
@click.option('-o', '--output', 
              help='Output file path (optional - will show code in terminal if not specified)')
@click.option('--test', is_flag=True, 
              help='Run built-in test cases to see examples')
@click.option('--speech', is_flag=True,
              help='Use speech input instead of typing description')
@click.option('--quick-speech', is_flag=True,
              help='Quick speech input (no confirmation)')
def main(description, output, test, speech, quick_speech):
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
    
    # Create generator and generate code
    generator = BOSLGenerator()
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
    generator = BOSLGenerator()
    
    test_cases = [
        "M8 x 25 bolt",
        "M6 x 20 fine thread bolt", 
        "cuboid 20mm 30mm 40mm",
        "cuboid 25mm with fillet 5mm",
        "cyl length 40mm diameter 25mm",
        "3/8 inch washer",
        "M10 nut"
    ]
    
    click.echo("Running test cases...\n")
    
    for test in test_cases:
        click.echo(f"Input: {test}")
        click.echo("output:")
        code = generator.generate(test)
        click.echo(code)
        click.echo("-" * 50)


if __name__ == '__main__':
    main()
