#!/usr/bin/env python3
"""
Web UI for NL-CAD - Natural Language CAD Generator
Provides a web interface with voice recognition and 3D STL rendering
"""
import os
import tempfile
import subprocess
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_file
from generation.bosl_generator import BOSLGenerator

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize BOSL generator
generator = BOSLGenerator()

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Serve the test page for debugging"""
    return render_template('test.html')

@app.route('/api/generate', methods=['POST'])
def generate_scad():
    """Generate OpenSCAD code from description"""
    try:
        data = request.get_json()
        description = data.get('description', '').strip()
        
        if not description:
            return jsonify({'error': 'No description provided'}), 400
        
        # Generate OpenSCAD code
        scad_code = generator.generate(description)
        
        return jsonify({
            'success': True,
            'scad_code': scad_code,
            'description': description
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
