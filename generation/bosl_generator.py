"""
Simple BOSL Generator - Easy to understand and modify
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class BOSLGenerator:
    def __init__(self, catalog_path: str = "data/bosl_catalog.json", 
                 system_prompt_path: str = "config/system_prompt.txt",
                 user_prompt_path: str = "config/user_prompt.txt"):
        """Initialize with the component catalog and prompt files"""
        self.catalog_path = catalog_path
        self.system_prompt_path = system_prompt_path
        self.user_prompt_path = user_prompt_path
        self.components = self._load_catalog()
        self.system_prompt = self._load_prompt(system_prompt_path)
        self.user_prompt = self._load_prompt(user_prompt_path)
    
    def _load_prompt(self, prompt_path: str) -> str:
        """Load a prompt file"""
        try:
            with open(prompt_path, 'r') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Prompt file {prompt_path} not found")
            return ""
    
    def _load_catalog(self) -> Dict:
        """Load the component definitions from JSON file"""
        try:
            with open(self.catalog_path, 'r') as f:
                data = json.load(f)
                return {comp['id']: comp for comp in data.get('components', [])}
        except FileNotFoundError:
            print(f"Warning: Catalog file {self.catalog_path} not found")
            return {}
    
    def generate(self, description: str) -> str:
        """Main function: turn description into OpenSCAD code"""
        # Step 1: Figure out what component they want
        component_id = self._find_component(description)
        if not component_id:
            return "// Error: Could not identify component"
        
        component = self.components[component_id]
        
        # Step 2: Extract parameters from the description
        params = self._extract_parameters(description, component)
        
        # Step 3: Generate the OpenSCAD code
        return self._generate_code(component, params)
    
    def _find_component(self, description: str) -> Optional[str]:
        """Find which component matches the description"""
        description_lower = description.lower()
        
        # Score each component based on keyword matches
        best_match = None
        best_score = 0
        
        for comp_id, comp in self.components.items():
            score = 0
            for keyword in comp.get('intent_keywords', []):
                if keyword.lower() in description_lower:
                    score += 1
            
            if score > best_score:
                best_score = score
                best_match = comp_id
        
        return best_match
    
    def _extract_parameters(self, description: str, component: Dict) -> Dict:
        """Extract parameter values from the description"""
        # Try Ollama first with prompt files
        ollama_params = self._extract_params_with_ollama(description, component)
        if ollama_params:
            print(f"Ollama extracted: {ollama_params}")
            return ollama_params
        
        # Fall back to regex-based extraction
        print("Falling back to regex extraction")
        description_lower = description.lower()
        params = {}
        
        # First, find all required parameters
        required_params = self._find_required_params(description_lower, component)
        params.update(required_params)
        
        # Then, find optional parameters
        optional_params = self._find_optional_params(description_lower, component)
        params.update(optional_params)
        
        return params
    
    def _find_required_params(self, text: str, component: Dict) -> Dict:
        """Find all required parameters"""
        params = {}
        
        for param in component.get('params', []):
            if not param.get('required', False):
                continue
                
            param_name = param['name']
            param_type = param.get('type', 'float')
            
            if param_type in ('float', 'int'):
                value = self._find_number_with_unit(text, param)
                if value is not None:
                    params[param_name] = int(value) if param_type == 'int' else value
            
            elif param_type == 'bool':
                if 'fine' in text:
                    params[param_name] = False
                elif any(word in text for word in ['coarse', 'course']):
                    params[param_name] = True
                else:
                    params[param_name] = param.get('default', True)
            
            elif param_type == 'float[]':
                values = self._find_dimensions(text)
                if values:
                    params[param_name] = values
        
        return params
    
    def _find_optional_params(self, text: str, component: Dict) -> Dict:
        """Find all optional parameters"""
        params = {}
        
        for param in component.get('params', []):
            if param.get('required', False):
                continue
                
            param_name = param['name']
            param_type = param.get('type', 'float')
            
            if param_type == 'float':
                value = self._find_optional_param(text, param_name)
                if value is not None:
                    params[param_name] = value
        
        return params
    
    def _extract_params_with_ollama(self, description: str, component: Dict) -> Dict:
        """Use Ollama with prompt files to extract parameters"""
        try:
            import requests
            
            # Format the user prompt with component info
            component_list = ", ".join([comp['id'] for comp in self.components.values()])
            user_prompt = self.user_prompt.replace("{description}", description).replace("{component_list}", component_list)
            
            # Call Ollama
            payload = {
                "model": "mistral:7b-instruct",  # Better instruction following model
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.0}
            }
            
            print(f"System prompt: {self.system_prompt}")
            print(f"User prompt: {user_prompt}")
            print(f"Payload: {payload}")
            
            response = requests.post("http://localhost:11434/api/chat", json=payload, timeout=10)
            response.raise_for_status()
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {response.headers}")
            print(f"Full response: {response.text}")
            
            content = response.json().get("message", {}).get("content", "")
            print(f"Ollama response content: {content}")
            
            # Extract JSON from response
            import json
            import re
            
            # First, try to clean the content by removing comments and fixing common issues
            cleaned_content = self._clean_json_content(content)
            print(f"Cleaned content: {cleaned_content}")
            
            # Try direct parsing of cleaned content
            try:
                params = json.loads(cleaned_content.strip())
                if 'component_id' in params:
                    return params
            except json.JSONDecodeError:
                pass
            
            # Fallback: search for JSON in the response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    raw_json = json_match.group(0)
                    # Clean the raw JSON as well
                    cleaned_raw_json = self._clean_json_content(raw_json)
                    params = json.loads(cleaned_raw_json)
                    
                    # Handle different response formats
                    if 'component_id' in params:
                        # Standard format: {"component_id": "cuboid", "size": [25,25,25]}
                        return params
                    elif any(comp in params for comp in ['cuboid', 'metric_bolt', 'metric_nut', 'washer', 'cyl']):
                        # Nested format: {"cuboid": {"size": [25,25,25]}}
                        # Convert to standard format
                        component_name = list(params.keys())[0]
                        component_params = params[component_name]
                        component_params['component_id'] = component_name
                        return component_params
                    else:
                        print(f"Unexpected JSON format: {params}")
                        return {}
                        
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    print(f"Matched text: {raw_json}")
            else:
                print("No JSON found in response")
                
        except Exception as e:
            print(f"Ollama extraction failed: {e}")
            import traceback
            traceback.print_exc()
        
        return {}
    
    def _clean_json_content(self, content: str) -> str:
        """Clean JSON content by removing comments and fixing common issues"""
        # Remove inline comments like (assuming king size bed is 152.4mm wide)
        content = re.sub(r'\([^)]*\)', '', content)
        
        # Remove trailing commas before closing braces/brackets
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Remove any text after the last }
        last_brace = content.rfind('}')
        if last_brace != -1:
            content = content[:last_brace + 1]
        
        # Remove any text before the first {
        first_brace = content.find('{')
        if first_brace != -1:
            content = content[first_brace:]
        
        return content.strip()
    
    def _find_number_with_unit(self, text: str, param: Dict) -> Optional[float]:
        """Find a number with its unit and convert to mm"""
        # Get synonyms for this parameter
        synonyms = param.get('synonyms', [param['name']])
        
        for synonym in synonyms:
            # Pattern: "synonym 10mm" or "synonym 10 mm"
            pattern = rf"{re.escape(synonym)}\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")"
            match = re.search(pattern, text)
            if match:
                number = float(match.group(1))
                unit = match.group(2)
                return self._convert_to_mm(number, unit)
            
            # Pattern: "M6" for metric bolts
            if synonym == 'size':
                m_match = re.search(r"\bm\s*(\d{1,3})\b", text)
                if m_match:
                    return float(m_match.group(1))
            
            # Pattern: "x 25" for length
            if synonym == 'l':
                x_match = re.search(r"\bx\s*(\d+(?:\.\d+)?)\b", text)
                if x_match:
                    return float(x_match.group(1))
        
        # Look for any number with unit as fallback
        match = re.search(r"(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")", text)
        if match:
            number = float(match.group(1))
            unit = match.group(2)
            return self._convert_to_mm(number, unit)
        
        return None
    
    def _find_dimensions(self, text: str) -> List[float]:
        """Find main dimensions (e.g., "20mm 30mm 40mm") - look for explicit size patterns"""

        
        # Look for explicit size patterns first
        size_patterns = [
            r"size\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")",  # "size 20mm"
            r"(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")\s+(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")\s+(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")",  # "20mm 30mm 40mm"
            r"(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")\s+x\s+(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")\s+x\s+(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")",  # "20mm x 30mm x 40mm"
        ]
        
        for i, pattern in enumerate(size_patterns):
            match = re.search(pattern, text)
            if match:

                if len(match.groups()) == 2:  # Single size
                    value = self._convert_to_mm(float(match.group(1)), match.group(2))
                    return [value, value, value]
                elif len(match.groups()) == 6:  # Three dimensions
                    values = []
                    for i in range(0, 6, 2):
                        value = self._convert_to_mm(float(match.group(i+1)), match.group(i+2))
                        values.append(value)
                    return values
        
        # Look for explicit dimension patterns first
        # Pattern: "25mm" (single dimension for cube)
        single_match = re.search(r"(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")(?!\s+with)", text)
        if single_match:
            number = float(single_match.group(1))
            unit = single_match.group(2)
            
            # Special case: if we got 'm' but the text clearly has 'mm', fix it
            if unit == 'm' and 'mm' in text:
                unit = 'mm'
            
            value = self._convert_to_mm(number, unit)
            return [value, value, value]
        
        # Pattern: "20mm 30mm 40mm" (three dimensions)
        all_matches = re.findall(r"(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")", text)
        if len(all_matches) >= 3:
            # Take first 3 dimensions
            return [self._convert_to_mm(float(m[0]), m[1]) for m in all_matches[:3]]
        
        return [10.0, 10.0, 10.0]  # Default cube
    
    def _find_optional_param(self, text: str, param_name: str) -> Optional[float]:
        """Find optional parameter values in the text (like fillet, chamfer)"""
        # Look for "param_name number unit" pattern
        pattern = rf"{param_name}\s*(\d+(?:\.\d+)?)\s*(mm|cm|m|in|inch|inches|\")"
        match = re.search(pattern, text)
        
        if match:
            value = self._convert_to_mm(float(match.group(1)), match.group(2))
            return value
        
        return None
    
    def _convert_to_mm(self, value: float, unit: str) -> float:
        """Convert any unit to millimeters"""
        unit = unit.lower()
        if unit in ['mm']:
            return value
        elif unit in ['cm']:
            return value * 10
        elif unit in ['m']:
            return value * 1000
        elif unit in ['in', 'inch', 'inches', '"']:
            return value * 25.4
        else:
            # If we get 'm' but the original text had 'mm', this is likely a regex bug
            # Check if the original text around this value had 'mm'
            print(f"WARNING: Unknown unit '{unit}', treating as mm")
            return value
    
    def _generate_code(self, component: Dict, params: Dict) -> str:
        """Generate the final OpenSCAD code"""
        lines = []
        
        # Add include/use statements
        for include in component.get('includes', []):
            if 'constants.scad' in include:
                lines.append(f"include <{include}>")
            else:
                lines.append(f"use <{include}>")
        
        # Build parameter string
        param_parts = []
        for param in component.get('params', []):
            param_name = param['name']
            if param_name in params:
                value = params[param_name]
                if isinstance(value, list):
                    # Format arrays nicely
                    formatted_values = [f"{v:.1f}" for v in value]
                    param_parts.append(f"{param_name}=[{', '.join(formatted_values)}]")
                elif isinstance(value, float):
                    param_parts.append(f"{param_name}={value:.1f}")
                else:
                    param_parts.append(f"{param_name}={value}")
        
        # Add the component call
        module_name = component['module']
        if param_parts:
            lines.append(f"{module_name}({', '.join(param_parts)});")
        else:
            lines.append(f"{module_name}();")
        
        return "\n".join(lines)


# Simple usage example
if __name__ == "__main__":
    generator = BOSLGenerator()
    
    # Test cases
    test_cases = [
        "M8 x 25 bolt",
        "cuboid 20mm 30mm 40mm",
        "3/8 inch washer"
    ]
    
    for test in test_cases:
        print(f"\nInput: {test}")
        print("Output:")
        print(generator.generate(test))
        print("-" * 40)
