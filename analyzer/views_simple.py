from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .utils.file_processor import FileProcessor
from .utils.analyzer import EnhancedPythonAnalyzer


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