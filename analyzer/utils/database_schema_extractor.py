import ast
import os
import re
from typing import Dict, List, Any, Tuple

class DatabaseField:
    """Represents a field in a database table"""
    
    def __init__(self, name: str, field_type: str, is_primary_key: bool = False, 
                 is_foreign_key: bool = False, is_unique: bool = False,
                 foreign_key_target: str = "", on_delete: str = ""):
        self.name = name
        self.field_type = field_type
        self.is_primary_key = is_primary_key
        self.is_foreign_key = is_foreign_key
        self.is_unique = is_unique
        self.foreign_key_target = foreign_key_target  # Format: "TableName.field_name"
        self.on_delete = on_delete

class DatabaseTable:
    """Represents a database table"""
    
    def __init__(self, name: str, file_path: str, line_number: int):
        self.name = name
        self.file_path = file_path
        self.line_number = line_number
        self.fields: List[DatabaseField] = []
        self.relationships: List[Dict[str, Any]] = []

class DatabaseSchemaExtractor:
    """Extract database schema from Django models"""
    
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.tables: List[DatabaseTable] = []
        self.relationships: List[Dict[str, Any]] = []
        
    def extract_schema(self) -> Dict[str, Any]:
        """Extract complete database schema from Django models"""
        # Find all models.py files in the project
        models_files = self._find_models_files()
        
        # Parse each models.py file
        for file_path in models_files:
            self._parse_models_file(file_path)
            
        # Build relationships
        self._build_relationships()
        
        return self._to_cytoscape_format()
    
    def _find_models_files(self) -> List[str]:
        """Find all models.py files in the project"""
        models_files = []
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file == 'models.py':
                    models_files.append(os.path.join(root, file))
        return models_files
    
    def _parse_models_file(self, file_path: str):
        """Parse a models.py file and extract table information"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            print(f"Syntax error in {file_path}: {str(e)}")
            return
            
        # Find all model classes (classes that inherit from models.Model)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if this class inherits from models.Model
                if self._is_django_model(node):
                    table = self._extract_table_info(node, file_path)
                    if table:
                        self.tables.append(table)
    
    def _is_django_model(self, class_node: ast.ClassDef) -> bool:
        """Check if a class is a Django model (inherits from models.Model)"""
        for base in class_node.bases:
            if isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
                if base.value.id == 'models' and base.attr == 'Model':
                    return True
            elif isinstance(base, ast.Name) and base.id == 'Model':
                # Direct import of Model
                return True
        return False
    
    def _extract_table_info(self, class_node: ast.ClassDef, file_path: str) -> DatabaseTable:
        """Extract table information from a model class"""
        table_name = class_node.name
        table = DatabaseTable(table_name, file_path, class_node.lineno)
        
        # Extract fields
        for stmt in class_node.body:
            if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
                target = stmt.targets[0]
                if isinstance(target, ast.Name):
                    field_name = target.id
                    field_info = self._extract_field_info(stmt.value, field_name)
                    if field_info:
                        table.fields.append(field_info)
                        
        return table
    
    def _extract_field_info(self, value_node: ast.AST, field_name: str) -> DatabaseField:
        """Extract field information from an assignment value"""
        if isinstance(value_node, ast.Call):
            # Field is a function call like models.CharField(...)
            if isinstance(value_node.func, ast.Attribute) and isinstance(value_node.func.value, ast.Name):
                if value_node.func.value.id == 'models':
                    field_type = value_node.func.attr
                    is_primary_key = False
                    is_foreign_key = False
                    is_unique = False
                    foreign_key_target = None
                    on_delete = None
                    
                    # Check for primary_key=True
                    for keyword in value_node.keywords:
                        if keyword.arg == 'primary_key' and isinstance(keyword.value, ast.Constant):
                            is_primary_key = bool(keyword.value.value) if hasattr(keyword.value, 'value') else False
                        elif keyword.arg == 'unique' and isinstance(keyword.value, ast.Constant):
                            is_unique = bool(keyword.value.value) if hasattr(keyword.value, 'value') else False
                        elif keyword.arg == 'on_delete' and isinstance(keyword.value, ast.Attribute):
                            on_delete = f"{value_node.func.value.id}.{value_node.func.attr}"
                            
                    # Check if this is a ForeignKey
                    if field_type == 'ForeignKey':
                        is_foreign_key = True
                        # Extract the target model
                        if value_node.args:
                            target_arg = value_node.args[0]
                            if isinstance(target_arg, ast.Name):
                                foreign_key_target = target_arg.id
                            elif isinstance(target_arg, ast.Constant):
                                foreign_key_target = str(target_arg.value)
                                
                    return DatabaseField(
                        field_name, 
                        field_type, 
                        is_primary_key, 
                        is_foreign_key, 
                        is_unique,
                        foreign_key_target if foreign_key_target else "",
                        on_delete if on_delete else ""
                    )
            elif isinstance(value_node.func, ast.Name):
                # Direct function call like CharField(...) - might be imported directly
                field_type = value_node.func.id
                is_primary_key = False
                is_foreign_key = (field_type == 'ForeignKey')
                is_unique = False
                foreign_key_target = None
                on_delete = None
                
                # Check for primary_key=True
                for keyword in value_node.keywords:
                    if keyword.arg == 'primary_key' and isinstance(keyword.value, ast.Constant):
                        is_primary_key = bool(keyword.value.value) if hasattr(keyword.value, 'value') else False
                    elif keyword.arg == 'unique' and isinstance(keyword.value, ast.Constant):
                        is_unique = bool(keyword.value.value) if hasattr(keyword.value, 'value') else False
                        
                # Check if this is a ForeignKey
                if is_foreign_key and value_node.args:
                    target_arg = value_node.args[0]
                    if isinstance(target_arg, ast.Name):
                        foreign_key_target = target_arg.id
                    elif isinstance(target_arg, ast.Constant):
                        foreign_key_target = str(target_arg.value)
                        
                return DatabaseField(
                    field_name, 
                    field_type, 
                    is_primary_key, 
                    is_foreign_key, 
                    is_unique,
                    foreign_key_target if foreign_key_target else "",
                    on_delete if on_delete else ""
                )
                
        return None  # type: ignore
    
    def _build_relationships(self):
        """Build relationships between tables based on ForeignKey fields"""
        for table in self.tables:
            for field in table.fields:
                if field.is_foreign_key and field.foreign_key_target:
                    # Find the target table
                    target_table = None
                    for t in self.tables:
                        if t.name == field.foreign_key_target:
                            target_table = t
                            break
                            
                    if target_table:
                        # Create relationship
                        relationship = {
                            'source_table': table.name,
                            'source_field': field.name,
                            'target_table': target_table.name,
                            'target_field': 'id',  # Assuming primary key is 'id'
                            'type': 'ForeignKey',
                            'on_delete': field.on_delete,
                            'source_file': table.file_path,
                            'source_line': table.line_number
                        }
                        table.relationships.append(relationship)
                        self.relationships.append(relationship)
    
    def _to_cytoscape_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to Cytoscape.js compatible format"""
        nodes = []
        edges = []
        
        # Convert tables to nodes
        for table in self.tables:
            # Create node for the table
            table_node = {
                'data': {
                    'id': f"table_{table.name}",
                    'label': table.name,
                    'type': 'table',
                    'file_path': table.file_path,
                    'line_number': table.line_number,
                    'fields': [
                        {
                            'name': field.name,
                            'type': field.field_type,
                            'is_primary_key': field.is_primary_key,
                            'is_foreign_key': field.is_foreign_key,
                            'is_unique': field.is_unique,
                            'foreign_key_target': field.foreign_key_target
                        }
                        for field in table.fields
                    ]
                }
            }
            nodes.append(table_node)
            
        # Convert relationships to edges
        for i, relationship in enumerate(self.relationships):
            edge = {
                'data': {
                    'id': f"rel_{i}",
                    'source': f"table_{relationship['source_table']}",
                    'target': f"table_{relationship['target_table']}",
                    'type': relationship['type'],
                    'source_field': relationship['source_field'],
                    'target_field': relationship['target_field'],
                    'on_delete': relationship['on_delete'],
                    'source_file': relationship['source_file'],
                    'source_line': relationship['source_line'],
                    'label': f"{relationship['source_field']} → {relationship['target_field']}"
                }
            }
            edges.append(edge)
            
        return {
            'nodes': nodes,
            'edges': edges
        }

# Example usage:
# extractor = DatabaseSchemaExtractor('/path/to/django/project')
# schema = extractor.extract_schema()