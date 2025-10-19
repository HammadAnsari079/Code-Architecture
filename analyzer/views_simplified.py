from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import os
import json
import zipfile
import tempfile
from .models import Project, AnalysisResult, CodeFile, Dependency, Component
from .utils.file_processor import FileProcessor
from .utils.analyzer import EnhancedPythonAnalyzer, DatabaseSchemaExtractor, ProjectAnalyzer
from .utils.graph_generator import GraphGenerator

def simple_upload_view(request):
    """Simple upload page view"""
    return render(request, 'simple_upload.html')

def analysis_results_view(request, project_id):
    """View for displaying analysis results"""
    context = {
        'project_id': project_id,
        'project_name': f'Project {project_id}'
    }
    return render(request, 'analysis_results.html', context)

@csrf_exempt
def process_files_view(request):
    """Handle file uploads and processing"""
    if request.method == 'POST':
        try:
            # Handle file uploads
            files = request.FILES.getlist('files')
            action = request.POST.get('action', 'analyze')
            
            if not files:
                return JsonResponse({'status': 'error', 'message': 'No files provided'})
            
            # Process files using FileProcessor
            processor = FileProcessor()
            processed_files = processor.process_files(files)
            
            # Filter to get only code files
            code_files = processor.get_code_files(processed_files)
            
            # Perform analysis on code files
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
                except Exception as e:
                    print(f"Error analyzing {file_info['name']}: {str(e)}")
            
            # Create a simple project representation
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
                'redirect_url': f'/simple/results/{project_data["id"]}/'
            })
        except Exception as e:
            print(f"Upload error: {str(e)}")
            return JsonResponse({'status': 'error', 'message': f'Upload failed: {str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

def flowchart_data_view(request, project_id):
    """Generate flowchart data for visualization"""
    try:
        # Create a flowchart with logical horizontal branching for options
        
        nodes = [
            # Step 1: User Interaction
            {"id": "start", "name": "Start: User Uploads Code", "type": "function"},
            {"id": "receive", "name": "System Receives Files", "type": "function"},
            
            # Step 2: File Processing Branch
            {"id": "process_branch", "name": "Process Files", "type": "function"},
            {"id": "extract", "name": "Extract Files", "type": "function"},
            {"id": "organize", "name": "Organize Structure", "type": "function"},
            
            # Step 3: Analysis Options (Horizontal branch)
            {"id": "analyze_options", "name": "Analysis Options", "type": "function"},
            {"id": "syntax_option", "name": "Syntax Analysis", "type": "function"},
            {"id": "component_option", "name": "Component Analysis", "type": "function"},
            {"id": "dependency_option", "name": "Dependency Analysis", "type": "function"},
            
            # Syntax Analysis Path
            {"id": "parse_syntax", "name": "Parse Code Syntax", "type": "function"},
            {"id": "validate_syntax", "name": "Validate Syntax", "type": "function"},
            
            # Component Analysis Path
            {"id": "find_components", "name": "Find Components", "type": "function"},
            {"id": "identify_functions", "name": "Identify Functions", "type": "function"},
            {"id": "identify_classes", "name": "Identify Classes", "type": "function"},
            
            # Dependency Analysis Path
            {"id": "map_dependencies", "name": "Map Dependencies", "type": "function"},
            {"id": "trace_calls", "name": "Trace Function Calls", "type": "function"},
            {"id": "find_imports", "name": "Find Import Statements", "type": "function"},
            
            # Step 4: Data Storage (Converge back)
            {"id": "store_data", "name": "Store Analysis Data", "type": "function"},
            {"id": "save_project", "name": "Save Project Info", "type": "function"},
            {"id": "save_files", "name": "Save Code Files", "type": "function"},
            {"id": "save_components", "name": "Save Components", "type": "function"},
            {"id": "save_dependencies", "name": "Save Dependencies", "type": "function"},
            
            # Step 5: Visualization Generation
            {"id": "generate_viz", "name": "Generate Visualizations", "type": "function"},
            {"id": "build_graph", "name": "Build Graph Structure", "type": "function"},
            {"id": "create_layout", "name": "Create Layout", "type": "function"},
            
            # Step 6: User Presentation
            {"id": "present", "name": "Present Results", "type": "function"},
            {"id": "render_flow", "name": "Render Flow Chart", "type": "function"},
            {"id": "render_db", "name": "Render Database", "type": "function"},
            {"id": "display", "name": "Display to User", "type": "function"},
            
            # Data entities
            {"id": "user_data", "name": "User Data", "type": "database"},
            {"id": "project_data", "name": "Project Data", "type": "database"},
            {"id": "file_data", "name": "File Data", "type": "database"},
            {"id": "component_data", "name": "Component Data", "type": "database"},
            {"id": "dependency_data", "name": "Dependency Data", "type": "database"},
        ]
        
        links = [
            # Linear flow
            {"source": "start", "target": "receive"},
            {"source": "receive", "target": "process_branch"},
            {"source": "process_branch", "target": "extract"},
            {"source": "extract", "target": "organize"},
            {"source": "organize", "target": "analyze_options"},
            
            # Horizontal branching for analysis options
            {"source": "analyze_options", "target": "syntax_option"},
            {"source": "analyze_options", "target": "component_option"},
            {"source": "analyze_options", "target": "dependency_option"},
            
            # Syntax analysis path
            {"source": "syntax_option", "target": "parse_syntax"},
            {"source": "parse_syntax", "target": "validate_syntax"},
            
            # Component analysis path
            {"source": "component_option", "target": "find_components"},
            {"source": "find_components", "target": "identify_functions"},
            {"source": "find_components", "target": "identify_classes"},
            
            # Dependency analysis path
            {"source": "dependency_option", "target": "map_dependencies"},
            {"source": "map_dependencies", "target": "trace_calls"},
            {"source": "map_dependencies", "target": "find_imports"},
            
            # Converge back to data storage
            {"source": "validate_syntax", "target": "store_data"},
            {"source": "identify_functions", "target": "store_data"},
            {"source": "identify_classes", "target": "store_data"},
            {"source": "trace_calls", "target": "store_data"},
            {"source": "find_imports", "target": "store_data"},
            
            # Data storage
            {"source": "store_data", "target": "save_project"},
            {"source": "store_data", "target": "save_files"},
            {"source": "store_data", "target": "save_components"},
            {"source": "store_data", "target": "save_dependencies"},
            
            # Data relationships
            {"source": "save_project", "target": "project_data"},
            {"source": "save_files", "target": "file_data"},
            {"source": "save_components", "target": "component_data"},
            {"source": "save_dependencies", "target": "dependency_data"},
            {"source": "project_data", "target": "user_data"},
            
            # Visualization generation
            {"source": "store_data", "target": "generate_viz"},
            {"source": "generate_viz", "target": "build_graph"},
            {"source": "build_graph", "target": "create_layout"},
            
            # User presentation
            {"source": "create_layout", "target": "present"},
            {"source": "present", "target": "render_flow"},
            {"source": "present", "target": "render_db"},
            {"source": "render_flow", "target": "display"},
            {"source": "render_db", "target": "display"},
        ]
        
        graph_data = {
            "nodes": nodes,
            "links": links
        }
        
        return JsonResponse({
            'status': 'success',
            'graph_data': graph_data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to generate flowchart: {str(e)}'
        })

def database_data_view(request, project_id):
    """Generate database relationship data for visualization"""
    try:
        # Create a procedural database diagram showing the data flow and relationships
        
        nodes = [
            {
                "id": "user", 
                "name": "User Accounts", 
                "fields": [
                    "User ID (Primary Key)",
                    "Username (Unique)",
                    "Email Address",
                    "Password (Hashed)",
                    "First Name",
                    "Last Name",
                    "Account Created",
                    "Last Login"
                ]
            },
            {
                "id": "project", 
                "name": "Code Projects", 
                "fields": [
                    "Project ID (Primary Key)",
                    "Project Name",
                    "Description",
                    "Upload Date",
                    "Owner (Foreign Key)",
                    "Processing Status",
                    "Storage Path"
                ]
            },
            {
                "id": "analysis_result", 
                "name": "Analysis Results", 
                "fields": [
                    "Result ID (Primary Key)",
                    "Project (Foreign Key)",
                    "Analysis Type",
                    "Result Data (JSON)",
                    "Creation Date"
                ]
            },
            {
                "id": "code_file", 
                "name": "Code Files", 
                "fields": [
                    "File ID (Primary Key)",
                    "Project (Foreign Key)",
                    "File Path",
                    "Programming Language",
                    "File Size (Bytes)",
                    "File Content",
                    "Upload Date"
                ]
            },
            {
                "id": "dependency", 
                "name": "Code Dependencies", 
                "fields": [
                    "Dependency ID (Primary Key)",
                    "Project (Foreign Key)",
                    "Source Module",
                    "Target Module",
                    "Dependency Type",
                    "Reference Line"
                ]
            },
            {
                "id": "component", 
                "name": "Code Components", 
                "fields": [
                    "Component ID (Primary Key)",
                    "Project (Foreign Key)",
                    "Component Name",
                    "Component Type",
                    "File Location",
                    "Line Number",
                    "Relationships (JSON)"
                ]
            }
        ]
        
        links = [
            {
                "source": "project", 
                "target": "user", 
                "relationship": "Ownership", 
                "cardinality": "Many-to-One"
            },
            {
                "source": "analysis_result", 
                "target": "project", 
                "relationship": "Analysis", 
                "cardinality": "Many-to-One"
            },
            {
                "source": "code_file", 
                "target": "project", 
                "relationship": "Contains", 
                "cardinality": "Many-to-One"
            },
            {
                "source": "dependency", 
                "target": "project", 
                "relationship": "Tracking", 
                "cardinality": "Many-to-One"
            },
            {
                "source": "component", 
                "target": "project", 
                "relationship": "Belongs To", 
                "cardinality": "Many-to-One"
            },
            {
                "source": "dependency", 
                "target": "code_file", 
                "relationship": "Source File", 
                "cardinality": "Many-to-One"
            },
            {
                "source": "component", 
                "target": "code_file", 
                "relationship": "Located In", 
                "cardinality": "Many-to-One"
            },
            {
                "source": "analysis_result", 
                "target": "component", 
                "relationship": "Component Results", 
                "cardinality": "One-to-Many"
            }
        ]
        
        graph_data = {
            "nodes": nodes,
            "links": links
        }
        
        return JsonResponse({
            'status': 'success',
            'graph_data': graph_data
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'Failed to generate database diagram: {str(e)}'
        })
