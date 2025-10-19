import ast
import os
from typing import Dict, List, Any, Tuple

class ControlFlowNode:
    """Represents a node in the control flow graph"""
    
    def __init__(self, node_id: str, node_type: str, label: str, 
                 code_snippet: str = "", file_path: str = "", 
                 line_number: int = 0, column_number: int = 0):
        self.id = node_id
        self.type = node_type  # start, end, process, decision, io
        self.label = label
        self.code_snippet = code_snippet
        self.file_path = file_path
        self.line_number = line_number
        self.column_number = column_number
        self.ast_node = None

class ControlFlowEdge:
    """Represents an edge in the control flow graph"""
    
    def __init__(self, source_id: str, target_id: str, label: str = ""):
        self.source = source_id
        self.target = target_id
        self.label = label

class ControlFlowGraphBuilder:
    """Builds control flow graphs from Python AST"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.content = ""
        self.tree = None
        self.nodes: List[ControlFlowNode] = []
        self.edges: List[ControlFlowEdge] = []
        self.node_counter = 0
        
    def read_file(self):
        """Read the file content"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
            
    def parse_ast(self):
        """Parse the Python file using AST"""
        try:
            self.tree = ast.parse(self.content)
        except SyntaxError as e:
            raise Exception(f"Syntax error in {self.file_path}: {str(e)}")
    
    def _get_node_id(self, prefix: str = "node") -> str:
        """Generate unique node IDs"""
        self.node_counter += 1
        return f"{prefix}_{self.node_counter}"
    
    def _get_code_snippet(self, node: ast.AST, context_lines: int = 2) -> str:
        """Extract code snippet with context lines"""
        lines = self.content.split('\n')
        start_line = max(0, node.lineno - 1 - context_lines)
        end_line = min(len(lines), node.lineno + context_lines)
        return '\n'.join(lines[start_line:end_line])
    
    def build_cfg_for_function(self, function_name: str) -> Dict[str, Any]:
        """Build control flow graph for a specific function"""
        self.read_file()
        self.parse_ast()
        
        # Find the target function
        target_function = None
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                target_function = node
                break
                
        if not target_function:
            raise Exception(f"Function '{function_name}' not found in {self.file_path}")
            
        # Clear previous nodes and edges
        self.nodes = []
        self.edges = []
        self.node_counter = 0
        
        # Create start node
        start_id = self._get_node_id("start")
        start_node = ControlFlowNode(
            start_id, 
            "start", 
            f"START ({function_name})",
            f"def {function_name}(...):",
            self.file_path,
            target_function.lineno,
            target_function.col_offset
        )
        start_node.ast_node = target_function
        self.nodes.append(start_node)
        
        # Process function body
        last_node_id = start_id
        for stmt in target_function.body:
            last_node_id = self._process_statement(stmt, last_node_id)
            
        # Create end node
        end_id = self._get_node_id("end")
        end_node = ControlFlowNode(
            end_id,
            "end",
            "END",
            "",  # End doesn't have specific code
            self.file_path,
            target_function.body[-1].lineno if target_function.body else target_function.lineno,
            0
        )
        self.nodes.append(end_node)
        
        # Connect last node to end
        self.edges.append(ControlFlowEdge(last_node_id, end_id))
        
        return self._to_cytoscape_format()
    
    def _process_statement(self, stmt: ast.AST, previous_node_id: str) -> str:
        """Process a statement and return the ID of the last node created"""
        if isinstance(stmt, ast.If):
            return self._process_if_statement(stmt, previous_node_id)
        elif isinstance(stmt, ast.For):
            return self._process_for_statement(stmt, previous_node_id)
        elif isinstance(stmt, ast.While):
            return self._process_while_statement(stmt, previous_node_id)
        elif isinstance(stmt, ast.Return):
            return self._process_return_statement(stmt, previous_node_id)
        elif isinstance(stmt, ast.Assign):
            return self._process_assign_statement(stmt, previous_node_id)
        elif isinstance(stmt, ast.Expr):
            return self._process_expr_statement(stmt, previous_node_id)
        else:
            # Generic process node for other statements
            node_id = self._get_node_id("process")
            label = self._get_statement_label(stmt)
            code_snippet = self._get_code_snippet(stmt)
            
            node = ControlFlowNode(
                node_id,
                "process",
                label,
                code_snippet,
                self.file_path,
                stmt.lineno,
                stmt.col_offset
            )
            node.ast_node = stmt
            self.nodes.append(node)
            self.edges.append(ControlFlowEdge(previous_node_id, node_id))
            return node_id
    
    def _process_if_statement(self, if_stmt: ast.If, previous_node_id: str) -> str:
        """Process an if statement with all its branches"""
        # Create decision node
        decision_id = self._get_node_id("decision")
        condition_text = ast.unparse(if_stmt.test) if hasattr(ast, 'unparse') else "condition"
        label = f"Is {condition_text}?"
        
        code_snippet = self._get_code_snippet(if_stmt)
        
        decision_node = ControlFlowNode(
            decision_id,
            "decision",
            label,
            code_snippet,
            self.file_path,
            if_stmt.lineno,
            if_stmt.col_offset
        )
        decision_node.ast_node = if_stmt
        self.nodes.append(decision_node)
        self.edges.append(ControlFlowEdge(previous_node_id, decision_id))
        
        # Process if body
        last_if_node_id = decision_id
        for stmt in if_stmt.body:
            last_if_node_id = self._process_statement(stmt, last_if_node_id)
        
        # Process else/elif branches
        last_else_node_id = None
        if if_stmt.orelse:
            # Process else body
            for stmt in if_stmt.orelse:
                if last_else_node_id is None:
                    last_else_node_id = decision_id  # Start from decision for else
                last_else_node_id = self._process_statement(stmt, last_else_node_id)
        
        # Create merge point after if-else
        merge_id = self._get_node_id("merge")
        merge_node = ControlFlowNode(
            merge_id,
            "process",
            "Merge",
            "",
            self.file_path,
            if_stmt.body[-1].lineno if if_stmt.body else if_stmt.lineno,
            0
        )
        self.nodes.append(merge_node)
        
        # Connect if branch to merge
        self.edges.append(ControlFlowEdge(last_if_node_id, merge_id))
        
        # Connect else branch to merge (or decision to merge if no else)
        if last_else_node_id:
            self.edges.append(ControlFlowEdge(last_else_node_id, merge_id))
        else:
            self.edges.append(ControlFlowEdge(decision_id, merge_id))
            
        return merge_id
    
    def _process_for_statement(self, for_stmt: ast.For, previous_node_id: str) -> str:
        """Process a for loop statement"""
        # Create loop start node
        loop_id = self._get_node_id("loop")
        target_text = ast.unparse(for_stmt.target) if hasattr(ast, 'unparse') else "target"
        iter_text = ast.unparse(for_stmt.iter) if hasattr(ast, 'unparse') else "iterable"
        label = f"For each {target_text} in {iter_text}"
        
        code_snippet = self._get_code_snippet(for_stmt)
        
        loop_node = ControlFlowNode(
            loop_id,
            "decision",
            label,
            code_snippet,
            self.file_path,
            for_stmt.lineno,
            for_stmt.col_offset
        )
        loop_node.ast_node = for_stmt
        self.nodes.append(loop_node)
        self.edges.append(ControlFlowEdge(previous_node_id, loop_id))
        
        # Process loop body
        last_body_node_id = loop_id
        for stmt in for_stmt.body:
            last_body_node_id = self._process_statement(stmt, last_body_node_id)
            
        # Create back edge to loop (simplified representation)
        # In a real CFG, this would be more complex
        self.edges.append(ControlFlowEdge(last_body_node_id, loop_id, "loop"))
        
        # Create loop exit node
        exit_id = self._get_node_id("process")
        exit_node = ControlFlowNode(
            exit_id,
            "process",
            "Exit loop",
            "",
            self.file_path,
            for_stmt.body[-1].lineno if for_stmt.body else for_stmt.lineno,
            0
        )
        self.nodes.append(exit_node)
        self.edges.append(ControlFlowEdge(loop_id, exit_id, "end"))
        
        return exit_id
    
    def _process_while_statement(self, while_stmt: ast.While, previous_node_id: str) -> str:
        """Process a while loop statement"""
        # Create loop condition node
        loop_id = self._get_node_id("loop")
        condition_text = ast.unparse(while_stmt.test) if hasattr(ast, 'unparse') else "condition"
        label = f"While {condition_text}"
        
        code_snippet = self._get_code_snippet(while_stmt)
        
        loop_node = ControlFlowNode(
            loop_id,
            "decision",
            label,
            code_snippet,
            self.file_path,
            while_stmt.lineno,
            while_stmt.col_offset
        )
        loop_node.ast_node = while_stmt
        self.nodes.append(loop_node)
        self.edges.append(ControlFlowEdge(previous_node_id, loop_id))
        
        # Process loop body
        last_body_node_id = loop_id
        for stmt in while_stmt.body:
            last_body_node_id = self._process_statement(stmt, last_body_node_id)
            
        # Create back edge to loop
        self.edges.append(ControlFlowEdge(last_body_node_id, loop_id, "loop"))
        
        # Create loop exit node
        exit_id = self._get_node_id("process")
        exit_node = ControlFlowNode(
            exit_id,
            "process",
            "Exit loop",
            "",
            self.file_path,
            while_stmt.body[-1].lineno if while_stmt.body else while_stmt.lineno,
            0
        )
        self.nodes.append(exit_node)
        self.edges.append(ControlFlowEdge(loop_id, exit_id, "end"))
        
        return exit_id
    
    def _process_return_statement(self, return_stmt: ast.Return, previous_node_id: str) -> str:
        """Process a return statement"""
        node_id = self._get_node_id("process")
        value_text = ast.unparse(return_stmt.value) if return_stmt.value and hasattr(ast, 'unparse') else ""
        label = f"Return {value_text}" if value_text else "Return"
        
        code_snippet = self._get_code_snippet(return_stmt)
        
        node = ControlFlowNode(
            node_id,
            "process",
            label,
            code_snippet,
            self.file_path,
            return_stmt.lineno,
            return_stmt.col_offset
        )
        node.ast_node = return_stmt
        self.nodes.append(node)
        self.edges.append(ControlFlowEdge(previous_node_id, node_id))
        return node_id
    
    def _process_assign_statement(self, assign_stmt: ast.Assign, previous_node_id: str) -> str:
        """Process an assignment statement"""
        node_id = self._get_node_id("process")
        targets_text = ", ".join([ast.unparse(target) for target in assign_stmt.targets]) if hasattr(ast, 'unparse') else "target"
        value_text = ast.unparse(assign_stmt.value) if hasattr(ast, 'unparse') else "value"
        label = f"{targets_text} = {value_text}"
        
        code_snippet = self._get_code_snippet(assign_stmt)
        
        node = ControlFlowNode(
            node_id,
            "process",
            label,
            code_snippet,
            self.file_path,
            assign_stmt.lineno,
            assign_stmt.col_offset
        )
        node.ast_node = assign_stmt
        self.nodes.append(node)
        self.edges.append(ControlFlowEdge(previous_node_id, node_id))
        return node_id
    
    def _process_expr_statement(self, expr_stmt: ast.Expr, previous_node_id: str) -> str:
        """Process an expression statement"""
        node_id = self._get_node_id("process")
        expr_text = ast.unparse(expr_stmt.value) if hasattr(ast, 'unparse') else "expression"
        label = expr_text
        
        code_snippet = self._get_code_snippet(expr_stmt)
        
        node = ControlFlowNode(
            node_id,
            "process",
            label,
            code_snippet,
            self.file_path,
            expr_stmt.lineno,
            expr_stmt.col_offset
        )
        node.ast_node = expr_stmt
        self.nodes.append(node)
        self.edges.append(ControlFlowEdge(previous_node_id, node_id))
        return node_id
    
    def _get_statement_label(self, stmt: ast.AST) -> str:
        """Generate a human-readable label for a statement"""
        if isinstance(stmt, ast.FunctionDef):
            return f"Function: {stmt.name}"
        elif isinstance(stmt, ast.ClassDef):
            return f"Class: {stmt.name}"
        elif isinstance(stmt, ast.Import):
            return f"Import: {', '.join([alias.name for alias in stmt.names])}"
        elif isinstance(stmt, ast.ImportFrom):
            return f"From {stmt.module} import {', '.join([alias.name for alias in stmt.names])}"
        else:
            # Generic label
            return type(stmt).__name__
    
    def _to_cytoscape_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to Cytoscape.js compatible format"""
        nodes = []
        edges = []
        
        # Convert nodes
        for node in self.nodes:
            cy_node = {
                'data': {
                    'id': node.id,
                    'label': node.label,
                    'type': node.type,
                    'code_snippet': node.code_snippet,
                    'file_path': node.file_path,
                    'line_number': node.line_number,
                    'column_number': node.column_number
                }
            }
            nodes.append(cy_node)
            
        # Convert edges
        for i, edge in enumerate(self.edges):
            cy_edge = {
                'data': {
                    'id': f"edge_{i}",
                    'source': edge.source,
                    'target': edge.target,
                    'label': edge.label
                }
            }
            edges.append(cy_edge)
            
        return {
            'nodes': nodes,
            'edges': edges
        }