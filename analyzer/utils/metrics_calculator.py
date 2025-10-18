import ast
from typing import Dict, List, Any, Tuple

class MetricsCalculator:
    """Calculate code metrics and complexity"""
    
    def __init__(self, analysis_data: Dict[str, Any]):
        self.analysis_data = analysis_data
        
    def calculate_cyclomatic_complexity(self) -> Dict[str, int]:
        """Calculate cyclomatic complexity for functions"""
        complexities = {}
        
        for file_analysis in self.analysis_data.get('file_analysis', []):
            file_path = file_analysis.get('file_path', '')
            functions = file_analysis.get('analysis', {}).get('functions', [])
            
            for func in functions:
                func_name = func.get('name', 'unknown')
                # Simplified complexity calculation
                # In a real implementation, this would parse the function AST
                complexity = 1  # Base complexity
                
                # Add complexity for control flow statements
                # This is a simplified version - a full implementation would parse the function body
                complexities[f"{file_path}:{func_name}"] = complexity
                
        return complexities
        
    def calculate_coupling(self) -> Dict[str, int]:
        """Calculate coupling between modules"""
        coupling = {}
        
        dependencies = self.analysis_data.get('dependencies', [])
        
        # Count dependencies for each module
        for dep in dependencies:
            source = dep.get('source', '')
            if source in coupling:
                coupling[source] += 1
            else:
                coupling[source] = 1
                
        return coupling
        
    def detect_circular_dependencies(self) -> List[List[str]]:
        """Detect circular dependencies between modules"""
        dependencies = self.analysis_data.get('dependencies', [])
        
        # Build dependency graph
        graph = {}
        for dep in dependencies:
            source = dep.get('source', '')
            target = dep.get('target', '')
            
            if source not in graph:
                graph[source] = []
            graph[source].append(target)
            
        # Detect cycles using DFS
        def dfs(node, visited, rec_stack, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            if node in graph:
                for neighbor in graph[node]:
                    if neighbor not in visited:
                        if dfs(neighbor, visited, rec_stack, path):
                            return True
                    elif neighbor in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(neighbor)
                        return path[cycle_start:] + [neighbor]
                        
            rec_stack.remove(node)
            path.pop()
            return False
            
        cycles = []
        visited = set()
        
        for node in graph:
            if node not in visited:
                rec_stack = set()
                path = []
                cycle = dfs(node, visited, rec_stack, path)
                if cycle:
                    cycles.append(cycle)
                    
        return cycles
        
    def find_most_connected_components(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Find the most connected components"""
        connections = {}
        
        # Count connections for each component
        for file_analysis in self.analysis_data.get('file_analysis', []):
            file_path = file_analysis.get('file_path', '')
            imports = file_analysis.get('analysis', {}).get('imports', [])
            functions = file_analysis.get('analysis', {}).get('functions', [])
            classes = file_analysis.get('analysis', {}).get('classes', [])
            
            # Count total elements as a proxy for connectivity
            connection_count = len(imports) + len(functions) + len(classes)
            connections[file_path] = connection_count
            
        # Sort by connection count and return top N
        sorted_connections = sorted(connections.items(), key=lambda x: x[1], reverse=True)
        return sorted_connections[:top_n]
        
    def detect_dead_code(self) -> List[str]:
        """Detect potentially dead code (unused functions/classes)"""
        # This is a simplified implementation
        # A full implementation would require more sophisticated analysis
        dead_code = []
        
        call_graph = self.analysis_data.get('call_graph', {})
        all_functions = set()
        called_functions = set()
        
        # Collect all functions and called functions
        for file_analysis in self.analysis_data.get('file_analysis', []):
            functions = file_analysis.get('analysis', {}).get('functions', [])
            for func in functions:
                all_functions.add(func.get('name', ''))
                
        for caller, callees in call_graph.items():
            called_functions.add(caller)
            for callee in callees:
                called_functions.add(callee)
                
        # Find functions that are defined but never called
        dead_functions = all_functions - called_functions
        dead_code.extend(list(dead_functions))
        
        return dead_code
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate a complete metrics report"""
        return {
            'cyclomatic_complexity': self.calculate_cyclomatic_complexity(),
            'coupling': self.calculate_coupling(),
            'circular_dependencies': self.detect_circular_dependencies(),
            'most_connected_components': self.find_most_connected_components(),
            'potential_dead_code': self.detect_dead_code()
        }