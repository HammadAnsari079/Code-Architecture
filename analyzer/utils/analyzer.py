import ast
import json
import os
import zipfile
import tarfile
from typing import Dict, List, Any

class BaseAnalyzer:
    """Base class for all analyzers"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ""
        self.tree = None
        
    def read_file(self):
        """Read the file content"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
            
    def analyze(self) -> Dict[str, Any]:
        """Main analysis method to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement analyze method")


class PythonAnalyzer(BaseAnalyzer):
    """Analyzer for Python files using AST"""
    
    def __init__(self, file_path: str):
        super().__init__(file_path)
        self.imports = []
        self.classes = []
        self.functions = []
        self.call_graph = {}
        
    def parse_ast(self):
        """Parse the Python file using AST"""
        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            raise Exception(f"Syntax error in {self.file_path}: {str(e)}")
            
    def extract_imports(self) -> List[Dict[str, Any]]:
        """Extract all import statements"""
        imports = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        'module': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'type': 'import'
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'module': f"{module}.{alias.name}",
                        'from_module': module,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'type': 'import_from'
                    })
        self.imports = imports
        return imports
        
    def extract_classes(self) -> List[Dict[str, Any]]:
        """Extract all class definitions"""
        classes = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'methods': [],
                    'bases': [ast.unparse(base) for base in node.bases] if hasattr(ast, 'unparse') else [],
                    'docstring': ast.get_docstring(node)
                }
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            'name': item.name,
                            'line': item.lineno,
                            'args': [arg.arg for arg in item.args.args],
                            'docstring': ast.get_docstring(item)
                        }
                        class_info['methods'].append(method_info)
                        
                classes.append(class_info)
                
        self.classes = classes
        return classes
        
    def extract_functions(self) -> List[Dict[str, Any]]:
        """Extract all function definitions (non-method)"""
        functions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and not isinstance(node.parent, ast.ClassDef):
                func_info = {
                    'name': node.name,
                    'line': node.lineno,
                    'args': [arg.arg for arg in node.args.args],
                    'docstring': ast.get_docstring(node),
                    'returns': ast.unparse(node.returns) if node.returns and hasattr(ast, 'unparse') else None
                }
                functions.append(func_info)
                
        self.functions = functions
        return functions
        
    def extract_function_calls(self) -> Dict[str, List[str]]:
        """Extract function calls to build call graph"""
        call_graph = {}
        
        class CallVisitor(ast.NodeVisitor):
            def __init__(self):
                self.calls = {}
                
            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                else:
                    func_name = "unknown"
                    
                # Get the context (which function this call is in)
                parent_func = self.get_parent_function(node)
                if parent_func:
                    if parent_func not in self.calls:
                        self.calls[parent_func] = []
                    self.calls[parent_func].append(func_name)
                    
                self.generic_visit(node)
                
            def get_parent_function(self, node):
                """Get the name of the function containing this node"""
                while hasattr(node, 'parent'):
                    node = node.parent
                    if isinstance(node, ast.FunctionDef):
                        return node.name
                return None
                
        # Add parent references to nodes
        for node in ast.walk(self.tree):
            for child in ast.iter_child_nodes(node):
                child.parent = node
                
        visitor = CallVisitor()
        visitor.visit(self.tree)
        self.call_graph = visitor.calls
        return visitor.calls
        
    def analyze(self) -> Dict[str, Any]:
        """Perform complete analysis of the Python file"""
        self.read_file()
        self.parse_ast()
        
        return {
            'imports': self.extract_imports(),
            'classes': self.extract_classes(),
            'functions': self.extract_functions(),
            'call_graph': self.extract_function_calls()
        }


class JavaScriptAnalyzer(BaseAnalyzer):
    """Analyzer for JavaScript files using esprima"""
    
    def __init__(self, file_path: str):
        super().__init__(file_path)
        # We'll implement this when we have esprima properly installed
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze JavaScript file"""
        self.read_file()
        # Placeholder implementation
        return {
            'imports': [],
            'classes': [],
            'functions': [],
            'call_graph': {}
        }


class JavaAnalyzer(BaseAnalyzer):
    """Analyzer for Java files using javalang"""
    
    def __init__(self, file_path: str):
        super().__init__(file_path)
        # We'll implement this when we have javalang properly installed
        
    def analyze(self) -> Dict[str, Any]:
        """Analyze Java file"""
        self.read_file()
        # Placeholder implementation
        return {
            'imports': [],
            'classes': [],
            'functions': [],
            'call_graph': {}
        }


