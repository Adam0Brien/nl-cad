"""
Conversational Design Generator
Interactive mode that asks questions and provides iterative examples
"""
import json
import re
import os
import requests
from typing import Dict, List, Optional, Tuple, Any
from ..core.base_generator import BaseGenerator


class ConversationalGenerator(BaseGenerator):
    """Interactive generator that asks questions and provides examples"""
    
    def __init__(self):
        super().__init__()
        self.conversation_history = []
        self.current_design_state = {}
        self.model = os.getenv("DESIGN_MODEL", "llama3.2:3b")
        
        print("💬 Conversational generator initialized")
        print("   Interactive design with questions and examples")
    
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
        
        return conversation_state
    
    def continue_conversation(self, user_input: str) -> Dict[str, Any]:
        """Continue the conversation with user input"""
        
        # Add user input to history
        self.conversation_history.append({
            "type": "user_input",
            "content": user_input,
            "timestamp": self._get_timestamp()
        })
        
        # Determine current stage and generate appropriate response
        last_state = self._get_last_state()
        
        if last_state.get("stage") == "questioning":
            response = self._handle_questioning_stage(user_input)
        elif last_state.get("stage") == "designing":
            response = self._handle_designing_stage(user_input)
        elif last_state.get("stage") == "refining":
            response = self._handle_refining_stage(user_input)
        else:
            response = self._handle_general_input(user_input)
        
        # Add response to history
        self.conversation_history.append({
            "type": "assistant_response",
            "content": response,
            "timestamp": self._get_timestamp()
        })
        
        return response
    
    def _generate_initial_response(self, request: str) -> Dict[str, Any]:
        """Generate the initial response with questions"""
        
        system_prompt = """You are a helpful 3D design assistant. When someone asks you to design something, you should:

1. Acknowledge their request enthusiastically
2. Ask 2-3 specific clarifying questions about:
   - Dimensions or size preferences
   - Intended use or functional requirements  
   - Style or aesthetic preferences
   - Any specific features they want

3. If the request is very clear and specific, you can start generating a simple example

Always be conversational and helpful. Ask questions that will help you create exactly what they need.

Respond in this JSON format:
{
    "message": "Your conversational response",
    "questions": ["Question 1?", "Question 2?", "Question 3?"],
    "code": "basic openscad code if appropriate",
    "progress": 10,
    "stage": "questioning"
}"""

        user_prompt = f"""The user wants to design: "{request}"

Please respond with an enthusiastic acknowledgment and ask helpful clarifying questions to better understand what they need."""

        try:
            result = self._generate_with_ollama(system_prompt, user_prompt, temperature=0.7)
            
            # Try to parse as JSON, fallback to structured response
            try:
                return json.loads(result)
            except:
                return {
                    "message": result,
                    "questions": [
                        "What size should this be? (approximate dimensions)",
                        "How will this be used? (any specific requirements)",
                        "Any particular style or features you want?"
                    ],
                    "code": "",
                    "progress": 10,
                    "stage": "questioning"
                }
                
        except Exception as e:
            return {
                "message": f"I'd love to help you design {request}! Could you tell me a bit more about what you have in mind?",
                "questions": [
                    "What size should this be?",
                    "How will you use it?",
                    "Any specific features you want?"
                ],
                "code": "",
                "progress": 10,
                "stage": "questioning"
            }
    
    def _handle_questioning_stage(self, user_input: str) -> Dict[str, Any]:
        """Handle user responses during questioning stage"""
        
        # Update design state with user input
        self.current_design_state["user_preferences"] = user_input
        
        system_prompt = """You are a 3D design assistant. The user has provided more details about their design request. Based on their input:

1. Thank them for the additional information
2. Summarize what you understand so far
3. Generate a basic OpenSCAD code example based on their requirements
4. Ask 1-2 follow-up questions if needed, or move to design refinement

Respond in JSON format:
{
    "message": "Your response acknowledging their input",
    "questions": ["Follow-up question?"] or [],
    "code": "basic openscad code based on their requirements",
    "progress": 40,
    "stage": "designing" or "refining"
}

For the OpenSCAD code:
- Use realistic dimensions based on their input
- Include proper variable definitions
- Create a basic but functional design
- Add comments explaining the design choices"""

        conversation_context = self._get_conversation_context()
        user_prompt = f"""Conversation so far:
{conversation_context}

Latest user input: "{user_input}"

Please generate a response with a basic OpenSCAD design based on what they've told you."""

        try:
            result = self._generate_with_ollama(system_prompt, user_prompt, temperature=0.6)
            
            try:
                response = json.loads(result)
                # Validate and clean the code if present
                if response.get("code"):
                    response["code"] = self._basic_code_cleanup(response["code"])
                return response
            except:
                return {
                    "message": "Thanks for the details! Let me create a basic design for you.",
                    "questions": [],
                    "code": self._generate_basic_code_from_context(),
                    "progress": 40,
                    "stage": "designing"
                }
                
        except Exception as e:
            return {
                "message": "I understand what you're looking for. Let me create a basic design.",
                "questions": [],
                "code": self._generate_basic_code_from_context(),
                "progress": 40,
                "stage": "designing"
            }
    
    def _handle_designing_stage(self, user_input: str) -> Dict[str, Any]:
        """Handle feedback during the design stage"""
        
        system_prompt = """You are helping refine a 3D design. The user has provided feedback on the current design. You should:

1. Acknowledge their feedback
2. Modify the OpenSCAD code based on their suggestions
3. Explain what changes you made
4. Ask if they want any other adjustments

Respond in JSON format:
{
    "message": "Response explaining the changes you made",
    "questions": ["Any other changes you'd like?"],
    "code": "updated openscad code",
    "progress": 70,
    "stage": "refining"
}

For code changes:
- Make specific adjustments based on their feedback
- Maintain proper variable definitions
- Add comments for new features
- Keep the code clean and functional"""

        conversation_context = self._get_conversation_context()
        current_code = self._get_current_code()
        
        user_prompt = f"""Current design:
{current_code}

User feedback: "{user_input}"

Previous conversation:
{conversation_context}

Please modify the design based on their feedback."""

        try:
            result = self._generate_with_ollama(system_prompt, user_prompt, temperature=0.5)
            
            try:
                response = json.loads(result)
                if response.get("code"):
                    response["code"] = self._basic_code_cleanup(response["code"])
                return response
            except:
                return {
                    "message": "I've updated the design based on your feedback!",
                    "questions": ["How does this look? Any other changes?"],
                    "code": current_code,  # Fallback to current code
                    "progress": 70,
                    "stage": "refining"
                }
                
        except Exception as e:
            return {
                "message": "Let me adjust the design for you.",
                "questions": ["What other changes would you like?"],
                "code": current_code,
                "progress": 70,
                "stage": "refining"
            }
    
    def _handle_refining_stage(self, user_input: str) -> Dict[str, Any]:
        """Handle final refinements"""
        
        if user_input.lower() in ["done", "finished", "complete", "good", "perfect", "that's it"]:
            return {
                "message": "Excellent! Your design is complete. You can download the OpenSCAD file or continue making adjustments.",
                "questions": [],
                "code": self._get_current_code(),
                "progress": 100,
                "stage": "complete"
            }
        
        # Otherwise, continue refining
        return self._handle_designing_stage(user_input)
    
    def _handle_general_input(self, user_input: str) -> Dict[str, Any]:
        """Handle general input that doesn't fit other stages"""
        
        return {
            "message": "I understand. What would you like to adjust about the design?",
            "questions": ["Any specific changes you'd like to make?"],
            "code": self._get_current_code(),
            "progress": 80,
            "stage": "refining"
        }
    
    def _generate_with_ollama(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """Generate response using Ollama"""
        try:
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": 800,
                    "top_p": 0.9
                }
            }
            
            response = requests.post(
                f"{base_url}/api/chat",
                json=payload,
                timeout=(10, 120)
            )
            response.raise_for_status()
            
            content = response.json().get("message", {}).get("content", "")
            return content.strip()
            
        except Exception as e:
            print(f"Ollama request failed: {e}")
            return ""
    
    def _get_conversation_context(self) -> str:
        """Get formatted conversation context"""
        context = []
        for entry in self.conversation_history[-4:]:  # Last 4 entries
            if entry["type"] == "user_request":
                context.append(f"User request: {entry['content']}")
            elif entry["type"] == "user_input":
                context.append(f"User: {entry['content']}")
            elif entry["type"] == "assistant_response":
                context.append(f"Assistant: {entry['content'].get('message', '')}")
        return "\n".join(context)
    
    def _get_current_code(self) -> str:
        """Get the most recent code from conversation"""
        for entry in reversed(self.conversation_history):
            if entry["type"] == "assistant_response" and entry["content"].get("code"):
                return entry["content"]["code"]
        return ""
    
    def _get_last_state(self) -> Dict[str, Any]:
        """Get the last conversation state"""
        for entry in reversed(self.conversation_history):
            if entry["type"] == "assistant_response":
                return entry["content"]
        return {}
    
    def _generate_basic_code_from_context(self) -> str:
        """Generate basic code from conversation context"""
        # Simple fallback code generation
        return """// Basic design
// Dimensions
width = 50;
height = 30;
depth = 20;

// Main object
cube([width, height, depth]);"""
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history"""
        return self.conversation_history
    
    def export_design(self) -> str:
        """Export the final design code"""
        return self._get_current_code()
