from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.urls import reverse
import os
import tempfile
import json
from .utils.file_processor import FileProcessor
from .utils.analyzer import PythonAnalyzer, JavaScriptAnalyzer, JavaAnalyzer, ArchitectureBuilder

def test_view(request):
    """Simple test view to verify setup"""
    return JsonResponse({'message': 'Backend is working correctly!'})

def index_view(request):
    """Main page view"""
    return render(request, 'simple_index.html')
    
def test_template(request):
    """Test template view"""
    return render(request, 'test.html')

def visualization_view(request, project_id):
    """View for displaying visualizations"""
    # In a real implementation, we would fetch project data from database
    # For now, we'll pass the project_id to the template
    context = {
        'project_id': project_id,
        'project_name': f'Project {project_id}'
    }
    return render(request, 'visualization.html', context)

@csrf_exempt
def upload_files(request):
    """Handle file uploads for code analysis"""
    if request.method == 'POST':
        try:
            # Handle file uploads
            files = request.FILES.getlist('files')
            
            if not files:
                return JsonResponse({'status': 'error', 'message': 'No files provided'})
            
            # Log the number of files for debugging
            print(f"Received {len(files)} files for upload")
            
            # Process files using FileProcessor
            processor = FileProcessor()
            processed_files = processor.process_files(files)
            
            # Filter to get only code files
            code_files = processor.get_code_files(processed_files)
            
            # Perform basic analysis on code files
            analysis_results = []
            for file_info in code_files:
                try:
                    if file_info['type'] == 'python':
                        analyzer = PythonAnalyzer(file_info['path'])
                        result = analyzer.analyze()
                        analysis_results.append({
                            'file': file_info['name'],
                            'language': 'python',
                            'analysis': result
                        })
                    elif file_info['type'] == 'javascript':
                        analyzer = JavaScriptAnalyzer(file_info['path'])
                        result = analyzer.analyze()
                        analysis_results.append({
                            'file': file_info['name'],
                            'language': 'javascript',
                            'analysis': result
                        })
                    elif file_info['type'] == 'java':
                        analyzer = JavaAnalyzer(file_info['path'])
                        result = analyzer.analyze()
                        analysis_results.append({
                            'file': file_info['name'],
                            'language': 'java',
                            'analysis': result
                        })
                except Exception as e:
                    print(f"Error analyzing {file_info['name']}: {str(e)}")
            
            # For demo purposes, we'll create a simple project representation
            # In a full implementation, this would save to the database
            project_data = {
                'id': 1,  # In a real app, this would be a database ID
                'name': 'Uploaded Project',
                'total_files': len(processed_files),
                'code_files': len(code_files),
                'analysis_results': analysis_results
            }
            
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