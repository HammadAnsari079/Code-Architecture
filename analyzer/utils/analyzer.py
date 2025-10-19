import ast
import json
import os
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from collections import defaultdict


class ControlFlowGraphBuilder:
    """Builds accurate control flow graphs for functions"""
    
    def __init__(self, function_node: ast.FunctionDef, file_path: str, file_content: str):
        self.function_node = function_node
        self.file_path = file_path
        self.file_content = file_content
        self.lines = file_content.split('\n')
        self.nodes = []
        self.edges = []
        self.node_counter = 0
        self.complexity = 1  # Base complexity
        
    def build(self) -> Dict[str, Any]:
        """Build complete CFG for the function"""
        # Create START node
        start_id = self.create_node(
            node_type='start',
            label=f"START: {self.function_node.name}()",
            line=self.function_node.lineno,
            code_snippet=f"def {self.function_node.name}({self._format_args()}):"
        )
        
        # Process function body
        last_nodes = [start_id]
        for stmt in self.function_node.body:
            last_nodes = self.visit_statement(stmt, last_nodes)
        
        # Create END node
        end_id = self.create_node(
            node_type='end',
            label='END',
            line=self.function_node.end_lineno or self.function_node.lineno,
            code_snippet='return'
        )
        
        # Connect last nodes to END
        for node_id in last_nodes:
            self.create_edge(node_id, end_id)
        
        return {
            'function_name': self.function_node.name,
            'file_path': self.file_path,
            'line_start': self.function_node.lineno,
            'line_end': self.function_node.end_lineno,
            'nodes': self.nodes,
            'edges': self.edges,
            'metrics': {
                'cyclomatic_complexity': self.complexity,
                'num_nodes': len(self.nodes),
                'num_decision_points': sum(1 for n in self.nodes if n['type'] == 'decision')
            }
        }
    
    def create_node(self, node_type: str, label: str, line: int, 
                    code_snippet: str, column: int = 0, ast_node_type: str = None) -> str:
        """Create a flowchart node"""
        node_id = f"node_{self.node_counter}"
        self.node_counter += 1
        
        # Get surrounding context (3 lines before and after)
        context_lines = []
        for i in range(max(0, line - 4), min(len(self.lines), line + 3)):
            context_lines.append(self.lines[i])
        
        node = {
            'id': node_id,
            'type': node_type,
            'label': label,
            'code_snippet': code_snippet.strip(),
            'ast_node_type': ast_node_type or node_type,
            'file_location': {
                'file': os.path.basename(self.file_path),
                'full_path': self.file_path,
                'line': line,
                'column': column
            },
            'context': {
                'function_name': self.function_node.name,
                'surrounding_lines': context_lines
            }
        }
        
        self.nodes.append(node)
        return node_id
    
    def create_edge(self, source: str, target: str, label: str = '') -> None:
        """Create an edge between nodes"""
        self.edges.append({
            'source': source,
            'target': target,
            'label': label,
            'type': 'conditional' if label else 'sequential'
        })
    
    def visit_statement(self, stmt: ast.AST, entry_nodes: List[str]) -> List[str]:
        """Visit a statement and return exit nodes"""
        if isinstance(stmt, ast.If):
            return self.visit_If(stmt, entry_nodes)
        elif isinstance(stmt, ast.While):
            return self.visit_While(stmt, entry_nodes)
        elif isinstance(stmt, ast.For):
            return self.visit_For(stmt, entry_nodes)
        elif isinstance(stmt, ast.Return):
            return self.visit_Return(stmt, entry_nodes)
        elif isinstance(stmt, ast.Assign):
            return self.visit_Assign(stmt, entry_nodes)
        elif isinstance(stmt, ast.Expr):
            return self.visit_Expr(stmt, entry_nodes)
        elif isinstance(stmt, ast.Try):
            return self.visit_Try(stmt, entry_nodes)
        else:
            # Generic statement
            node_id = self.create_node(
                node_type='process',
                label=self._get_statement_label(stmt),
                line=stmt.lineno,
                code_snippet=ast.unparse(stmt) if hasattr(ast, 'unparse') else str(stmt),
                ast_node_type=type(stmt).__name__
            )
            for entry in entry_nodes:
                self.create_edge(entry, node_id)
            return [node_id]
    
    def visit_If(self, node: ast.If, entry_nodes: List[str]) -> List[str]:
        """Handle if/elif/else statements"""
        self.complexity += 1  # Each decision point adds 1
        
        # Create decision diamond
        condition = ast.unparse(node.test) if hasattr(ast, 'unparse') else 'condition'
        decision_id = self.create_node(
            node_type='decision',
            label=f"IF {condition}?",
            line=node.lineno,
            code_snippet=f"if {condition}:",
            ast_node_type='If'
        )
        
        # Connect entry nodes to decision
        for entry in entry_nodes:
            self.create_edge(entry, decision_id)
        
        # Process TRUE branch (if body)
        true_exits = [decision_id]
        for stmt in node.body:
            true_exits = self.visit_statement(stmt, true_exits)
        
        # Connect decision to first statement in TRUE branch with YES label
        if node.body:
            first_true_stmt = node.body[0]
            true_node_id = [n['id'] for n in self.nodes 
                           if n['file_location']['line'] == first_true_stmt.lineno]
            if true_node_id:
                self.create_edge(decision_id, true_node_id[0], 'YES')
        
        # Process FALSE branch (else/elif)
        false_exits = []
        if node.orelse:
            false_exits = [decision_id]
            for stmt in node.orelse:
                false_exits = self.visit_statement(stmt, false_exits)
            
            # Connect decision to first statement in FALSE branch with NO label
            first_false_stmt = node.orelse[0]
            false_node_id = [n['id'] for n in self.nodes 
                            if n['file_location']['line'] == first_false_stmt.lineno]
            if false_node_id:
                self.create_edge(decision_id, false_node_id[0], 'NO')
        else:
            # No else branch, decision exits directly
            false_exits = [decision_id]
        
        # Return both exits
        return true_exits + false_exits
    
    def visit_While(self, node: ast.While, entry_nodes: List[str]) -> List[str]:
        """Handle while loops"""
        self.complexity += 1
        
        condition = ast.unparse(node.test) if hasattr(ast, 'unparse') else 'condition'
        decision_id = self.create_node(
            node_type='decision',
            label=f"WHILE {condition}?",
            line=node.lineno,
            code_snippet=f"while {condition}:",
            ast_node_type='While'
        )
        
        for entry in entry_nodes:
            self.create_edge(entry, decision_id)
        
        # Process loop body
        body_exits = [decision_id]
        for stmt in node.body:
            body_exits = self.visit_statement(stmt, body_exits)
        
        # Create back-edge from loop body to condition
        for exit_node in body_exits:
            self.create_edge(exit_node, decision_id, 'LOOP')
        
        # Exit loop (condition false)
        return [decision_id]
    
    def visit_For(self, node: ast.For, entry_nodes: List[str]) -> List[str]:
        """Handle for loops"""
        self.complexity += 1
        
        target = ast.unparse(node.target) if hasattr(ast, 'unparse') else 'item'
        iter_expr = ast.unparse(node.iter) if hasattr(ast, 'unparse') else 'iterable'
        
        decision_id = self.create_node(
            node_type='decision',
            label=f"FOR {target} in {iter_expr}",
            line=node.lineno,
            code_snippet=f"for {target} in {iter_expr}:",
            ast_node_type='For'
        )
        
        for entry in entry_nodes:
            self.create_edge(entry, decision_id)
        
        # Process loop body
        body_exits = [decision_id]
        for stmt in node.body:
            body_exits = self.visit_statement(stmt, body_exits)
        
        # Back-edge
        for exit_node in body_exits:
            self.create_edge(exit_node, decision_id, 'NEXT')
        
        return [decision_id]
    
    def visit_Return(self, node: ast.Return, entry_nodes: List[str]) -> List[str]:
        """Handle return statements"""
        return_value = ast.unparse(node.value) if node.value and hasattr(ast, 'unparse') else 'None'
        
        return_id = self.create_node(
            node_type='process',
            label=f"RETURN {return_value}",
            line=node.lineno,
            code_snippet=f"return {return_value}",
            ast_node_type='Return'
        )
        
        for entry in entry_nodes:
            self.create_edge(entry, return_id)
        
        return [return_id]
    
    def visit_Assign(self, node: ast.Assign, entry_nodes: List[str]) -> List[str]:
        """Handle assignment statements"""
        targets = ', '.join([ast.unparse(t) if hasattr(ast, 'unparse') else 'var' 
                            for t in node.targets])
        value = ast.unparse(node.value) if hasattr(ast, 'unparse') else 'value'
        
        assign_id = self.create_node(
            node_type='process',
            label=f"{targets} = {value}",
            line=node.lineno,
            code_snippet=f"{targets} = {value}",
            ast_node_type='Assign'
        )
        
        for entry in entry_nodes:
            self.create_edge(entry, assign_id)
        
        return [assign_id]
    
    def visit_Expr(self, node: ast.Expr, entry_nodes: List[str]) -> List[str]:
        """Handle expression statements (usually function calls)"""
        expr = ast.unparse(node.value) if hasattr(ast, 'unparse') else 'expression'
        
        expr_id = self.create_node(
            node_type='process',
            label=expr,
            line=node.lineno,
            code_snippet=expr,
            ast_node_type='Expr'
        )
        
        for entry in entry_nodes:
            self.create_edge(entry, expr_id)
        
        return [expr_id]
    
    def visit_Try(self, node: ast.Try, entry_nodes: List[str]) -> List[str]:
        """Handle try/except blocks"""
        self.complexity += len(node.handlers)
        
        # Try block
        try_exits = entry_nodes
        for stmt in node.body:
            try_exits = self.visit_statement(stmt, try_exits)
        
        all_exits = try_exits
        
        # Exception handlers
        for handler in node.handlers:
            handler_exits = entry_nodes  # Each handler starts from entry
            for stmt in handler.body:
                handler_exits = self.visit_statement(stmt, handler_exits)
            all_exits.extend(handler_exits)
        
        # Finally block
        if node.finalbody:
            for stmt in node.finalbody:
                all_exits = self.visit_statement(stmt, all_exits)
        
        return all_exits
    
    def _format_args(self) -> str:
        """Format function arguments"""
        args = []
        for arg in self.function_node.args.args:
            args.append(arg.arg)
        return ', '.join(args)
    
    def _get_statement_label(self, stmt: ast.AST) -> str:
        """Get human-readable label for statement"""
        if hasattr(ast, 'unparse'):
            label = ast.unparse(stmt)
            return label[:50] + '...' if len(label) > 50 else label
        return type(stmt).__name__


