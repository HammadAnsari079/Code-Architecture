from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
from django.core import serializers
import os
import tempfile
import json
from .utils.file_processor import FileProcessor
from .utils.analyzer import EnhancedPythonAnalyzer, DatabaseSchemaExtractor, ProjectAnalyzer
from .models import Project, AnalysisResult, CodeFile, Dependency, Component
import uuid

def test_view(request):
    """Simple test view to verify setup"""
    return JsonResponse({'message': 'Backend is working correctly!'})

def index_view(request):
    """Main page view with project listing"""
    # Get all projects for display
    projects = Project.objects.all().order_by('-uploaded_at')
    context = {
        'projects': projects
    }
    return render(request, 'simple_index_fixed.html', context)
    
def test_template(request):
    """Test template view"""
    return render(request, 'test.html')

def visualization_view(request, project_id):
    """View for displaying visualizations"""
    try:
        # Fetch the actual project from database
        project = Project.objects.get(id=project_id)
        context = {
            'project_id': project.id,
            'project_name': project.name,
            'project_description': project.description,
            'uploaded_at': project.uploaded_at
        }
        return render(request, 'visualization.html', context)
    except Project.DoesNotExist:
        # Fallback for demo purposes
        context = {
            'project_id': project_id,
            'project_name': f'Project {project_id}'
        }
        return render(request, 'visualization.html', context)


def get_flowchart_data(request, project_id, file_name, function_name):
    """Generate flowchart data for a specific function in a file"""
    try:
        project = Project.objects.get(id=project_id)
        
        # Find the specific file
        # We need to handle potential path differences (basename vs full path)
        code_file = None
        all_files = CodeFile.objects.filter(project=project)
        
        for cf in all_files:
            if os.path.basename(cf.file_path) == file_name:
                code_file = cf
                break
        
        if not code_file:
            # Fallback: try to find by partial match
            for cf in all_files:
                if file_name in cf.file_path:
                    code_file = cf
                    break
        
        if code_file:
            # Use the analyzer to generate real CFG
            # Create a temporary file to analyze
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as temp:
                temp.write(code_file.content)
                temp_path = temp.name
            
            try:
                analyzer = EnhancedPythonAnalyzer(temp_path)
                # We need to manually set the file path to the original name for display purposes
                analyzer.file_path = code_file.file_path 
                result = analyzer.analyze()
                
                # Find the specific function's CFG
                target_cfg = None
                for cfg in result.get('control_flow_graphs', []):
                    if cfg['function_name'] == function_name:
                        target_cfg = cfg
                        break
                
                if target_cfg:
                    # Transform to Cytoscape format
                    nodes = []
                    edges = []
                    
                    for node in target_cfg['nodes']:
                        # Map analyzer node types to UI node types
                        ui_type = 'process'
                        if node['type'] == 'start': ui_type = 'start'
                        elif node['type'] == 'end': ui_type = 'end'
                        elif node['type'] == 'decision': ui_type = 'decision'
                        
                        nodes.append({
                            'data': {
                                'id': node['id'],
                                'label': node['label'],
                                'type': ui_type,
                                'code': node['code_snippet']
                            }
                        })
                    
                    for edge in target_cfg['edges']:
                        edges.append({
                            'data': {
                                'source': edge['source'],
                                'target': edge['target'],
                                'label': edge['label']
                            }
                        })
                        
                    return JsonResponse({
                        'status': 'success',
                        'data': {'nodes': nodes, 'edges': edges},
                        'project_id': project_id,
                        'file_name': file_name,
                        'function_name': function_name
                    })
                else:
                    return JsonResponse({
                        'status': 'error',
                        'message': f'Function {function_name} not found in {file_name}'
                    })
            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
        else:
             return JsonResponse({
                'status': 'error',
                'message': f'File {file_name} not found in project'
            })

    except Project.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Project not found'})
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error generating flowchart: {str(e)}'
        })

