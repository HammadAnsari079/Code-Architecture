import os
import tempfile
import zipfile
import tarfile
from typing import List, Dict, Any

class FileProcessor:
    """Handle processing of various file types including folders and archives"""
    
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    def process_files(self, files) -> List[Dict[str, Any]]:
        """Process uploaded files and extract code files"""
        processed_files = []
        
        for file in files:
            filename = os.path.basename(file.name)
            file_path = os.path.join(self.temp_dir, filename)
            
            # Save the file
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            # Process based on file type
            if self._is_archive(filename):
                extracted_files = self._extract_archive(file_path)
                processed_files.extend(extracted_files)
            else:
                # Regular file
                processed_files.append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'type': self._get_file_type(filename)
                })
                
        return processed_files
    
    def _is_archive(self, filename: str) -> bool:
        """Check if file is an archive"""
        return filename.endswith(('.zip', '.tar.gz', '.tgz'))
    
    def _extract_archive(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract files from archive"""
        extracted_files = []
        archive_dir = os.path.join(self.temp_dir, 'extracted')
        os.makedirs(archive_dir, exist_ok=True)
        
        try:
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(archive_dir)
                    for file_info in zip_ref.filelist:
                        if not file_info.is_dir():
                            extracted_path = os.path.join(archive_dir, file_info.filename)
                            extracted_files.append({
                                'name': file_info.filename,
                                'path': extracted_path,
                                'size': file_info.file_size,
                                'type': self._get_file_type(file_info.filename)
                            })
                            
            elif file_path.endswith(('.tar.gz', '.tgz')):
                with tarfile.open(file_path, 'r:gz') as tar_ref:
                    tar_ref.extractall(archive_dir)
                    for member in tar_ref.getmembers():
                        if member.isfile():
                            extracted_path = os.path.join(archive_dir, member.name)
                            extracted_files.append({
                                'name': member.name,
                                'path': extracted_path,
                                'size': member.size,
                                'type': self._get_file_type(member.name)
                            })
                            
        except Exception as e:
            print(f"Error extracting archive {file_path}: {str(e)}")
            
        return extracted_files
    
    def _get_file_type(self, filename: str) -> str:
        """Determine file type based on extension"""
        if filename.endswith('.py'):
            return 'python'
        elif filename.endswith('.js'):
            return 'javascript'
        elif filename.endswith('.java'):
            return 'java'
        elif filename.endswith('.html'):
            return 'html'
        elif filename.endswith('.css'):
            return 'css'
        else:
            return 'other'
    
    def get_code_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter and return only code files"""
        code_extensions = ['.py', '.js', '.java', '.jsx', '.ts', '.tsx']
        code_files = [f for f in files if any(f['name'].endswith(ext) for ext in code_extensions)]
        return code_files
    
    def cleanup(self):
        """Clean up temporary files"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Error cleaning up temp directory: {str(e)}")