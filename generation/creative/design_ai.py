"""
Design AI - Analyzes objects and generates spatial reasoning rules for OpenSCAD generation
"""
import os
import requests


class DesignAI:
    """
    Analyzes 3D objects and generates specific spatial rules for proper OpenSCAD code generation
    """
    
    def __init__(self, system_prompt_path="config/creative/design/system_prompt.txt", 
                 user_prompt_path="config/creative/design/user_prompt.txt"):
        """Initialize Design AI with prompts for spatial analysis"""
        self.system_prompt = self._load_prompt(system_prompt_path)
        self.user_prompt_template = self._load_prompt(user_prompt_path)
    
    def _load_prompt(self, prompt_path):
        """Load prompt from file with fallback"""
        try:
            with open(prompt_path, 'r') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: {prompt_path} not found, using fallback")
            if "system" in prompt_path:
                return "Analyze 3D objects and generate spatial rules for OpenSCAD generation."
            else:
                return "Generate spatial rules for: {description}"
    
    def analyze_object(self, description):
        """
        Analyze an object description and generate spatial rules
        
        Args:
            description (str): User's description of the object to create
            
        Returns:
            str: Generated spatial rules and constraints for the object
        """
        user_prompt = self.user_prompt_template.format(description=description)
        
        # Call LLM for design analysis
        spatial_rules = self._call_llm_for_analysis(user_prompt)
        
        return spatial_rules
    
    def _call_llm_for_analysis(self, user_prompt):
        """
        Call LLM for design analysis and spatial rule generation
        """
        model = os.getenv("DESIGN_MODEL", "llama3.2:3b")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.3,      # Lower temperature for consistent analysis
                "num_predict": 800,      # Longer for detailed spatial analysis
                "top_p": 0.8
            }
        }
        
        try:
            response = requests.post(f"{base_url}/api/chat", json=payload, timeout=30)
            response.raise_for_status()
            return response.json()['message']['content'].strip()
        except Exception as e:
            # Smart fallback based on object type
            if "ladder" in user_prompt.lower():
                return """OBJECT ANALYSIS: Simple ladder with two rails and rungs.

COMPONENTS WITH EXACT POSITIONING:
- Rail 1: Center at X=-25, Y=0, Z=50 (dimensions: 5x5x100mm)
- Rail 2: Center at X=+25, Y=0, Z=50 (dimensions: 5x5x100mm)  
- Rung 1: Center at X=0, Y=0, Z=20 (dimensions: 50x5x5mm)
- Rung 2: Center at X=0, Y=0, Z=40 (dimensions: 50x5x5mm)
- Rung 3: Center at X=0, Y=0, Z=60 (dimensions: 50x5x5mm)
- Rung 4: Center at X=0, Y=0, Z=80 (dimensions: 50x5x5mm)

POSITIONING TEMPLATE FOR CODE AI:
// Rail 1: translate([-25, 0, 50]) cube([5, 5, 100], center=true);
// Rail 2: translate([25, 0, 50]) cube([5, 5, 100], center=true);
// Rung 1: translate([0, 0, 20]) cube([50, 5, 5], center=true);
// Rung 2: translate([0, 0, 40]) cube([50, 5, 5], center=true);
// Rung 3: translate([0, 0, 60]) cube([50, 5, 5], center=true);
// Rung 4: translate([0, 0, 80]) cube([50, 5, 5], center=true);"""
            else:
                return f"""OBJECT ANALYSIS: Using basic fallback rules for unknown object.

COMPONENTS WITH EXACT POSITIONING:
- Main part: Center at X=0, Y=0, Z=25 (dimensions: 50x50x50mm)

POSITIONING TEMPLATE FOR CODE AI:
// Main part: translate([0, 0, 25]) cube([50, 50, 50], center=true);

ERROR: {e}"""


# For backward compatibility
__all__ = ['DesignAI']