class DatabaseSchemaExtractor:
    """Extracts database schema from Django/SQLAlchemy models"""
    
    def __init__(self, file_path: str, file_content: str):
        self.file_path = file_path
        self.file_content = file_content
        self.tree = None
        self.tables = []
        self.relationships = []
        
    def extract(self) -> Dict[str, Any]:
        """Extract complete database schema"""
        try:
            self.tree = ast.parse(self.file_content)
        except SyntaxError:
            return {'tables': [], 'relationships': []}
        
        self.extract_django_models()
        return {
            'tables': self.tables,
            'relationships': self.relationships
        }
    
    def extract_django_models(self):
        """Extract Django model definitions"""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                # Check if it's a Django model (inherits from models.Model)
                is_model = any(
                    (isinstance(base, ast.Attribute) and base.attr == 'Model') or
                    (isinstance(base, ast.Name) and base.id == 'Model')
                    for base in node.bases
                )
                
                if is_model:
                    table_info = self.extract_model_fields(node)
                    if table_info:
                        self.tables.append(table_info)
    
    def extract_model_fields(self, class_node: ast.ClassDef) -> Dict[str, Any]:
        """Extract fields from a Django model class"""
        table = {
            'name': class_node.name,
            'fields': [],
            'file_location': {
                'file': os.path.basename(self.file_path),
                'full_path': self.file_path,
                'line': class_node.lineno
            }
        }
        
        for item in class_node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        field_name = target.id
                        field_info = self.analyze_field(field_name, item.value, item.lineno)
                        if field_info:
                            table['fields'].append(field_info)
                            
                            # Check for foreign key relationship
                            if field_info['is_foreign_key']:
                                self.relationships.append({
                                    'from_table': class_node.name,
                                    'from_field': field_name,
                                    'to_table': field_info['references']['table'],
                                    'to_field': 'id',
                                    'type': '1:N',
                                    'on_delete': field_info['references'].get('on_delete', 'CASCADE'),
                                    'file_location': {
                                        'file': os.path.basename(self.file_path),
                                        'full_path': self.file_path,
                                        'line': item.lineno
                                    }
                                })
        
        return table if table['fields'] else None
    
    def analyze_field(self, field_name: str, value_node: ast.AST, line: int) -> Optional[Dict[str, Any]]:
        """Analyze a model field to extract its properties"""
        if not isinstance(value_node, ast.Call):
            return None
        
        # Get field type
        field_type = self._get_field_type(value_node.func)
        if not field_type:
            return None
        
        field_info = {
            'name': field_name,
            'type': field_type,
            'constraints': [],
            'is_primary_key': False,
            'is_foreign_key': False,
            'is_unique': False,
            'file_location': {
                'file': os.path.basename(self.file_path),
                'full_path': self.file_path,
                'line': line
            }
        }
        
        # Check field properties from arguments
        for keyword in value_node.keywords:
            if keyword.arg == 'primary_key' and self._is_true(keyword.value):
                field_info['is_primary_key'] = True
                field_info['constraints'].append('PRIMARY KEY')
            elif keyword.arg == 'unique' and self._is_true(keyword.value):
                field_info['is_unique'] = True
                field_info['constraints'].append('UNIQUE')
        
        # Check for ForeignKey
        if 'ForeignKey' in field_type or 'OneToOneField' in field_type:
            field_info['is_foreign_key'] = True
            field_info['constraints'].append('FOREIGN KEY')
            
            # Extract referenced model
            if value_node.args:
                ref_model = self._extract_model_reference(value_node.args[0])
                on_delete = self._extract_on_delete(value_node)
                
                field_info['references'] = {
                    'table': ref_model,
                    'on_delete': on_delete
                }
        
        # Auto-detect primary key
        if field_name == 'id' and not field_info['is_primary_key']:
            field_info['is_primary_key'] = True
            field_info['constraints'].append('PRIMARY KEY')
        
        return field_info
    
    def _get_field_type(self, func_node: ast.AST) -> Optional[str]:
        """Extract field type from function call"""
        if isinstance(func_node, ast.Attribute):
            return func_node.attr
        elif isinstance(func_node, ast.Name):
            return func_node.id
        return None
    
    def _is_true(self, node: ast.AST) -> bool:
        """Check if node represents True"""
        return isinstance(node, ast.Constant) and node.value is True
    
    def _extract_model_reference(self, node: ast.AST) -> str:
        """Extract referenced model name from ForeignKey argument"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return 'Unknown'
    
    def _extract_on_delete(self, call_node: ast.Call) -> str:
        """Extract on_delete behavior from ForeignKey"""
        for keyword in call_node.keywords:
            if keyword.arg == 'on_delete':
                if isinstance(keyword.value, ast.Attribute):
                    return keyword.value.attr
        return 'CASCADE'


class EnhancedPythonAnalyzer:
    """Enhanced Python analyzer with CFG and database schema extraction"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ""
        self.tree = None
        self.imports = []
        self.classes = []
        self.functions = []
        self.call_graph = {}
        self.control_flow_graphs = []
        self.database_schema = None
        
    def read_file(self):
        """Read the file content"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
    
    def parse_ast(self):
        """Parse the Python file using AST"""
        try:
            self.tree = ast.parse(self.content)
            self._add_parent_references(self.tree)
        except SyntaxError as e:
            raise Exception(f"Syntax error in {self.file_path}: {str(e)}")
    
    def _add_parent_references(self, tree):
        """Add parent references to all AST nodes"""
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                child.parent = parent
    
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
                        'type': 'import',
                        'file': os.path.basename(self.file_path)
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append({
                        'module': f"{module}.{alias.name}" if module else alias.name,
                        'from_module': module,
                        'name': alias.name,
                        'alias': alias.asname,
                        'line': node.lineno,
                        'type': 'import_from',
                        'file': os.path.basename(self.file_path)
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
                    'end_line': node.end_lineno,
                    'methods': [],
                    'bases': [ast.unparse(base) if hasattr(ast, 'unparse') else 'Base' 
                             for base in node.bases],
                    'docstring': ast.get_docstring(node),
                    'file': os.path.basename(self.file_path),
                    'full_path': self.file_path
                }
                
                # Extract methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            'name': item.name,
                            'line': item.lineno,
                            'end_line': item.end_lineno,
                            'args': [arg.arg for arg in item.args.args],
                            'returns': ast.unparse(item.returns) if item.returns and hasattr(ast, 'unparse') else None,
                            'docstring': ast.get_docstring(item),
                            'is_async': isinstance(item, ast.AsyncFunctionDef),
                            'decorators': [ast.unparse(d) if hasattr(ast, 'unparse') else 'decorator' 
                                          for d in item.decorator_list]
                        }
                        class_info['methods'].append(method_info)
                
                classes.append(class_info)
        
        self.classes = classes
        return classes
    
    def extract_functions(self) -> List[Dict[str, Any]]:
        """Extract all standalone function definitions"""
        functions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                # Check if this is a standalone function (not a method)
                is_method = False
                current = node
                while hasattr(current, 'parent'):
                    if isinstance(current.parent, ast.ClassDef):
                        is_method = True
                        break
                    current = current.parent
                
                if not is_method:
                    func_info = {
                        'name': node.name,
                        'line': node.lineno,
                        'end_line': node.end_lineno,
                        'args': [arg.arg for arg in node.args.args],
                        'returns': ast.unparse(node.returns) if node.returns and hasattr(ast, 'unparse') else None,
                        'docstring': ast.get_docstring(node),
                        'is_async': isinstance(node, ast.AsyncFunctionDef),
                        'decorators': [ast.unparse(d) if hasattr(ast, 'unparse') else 'decorator' 
                                      for d in node.decorator_list],
                        'file': os.path.basename(self.file_path),
                        'full_path': self.file_path
                    }
                    functions.append(func_info)
        
        self.functions = functions
        return functions
    
    def build_control_flow_graphs(self):
        """Build CFG for all functions"""
        cfgs = []
        
        # Build CFG for standalone functions
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                try:
                    builder = ControlFlowGraphBuilder(node, self.file_path, self.content)
                    cfg = builder.build()
                    cfgs.append(cfg)
                except Exception as e:
                    print(f"Error building CFG for {node.name}: {e}")
        
        self.control_flow_graphs = cfgs
        return cfgs
    
    def extract_database_schema(self):
        """Extract database schema if file contains models"""
        extractor = DatabaseSchemaExtractor(self.file_path, self.content)
        self.database_schema = extractor.extract()
        return self.database_schema
    
    def analyze(self) -> Dict[str, Any]:
        """Perform complete analysis"""
        self.read_file()
        self.parse_ast()
        
        # Check if this is a models file
        is_models_file = 'models.py' in self.file_path or 'model' in self.file_path.lower()
        
        result = {
            'file_path': self.file_path,
            'file_name': os.path.basename(self.file_path),
            'imports': self.extract_imports(),
            'classes': self.extract_classes(),
            'functions': self.extract_functions(),
            'control_flow_graphs': self.build_control_flow_graphs(),
        }
        
        # Add database schema if it's a models file
        if is_models_file:
            result['database_schema'] = self.extract_database_schema()
        
        return result


class ProjectAnalyzer:
    """Analyzes entire project/codebase"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.files = []
        self.analysis_results = []
        self.all_tables = []
        self.all_relationships = []
        
    def scan_files(self, extensions: List[str] = ['.py']):
        """Scan project for files to analyze"""
        for root, dirs, files in os.walk(self.project_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in [
                'venv', 'env', '.venv', '__pycache__', '.git', 
                'node_modules', '.idea', '.vscode'
            ]]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    self.files.append(file_path)
        
        return self.files
    
    def analyze_project(self) -> Dict[str, Any]:
        """Analyze entire project"""
        self.scan_files()
        
        for file_path in self.files:
            try:
                analyzer = EnhancedPythonAnalyzer(file_path)
                result = analyzer.analyze()
                self.analysis_results.append(result)
                
                # Collect database schema
                if 'database_schema' in result and result['database_schema']:
                    self.all_tables.extend(result['database_schema'].get('tables', []))
                    self.all_relationships.extend(result['database_schema'].get('relationships', []))
                    
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
        
        return {
            'project_path': self.project_path,
            'total_files': len(self.files),
            'file_analysis': self.analysis_results,
            'database_schema': {
                'tables': self.all_tables,
                'relationships': self.all_relationships
            },
            'architecture_pattern': self.detect_architecture_pattern(),
            'summary': self.generate_summary()
        }
    
    def detect_architecture_pattern(self) -> str:
        """Detect architecture pattern"""
        file_names = [os.path.basename(f) for f in self.files]
        dir_names = list(set([os.path.basename(os.path.dirname(f)) for f in self.files]))
        
        # Django MVT
        if 'models.py' in file_names and 'views.py' in file_names and 'urls.py' in file_names:
            return 'Django MVT'
        
        # Flask
        if 'app.py' in file_names or '__init__.py' in file_names:
            if any('flask' in str(r.get('imports', [])) for r in self.analysis_results):
                return 'Flask Application'
        
        # FastAPI
        if any('fastapi' in str(r.get('imports', [])) for r in self.analysis_results):
            return 'FastAPI Application'
        
        # Layered Architecture
        if 'controllers' in dir_names and 'services' in dir_names and 'models' in dir_names:
            return 'Layered Architecture'
        
        return 'Custom Architecture'
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate project summary"""
        total_classes = sum(len(r.get('classes', [])) for r in self.analysis_results)
        total_functions = sum(len(r.get('functions', [])) for r in self.analysis_results)
        total_cfgs = sum(len(r.get('control_flow_graphs', [])) for r in self.analysis_results)
        
        avg_complexity = 0
        if total_cfgs > 0:
            complexities = []
            for r in self.analysis_results:
                for cfg in r.get('control_flow_graphs', []):
                    complexities.append(cfg['metrics']['cyclomatic_complexity'])
            avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        
        return {
            'total_files': len(self.files),
            'total_classes': total_classes,
            'total_functions': total_functions,
            'total_control_flow_graphs': total_cfgs,
            'average_cyclomatic_complexity': round(avg_complexity, 2),
            'total_database_tables': len(self.all_tables),
            'total_relationships': len(self.all_relationships)
        }


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Test with a single file
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        
        if os.path.isfile(file_path):
            print(f"Analyzing file: {file_path}\n")
            analyzer = EnhancedPythonAnalyzer(file_path)
            result = analyzer.analyze()
            
            print("=" * 80)
            print(f"FILE: {result['file_name']}")
            print("=" * 80)
            
            # Print imports
            print(f"\nIMPORTS ({len(result['imports'])}):")
            for imp in result['imports'][:5]:  # Show first 5
                if imp['type'] == 'import':
                    print(f"  - import {imp['module']}")
                else:
                    print(f"  - from {imp['from_module']} import {imp['name']}")
            
            # Print classes
            print(f"\nCLASSES ({len(result['classes'])}):")
            for cls in result['classes']:
                print(f"  - {cls['name']} (line {cls['line']})")
                print(f"    Methods: {', '.join([m['name'] for m in cls['methods'][:5]])}")
            
            # Print functions
            print(f"\nFUNCTIONS ({len(result['functions'])}):")
            for func in result['functions'][:5]:
                print(f"  - {func['name']}({', '.join(func['args'])}) at line {func['line']}")
            
            # Print CFGs
            print(f"\nCONTROL FLOW GRAPHS ({len(result['control_flow_graphs'])}):")
            for cfg in result['control_flow_graphs'][:3]:  # Show first 3
                print(f"\n  Function: {cfg['function_name']}")
                print(f"  Complexity: {cfg['metrics']['cyclomatic_complexity']}")
                print(f"  Nodes: {cfg['metrics']['num_nodes']}")
                print(f"  Decision Points: {cfg['metrics']['num_decision_points']}")
                
                print(f"\n  Flowchart Structure:")
                for i, node in enumerate(cfg['nodes'][:10]):  # Show first 10 nodes
                    print(f"    [{node['type'].upper()}] {node['label']}")
                    if i < len(cfg['nodes']) - 1:
                        edges = [e for e in cfg['edges'] if e['source'] == node['id']]
                        for edge in edges:
                            label = f" ({edge['label']})" if edge['label'] else ""
                            print(f"      ↓{label}")
            
            # Print database schema if available
            if 'database_schema' in result and result['database_schema']:
                schema = result['database_schema']
                print(f"\nDATABASE SCHEMA:")
                print(f"  Tables: {len(schema['tables'])}")
                for table in schema['tables']:
                    print(f"\n  Table: {table['name']}")
                    for field in table['fields']:
                        icon = '🔑' if field['is_primary_key'] else '🔗' if field['is_foreign_key'] else '📝'
                        constraints = f" ({', '.join(field['constraints'])})" if field['constraints'] else ''
                        print(f"    {icon} {field['name']}: {field['type']}{constraints}")
                
                print(f"\n  Relationships: {len(schema['relationships'])}")
                for rel in schema['relationships']:
                    print(f"    {rel['from_table']}.{rel['from_field']} → {rel['to_table']}.{rel['to_field']} ({rel['type']})")
            
            # Save to JSON
            output_file = file_path.replace('.py', '_analysis.json')
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nFull analysis saved to: {output_file}")
            
        elif os.path.isdir(file_path):
            print(f"Analyzing project: {file_path}\n")
            analyzer = ProjectAnalyzer(file_path)
            result = analyzer.analyze_project()
            
            print("=" * 80)
            print(f"PROJECT ANALYSIS: {result['project_path']}")
            print("=" * 80)
            
            print(f"\nArchitecture Pattern: {result['architecture_pattern']}")
            
            print(f"\nSummary:")
            summary = result['summary']
            for key, value in summary.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
            
            # Database schema
            schema = result['database_schema']
            if schema['tables']:
                print(f"\nDATABASE SCHEMA:")
                print(f"  Total Tables: {len(schema['tables'])}")
                for table in schema['tables'][:5]:  # Show first 5
                    print(f"    - {table['name']} ({len(table['fields'])} fields)")
                
                print(f"\n  Total Relationships: {len(schema['relationships'])}")
                for rel in schema['relationships'][:5]:  # Show first 5
                    print(f"    - {rel['from_table']}.{rel['from_field']} → {rel['to_table']}.{rel['to_field']}")
            
            # Save to JSON
            output_file = os.path.join(file_path, 'project_analysis.json')
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nFull project analysis saved to: {output_file}")
    
    else:
        print("Usage:")
        print("  Analyze single file: python analyzer.py path/to/file.py")
        print("  Analyze project:     python analyzer.py path/to/project/")
        print("\nExample Django models.py to test:")
        
        example_code = '''
# Example Django models.py
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def process_order(self):
        if self.status != 'pending':
            return False
        
        if self.total > 1000:
            self.priority = 'high'
        else:
            self.priority = 'normal'
        
        self.status = 'processing'
        self.save()
        return True

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
'''
        
        print(example_code)
        print("\nSave this as 'test_models.py' and run:")
        print("  python analyzer.py test_models.py")