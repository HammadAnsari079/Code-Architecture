from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
import os
import json
import tempfile
from .models import Project, AnalysisResult
from .utils.file_processor import FileProcessor
from .utils.analyzer import EnhancedPythonAnalyzer, DatabaseSchemaExtractor, ProjectAnalyzer
from .utils.control_flow_builder import ControlFlowGraphBuilder
from .utils.database_schema_extractor import DatabaseSchemaExtractor
from .utils.enhanced_graph_generator import EnhancedGraphGenerator

def enhanced_visualization_view(request, project_id):
    """Enhanced visualization view with interactive features"""
    # In a real implementation, we would fetch project data from database
    # For now, we'll pass the project_id to the template
    context = {
        'project_id': project_id,
        'project_name': f'Project {project_id}'
    }
    return render(request, 'enhanced_visualization.html', context)

@csrf_exempt
def get_function_flowchart(request, project_id, file_path, function_name):
    """Generate flowchart for a specific function"""
    if request.method == 'GET':
        try:
            # In a real implementation, we would retrieve the file from the database
            # For now, we'll simulate with a temporary file
            full_file_path = os.path.join(tempfile.gettempdir(), file_path)
            
            # Check if file exists
            if not os.path.exists(full_file_path):
                return JsonResponse({
                    'status': 'error', 
                    'message': f'File {file_path} not found'
                })
            
            # Build control flow graph
            cfg_builder = ControlFlowGraphBuilder(full_file_path)
            flowchart_data = cfg_builder.build_cfg_for_function(function_name)
            
            # Generate Cytoscape.js format
            graph_generator = EnhancedGraphGenerator(flowchart_data)
            cytoscape_data = graph_generator.to_cytoscape_format()
            
            # Generate styles and layout
            style = graph_generator.generate_flowchart_style()
            layout = graph_generator.generate_layout_config('flowchart')
            
            return JsonResponse({
                'status': 'success',
                'data': cytoscape_data,
                'style': style,
                'layout': layout
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error generating flowchart: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def get_database_erd(request, project_id):
    """Generate ERD for database schema"""
    if request.method == 'GET':
        try:
            # In a real implementation, we would analyze the project's models.py files
            # For now, we'll simulate with the current project directory
            project_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Extract database schema
            schema_extractor = DatabaseSchemaExtractor(project_path)
            schema_data = schema_extractor.extract_schema()
            
            # Generate Cytoscape.js format
            graph_generator = EnhancedGraphGenerator(schema_data)
            cytoscape_data = graph_generator.to_cytoscape_format()
            
            # Generate styles and layout
            style = graph_generator.generate_erd_style()
            layout = graph_generator.generate_layout_config('erd')
            
            return JsonResponse({
                'status': 'success',
                'data': cytoscape_data,
                'style': style,
                'layout': layout
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error generating ERD: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def get_code_snippet(request, file_path, line_number):
    """Get code snippet for a specific file and line number"""
    if request.method == 'GET':
        try:
            # In a real implementation, we would retrieve the file from the database
            # For now, we'll simulate with a temporary file
            full_file_path = os.path.join(tempfile.gettempdir(), file_path)
            
            # Check if file exists
            if not os.path.exists(full_file_path):
                return JsonResponse({
                    'status': 'error', 
                    'message': f'File {file_path} not found'
                })
            
            # Read the file and extract snippet
            with open(full_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extract context lines (5 before and after)
            start_line = max(0, int(line_number) - 6)
            end_line = min(len(lines), int(line_number) + 5)
            snippet_lines = lines[start_line:end_line]
            
            # Create snippet with line numbers
            snippet = []
            for i, line in enumerate(snippet_lines, start=start_line + 1):
                snippet.append({
                    'line_number': i,
                    'content': line.rstrip(),
                    'is_target': i == int(line_number)
                })
            
            return JsonResponse({
                'status': 'success',
                'snippet': snippet,
                'file_path': file_path,
                'target_line': int(line_number)
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error retrieving code snippet: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
def jump_to_code(request):
    """Generate URL to jump to code in editor"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_path = data.get('file_path', '')
            line_number = data.get('line_number', 1)
            
            # Generate VS Code URL
            # Note: This requires VS Code to be installed and the vscode:// protocol to be registered
            vscode_url = f"vscode://file/{file_path}:{line_number}"
            
            return JsonResponse({
                'status': 'success',
                'vscode_url': vscode_url,
                'file_path': file_path,
                'line_number': line_number
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'Error generating jump URL: {str(e)}'
            })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})