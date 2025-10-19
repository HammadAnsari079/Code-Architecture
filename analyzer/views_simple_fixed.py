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
        # Try to fetch actual project data
        try:
            project = Project.objects.get(id=project_id)
            # Get the actual code file for this project
            code_files = CodeFile.objects.filter(project=project)
            
            # If we have actual code files, try to generate real flowchart data
            if code_files.exists():
                # For demo purposes, we'll create project-specific flowcharts based on the project ID
                # In a real implementation, this would analyze the actual code
                
                # Generate flowchart based on project ID to ensure uniqueness
                flowchart_data = {
                    'nodes': [
                        {'id': 'start', 'label': f'START ({function_name} - Project {project_id})', 'type': 'start'},
                        {'id': 'process_data', 'label': f'Process {file_name} data', 'type': 'process'},
                        {'id': 'decision_point', 'label': f'Check {function_name} logic?', 'type': 'decision'},
                        {'id': 'action_a', 'label': 'Execute primary action', 'type': 'process'},
                        {'id': 'action_b', 'label': 'Execute alternative action', 'type': 'process'},
                        {'id': 'combine_results', 'label': 'Combine processing results', 'type': 'process'},
                        {'id': 'end', 'label': 'END', 'type': 'end'}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'process_data'},
                        {'source': 'process_data', 'target': 'decision_point'},
                        {'source': 'decision_point', 'target': 'action_a', 'label': 'YES'},
                        {'source': 'decision_point', 'target': 'action_b', 'label': 'NO'},
                        {'source': 'action_a', 'target': 'combine_results'},
                        {'source': 'action_b', 'target': 'combine_results'},
                        {'source': 'combine_results', 'target': 'end'}
                    ]
                }
                
                return JsonResponse({
                    'status': 'success',
                    'data': flowchart_data,
                    'project_id': project_id,
                    'file_name': file_name,
                    'function_name': function_name
                })
        except Project.DoesNotExist:
            pass
        
        # Get the function name from query parameters
        function_name = request.GET.get('function', function_name)
        
        # Generate flowchart based on file name and function name
        if 'order' in file_name.lower() or 'order' in function_name.lower():
            # Flowchart for order processing functions
            flowchart_data = {
                'nodes': [
                    {'id': 'start', 'label': f'START ({function_name})', 'type': 'start'},
                    {'id': 'get_order', 'label': 'Get order from database', 'type': 'process'},
                    {'id': 'check_status', 'label': "Is status == 'pending'?", 'type': 'decision'},
                    {'id': 'return_false', 'label': 'Return False', 'type': 'process'},
                    {'id': 'check_total', 'label': 'Is total > 1000?', 'type': 'decision'},
                    {'id': 'set_high', 'label': "Set priority = 'high'", 'type': 'process'},
                    {'id': 'set_normal', 'label': "Set priority = 'normal'", 'type': 'process'},
                    {'id': 'set_status', 'label': "Set status = 'processing'", 'type': 'process'},
                    {'id': 'save_order', 'label': 'Save order', 'type': 'process'},
                    {'id': 'return_true', 'label': 'Return True', 'type': 'process'},
                    {'id': 'end', 'label': 'END', 'type': 'end'}
                ],
                'edges': [
                    {'source': 'start', 'target': 'get_order'},
                    {'source': 'get_order', 'target': 'check_status'},
                    {'source': 'check_status', 'target': 'return_false', 'label': 'NO'},
                    {'source': 'return_false', 'target': 'end'},
                    {'source': 'check_status', 'target': 'check_total', 'label': 'YES'},
                    {'source': 'check_total', 'target': 'set_high', 'label': 'YES'},
                    {'source': 'check_total', 'target': 'set_normal', 'label': 'NO'},
                    {'source': 'set_high', 'target': 'set_status'},
                    {'source': 'set_normal', 'target': 'set_status'},
                    {'source': 'set_status', 'target': 'save_order'},
                    {'source': 'save_order', 'target': 'return_true'},
                    {'source': 'return_true', 'target': 'end'}
                ]
            }
        elif 'user' in file_name.lower() or 'auth' in file_name.lower() or 'login' in function_name.lower():
            # Flowchart for authentication functions
            flowchart_data = {
                'nodes': [
                    {'id': 'start', 'label': f'START ({function_name})', 'type': 'start'},
                    {'id': 'get_user', 'label': 'Get user from database', 'type': 'process'},
                    {'id': 'check_password', 'label': 'Check password?', 'type': 'decision'},
                    {'id': 'return_none', 'label': 'Return None', 'type': 'process'},
                    {'id': 'create_session', 'label': 'Create session', 'type': 'process'},
                    {'id': 'return_user', 'label': 'Return user', 'type': 'process'},
                    {'id': 'end', 'label': 'END', 'type': 'end'}
                ],
                'edges': [
                    {'source': 'start', 'target': 'get_user'},
                    {'source': 'get_user', 'target': 'check_password'},
                    {'source': 'check_password', 'target': 'return_none', 'label': 'NO'},
                    {'source': 'return_none', 'target': 'end'},
                    {'source': 'check_password', 'target': 'create_session', 'label': 'YES'},
                    {'source': 'create_session', 'target': 'return_user'},
                    {'source': 'return_user', 'target': 'end'}
                ]
            }
        elif 'payment' in file_name.lower() or 'transaction' in function_name.lower():
            # Flowchart for payment functions
            flowchart_data = {
                'nodes': [
                    {'id': 'start', 'label': f'START ({function_name})', 'type': 'start'},
                    {'id': 'validate_payment', 'label': 'Validate payment info', 'type': 'process'},
                    {'id': 'check_funds', 'label': 'Check available funds?', 'type': 'decision'},
                    {'id': 'insufficient_funds', 'label': 'Insufficient funds', 'type': 'process'},
                    {'id': 'process_payment', 'label': 'Process payment', 'type': 'process'},
                    {'id': 'update_ledger', 'label': 'Update ledger', 'type': 'process'},
                    {'id': 'send_confirmation', 'label': 'Send confirmation', 'type': 'process'},
                    {'id': 'end', 'label': 'END', 'type': 'end'}
                ],
                'edges': [
                    {'source': 'start', 'target': 'validate_payment'},
                    {'source': 'validate_payment', 'target': 'check_funds'},
                    {'source': 'check_funds', 'target': 'insufficient_funds', 'label': 'NO'},
                    {'source': 'insufficient_funds', 'target': 'end'},
                    {'source': 'check_funds', 'target': 'process_payment', 'label': 'YES'},
                    {'source': 'process_payment', 'target': 'update_ledger'},
                    {'source': 'update_ledger', 'target': 'send_confirmation'},
                    {'source': 'send_confirmation', 'target': 'end'}
                ]
            }
        else:
            # Generic flowchart based on file name
            if 'model' in file_name.lower():
                flowchart_data = {
                    'nodes': [
                        {'id': 'start', 'label': f'START ({function_name})', 'type': 'start'},
                        {'id': 'validate_data', 'label': 'Validate input data', 'type': 'process'},
                        {'id': 'check_existing', 'label': 'Check if exists?', 'type': 'decision'},
                        {'id': 'update_record', 'label': 'Update existing record', 'type': 'process'},
                        {'id': 'create_record', 'label': 'Create new record', 'type': 'process'},
                        {'id': 'save_to_db', 'label': 'Save to database', 'type': 'process'},
                        {'id': 'return_result', 'label': 'Return result', 'type': 'process'},
                        {'id': 'end', 'label': 'END', 'type': 'end'}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'validate_data'},
                        {'source': 'validate_data', 'target': 'check_existing'},
                        {'source': 'check_existing', 'target': 'update_record', 'label': 'YES'},
                        {'source': 'check_existing', 'target': 'create_record', 'label': 'NO'},
                        {'source': 'update_record', 'target': 'save_to_db'},
                        {'source': 'create_record', 'target': 'save_to_db'},
                        {'source': 'save_to_db', 'target': 'return_result'},
                        {'source': 'return_result', 'target': 'end'}
                    ]
                }
            elif 'view' in file_name.lower():
                flowchart_data = {
                    'nodes': [
                        {'id': 'start', 'label': f'START ({function_name})', 'type': 'start'},
                        {'id': 'get_request', 'label': 'Get HTTP request', 'type': 'process'},
                        {'id': 'validate_input', 'label': 'Validate input data', 'type': 'process'},
                        {'id': 'process_data', 'label': 'Process business logic', 'type': 'process'},
                        {'id': 'render_response', 'label': 'Render response', 'type': 'process'},
                        {'id': 'return_http', 'label': 'Return HTTP response', 'type': 'process'},
                        {'id': 'end', 'label': 'END', 'type': 'end'}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'get_request'},
                        {'source': 'get_request', 'target': 'validate_input'},
                        {'source': 'validate_input', 'target': 'process_data'},
                        {'source': 'process_data', 'target': 'render_response'},
                        {'source': 'render_response', 'target': 'return_http'},
                        {'source': 'return_http', 'target': 'end'}
                    ]
                }
            else:
                # Completely generic flowchart with project-specific labeling
                flowchart_data = {
                    'nodes': [
                        {'id': 'start', 'label': f'START ({function_name} - Project {project_id})', 'type': 'start'},
                        {'id': 'step1', 'label': 'Process input data', 'type': 'process'},
                        {'id': 'decision1', 'label': 'Check condition?', 'type': 'decision'},
                        {'id': 'action1', 'label': 'Take action A', 'type': 'process'},
                        {'id': 'action2', 'label': 'Take action B', 'type': 'process'},
                        {'id': 'combine', 'label': 'Combine results', 'type': 'process'},
                        {'id': 'end', 'label': 'END', 'type': 'end'}
                    ],
                    'edges': [
                        {'source': 'start', 'target': 'step1'},
                        {'source': 'step1', 'target': 'decision1'},
                        {'source': 'decision1', 'target': 'action1', 'label': 'YES'},
                        {'source': 'decision1', 'target': 'action2', 'label': 'NO'},
                        {'source': 'action1', 'target': 'combine'},
                        {'source': 'action2', 'target': 'combine'},
                        {'source': 'combine', 'target': 'end'}
                    ]
                }
        
        return JsonResponse({
            'status': 'success',
            'data': flowchart_data,
            'project_id': project_id,
            'file_name': file_name,
            'function_name': function_name
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Error generating flowchart: {str(e)}'
        })

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