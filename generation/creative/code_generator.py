"""
Code Generation - Generate final OpenSCAD code from components and parameters
"""
from typing import Dict


class CodeGenerator:
    @staticmethod
    def generate_code(component: Dict, params: Dict) -> str:
        """Generate the final OpenSCAD code"""
        lines = []
        
        # Add include statements
        for include in component.get('includes', []):
            lines.append(f"include <{include}>")
        
        # Build parameter string
        param_parts = []
        for param in component.get('params', []):
            param_name = param['name']
            if param_name in params:
                value = params[param_name]
                if isinstance(value, list):
                    # Format arrays
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

