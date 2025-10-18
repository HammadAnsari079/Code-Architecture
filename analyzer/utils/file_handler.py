import os
import zipfile
import tarfile
import tempfile
from typing import List, Dict, Tuple

class FileHandler:
    """Handle file extraction and organization"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.extracted_files = []
        self.language_files = {}
        
    def extract_files(self) -> List[Dict[str, str]]:
        """Extract files from zip or tar.gz archives"""
        if self.file_path.endswith('.zip'):
            return self._extract_zip()
        elif self.file_path.endswith('.tar.gz') or self.file_path.endswith('.tgz'):
            return self._extract_tar()
        else:
            # Single file
            return self._handle_single_file()
            
    def _extract_zip(self) -> List[Dict[str, str]]:
        """Extract files from ZIP archive"""
        extracted = []
        with zipfile.ZipFile(self.file_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if not file_info.is_dir():
                    # Extract to temporary location
                    zip_ref.extract(file_info, tempfile.gettempdir())
                    file_path = os.path.join(tempfile.gettempdir(), file_info.filename)
                    extracted.append({
                        'name': file_info.filename,
                        'path': file_path,
                        'size': str(file_info.file_size)
                    })
        self.extracted_files = extracted
        return extracted
        
    def _extract_tar(self) -> List[Dict[str, str]]:
        """Extract files from TAR.GZ archive"""
        extracted = []
        with tarfile.open(self.file_path, 'r:gz') as tar_ref:
            for member in tar_ref.getmembers():
                if member.isfile():
                    # Extract to temporary location
                    tar_ref.extract(member, tempfile.gettempdir())
                    file_path = os.path.join(tempfile.gettempdir(), member.name)
                    extracted.append({
                        'name': member.name,
                        'path': file_path,
                        'size': str(member.size)
                    })
        self.extracted_files = extracted
        return extracted
        
    def _handle_single_file(self) -> List[Dict[str, str]]:
        """Handle single file upload"""
        file_name = os.path.basename(self.file_path)
        return [{
            'name': file_name,
            'path': self.file_path,
            'size': str(os.path.getsize(self.file_path))
        }]
        
    def organize_by_language(self) -> Dict[str, List[Dict[str, str]]]:
        """Organize extracted files by programming language"""
        language_files = {
            'python': [],
            'javascript': [],
            'java': [],
            'other': []
        }
        
        for file_info in self.extracted_files:
            file_path = file_info['path']
            language = self._detect_language(file_path)
            
            if language == 'python':
                language_files['python'].append(file_info)
            elif language == 'javascript':
                language_files['javascript'].append(file_info)
            elif language == 'java':
                language_files['java'].append(file_info)
            else:
                language_files['other'].append(file_info)
                
        self.language_files = language_files
        return language_files
        
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language of a file"""
        try:
            # Check file extension
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.py':
                return 'python'
            elif ext in ['.js', '.jsx']:
                return 'javascript'
            elif ext in ['.java']:
                return 'java'
            else:
                # Try to detect by content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(1024)  # Read first 1KB
                    
                if 'def ' in content and 'import ' in content:
                    return 'python'
                elif 'function ' in content or 'var ' in content or 'let ' in content:
                    return 'javascript'
                elif 'public class ' in content or 'private ' in content:
                    return 'java'
                    
            return 'other'
        except Exception:
            # Fallback to extension-based detection
            ext = os.path.splitext(file_path)[1].lower()
            if ext == '.py':
                return 'python'
            elif ext in ['.js', '.jsx']:
                return 'javascript'
            elif ext == '.java':
                return 'java'
            else:
                return 'other'
                
    def get_project_structure(self) -> Dict[str, List[str]]:
        """Get directory structure of the project"""
        directories = set()
        files = []
        
        for file_info in self.extracted_files:
            file_name = file_info['name']
            dir_path = os.path.dirname(file_name)
            
            # Add all parent directories
            path_parts = dir_path.split('/')
            current_path = ""
            for part in path_parts:
                if part:
                    current_path = f"{current_path}/{part}" if current_path else part
                    directories.add(current_path)
                    
            files.append(file_name)
            
        return {
            'directories': list(directories),
            'files': files
        }