def get_erd_data(request, project_id):
    """Generate ERD data for the project"""
    try:
        project = Project.objects.get(id=project_id)
        code_files = CodeFile.objects.filter(project=project, language='python')
        
        all_tables = []
        all_relationships = []
        
        for cf in code_files:
            # Only analyze files that might contain models
            if 'models' in cf.file_path.lower() or 'model' in cf.file_path.lower():
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as temp:
                    temp.write(cf.content)
                    temp_path = temp.name
                
                try:
                    analyzer = EnhancedPythonAnalyzer(temp_path)
                    schema = analyzer.extract_database_schema()
                    
                    if schema:
                        all_tables.extend(schema.get('tables', []))
                        all_relationships.extend(schema.get('relationships', []))
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
        
        # Transform to Cytoscape elements
        elements = []
        
        # Add tables
        for table in all_tables:
            table_id = table['name']
            elements.append({
                'data': {'id': table_id, 'label': table['name']},
                'classes': 'table'
            })
            
            # Add fields
            for field in table['fields']:
                field_id = f"{table_id}_{field['name']}"
                field_label = f"{field['name']} ({field['type']})"
                classes = 'field'
                if field.get('is_primary_key'): classes += ' pk'
                if field.get('is_foreign_key'): classes += ' fk'
                
                elements.append({
                    'data': {'id': field_id, 'label': field_label, 'parent': table_id},
                    'classes': classes
                })
        
        # Add relationships
        for rel in all_relationships:
            source = rel['from_table']
            target = rel['to_table']
            # Only add if both exist
            if any(t['name'] == source for t in all_tables) and any(t['name'] == target for t in all_tables):
                elements.append({
                    'data': {
                        'source': source,
                        'target': target,
                        'label': rel.get('type', 'rel')
                    },
                    'classes': 'relationship'
                })
                
        return JsonResponse({
            'status': 'success',
            'data': elements
        })
        
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def get_dependency_data(request, project_id):
    """Generate dependency graph data"""
    try:
        project = Project.objects.get(id=project_id)
        code_files = CodeFile.objects.filter(project=project, language='python')
        
        elements = []
        files_map = {} # map filename to id
        
        # Create nodes for files
        for cf in code_files:
            file_name = os.path.basename(cf.file_path)
            file_id = f"file_{cf.id}"
            files_map[file_name] = file_id
            
            elements.append({
                'data': {'id': file_id, 'label': file_name},
                'classes': 'file'
            })
            
        # Analyze imports to create edges
        for cf in code_files:
            source_id = files_map.get(os.path.basename(cf.file_path))
            if not source_id: continue
            
            with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as temp:
                temp.write(cf.content)
                temp_path = temp.name
            
            try:
                analyzer = EnhancedPythonAnalyzer(temp_path)
                imports = analyzer.extract_imports()
                
                for imp in imports:
                    # Try to match import to a file in the project
                    # This is a simple heuristic
                    module_name = imp.get('module', '')
                    if not module_name: continue
                    
                    # Check if any file matches this module
                    for fname, fid in files_map.items():
                        if fname.startswith(module_name) or module_name in fname:
                            if fid != source_id: # Avoid self-loops
                                elements.append({
                                    'data': {
                                        'source': source_id,
                                        'target': fid,
                                        'label': 'imports'
                                    }
                                })
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
        return JsonResponse({
            'status': 'success',
            'data': elements
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def get_component_data(request, project_id):
    """Generate component diagram data based on classes and folders"""
    try:
        project = Project.objects.get(id=project_id)
        code_files = CodeFile.objects.filter(project=project, language='python')
        
        elements = []
        
        # Group by folder (simple component detection)
        components = {}
        
        for cf in code_files:
            folder = os.path.dirname(cf.file_path)
            if not folder: folder = "root"
            folder_name = os.path.basename(folder)
            
            if folder_name not in components:
                components[folder_name] = []
            components[folder_name].append(cf)
            
        # Create component nodes
        for comp_name, files in components.items():
            comp_id = f"comp_{comp_name}"
            elements.append({
                'data': {'id': comp_id, 'label': comp_name},
                'classes': 'component'
            })
            
            # Add classes as services/models inside components
            for cf in files:
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as temp:
                    temp.write(cf.content)
                    temp_path = temp.name
                
                try:
                    analyzer = EnhancedPythonAnalyzer(temp_path)
                    classes = analyzer.extract_classes()
                    
                    for cls in classes:
                        cls_id = f"cls_{cls['name']}"
                        cls_type = 'service'
                        if 'model' in comp_name.lower() or 'model' in cf.file_path.lower():
                            cls_type = 'model'
                        
                        elements.append({
                            'data': {'id': cls_id, 'label': cls['name'], 'parent': comp_id},
                            'classes': cls_type
                        })
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
        return JsonResponse({
            'status': 'success',
            'data': elements
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})

def documentation_view(request):
    """View for displaying project documentation"""
    # Read the documentation files
    try:
        with open('docs/upload_process_flow.txt', 'r') as f:
            upload_flow = f.read()
        with open('docs/database_flow.txt', 'r') as f:
            database_flow = f.read()
        with open('docs/project_overview.txt', 'r') as f:
            project_overview = f.read()
    except FileNotFoundError:
        upload_flow = database_flow = project_overview = "Documentation not found"
    
    context = {
        'upload_flow': upload_flow,
        'database_flow': database_flow,
        'project_overview': project_overview
    }
    return render(request, 'documentation.html', context)

@csrf_exempt
def upload_files(request):
    """Handle file uploads for code analysis"""
    if request.method == 'POST':
        try:
            # Handle file uploads
            files = request.FILES.getlist('files')
            
            if not files:
                return JsonResponse({'status': 'error', 'message': 'No files provided'})
            
            # Log detailed information about received files for debugging
            print(f"Received {len(files)} files for upload")
            for i, file in enumerate(files):
                print(f"File {i}: name='{file.name}', size={file.size}, content_type='{getattr(file, 'content_type', 'N/A')}'")
                # Check if the file has a relative path attribute
                if hasattr(file, 'webkitRelativePath'):
                    print(f"  webkitRelativePath: '{file.webkitRelativePath}'")
            
            # Create a new project in the database with a unique name
            project_count = Project.objects.count() + 1
            project = Project.objects.create(
                name=f"Project {project_count}",
                description="Uploaded codebase for analysis",
                file_path="",  # Will be updated after processing
                uploaded_by=None  # This is now optional
            )
            
            # Process files using FileProcessor
            processor = FileProcessor()
            processed_files = processor.process_files(files)
            
            # Log information about processed files
            print(f"Processed {len(processed_files)} files")
            for i, file_info in enumerate(processed_files):
                print(f"Processed file {i}: name='{file_info['name']}', path='{file_info['path']}', type='{file_info['type']}'")
            
            # Filter to get only code files
            code_files = processor.get_code_files(processed_files)
            
            # Perform basic analysis on code files
            analysis_results = []
            for file_info in code_files:
                try:
                    if file_info['type'] == 'python':
                        analyzer = EnhancedPythonAnalyzer(file_info['path'])
                        result = analyzer.analyze()
                        analysis_results.append({
                            'file': file_info['name'],
                            'language': 'python',
                            'analysis': result
                        })
                        
                        # Save code file info to database
                        CodeFile.objects.create(
                            project=project,
                            file_path=file_info['path'],
                            language='python',
                            size=os.path.getsize(file_info['path']),
                            content=open(file_info['path'], 'r', encoding='utf-8').read()
                        )
                    # Note: JavaScript and Java analyzers not yet implemented in the new version
                    elif file_info['type'] == 'javascript':
                        # For now, we'll create a placeholder analysis
                        analysis_results.append({
                            'file': file_info['name'],
                            'language': 'javascript',
                            'analysis': {
                                'file_path': file_info['path'],
                                'file_name': file_info['name'],
                                'imports': [],
                                'classes': [],
                                'functions': [],
                                'control_flow_graphs': []
                            }
                        })
                        
                        # Save code file info to database
                        CodeFile.objects.create(
                            project=project,
                            file_path=file_info['path'],
                            language='javascript',
                            size=os.path.getsize(file_info['path']),
                            content=open(file_info['path'], 'r', encoding='utf-8').read()
                        )
                    elif file_info['type'] == 'java':
                        # For now, we'll create a placeholder analysis
                        analysis_results.append({
                            'file': file_info['name'],
                            'language': 'java',
                            'analysis': {
                                'file_path': file_info['path'],
                                'file_name': file_info['name'],
                                'imports': [],
                                'classes': [],
                                'functions': [],
                                'control_flow_graphs': []
                            }
                        })
                        
                        # Save code file info to database
                        CodeFile.objects.create(
                            project=project,
                            file_path=file_info['path'],
                            language='java',
                            size=os.path.getsize(file_info['path']),
                            content=open(file_info['path'], 'r', encoding='utf-8').read()
                        )
                except Exception as e:
                    print(f"Error analyzing {file_info['name']}: {str(e)}")
            
            # Save analysis results to database
            AnalysisResult.objects.create(
                project=project,
                analysis_type='code_analysis',
                result_data={
                    'total_files': len(processed_files),
                    'code_files': len(code_files),
                    'analysis_results': analysis_results
                }
            )
            
            # For demo purposes, we'll create a simple project representation
            project_data = {
                'id': project.id,
                'name': project.name,
                'total_files': len(processed_files),
                'code_files': len(code_files),
                'analysis_results': analysis_results
            }
            
            # Update project file path
            project.file_path = f"project_{project.id}"
            project.save()
            
            # Clean up
            processor.cleanup()
            
            # Return success response with redirect URL for visualization
            return JsonResponse({
                'status': 'success',
                'message': f'Successfully processed {len(processed_files)} files ({len(code_files)} code files)',
                'project_id': project_data['id'],
                'redirect_url': f'/visualization/{project_data["id"]}/'
            })
        except Exception as e:
            print(f"Upload error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'Upload failed: {str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})