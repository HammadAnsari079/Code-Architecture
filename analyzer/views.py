import os
import json
import tempfile
from django.shortcuts import render
from django.http import JsonResponse

def test_view(request):
    """Simple test view to verify setup"""
    return JsonResponse({'message': 'Backend is working correctly!'})

import tempfile
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Project, AnalysisResult, CodeFile, Dependency, Component
from .utils.file_handler import FileHandler
from .utils.analyzer import PythonAnalyzer, JavaScriptAnalyzer, JavaAnalyzer, ArchitectureBuilder
from .utils.graph_generator import GraphGenerator
from .utils.mermaid_generator import MermaidGenerator
from .utils.metrics_calculator import MetricsCalculator

@csrf_exempt
@require_http_methods(["POST"])
def project_upload(request):
    """Handle project file upload"""
    if 'file' not in request.FILES:
        return JsonResponse({'error': 'No file provided'}, status=400)
        
    uploaded_file = request.FILES['file']
    
    # Save file to temporary location
    file_name = uploaded_file.name
    file_path = os.path.join(tempfile.gettempdir(), file_name)
    
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
            
    # Create project record
    project = Project.objects.create(
        name=file_name,
        file_path=file_path,
        uploaded_by=request.user if request.user.is_authenticated else None
    )
    
    return JsonResponse({
        'project_id': project.id,
        'message': 'File uploaded successfully'
    })

def analyze_code(request, project_id):
    """Trigger code analysis for a project"""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
        
    # Update project status
    project.status = 'analyzing'
    project.save()
    
    try:
        # Handle file extraction
        file_handler = FileHandler(project.file_path)
        extracted_files = file_handler.extract_files()
        language_files = file_handler.organize_by_language()
        project_structure = file_handler.get_project_structure()
        
        # Perform analysis for each language
        analysis_results = {
            'project_structure': project_structure,
            'file_analysis': [],
            'dependencies': [],
            'call_graph': {}
        }
        
        # Analyze Python files
        for file_info in language_files.get('python', []):
            try:
                analyzer = PythonAnalyzer(file_info['path'])
                result = analyzer.analyze()
                
                analysis_results['file_analysis'].append({
                    'file_path': file_info['name'],
                    'language': 'python',
                    'analysis': result
                })
                
                # Collect dependencies
                for imp in result.get('imports', []):
                    analysis_results['dependencies'].append({
                        'source': file_info['name'],
                        'target': imp['module'],
                        'type': 'import'
                    })
                    
                # Merge call graphs
                call_graph = result.get('call_graph', {})
                for caller, callees in call_graph.items():
                    if caller not in analysis_results['call_graph']:
                        analysis_results['call_graph'][caller] = []
                    analysis_results['call_graph'][caller].extend(callees)
                    
            except Exception as e:
                print(f"Error analyzing {file_info['name']}: {str(e)}")
                
        # Store analysis results in database
        AnalysisResult.objects.create(
            project=project,
            analysis_type='complete',
            result_data=analysis_results
        )
        
        # Build architecture
        architecture_builder = ArchitectureBuilder(analysis_results)
        architecture_pattern = architecture_builder.detect_architecture_pattern()
        component_diagram = architecture_builder.generate_component_diagram()
        dependency_graph = architecture_builder.build_dependency_graph()
        
        # Store architecture results
        AnalysisResult.objects.create(
            project=project,
            analysis_type='architecture',
            result_data={
                'pattern': architecture_pattern,
                'component_diagram': component_diagram,
                'dependency_graph': dependency_graph
            }
        )
        
        # Update project status
        project.status = 'completed'
        project.save()
        
        return JsonResponse({
            'project_id': project.id,
            'message': 'Analysis completed successfully',
            'architecture_pattern': architecture_pattern
        })
        
    except Exception as e:
        project.status = 'failed'
        project.save()
        return JsonResponse({'error': str(e)}, status=500)

def diagram_generation(request, project_id, diagram_type):
    """Generate diagram data for visualization"""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
        
    try:
        # Get analysis results
        analysis_result = AnalysisResult.objects.get(
            project=project,
            analysis_type='architecture'
        )
        
        diagram_data = analysis_result.result_data
        
        if diagram_type == 'component':
            data = diagram_data.get('component_diagram', {})
        elif diagram_type == 'dependency':
            data = diagram_data.get('dependency_graph', {})
        else:
            return JsonResponse({'error': 'Invalid diagram type'}, status=400)
            
        # Convert to visualization format
        graph_generator = GraphGenerator(data)
        
        if request.GET.get('format') == 'cytoscape':
            formatted_data = graph_generator.to_cytoscape_format()
        elif request.GET.get('format') == 'd3':
            formatted_data = graph_generator.to_d3_format()
        else:
            formatted_data = data
            
        return JsonResponse(formatted_data)
        
    except AnalysisResult.DoesNotExist:
        return JsonResponse({'error': 'Analysis not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def export_diagram(request, project_id, diagram_type):
    """Export diagram in various formats"""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
        
    try:
        # Get analysis results
        analysis_result = AnalysisResult.objects.get(
            project=project,
            analysis_type='architecture'
        )
        
        diagram_data = analysis_result.result_data
        
        if diagram_type == 'component':
            data = diagram_data.get('component_diagram', {})
        elif diagram_type == 'dependency':
            data = diagram_data.get('dependency_graph', {})
        else:
            return JsonResponse({'error': 'Invalid diagram type'}, status=400)
            
        # Generate Mermaid code
        mermaid_generator = MermaidGenerator(data)
        mermaid_code = mermaid_generator.generate_component_diagram()
        
        # Return as text file
        response = HttpResponse(mermaid_code, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{project.name}_{diagram_type}_diagram.mmd"'
        return response
        
    except AnalysisResult.DoesNotExist:
        return JsonResponse({'error': 'Analysis not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def project_list(request):
    """List all analyzed projects"""
    projects = Project.objects.all().order_by('-uploaded_at')
    
    project_data = []
    for project in projects:
        project_data.append({
            'id': project.id,
            'name': project.name,
            'description': project.description,
            'uploaded_at': project.uploaded_at,
            'status': project.status
        })
        
    return JsonResponse({'projects': project_data})

def metrics_view(request, project_id):
    """Get code metrics and insights"""
    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return JsonResponse({'error': 'Project not found'}, status=404)
        
    try:
        # Get analysis results
        analysis_result = AnalysisResult.objects.get(
            project=project,
            analysis_type='complete'
        )
        
        # Calculate metrics
        metrics_calculator = MetricsCalculator(analysis_result.result_data)
        metrics_report = metrics_calculator.generate_report()
        
        return JsonResponse(metrics_report)
        
    except AnalysisResult.DoesNotExist:
        return JsonResponse({'error': 'Analysis not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)