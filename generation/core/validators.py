"""
Validators - Parameter validation and error generation
"""
from typing import Dict, List


class Validators:
    @staticmethod
    def get_missing_required_params(component: Dict, params: Dict) -> List[str]:
        """Return list of missing required parameters"""
        return [p['name'] for p in component.get('params', []) 
                if p.get('required', False) and p['name'] not in params]
    
    @staticmethod
    def generate_error_message(component: Dict, missing: List[str]) -> str:
        """Generate simple error message for missing parameters"""
        comp_id = component['id']
        missing_str = ', '.join(missing)
        return f"// Error: {comp_id} missing required parameters: {missing_str}\n// Example: {comp_id} with proper values"

