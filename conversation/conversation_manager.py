"""
Conversation Manager
Handles interactive design conversations without code generation inheritance
"""
import json
import re
import os
import requests
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


class ConversationManager:
    """Manages interactive design conversations"""
    
    def __init__(self):
        self.conversation_history = []
        self.current_design_state = {}
        self.design_model = os.getenv("DESIGN_MODEL", "llama3.2:3b")
        self.code_model = os.getenv("CODE_MODEL", "codegemma:7b")
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        
        print("💬 Conversation manager initialized")
        print(f"   Design model: {self.design_model}")
        print(f"   Code model: {self.code_model}")
    
    def start_conversation(self, initial_request: str) -> Dict[str, Any]:
        """Start a new design conversation"""
        self.conversation_history = []
        self.current_design_state = {}
        
        # Analyze the initial request
        response = self._generate_initial_response(initial_request)
        
        conversation_state = {
            "stage": "questioning",  # questioning, designing, refining, complete
            "message": response.get("message", ""),
            "questions": response.get("questions", []),
            "current_code": response.get("code", ""),
            "design_progress": response.get("progress", 0),
            "conversation_id": len(self.conversation_history)
        }
        
        self.conversation_history.append({
            "type": "user_request",
            "content": initial_request,
            "timestamp": self._get_timestamp()
        })
        
        self.conversation_history.append({
            "type": "assistant_response", 
            "content": conversation_state,
            "timestamp": self._get_timestamp()
        })
        
        return {
            "stage": conversation_state["stage"],
            "message": conversation_state["message"],
            "questions": conversation_state["questions"],
            "code": conversation_state["current_code"],
            "progress": conversation_state["design_progress"]
        }
    
    def continue_conversation(self, user_response: str) -> Dict[str, Any]:
        """Continue the conversation with user response"""
        if not self.conversation_history:
            raise ValueError("No active conversation. Please start a conversation first.")
        
        # Add user response to history
        self.conversation_history.append({
            "type": "user_response",
            "content": user_response,
            "timestamp": self._get_timestamp()
        })
        
        # Get current stage
        last_state = self.conversation_history[-2]["content"]
        current_stage = last_state.get("stage", "questioning")
        
        # Process based on current stage
        if current_stage == "questioning":
            response = self._process_questioning_stage(user_response)
        elif current_stage == "designing":
            response = self._process_designing_stage(user_response)
        elif current_stage == "refining":
            response = self._process_refining_stage(user_response)
        else:
            response = self._process_complete_stage(user_response)
        
        # Add assistant response to history
        self.conversation_history.append({
            "type": "assistant_response",
            "content": response,
            "timestamp": self._get_timestamp()
        })
        
        return {
            "stage": response.get("stage"),
            "message": response.get("message"),
            "questions": response.get("questions", []),
            "code": response.get("current_code", ""),
            "progress": response.get("design_progress", 0)
        }
    
    def _generate_initial_response(self, request: str) -> Dict[str, Any]:
        """Generate initial response with questions"""
        prompt = f"""You are starting a NEW conversation with a user about a 3D design project. Forget any previous conversations.

CURRENT USER REQUEST: {request}

Your task is to understand what the user wants to create by asking clarifying questions for THIS specific project only.

Analyze ONLY this request and respond with:
1. A friendly message acknowledging their request
2. 2-3 specific questions to understand their design better
3. Estimated progress (start at 10%)

Focus on:
- Specific dimensions and sizes
- Style preferences  
- Functional requirements
- Materials or appearance

Respond in JSON format:
{{
    "message": "I'd love to help you create that! Let me ask a few questions to design exactly what you need.",
    "questions": ["Question 1?", "Question 2?", "Question 3?"],
    "progress": 10
}}"""
        
        try:
            response = self._call_ollama(prompt, self.design_model)
            return self._parse_json_response(response)
        except Exception as e:
            print(f"Error generating initial response: {e}")
            # Provide intelligent fallback based on the request
            return self._generate_fallback_initial_response(request)
    
    def _process_questioning_stage(self, user_response: str) -> Dict[str, Any]:
        """Process responses during questioning stage"""
        # Update design state with user answers
        self.current_design_state["user_answers"] = self.current_design_state.get("user_answers", [])
        self.current_design_state["user_answers"].append(user_response)
        
        # Decide if we have enough information
        answers_count = len(self.current_design_state.get("user_answers", []))
        
        if answers_count >= 2:  # Move to designing after a couple answers
            return self._move_to_designing_stage()
        else:
            return self._continue_questioning(user_response)
    
    def _continue_questioning(self, user_response: str) -> Dict[str, Any]:
        """Continue asking questions"""
        # Get only the current conversation context
        current_answers = self.current_design_state.get("user_answers", [])
        initial_request = self.conversation_history[0]["content"] if self.conversation_history else "design request"
        
        prompt = f"""You are a 3D design assistant helping with ONE specific project.

CURRENT PROJECT: {initial_request}

USER HAS PROVIDED THESE ANSWERS SO FAR:
{chr(10).join(f"- {answer}" for answer in current_answers[-3:])}  

LATEST USER RESPONSE: "{user_response}"

Based ONLY on this current project and responses, generate 1-2 follow-up questions to better understand their design needs.

Respond in JSON format:
{{
    "message": "Great information! A couple more questions:",
    "questions": ["Follow-up question 1?", "Follow-up question 2?"],
    "progress": 25
}}"""
        
        try:
            response = self._call_ollama(prompt, self.design_model)
            parsed = self._parse_json_response(response)
            parsed["stage"] = "questioning"
            return parsed
        except Exception as e:
            print(f"AI unavailable, using smart fallback: {e}")
            # Generate context-aware questions based on user response
            fallback = self._generate_fallback_questions(user_response)
            fallback["stage"] = "questioning"  # Explicitly ensure we stay in questioning
            return fallback
    
    def _move_to_designing_stage(self) -> Dict[str, Any]:
        """Move to designing stage and generate first code"""
        # Compile all user information
        initial_request = self.conversation_history[0]["content"]
        user_answers = self.current_design_state.get("user_answers", [])
        
        # Generate design description
        design_prompt = f"""Create a detailed design description for: {initial_request}

User provided these details:
{chr(10).join(f"- {answer}" for answer in user_answers)}

Create a comprehensive design specification including:
- Exact dimensions
- Detailed geometry description
- Component breakdown
- Style and appearance details

Write this as a detailed technical specification for OpenSCAD code generation."""
        
        try:
            design_response = self._call_ollama(design_prompt, self.design_model)
            self.current_design_state["design_specification"] = design_response
            
            # Generate initial code
            code = self._generate_code_from_design(design_response)
            
            return {
                "stage": "designing",
                "message": "Perfect! Based on your requirements, I've created an initial design. Here's the first version:",
                "current_code": code,
                "design_progress": 60,
                "questions": ["What do you think of this initial design? Any changes needed?"]
            }
        except Exception as e:
            print(f"AI unavailable for design stage, using fallback: {e}")
            # Create fallback design specification
            fallback_spec = self._create_fallback_design_spec(initial_request, user_answers)
            self.current_design_state["design_specification"] = fallback_spec
            
            # Generate code from fallback spec
            code = self._generate_code_from_design(fallback_spec)
            
            return {
                "stage": "designing",
                "message": "I've created an initial design based on your requirements. Here's what I came up with:",
                "current_code": code,
                "design_progress": 60,
                "questions": ["How does this look? What would you like to change?"]
            }
    
    def _process_designing_stage(self, user_response: str) -> Dict[str, Any]:
        """Process feedback during designing stage"""
        if "good" in user_response.lower() or "perfect" in user_response.lower() or "done" in user_response.lower():
            return self._move_to_complete_stage()
        else:
            return self._refine_design(user_response)
    
    def _refine_design(self, feedback: str) -> Dict[str, Any]:
        """Refine design based on feedback"""
        current_spec = self.current_design_state.get("design_specification", "")
        
        refine_prompt = f"""Current design specification:
{current_spec}

User feedback: {feedback}

Update the design specification to incorporate the user's feedback.
Focus on the specific changes they mentioned."""
        
        try:
            updated_spec = self._call_ollama(refine_prompt, self.design_model)
            self.current_design_state["design_specification"] = updated_spec
            
            # Generate updated code
            code = self._generate_code_from_design(updated_spec)
            
            return {
                "stage": "refining",
                "message": "I've updated the design based on your feedback:",
                "current_code": code,
                "design_progress": 80,
                "questions": ["How does this revised version look?"]
            }
        except Exception as e:
            return {
                "stage": "refining",
                "message": "I'm working on incorporating your feedback...",
                "current_code": self.current_design_state.get("current_code", ""),
                "design_progress": 75
            }
    
    def _process_refining_stage(self, user_response: str) -> Dict[str, Any]:
        """Process feedback during refining stage"""
        if "good" in user_response.lower() or "perfect" in user_response.lower() or "done" in user_response.lower():
            return self._move_to_complete_stage()
        else:
            return self._refine_design(user_response)
    
    def _move_to_complete_stage(self) -> Dict[str, Any]:
        """Move to completion stage"""
        return {
            "stage": "complete",
            "message": "🎉 Your design is complete! The OpenSCAD code is ready to use.",
            "current_code": self.current_design_state.get("current_code", ""),
            "design_progress": 100
        }
    
    def _process_complete_stage(self, user_response: str) -> Dict[str, Any]:
        """Handle responses when design is complete"""
        return {
            "stage": "complete",
            "message": "Your design is already complete! Would you like to start a new design?",
            "current_code": self.current_design_state.get("current_code", ""),
            "design_progress": 100
        }
    
    def _generate_code_from_design(self, design_specification: str) -> str:
        """Generate OpenSCAD code from design specification"""
        # Read the code generation prompt
        try:
            with open('/home/jorringe/nl-cad/config/code_system_prompt.txt', 'r') as f:
                code_system_prompt = f.read()
        except FileNotFoundError:
            code_system_prompt = "Generate clean OpenSCAD code with all variables defined."
        
        code_prompt = f"""{code_system_prompt}

Design Specification:
{design_specification}

Generate complete, functional OpenSCAD code that implements this design exactly.
CRITICAL: Define ALL variables at the top with actual numeric values.
"""
        
        try:
            code = self._call_ollama(code_prompt, self.code_model)
            cleaned_code = self._clean_generated_code(code)
            self.current_design_state["current_code"] = cleaned_code
            return cleaned_code
        except Exception as e:
            print(f"Error generating code: {e}")
            # Generate fallback code based on the design specification
            fallback_code = self._generate_fallback_code(design_specification)
            self.current_design_state["current_code"] = fallback_code
            return fallback_code
    
    def _clean_generated_code(self, code: str) -> str:
        """Clean and validate generated code"""
        # Remove markdown code blocks
        code = re.sub(r'```(?:openscad|scad)?\n?', '', code)
        code = re.sub(r'```\n?', '', code)
        
        # Fix common syntax errors
        code = re.sub(r'\.push\(', '// INVALID: .push(', code)  # Mark invalid JS syntax
        code = re.sub(r'\[\]', '// INVALID: empty array', code)  # Mark invalid arrays
        code = re.sub(r'for \(.*<.*\)', '// INVALID: JavaScript-style for loop', code)  # Mark JS loops
        
        # Clean up common issues
        lines = code.split('\n')
        cleaned_lines = []
        variable_names = set()
        
        # First pass: collect variable definitions
        for line in lines:
            line = line.strip()
            if '=' in line and not line.startswith('//'):
                # Extract variable name
                var_match = re.match(r'(\w+)\s*=', line)
                if var_match:
                    variable_names.add(var_match.group(1))
        
        # Second pass: validate and clean
        for line in lines:
            line = line.strip()
            
            # Skip lines marked as invalid
            if 'INVALID:' in line:
                continue
                
            # Skip incomplete assembly sections
            if line in ['// Base', '// Lid', '// Hinge', '// Carvings'] and not line.endswith(';'):
                continue
                
            # Check for undefined variables in non-comment lines
            if line and not line.startswith('//') and not '=' in line:
                words = re.findall(r'\b[a-zA-Z_]\w*\b', line)
                undefined_vars = [w for w in words if w not in variable_names and w not in [
                    'cube', 'cylinder', 'sphere', 'translate', 'rotate', 'scale', 'union', 'difference', 
                    'intersection', 'hull', 'minkowski', 'for', 'if', 'module', 'function', 'true', 'false'
                ]]
                if undefined_vars:
                    line = f"// SKIPPED - undefined variables: {', '.join(undefined_vars)}"
            
            cleaned_lines.append(line)
        
        cleaned_code = '\n'.join(cleaned_lines)
        
        # If the code looks too broken, use fallback
        if cleaned_code.count('INVALID:') > 2 or cleaned_code.count('SKIPPED') > 3:
            print("Generated code has too many errors, using fallback template")
            return self._generate_fallback_code("treasure chest with wooden appearance and Greek influences")
        
        return cleaned_code
    
    def _call_ollama(self, prompt: str, model: str, retries: int = 2) -> str:
        """Call Ollama API with retry logic"""
        last_error = None
        
        for attempt in range(retries + 1):
            try:
                # Increase timeout for larger models, add retry logic
                timeout = 1000
                
                if attempt > 0:
                    print(f"Retrying Ollama call (attempt {attempt + 1}/{retries + 1})...")
                
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "stop": ["```", "User:", "Human:"]
                        }
                    },
                    timeout=timeout
                )
                
                if response.status_code == 200:
                    result = response.json()["response"]
                    if result.strip():  # Make sure we got a non-empty response
                        return result
                    else:
                        raise Exception("Empty response from model")
                else:
                    raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.ReadTimeout:
                last_error = f"Model '{model}' timed out. This can happen with complex requests."
                print(f"Timeout on attempt {attempt + 1}: {last_error}")
                if attempt < retries:
                    print("Trying again with simpler prompt...")
                    # Simplify prompt for retry
                    if len(prompt) > 1000:
                        prompt = prompt[:800] + "\n\nPlease provide a concise response."
            except Exception as e:
                last_error = str(e)
                print(f"Error on attempt {attempt + 1}: {last_error}")
                if attempt < retries:
                    print("Retrying...")
        
        # If all retries failed, provide a fallback response based on the context
        print(f"All Ollama attempts failed: {last_error}")
        raise Exception(f"Failed to connect to AI model after {retries + 1} attempts: {last_error}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from model"""
        try:
            # Try to find JSON in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Fallback if no JSON found
                return {"message": response}
        except json.JSONDecodeError:
            return {"message": response}
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        return datetime.now().isoformat()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get full conversation history"""
        return self.conversation_history
    
    def get_current_code(self) -> str:
        """Get current generated code"""
        return self.current_design_state.get("current_code", "")
    
    def reset_conversation(self):
        """Reset conversation state to start fresh"""
        print("🔄 Resetting conversation state...")
        self.conversation_history = []
        self.current_design_state = {}
    
    def start_fresh_conversation(self, initial_request: str) -> Dict[str, Any]:
        """Start a completely fresh conversation with no history"""
        self.reset_conversation()
        return self.start_conversation(initial_request)
    
    def _generate_fallback_initial_response(self, request: str) -> Dict[str, Any]:
        """Generate intelligent fallback responses when AI is unavailable"""
        request_lower = request.lower()
        
        # Analyze the request and provide relevant questions
        if any(word in request_lower for word in ['chest', 'box', 'storage', 'container']):
            return {
                "message": f"I'd love to help you create a {request}! Since I'm having trouble connecting to the AI, let me ask some key questions:",
                "questions": [
                    "What dimensions do you need? (length x width x height in mm)",
                    "Do you want a hinged lid or removable top?",
                    "Any decorative elements like handles, patterns, or trim?"
                ],
                "progress": 10
            }
        elif any(word in request_lower for word in ['vase', 'cup', 'mug', 'bowl']):
            return {
                "message": f"I'd love to help you create a {request}! Let me ask some essential questions:",
                "questions": [
                    "What height and diameter do you want? (in mm)",
                    "What style: modern, classic, decorative, or functional?",
                    "Do you need any special features like handles or patterns?"
                ],
                "progress": 10
            }
        else:
            return {
                "message": f"I'd love to help you create {request}! Let me ask a few questions to understand your design better:",
                "questions": [
                    "What are the approximate dimensions you need?",
                    "What style are you looking for? (modern, classic, decorative, etc.)",
                    "Are there any specific functional requirements?"
                ],
                "progress": 10
            }
    
    def _generate_fallback_code(self, design_specification: str) -> str:
        """Generate basic fallback code when AI models are unavailable"""
        spec_lower = design_specification.lower()
        
        if any(word in spec_lower for word in ['chest', 'box', 'storage']):
            return """// Wooden treasure chest with Greek influences
// All dimensions in millimeters
chest_length = 200;
chest_width = 150;
chest_height = 100;
wall_thickness = 8;
lid_height = 30;
corner_radius = 5;
greek_column_width = 12;
greek_column_height = 80;

// Main chest body
difference() {
    // Outer shell with rounded corners
    translate([corner_radius, corner_radius, 0])
        minkowski() {
            cube([chest_length - 2*corner_radius, chest_width - 2*corner_radius, chest_height]);
            cylinder(r=corner_radius, h=0.1);
        }
    
    // Inner cavity
    translate([wall_thickness, wall_thickness, wall_thickness])
        cube([chest_length - 2*wall_thickness, chest_width - 2*wall_thickness, chest_height]);
}

// Greek-style decorative columns on corners
for (x = [0, chest_length - greek_column_width]) {
    for (y = [0, chest_width - greek_column_width]) {
        translate([x, y, 0])
            cube([greek_column_width, greek_column_width, greek_column_height]);
    }
}

// Lid (separate piece)
translate([0, chest_width + 20, 0]) {
    difference() {
        cube([chest_length, chest_width, lid_height]);
        
        // Decorative Greek pattern on lid
        for (i = [20:40:chest_length-40]) {
            translate([i, chest_width/2 - 5, lid_height - 3])
                cube([30, 10, 4]);
        }
    }
}"""
        
        elif any(word in spec_lower for word in ['vase', 'cup', 'mug', 'bowl']):
            return """// Decorative vase with Greek influences
// All dimensions in millimeters  
vase_height = 150;
base_diameter = 80;
top_diameter = 60;
wall_thickness = 3;
base_height = 20;
greek_band_height = 15;

// Main vase body with tapered profile
difference() {
    // Outer profile
    union() {
        // Base
        cylinder(d=base_diameter, h=base_height);
        
        // Tapered body
        translate([0, 0, base_height])
            hull() {
                cylinder(d=base_diameter, h=0.1);
                translate([0, 0, vase_height - base_height])
                    cylinder(d=top_diameter, h=0.1);
            }
    }
    
    // Inner cavity
    translate([0, 0, wall_thickness])
        hull() {
            cylinder(d=base_diameter - 2*wall_thickness, h=0.1);
            translate([0, 0, vase_height - wall_thickness])
                cylinder(d=top_diameter - 2*wall_thickness, h=0.1);
        }
}

// Greek decorative band
translate([0, 0, vase_height * 0.6])
    difference() {
        cylinder(d=base_diameter + 4, h=greek_band_height);
        cylinder(d=base_diameter - 2, h=greek_band_height);
        
        // Greek key pattern
        for (angle = [0:30:360]) {
            rotate([0, 0, angle])
                translate([base_diameter/2 + 1, 0, greek_band_height/2])
                    cube([6, 2, 8], center=true);
        }
    }"""
        
        else:
            return """// Custom design
// All dimensions in millimeters
object_width = 50;
object_height = 30;
object_depth = 20;

// Basic object structure
cube([object_width, object_height, object_depth]);

// Add your custom modifications here
// This is a basic template - modify as needed"""
    
    def _generate_fallback_questions(self, user_response: str) -> Dict[str, Any]:
        """Generate context-aware follow-up questions when AI is unavailable"""
        response_lower = user_response.lower()
        
        if any(word in response_lower for word in ['wood', 'wooden', 'oak', 'pine', 'mahogany']):
            return {
                "stage": "questioning",
                "message": "Great! Wood texture and finish are important. A couple more questions:",
                "questions": [
                    "What type of wood finish do you prefer? (smooth, rustic, carved details)",
                    "Do you want visible wood grain patterns in the design?"
                ],
                "progress": 30
            }
        elif any(word in response_lower for word in ['greek', 'classical', 'column', 'ancient']):
            return {
                "stage": "questioning", 
                "message": "Excellent! Greek influences will add elegance. Let me ask:",
                "questions": [
                    "Which Greek elements do you prefer? (columns, key patterns, relief carvings)",
                    "Should the Greek styling be subtle or prominent?"
                ],
                "progress": 30
            }
        elif any(number in response_lower for number in ['mm', 'cm', 'inch', '10', '20', '30', '40', '50']):
            return {
                "stage": "questioning",
                "message": "Perfect! I have the size information. One more question:",
                "questions": [
                    "Any specific functional requirements? (hinges, compartments, handles, etc.)"
                ],
                "progress": 40
            }
        else:
            return {
                "stage": "questioning",
                "message": "Thanks for that detail! Just a couple more questions:",
                "questions": [
                    "What's the primary function of this design?",
                    "Any size constraints I should know about?"
                ],
                "progress": 30
            }
    
    def _create_fallback_design_spec(self, initial_request: str, user_answers: List[str]) -> str:
        """Create a design specification when AI is unavailable"""
        request_lower = initial_request.lower()
        answers_text = " ".join(user_answers).lower()
        
        # Extract key information from user answers
        dimensions = []
        materials = []
        styles = []
        features = []
        
        # Look for dimensions
        import re
        dimension_matches = re.findall(r'(\d+)\s*(mm|cm|inch|inches)', answers_text)
        for value, unit in dimension_matches:
            if unit in ['cm']:
                dimensions.append(f"{int(value) * 10}mm")
            elif unit in ['inch', 'inches']:
                dimensions.append(f"{int(float(value) * 25.4)}mm")
            else:
                dimensions.append(f"{value}{unit}")
        
        # Look for materials and styles
        if any(word in answers_text for word in ['wood', 'wooden', 'oak', 'pine']):
            materials.append("wooden texture")
        if any(word in answers_text for word in ['greek', 'classical', 'column']):
            styles.append("Greek classical influences")
        if any(word in answers_text for word in ['modern', 'contemporary']):
            styles.append("modern design")
        if any(word in answers_text for word in ['hinge', 'lid', 'compartment']):
            features.append("functional elements")
        
        # Generate specification based on request type
        if any(word in request_lower for word in ['chest', 'box', 'storage']):
            spec = f"""Wooden treasure chest design with the following specifications:

DIMENSIONS:
- Length: {dimensions[0] if dimensions else '200mm'}
- Width: {dimensions[1] if len(dimensions) > 1 else '150mm'} 
- Height: {dimensions[2] if len(dimensions) > 2 else '100mm'}
- Wall thickness: 8mm
- Lid height: 30mm

MATERIALS & FINISH:
- {materials[0] if materials else 'Wooden appearance'}
- Smooth finish with visible grain patterns
- Rounded corners for safety and aesthetics

STYLE ELEMENTS:
- {styles[0] if styles else 'Classical design'}
- Decorative corner elements
- Ornamental patterns on lid
- Traditional proportions

FUNCTIONAL FEATURES:
- Hinged lid (optional separate piece)
- Interior storage cavity
- Stable base design
- {features[0] if features else 'Practical storage solution'}"""
        
        elif any(word in request_lower for word in ['vase', 'cup', 'bowl']):
            spec = f"""Decorative vessel design with the following specifications:

DIMENSIONS:
- Height: {dimensions[0] if dimensions else '150mm'}
- Base diameter: {dimensions[1] if len(dimensions) > 1 else '80mm'}
- Top diameter: {dimensions[2] if len(dimensions) > 2 else '60mm'}
- Wall thickness: 3mm

MATERIALS & FINISH:
- {materials[0] if materials else 'Smooth surface finish'}
- Elegant proportions
- Professional appearance

STYLE ELEMENTS:
- {styles[0] if styles else 'Classical proportions'}
- Decorative band elements
- Tapered profile for elegance
- Stable base design

FUNCTIONAL FEATURES:
- Practical vessel design
- Easy to clean interior
- Stable base for safety"""
        
        else:
            spec = f"""Custom design with the following specifications:

DIMENSIONS:
- Primary dimension: {dimensions[0] if dimensions else '50mm'}
- Secondary dimension: {dimensions[1] if len(dimensions) > 1 else '30mm'}
- Height: {dimensions[2] if len(dimensions) > 2 else '20mm'}

MATERIALS & FINISH:
- {materials[0] if materials else 'Standard finish'}
- Clean, professional appearance

STYLE ELEMENTS:
- {styles[0] if styles else 'Functional design'}
- Appropriate proportions
- User-specified requirements

FUNCTIONAL FEATURES:
- {features[0] if features else 'Basic functionality'}
- Practical design approach"""
        
        return spec
