#!/usr/bin/env python3
"""
Web UI for NL-CAD - Natural Language CAD Generator
Provides a web interface with voice recognition and 3D STL rendering
Supports multiple generator modes: BOSL, Cube-only, and Maze
"""
import os
import tempfile
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from generation.catalog.bosl_generator import BOSLGenerator
from generation.creative.hybrid_generator import HybridCADGenerator
from generation.catalog.cube_generator import CubeGenerator
from generation.catalog.maze_generator import MazeGenerator
from conversation.conversation_manager import ConversationManager
from generation.creative.two_stage_generator import TwoStageGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize generators
generators = {
    'bosl': BOSLGenerator(),
    'cube': CubeGenerator(),
    'maze': MazeGenerator(),
    'hybrid': HybridCADGenerator(),
    'two-stage': TwoStageGenerator()
}

# Global conversational session storage (in production, use Redis or database)
conversation_sessions = {}

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Serve the test page for debugging"""
    return render_template('test.html')

@app.route('/conversation')
def conversation():
    """Serve the conversational design interface"""
    return render_template('conversation.html')

@app.route('/api/modes')
def get_modes():
    """Get available generator modes"""
    return jsonify({
        'modes': [
            {
                'id': 'bosl',
                'name': 'BOSL Generator',
                'description': 'Mechanical parts using BOSL2 library (bolts, nuts, washers, etc.)',
                'icon': '🔧'
            },
            {
                'id': 'cube',
                'name': 'Cube Generator', 
                'description': 'Voxel-style objects using only cubes (Minecraft-like)',
                'icon': '🧊'
            },
            {
                'id': 'maze',
                'name': 'Maze Generator',
                'description': 'Mazes with walls and paths (rectangular, circular, multi-level)',
                'icon': '🌀'
            },
            {
                'id': 'conversation',
                'name': 'Conversational Design',
                'description': 'Interactive design with questions and iterative examples',
                'icon': '💬'
            },
            {
                'id': 'hybrid',
                'name': 'Smart Generator (Recommended)',
                'description': 'Intelligently chooses the best generator: BOSL for parts, Cube for furniture, Maze for mazes',
                'icon': '🤖'
            },
            {
                'id': 'two-stage',
                'name': 'Two Stage Generator',
                'description': 'Two stage generator: first design, then code',
                'icon': '🎭'
            }
        ]
    })

@app.route('/api/generate', methods=['POST'])
def generate_scad():
    """Generate OpenSCAD code from description using specified generator mode"""
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        mode = data.get('mode', 'hybrid').lower()
        print(f"🔧 Selected mode: {mode}")  # Debug what mode is actually being used
        
        if not description:
            return jsonify({'error': 'No description provided'}), 400
        
        if mode not in generators:
            return jsonify({'error': f'Invalid mode: {mode}. Valid modes: {list(generators.keys())}'}), 400
        
        # Select appropriate generator
        generator = generators[mode]
        
        # Generate OpenSCAD code
        scad_code = generator.generate(description)
        
        return jsonify({
            'success': True,
            'scad_code': scad_code,
            'description': description,
            'mode': mode
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate_stl', methods=['POST'])
def generate_stl():
    """Generate STL from OpenSCAD code"""
    try:
        data = request.get_json()
        scad_code = data.get('scad_code', '').strip()
        filename = data.get('filename', 'model')
        
        if not scad_code:
            return jsonify({'error': 'No OpenSCAD code provided'}), 400
        
        # Create temporary files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            scad_file = temp_path / f"{filename}.scad"
            stl_file = temp_path / f"{filename}.stl"
            
            # Write OpenSCAD code to file
            scad_file.write_text(scad_code)
            
            # Convert to STL using OpenSCAD
            cmd = [
                'openscad',
                '--export-format', 'stl',
                '-o', str(stl_file),
                str(scad_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                return jsonify({
                    'error': 'OpenSCAD conversion failed',
                    'details': result.stderr
                }), 500
            
            if not stl_file.exists():
                return jsonify({'error': 'STL file was not created'}), 500
            
            # Read STL content
            stl_content = stl_file.read_bytes()
            
            # Save to output directory for persistence
            output_dir = Path('output')
            output_dir.mkdir(exist_ok=True)
            output_stl = output_dir / f"{filename}.stl"
            output_stl.write_bytes(stl_content)
            
            return jsonify({
                'success': True,
                'filename': f"{filename}.stl",
                'size': len(stl_content),
                'path': str(output_stl)
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'OpenSCAD conversion timed out'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/download_stl/<filename>')
def download_stl(filename):
    """Download STL file"""
    try:
        output_dir = Path('output')
        stl_file = output_dir / filename
        
        if not stl_file.exists():
            return jsonify({'error': 'STL file not found'}), 404
        
        return send_file(
            stl_file,
            as_attachment=True,
            download_name=filename,
            mimetype='application/octet-stream'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/start', methods=['POST'])
def start_conversation():
    """Start a new conversational design session"""
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        session_id = data.get('session_id', f"session_{len(conversation_sessions)}")
        
        if not description:
            return jsonify({'error': 'No description provided'}), 400
        
        # Create new conversation manager
        conversation_manager = ConversationManager()
        conversation_sessions[session_id] = conversation_manager
        
        # Start the conversation
        response = conversation_manager.start_conversation(description)
        response['session_id'] = session_id
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/continue', methods=['POST'])
def continue_conversation():
    """Continue an existing conversational design session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', '')
        user_input = data.get('user_input', '').strip()
        
        if not session_id or session_id not in conversation_sessions:
            return jsonify({'error': 'Invalid or expired session'}), 400
        
        if not user_input:
            return jsonify({'error': 'No user input provided'}), 400
        
        conversation_manager = conversation_sessions[session_id]
        response = conversation_manager.continue_conversation(user_input)
        response['session_id'] = session_id
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/history/<session_id>')
def get_conversation_history(session_id):
    """Get the full conversation history for a session"""
    try:
        if session_id not in conversation_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        conversation_manager = conversation_sessions[session_id]
        history = conversation_manager.get_conversation_history()
        
        return jsonify({
            'session_id': session_id,
            'history': history
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/export/<session_id>')
def export_conversation_design(session_id):
    """Export the final design from a conversation session"""
    try:
        if session_id not in conversation_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        conversation_manager = conversation_sessions[session_id]
        code = conversation_manager.get_current_code()
        
        return jsonify({
            'session_id': session_id,
            'code': code
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/conversation/reset/<session_id>', methods=['POST'])
def reset_conversation(session_id):
    """Reset a conversation session to start fresh"""
    try:
        if session_id not in conversation_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        conversation_manager = conversation_sessions[session_id]
        conversation_manager.reset_conversation()
        
        return jsonify({
            'message': 'Conversation reset successfully',
            'session_id': session_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/models')
def list_models():
    """List available STL files"""
    try:
        output_dir = Path('output')
        if not output_dir.exists():
            return jsonify({'models': []})
        
        stl_files = list(output_dir.glob('*.stl'))
        models = []
        
        for stl_file in stl_files:
            stat = stl_file.stat()
            models.append({
                'filename': stl_file.name,
                'size': stat.st_size,
                'modified': stat.st_mtime
            })
        
        # Sort by modification time (newest first)
        models.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({'models': models})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create output directory
    Path('output').mkdir(exist_ok=True)
    
    # Run Flask app
    app.run(debug=False, host='127.0.0.1', port=5000)
