"""
Base OpenSCAD Generator - Abstract base class for all generators
"""
import json
import re
import os
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseGenerator(ABC):
    """Abstract base class for OpenSCAD generators"""
    
    def __init__(self, 
                 system_prompt_path: str,
                 user_prompt_path: str):
        """Initialize with prompt files"""
        self.system_prompt_path = system_prompt_path
        self.user_prompt_path = user_prompt_path
        self.system_prompt = self._load_prompt(system_prompt_path)
        self.user_prompt = self._load_prompt(user_prompt_path)
    
    def _load_prompt(self, prompt_path: str) -> str:
        """Load a prompt file"""
        try:
            with open(prompt_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Prompt file {prompt_path} not found, using default")
            return self._get_default_prompt(prompt_path)
    
    @abstractmethod
    def _get_default_prompt(self, prompt_path: str) -> str:
        """Get default prompts if files don't exist - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def generate(self, description: str) -> str:
        """Main function: turn description into OpenSCAD code - must be implemented by subclasses"""
        pass
    
    def _generate_with_ollama(self, description: str, temperature: float = 0.2, num_predict: int = 2500) -> str:
        """Use Ollama to generate OpenSCAD code"""
        try:
            print("🔧 Preparing LLM request...")
            
            # Format the user prompt with description
            user_prompt = self.user_prompt.replace("{description}", description)
            print(f"📝 User prompt: {user_prompt[:100]}...")
            
            # Resolve Ollama configuration from environment
            model = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            try:
                num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", str(num_predict)))
            except ValueError:
                pass
            
            print(f"🤖 Using model: {model}")
            print(f"🌐 Ollama URL: {base_url}")
            print(f"🎯 Tokens to generate: {num_predict}")
            
            # Call Ollama
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": num_predict,
                    "top_p": 0.9
                }
            }
            
            print("📡 Sending request to Ollama...")
            print(f"💬 System prompt length: {len(self.system_prompt)} characters")
            print(f"❓ User prompt length: {len(user_prompt)} characters")
            
            # Configurable timeouts
            connect_timeout = float(os.getenv("OLLAMA_CONNECT_TIMEOUT", "10"))
            read_timeout = float(os.getenv("OLLAMA_READ_TIMEOUT", "600"))
            print(f"⏱️  Timeouts: connect={connect_timeout}s, read={read_timeout}s")
            
            print("🔄 Waiting for LLM response...")
            response = requests.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=(connect_timeout, read_timeout),
            )
            response.raise_for_status()
            print("✅ Received LLM response!")
            
            content = response.json().get("message", {}).get("content", "")
            print(f"📊 LLM response length: {len(content)} characters")
            
            # Show a preview of the response
            preview = content[:200].replace('\n', ' ')
            print(f"👀 Response preview: {preview}...")
            
            print("🔍 Extracting OpenSCAD code...")
            # Extract OpenSCAD code from response
            code = self._extract_openscad_code(content)
            
            if code:
                print(f"✅ Found OpenSCAD code! ({len(code)} characters)")
                print("🧹 Validating and cleaning code...")
                return self._validate_and_clean_code(code)
            else:
                print("❌ No valid OpenSCAD code found in LLM response")
                print("📄 Full response:")
                print(content)
                return ""
                
        except Exception as e:
            print(f"Ollama generation failed: {e}")
            import traceback
            traceback.print_exc()
            return ""
    
    def _extract_openscad_code(self, content: str) -> str:
        """Extract OpenSCAD code from LLM response"""
        print("🔍 Extracting OpenSCAD code from LLM response...")
        
        # Look for code blocks first
        print("   🔎 Looking for code blocks (```...```)...")
        code_block_match = re.search(r'```(?:openscad|scad)?\s*\n(.*?)\n```', content, re.DOTALL | re.IGNORECASE)
        if code_block_match:
            print("   ✅ Found code block!")
            return code_block_match.group(1).strip()
        
        # Look for code between specific markers
        print("   🔎 Looking for specific markers...")
        markers = [
            (r'// .*:', r'(?:\n\n|\Z)'),
            (r'// Generated.*:', r'(?:\n\n|\Z)'),
            (r'^(?=union|translate|cube|difference|//)', r'\Z')  # Code starting with typical patterns
        ]
        
        for i, (start_marker, end_marker) in enumerate(markers):
            print(f"      Trying marker {i+1}: {start_marker[:20]}...")
            pattern = f'{start_marker}(.*?){end_marker}'
            match = re.search(pattern, content, re.DOTALL | re.MULTILINE)
            if match:
                print(f"   ✅ Found code with marker {i+1}!")
                return match.group(1).strip()
        
        # If no specific markers, try to extract anything that looks like OpenSCAD
        print("   🔎 Trying line-by-line extraction...")
        lines = content.split('\n')
        code_lines = []
        in_code = False
        
        for line_num, line in enumerate(lines):
            stripped = line.strip()
            # Start collecting if we see OpenSCAD-like syntax
            if (stripped.startswith(('union', 'translate', 'cube', 'difference', '//', 'cylinder', 'sphere')) or
                any(openscad_func in stripped for openscad_func in ['cube(', 'translate(', 'cylinder(', 'sphere(', 'union(', 'difference('])):
                if not in_code:
                    print(f"      📍 Code start detected at line {line_num+1}: {stripped[:30]}...")
                in_code = True
            
            if in_code:
                code_lines.append(line)
                
            # Stop if we hit explanatory text after code
            if in_code and stripped and not any(char in stripped for char in '(){};[]'):
                if len(stripped.split()) > 5:  # Likely explanatory text
                    print(f"      🛑 Code end detected at line {line_num+1}: {stripped[:30]}...")
                    break
        
        if code_lines:
            print(f"   ✅ Extracted {len(code_lines)} lines of code!")
            return '\n'.join(code_lines).strip()
        
        # Last resort: return the whole content if it seems to be mostly code
        print("   🔎 Checking if entire response is code...")
        if self._looks_like_openscad_code(content):
            print("   ✅ Entire response appears to be OpenSCAD code!")
            return content.strip()
        
        print("   ❌ No OpenSCAD code found in response")
        return ""
    
    def _looks_like_openscad_code(self, text: str) -> bool:
        """Check if text looks like OpenSCAD code - can be overridden by subclasses"""
        openscad_indicators = ['cube(', 'translate(', 'union(', 'difference(', 'cylinder(', 'sphere(']
        return any(indicator in text for indicator in openscad_indicators)
    
    @abstractmethod
    def _validate_and_clean_code(self, code: str) -> str:
        """Validate and clean the generated OpenSCAD code - must be implemented by subclasses"""
        pass
    
    def _basic_code_cleanup(self, code: str) -> str:
        """Basic code cleanup that all generators can use"""
        lines = code.split('\n')
        cleaned_lines = []
        skipped_lines = 0
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines at the start
            if not cleaned_lines and not stripped:
                continue
                
            # Skip obvious non-code lines
            if stripped.startswith(('Here', 'This', 'The', 'Note:', 'Remember:')):
                print(f"⚠️  Skipping explanatory text: {stripped[:50]}...")
                skipped_lines += 1
                continue
            
            # Fix invalid variable declarations (remove 'var' but keep the assignment)
            if stripped.startswith('var ') and ' = ' in stripped:
                # Convert 'var seatWidth = 100;' to 'seatWidth = 100;'
                fixed_line = stripped.replace('var ', '')
                print(f"🔧 Fixed variable declaration: {stripped[:50]}... -> {fixed_line[:50]}...")
                cleaned_lines.append(fixed_line)
                continue
            
            # Skip obvious non-code lines
            if stripped.startswith(('Here', 'This', 'The', 'Note:', 'Remember:')):
                print(f"⚠️  Skipping explanatory text: {stripped[:50]}...")
                skipped_lines += 1
                continue
                
            cleaned_lines.append(line)
        
        print(f"📊 Basic cleanup complete:")
        print(f"   • Original lines: {len(lines)}")
        print(f"   • Cleaned lines: {len(cleaned_lines)}")
        print(f"   • Skipped lines: {skipped_lines}")
        
        cleaned_code = '\n'.join(cleaned_lines).strip()
        
        # Ensure it ends properly
        if cleaned_code and not cleaned_code.rstrip().endswith((';', '}', ')')):
            print("🔧 Adding missing semicolon...")
            cleaned_code += ';'
        
        return cleaned_code
