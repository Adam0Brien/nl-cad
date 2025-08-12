#!/usr/bin/env python3
"""
Speech recognition module for nl-cad
Converts speech to text for CAD component generation
"""
import time
from typing import Optional

try:
    import speech_recognition as sr
    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    sr = None


class SpeechRecognizer:
    def __init__(self, timeout: float = 10.0, phrase_timeout: float = 3.0):
        """
        Initialize speech recognizer
        
        Args:
            timeout: Maximum time to wait for speech to start
            phrase_timeout: How long to wait after speech stops
        """
        if not SPEECH_AVAILABLE:
            raise ImportError("Speech recognition libraries not available. Install with: pip install SpeechRecognition")
        
        self.recognizer = sr.Recognizer()
        self.timeout = timeout
        self.phrase_timeout = phrase_timeout
        
        # Use default microphone for now
        print("Using default microphone...")
        self.microphone = sr.Microphone()
        
        # Adjust for ambient noise on initialization
        print("Calibrating microphone for ambient noise...")
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            # Make it much more sensitive to pick up speech
            self.recognizer.energy_threshold = 50  # Very low threshold
            print(f"Microphone calibrated! Energy threshold: {self.recognizer.energy_threshold}")
        except Exception as e:
            print(f"Warning: Could not calibrate microphone: {e}")
            # Set a very low energy threshold as fallback
            self.recognizer.energy_threshold = 50
            print("Proceeding with default settings...")
    
    def _find_best_microphone(self):
        """Try to find the best available microphone"""
        try:
            # Get list of microphones
            mic_list = sr.Microphone.list_microphone_names()
            print(f"Found {len(mic_list)} microphones")
            
            # Preferred microphone names (in order of preference)
            preferred = ["ALC257 Analog", "pipewire", "default"]
            
            # Try to find a preferred microphone
            for pref in preferred:
                for i, name in enumerate(mic_list):
                    if pref.lower() in name.lower():
                        print(f"Using microphone: {name}")
                        return sr.Microphone(device_index=i)
            
            # Fallback to default microphone
            print("Using default microphone")
            return sr.Microphone()
            
        except Exception as e:
            print(f"Error finding microphone: {e}")
            print("Using default microphone")
            return sr.Microphone()
    
    def listen_once(self, prompt: str = "Speak your CAD request now:") -> Optional[str]:
        """
        Listen for a single speech input and convert to text
        
        Args:
            prompt: Message to display to user
            
        Returns:
            Recognized text or None if recognition failed
        """
        print(f"\n🎤 {prompt}")
        print("Listening... (speak within 10 seconds)")
        
        try:
            with self.microphone as source:
                # Show current energy threshold
                print(f"Energy threshold: {self.recognizer.energy_threshold}")
                print("Speak now - I'm listening for ANY sound...")
                
                # Listen for audio with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=self.timeout,
                    phrase_time_limit=self.phrase_timeout
                )
            
            print("Processing speech...")
            
            # Try Google Speech Recognition first (requires internet)
            try:
                text = self.recognizer.recognize_google(audio)
                print(f"✅ Heard: '{text}'")
                return text
                
            except sr.RequestError:
                # Fallback to offline recognition
                print("No internet connection, trying offline recognition...")
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    print(f"✅ Heard (offline): '{text}'")
                    return text
                except sr.RequestError:
                    print("❌ Offline recognition not available")
                    return None
                    
        except sr.WaitTimeoutError:
            print("❌ No speech detected within timeout period")
            return None
            
        except sr.UnknownValueError:
            print("❌ Could not understand the speech")
            return None
            
        except Exception as e:
            print(f"❌ Speech recognition error: {e}")
            return None
    
    def listen_with_confirmation(self, max_attempts: int = 3) -> Optional[str]:
        """
        Listen for speech with confirmation loop
        
        Args:
            max_attempts: Maximum number of attempts before giving up
            
        Returns:
            Confirmed text or None if user cancels/max attempts reached
        """
        for attempt in range(max_attempts):
            text = self.listen_once()
            
            if text is None:
                if attempt < max_attempts - 1:
                    print(f"Attempt {attempt + 1}/{max_attempts} failed. Try again.")
                    continue
                else:
                    print("Max attempts reached.")
                    return None
            
            # Ask for confirmation
            print(f"\nI heard: '{text}'")
            confirm = input("Is this correct? (y/n/retry): ").lower().strip()
            
            if confirm in ['y', 'yes', '']:
                return text
            elif confirm in ['n', 'no']:
                return None
            elif confirm in ['r', 'retry']:
                continue
            else:
                # Treat unknown input as 'yes'
                return text
                
        return None
    
    def test_microphone(self) -> bool:
        """
        Test if microphone is working
        
        Returns:
            True if microphone test successful
        """
        try:
            print("Testing microphone... Say something!")
            text = self.listen_once("Testing microphone:")
            return text is not None
        except Exception as e:
            print(f"Microphone test failed: {e}")
            return False


# Utility functions for easy integration
def quick_speech_to_text(timeout: float = 15.0) -> Optional[str]:
    """
    Quick one-shot speech recognition
    
    Args:
        timeout: Maximum time to wait for speech
        
    Returns:
        Recognized text or None
    """
    if not SPEECH_AVAILABLE:
        print("❌ Speech recognition not available. Install with: pip install SpeechRecognition")
        return None
        
    try:
        recognizer = SpeechRecognizer(timeout=timeout)
        return recognizer.listen_once()
    except Exception as e:
        print(f"Speech recognition failed: {e}")
        return None


def speech_to_text_with_confirmation() -> Optional[str]:
    """
    Speech recognition with user confirmation
    
    Returns:
        Confirmed text or None
    """
    if not SPEECH_AVAILABLE:
        print("❌ Speech recognition not available. Install with: pip install SpeechRecognition")
        return None
        
    try:
        recognizer = SpeechRecognizer()
        return recognizer.listen_with_confirmation()
    except Exception as e:
        print(f"Speech recognition failed: {e}")
        return None


if __name__ == "__main__":
    # Test the speech recognizer
    print("Testing Speech Recognizer")
    print("=" * 40)
    
    recognizer = SpeechRecognizer()
    
    # Test microphone
    if not recognizer.test_microphone():
        print("Microphone test failed. Please check your audio setup.")
        exit(1)
    
    # Test with confirmation
    print("\nTesting with confirmation:")
    result = recognizer.listen_with_confirmation()
    if result:
        print(f"Final result: {result}")
    else:
        print("No speech recognized")
