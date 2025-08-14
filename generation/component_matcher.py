"""
Component Matching - Find which component matches a description
"""
import json
from typing import Optional, Dict


class ComponentMatcher:
    def __init__(self, catalog_path: str):
        with open(catalog_path, 'r') as f:
            catalog = json.load(f)
        # Convert list to dict for easier lookup
        self.components = {comp['id']: comp for comp in catalog['components']}
    
    def find_component(self, description: str) -> Optional[Dict]:
        """Find which component matches the description"""
        description_lower = description.lower()
        
        # Special case: threading keywords bias toward threaded rod
        threading_keywords = ["threaded", "thread", "lead screw", "leadscrew", "acme", "trapezoidal"]
        if any(k in description_lower for k in threading_keywords):
            if any(k in description_lower for k in ["rod", "screw", "acme"]):
                if "trapezoidal_threaded_rod" in self.components:
                    return self.components["trapezoidal_threaded_rod"]
        
        # Score components by keyword matches
        best_match = None
        best_score = 0
        
        for comp_id, comp in self.components.items():
            score = sum(1 for keyword in comp.get('intent_keywords', [])
                       if keyword.lower() in description_lower)
            
            if score > best_score:
                best_score = score
                best_match = comp
        
        return best_match