class ArchitectureBuilder:
    """Build architecture diagrams and detect patterns"""
    
    def __init__(self, analysis_results: Dict[str, Any]):
        self.analysis_results = analysis_results
        
    def detect_architecture_pattern(self) -> str:
        """Detect the architecture pattern of the codebase"""
        # Simple heuristic-based detection
        files = self.analysis_results.get('files', [])
        file_names = [f.get('name', '') for f in files]
        
        # Check for Django MVT pattern
        if 'models.py' in file_names and 'views.py' in file_names and 'urls.py' in file_names:
            return 'Django MVT'
            
        # Check for MVC pattern
        if 'models' in file_names and 'controllers' in file_names and 'views' in file_names:
            return 'MVC'
            
        # Check for microservices pattern
        if 'docker-compose.yml' in file_names or 'kubernetes' in str(file_names):
            return 'Microservices'
            
        # Check for layered architecture
        directories = self.analysis_results.get('directories', [])
        if 'controllers' in directories and 'services' in directories and 'repositories' in directories:
            return 'Layered Architecture'
            
        return 'Unknown'
        
    def generate_component_diagram(self) -> Dict[str, Any]:
        """Generate component diagram data for visualization"""
        nodes = []
        edges = []
        
        # Create nodes for classes and functions
        for file_result in self.analysis_results.get('file_analysis', []):
            file_path = file_result.get('file_path', '')
            classes = file_result.get('analysis', {}).get('classes', [])
            functions = file_result.get('analysis', {}).get('functions', [])
            
            # Add file as a node
            file_node = {
                'id': f"file_{file_path}",
                'label': os.path.basename(file_path),
                'type': 'file'
            }
            nodes.append(file_node)
            
            # Add classes as nodes
            for cls in classes:
                class_node = {
                    'id': f"class_{file_path}_{cls['name']}",
                    'label': cls['name'],
                    'type': 'class',
                    'parent': f"file_{file_path}"
                }
                nodes.append(class_node)
                
                # Add edges from file to class
                edges.append({
                    'source': f"file_{file_path}",
                    'target': f"class_{file_path}_{cls['name']}",
                    'type': 'contains'
                })
                
                # Add methods as nodes
                for method in cls.get('methods', []):
                    method_node = {
                        'id': f"method_{file_path}_{cls['name']}_{method['name']}",
                        'label': method['name'],
                        'type': 'method',
                        'parent': f"class_{file_path}_{cls['name']}"
                    }
                    nodes.append(method_node)
                    
                    # Add edges from class to method
                    edges.append({
                        'source': f"class_{file_path}_{cls['name']}",
                        'target': f"method_{file_path}_{cls['name']}_{method['name']}",
                        'type': 'contains'
                    })
                    
            # Add functions as nodes
            for func in functions:
                func_node = {
                    'id': f"function_{file_path}_{func['name']}",
                    'label': func['name'],
                    'type': 'function',
                    'parent': f"file_{file_path}"
                }
                nodes.append(func_node)
                
                # Add edges from file to function
                edges.append({
                    'source': f"file_{file_path}",
                    'target': f"function_{file_path}_{func['name']}",
                    'type': 'contains'
                })
                
        # Create edges for imports/dependencies
        dependencies = self.analysis_results.get('dependencies', [])
        for dep in dependencies:
            edges.append({
                'source': f"file_{dep['source']}",
                'target': f"file_{dep['target']}",
                'type': 'depends'
            })
            
        return {
            'nodes': nodes,
            'edges': edges
        }
        
    def build_dependency_graph(self) -> Dict[str, Any]:
        """Build dependency graph for visualization"""
        nodes = []
        edges = []
        
        # Collect all unique modules/files
        modules = set()
        dependencies = self.analysis_results.get('dependencies', [])
        
        for dep in dependencies:
            modules.add(dep['source'])
            modules.add(dep['target'])
            
        # Create nodes
        for module in modules:
            nodes.append({
                'id': module,
                'label': module,
                'type': 'module'
            })
            
        # Create edges
        for dep in dependencies:
            edges.append({
                'source': dep['source'],
                'target': dep['target'],
                'type': dep.get('type', 'dependency')
            })
            
        return {
            'nodes': nodes,
            'edges': edges
        }

# Monkey patch AST nodes to add parent references
def add_parent_references():
    """Add parent references to AST nodes for traversal"""
    def on_enter(node, parent):
        node.parent = parent
        
    def visit_node(node, parent=None):
        on_enter(node, parent)
        for child in ast.iter_child_nodes(node):
            visit_node(child, node)
            
    return visit_node