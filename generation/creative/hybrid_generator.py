"""
Hybrid CAD Generation System

Combines catalog-based generation with AI fallbacks:
1. Try fast catalog approach first
2. AI parameter completion for missing parameters  
3. Creative AI generation for novel requests
"""

import json
import requests
import os
from .code_generator import CodeGenerator
from ..catalog.component_matcher import ComponentMatcher  
from ..core.parameter_extractor import ParameterExtractor
from .design_ai import DesignAI


class ComponentNotFound(Exception):
    """Raised when no catalog component matches user intent"""
    pass


class ParameterMissing(Exception):
    """Raised when required parameters are missing"""
    def __init__(self, message, missing_params=None):
        super().__init__(message)
        self.missing_params = missing_params or []


class HybridCADGenerator:
    """
    Intelligent CAD generation with multiple fallback strategies
    """
    
    def __init__(self, catalog_path="data/bosl_catalog.json"):
        # Initialize existing modular components
        self.matcher = ComponentMatcher(catalog_path)
        
        # Load specialized prompts for different strategies
        self._load_prompts()
        
        self.code_gen = CodeGenerator()
    
    def _load_prompts(self):
        """Load specialized prompts for catalog vs creative generation"""
        # Catalog-based prompts (parameter extraction)
        try:
            with open("config/catalog/bosl/system_prompt.txt", 'r') as f:
                self.catalog_system_prompt = f.read()
        except FileNotFoundError:
            self.catalog_system_prompt = "Extract OpenSCAD component parameters from user descriptions."
            
        try:
            with open("config/catalog/bosl/user_prompt.txt", 'r') as f:
                self.catalog_user_prompt = f.read()
        except FileNotFoundError:
            self.catalog_user_prompt = "Extract parameters for: {description}"
            
        # Creative AI prompts (custom OpenSCAD generation)
        try:
            with open("config/creative/code/system_prompt.txt", 'r') as f:
                self.creative_system_prompt = f.read()
        except FileNotFoundError:
            self.creative_system_prompt = "Generate OpenSCAD code using only cube() and translate()."
            
        try:
            with open("config/creative/code/user_prompt.txt", 'r') as f:
                self.creative_user_prompt = f.read()
        except FileNotFoundError:
            self.creative_user_prompt = "Generate OpenSCAD code for: {description}"
        
        # Initialize extractor with catalog prompts
        self.extractor = ParameterExtractor(self.catalog_system_prompt, self.catalog_user_prompt)
        
    def generate(self, user_request):
        """
        Main generation method with comprehensive fallback chain
        """
        print(f"🔀 Hybrid generation for: '{user_request}'")
        
        # STRATEGY 1: Try BOSL catalog first (fastest for mechanical parts)
        try:
            print("🔧 Trying BOSL catalog generation...")
            return self._catalog_based_generation(user_request)
        except ComponentNotFound:
            print("⚡ No catalog match - falling back to AI creative generation...")
            # STRATEGY 3: Creative AI generation
            return self._ai_generate_scad(user_request)
            
        except ParameterMissing as e:
            print(f"🧠 Missing parameters: {e.missing_params} - using AI completion...")
            # STRATEGY 2: AI parameter completion
            return self._ai_complete_parameters(user_request, e.missing_params)
    
    def _catalog_based_generation(self, user_request):
        """
        Current catalog-based approach with better error handling
        """
        # Find component match
        component_id = self.matcher.find_component(user_request)
        if not component_id:
            raise ComponentNotFound(f"No component found for: {user_request}")
        
        # Get the component object from the catalog
        component = self.matcher.components[component_id]
        
        # Extract parameters  
        parameters = self.extractor.extract_parameters(user_request, component, "")
        
        # Validate required parameters
        missing = self._find_missing_required_params(component, parameters)
        if missing:
            raise ParameterMissing(f"Missing required parameters: {missing}", missing)
        
        # Generate code
        return self.code_gen.generate_code(component, parameters)
    
    def _ai_complete_parameters(self, user_request, missing_params):
        """
        Use AI to infer missing parameters for known components
        """
        # This would use the catalog system to infer missing parameters
        # For now, fall back to creative generation
        return self._ai_generate_scad(user_request)
    
    def _ai_generate_scad(self, user_request):
        """
        Use AI to generate custom OpenSCAD code for novel requests
        """
        # Format the user prompt with the description
        user_prompt = self.creative_user_prompt.replace("{description}", user_request)
        
        # Call the LLM for creative code generation
        return self._call_llm_for_code(user_prompt, self.creative_system_prompt)
    
    def _ai_infer_parameters(self, user_request, component, missing_params):
        """
        Use AI to infer missing parameters
        """
        prompt = f"""
The user wants: {user_request}

We identified this component: {component}

But we're missing these required parameters: {missing_params}

Please infer reasonable values for the missing parameters and return a complete JSON object.

Required format:
{{"component_id": "{component.get('id', '')}", "missing_param1": value, "missing_param2": value}}
"""
        
        response = self._call_llm_for_json(prompt)
        return response
    
    def _call_llm_for_code(self, user_prompt, system_prompt):
        """
        Call LLM for creative OpenSCAD code generation (no JSON constraint)
        """
        model = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        payload = {
            "model": model,
            # No JSON format constraint - allow creative generation
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,      # More creative for novel designs
                "num_predict": 500,      # Longer responses for complex code
                "top_p": 0.9
            }
        }
        
        try:
            response = requests.post(f"{base_url}/api/chat", json=payload, timeout=180)
            response.raise_for_status()
            return response.json()['message']['content'].strip()
        except Exception as e:
            return f"// Error generating custom code: {e}\n// Fallback to basic shape\ncube([50,50,50]);"
    
    def _call_llm_for_json(self, prompt):
        """
        Call LLM for parameter completion (with JSON constraint)
        """
        model = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        payload = {
            "model": model,
            "format": "json",  # Constrain to JSON for parameter extraction
            "messages": [
                {"role": "system", "content": self.catalog_system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {
                "temperature": 0.5,      # Balanced creativity
                "num_predict": 200
            }
        }
        
        try:
            response = requests.post(f"{base_url}/api/chat", json=payload, timeout=180)
            response.raise_for_status()
            return json.loads(response.json()['message']['content'])
        except Exception as e:
            print(f"Parameter completion failed: {e}")
            return {}
    
    def _find_missing_required_params(self, component, parameters):
        """
        Find which required parameters are missing
        """
        required = component.get('required_params', [])
        provided = list(parameters.keys())
        missing = [param for param in required if param not in provided]
        return missing
    
    def _should_use_cube_generator(self, user_request):
        """
        Smart detection for furniture and objects that should use cube generator
        """
        furniture_keywords = [
            'table', 'chair', 'bench', 'desk', 'shelf', 'cabinet', 'drawer',
            'sofa', 'couch', 'bed', 'nightstand', 'dresser', 'wardrobe',
            'bookcase', 'filing', 'storage', 'organizer', 'rack', 'stand',
            'coffee', 'dining', 'kitchen', 'bathroom', 'bedroom', 'living',
            'office', 'study', 'workshop', 'garage', 'patio', 'garden'
        ]
        
        object_keywords = [
            'house', 'building', 'tower', 'castle', 'bridge', 'car', 'truck',
            'robot', 'figure', 'sculpture', 'art', 'decoration', 'ornament',
            'toy', 'game', 'model', 'miniature', 'dollhouse', 'playset'
        ]
        
        user_lower = user_request.lower()
        
        # Check for furniture keywords
        for keyword in furniture_keywords:
            if keyword in user_lower:
                return True
        
        # Check for object keywords
        for keyword in object_keywords:
            if keyword in user_lower:
                return True
        
        return False
    
    def _should_use_maze_generator(self, user_request):
        """
        Smart detection for maze-like requests
        """
        maze_keywords = [
            'maze', 'labyrinth', 'puzzle', 'path', 'corridor', 'hallway',
            'tunnel', 'passage', 'route', 'circuit', 'trail', 'track'
        ]
        
        user_lower = user_request.lower()
        
        for keyword in maze_keywords:
            if keyword in user_lower:
                return True
        
        return False
    
    def _generate_with_cube_generator(self, user_request):
        """
        Generate voxel-style OpenSCAD code using cube generator approach
        """
        try:
            # Import cube generator dynamically to avoid circular imports
            from ..catalog.cube_generator import CubeGenerator
            cube_gen = CubeGenerator()
            return cube_gen.generate(user_request)
        except Exception as e:
            print(f"⚠️ Cube generator failed: {e} - falling back to AI generation")
            # Fall back to AI generation if cube generator fails
            return self._ai_generate_scad(user_request)
    
    def _generate_with_maze_generator(self, user_request):
        """
        Generate maze OpenSCAD code using maze generator approach
        """
        try:
            # Import maze generator dynamically to avoid circular imports
            from ..catalog.maze_generator import MazeGenerator
            maze_gen = MazeGenerator()
            return maze_gen.generate(user_request)
        except Exception as e:
            print(f"⚠️ Maze generator failed: {e}")
            raise e
    
    def _generate_with_enhanced_generator(self, user_request):
        """
        Generate OpenSCAD code using enhanced generator approach
        """
        try:
            # Import enhanced generator dynamically to avoid circular imports
            from .enhanced_generator import EnhancedGenerator
            enhanced_gen = EnhancedGenerator()
            return enhanced_gen.generate(user_request)
        except Exception as e:
            print(f"⚠️ Enhanced generator failed: {e}")
            raise e