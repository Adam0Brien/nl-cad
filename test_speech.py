#!/usr/bin/env python3
"""
Test speech integration with the nl-cad project
"""
from speech.speech_recognizer import SpeechRecognizer, quick_speech_to_text
from generation.bosl_generator import BOSLGenerator


def test_speech_integration():
    """Test the complete speech-to-CAD pipeline"""
    print("🎤 Testing Speech Integration with NL-CAD")
    print("=" * 50)
    
    # Test cases that work well with speech
    speech_test_cases = [
        "Try saying: 'M8 bolt 25 millimeters long'",
        "Try saying: 'Create a cube 20 millimeters'", 
        "Try saying: 'Make a cylinder 40mm tall and 25mm wide'",
        "Try saying: 'I need an M6 nut'",
        "Try saying: 'Generate a washer for M10 bolt'"
    ]
    
    generator = BOSLGenerator()
    recognizer = SpeechRecognizer()
    
    # Test microphone first
    print("🔧 Testing microphone...")
    if not recognizer.test_microphone():
        print("❌ Microphone test failed. Please check your audio setup.")
        print("Ensure you have:")
        print("- A working microphone")
        print("- Installed: pip install SpeechRecognition pyaudio")
        print("- Proper permissions for microphone access")
        return
    
    print("✅ Microphone working!")
    print()
    
    for i, suggestion in enumerate(speech_test_cases, 1):
        print(f"Test {i}/5: {suggestion}")
        print("-" * 50)
        
        # Get speech input
        text = recognizer.listen_with_confirmation()
        
        if text:
            print(f"🗣️  Speech Input: '{text}'")
            
            # Generate CAD code
            code = generator.generate(text)
            print("🔧 Generated OpenSCAD:")
            print(code)
            
            # Ask if user wants to continue
            cont = input("\nContinue to next test? (y/n): ").lower().strip()
            if cont in ['n', 'no']:
                break
        else:
            print("❌ No speech recognized. Skipping to next test.")
        
        print("\n" + "=" * 50 + "\n")
    
    print("🎉 Speech integration test complete!")


def test_quick_speech():
    """Test quick speech mode"""
    print("🎤 Testing Quick Speech Mode")
    print("=" * 30)
    
    generator = BOSLGenerator()
    
    print("Speak a CAD request (you have 10 seconds)...")
    text = quick_speech_to_text(timeout=10.0)
    
    if text:
        print(f"🗣️  Heard: '{text}'")
        code = generator.generate(text)
        print("🔧 Generated:")
        print(code)
    else:
        print("❌ No speech detected")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        test_quick_speech()
    else:
        test_speech_integration()
