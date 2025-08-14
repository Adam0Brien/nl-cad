"""
Parameter Extraction - Extract parameters from descriptions using Ollama + regex fallback
"""
import json
import re
import os
import requests
from typing import Dict, Optional


class ParameterExtractor:
    def __init__(self, system_prompt: str = "", user_prompt: str = ""):
        self.system_prompt = system_prompt
        self.user_prompt = user_prompt
    
    def extract_parameters(self, description: str, component: Dict, component_list: str) -> Dict:
        """Extract parameters using Ollama first, then regex fallback"""
        # Try Ollama first
        ollama_params = self._try_ollama_extraction(description, component, component_list)
        if ollama_params:
            print(f"✅ Ollama extracted: {ollama_params}")
            return ollama_params
        
        # Simple regex fallback
        print("⚠️  Falling back to regex extraction")
        return self._simple_regex_extraction(description.lower(), component)
    
    def _try_ollama_extraction(self, description: str, component: Dict, component_list: str) -> Dict:
        """Try to extract parameters using Ollama"""
        try:
            # Format prompt
            user_prompt = self.user_prompt.replace("{description}", description)
            
            # Ollama configuration
            model = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            num_predict = int(os.getenv("OLLAMA_NUM_PREDICT", "500"))
            
            # API call
            payload = {
                "model": model,
                "format": "json",  # Keep JSON for now, but could remove for more flexibility
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3,      # Add some creativity for parameter inference
                    "num_predict": num_predict,
                    "top_p": 0.9,           # Allow more diverse responses
                    "repeat_penalty": 1.1    # Reduce repetitive outputs
                }
            }
            
            connect_timeout = float(os.getenv("OLLAMA_CONNECT_TIMEOUT", "10"))
            read_timeout = float(os.getenv("OLLAMA_READ_TIMEOUT", "180"))
            
            response = requests.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=(connect_timeout, read_timeout)
            )
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "")
            print(f"Ollama response content: {content}")
            
            # Parse JSON response
            cleaned_content = self._clean_json(content)
            print(f"Cleaned content: {cleaned_content}")
            
            params = json.loads(cleaned_content)
            params = self._normalize_params(params)
            
            if self._validate_basic_params(component, params):
                return params
            else:
                print(f"Unexpected JSON format: {params}")
                return {}
                
        except Exception as e:
            print(f"Ollama extraction failed: {e}")
            return {}
    
    def _simple_regex_extraction(self, text: str, component: Dict) -> Dict:
        """Simple regex extraction for common patterns"""
        params = {}
        numbers = re.findall(r'(\d+(?:\.\d+)?)', text)
        
        for param in component.get('params', []):
            param_name = param['name']
            
            # Extract M6, M8, etc. for metric components
            if param_name == 'size' and 'm' in text:
                m_match = re.search(r'm(\d+)', text)
                if m_match:
                    params[param_name] = int(m_match.group(1))
            
            # Extract "x 25" format for length
            elif param_name == 'l' and 'x' in text:
                x_match = re.search(r'x\s*(\d+)', text)
                if x_match:
                    params[param_name] = float(x_match.group(1))
            
            # Use first available number for other params
            elif numbers and param.get('required', False):
                params[param_name] = float(numbers.pop(0))
        
        return params
    
    def _clean_json(self, content: str) -> str:
        """Clean JSON content"""
        content = re.sub(r'\([^)]*\)', '', content)  # Remove comments
        content = re.sub(r',(\s*[}\]])', r'\1', content)  # Remove trailing commas
        
        start = content.find('{')
        end = content.rfind('}') + 1
        return content[start:end] if start != -1 and end > start else content
    
    def _normalize_params(self, params: Dict) -> Dict:
        """Normalize parameter names"""
        if 'diameter' in params and 'd' not in params:
            params['d'] = params.pop('diameter')
        return params
    
    def _validate_basic_params(self, component: Dict, params: Dict) -> bool:
        """Basic validation of parameters"""
        for param in component.get('params', []):
            if param.get('required', False) and param['name'] not in params:
                print(f"AI missing required param: {param['name']}")
                return False
        return True
