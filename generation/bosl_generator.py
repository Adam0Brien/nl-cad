"""
Simple BOSL Generator - Clean orchestrator using modular components
"""
import json
from pathlib import Path
from typing import Dict

from .component_matcher import ComponentMatcher
from .parameter_extractor import ParameterExtractor
from .code_generator import CodeGenerator
from .validators import Validators


class BOSLGenerator:
    def __init__(self, catalog_path: str = "data/bosl_catalog.json", 
                 system_prompt_path: str = "config/system_prompt.txt",
                 user_prompt_path: str = "config/user_prompt.txt"):
        """Initialize with the component catalog and prompt files"""
        self.components = self._load_catalog(catalog_path)
        system_prompt = self._load_prompt(system_prompt_path)
        user_prompt = self._load_prompt(user_prompt_path)
        
        # Initialize modules
        self.matcher = ComponentMatcher(self.components)
        self.extractor = ParameterExtractor(system_prompt, user_prompt)
        self.generator = CodeGenerator()
        self.validator = Validators()
    
    def generate(self, description: str) -> str:
        """Main function: turn description into OpenSCAD code"""
        # Step 1: Find component
        component_id = self.matcher.find_component(description)
        if not component_id:
            return "// Error: Could not identify component"
        
        component = self.components[component_id]
        
        # Step 2: Extract parameters
        component_list = ", ".join(self.components.keys())
        params = self.extractor.extract_parameters(description, component, component_list)
        
        # Step 3: Validate required params
        missing = self.validator.get_missing_required_params(component, params)
        if missing:
            return self.validator.generate_error_message(component, missing)
        
        # Step 4: Generate code
        return self.generator.generate_code(component, params)
    
    def _load_catalog(self, catalog_path: str) -> Dict:
        """Load the component definitions from JSON file"""
        try:
            with open(catalog_path, 'r') as f:
                data = json.load(f)
                return {comp['id']: comp for comp in data.get('components', [])}
        except FileNotFoundError:
            print(f"Warning: Catalog file {catalog_path} not found")
            return {}
    
    def _load_prompt(self, prompt_path: str) -> str:
        """Load a prompt file"""
        try:
            with open(prompt_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Prompt file {prompt_path} not found")
            return ""