from typing import Dict, List, Any

class MermaidGenerator:
    """Generate Mermaid.js code for architecture diagrams"""
    
    def __init__(self, graph_data: Dict[str, Any]):
        self.graph_data = graph_data
        
    def generate_component_diagram(self) -> str:
        """Generate Mermaid component diagram"""
        mermaid_code = ["graph TD"]
        
        # Add nodes
        for node in self.graph_data.get('nodes', []):
            node_type = node.get('type', 'component')
            label = node.get('label', node.get('id', ''))
            
            # Style based on node type
            if node_type == 'class':
                mermaid_code.append(f"    {node['id']}[[{label}]]")
            elif node_type == 'function':
                mermaid_code.append(f"    {node['id']}[{label}]")
            elif node_type == 'file':
                mermaid_code.append(f"    {node['id']}>{{{label}}}")
            else:
                mermaid_code.append(f"    {node['id']}[{label}]")
                
        # Add edges
        for edge in self.graph_data.get('edges', []):
            edge_type = edge.get('type', 'default')
            
            # Style based on edge type
            if edge_type == 'contains':
                mermaid_code.append(f"    {edge['source']} -- contains --> {edge['target']}")
            elif edge_type == 'depends':
                mermaid_code.append(f"    {edge['source']} -.-> {edge['target']}")
            elif edge_type == 'inherits':
                mermaid_code.append(f"    {edge['source']} --|> {edge['target']}")
            else:
                mermaid_code.append(f"    {edge['source']} --> {edge['target']}")
                
        return "\n".join(mermaid_code)
        
    def generate_flowchart(self) -> str:
        """Generate Mermaid flowchart"""
        mermaid_code = ["flowchart TD"]
        
        # Add nodes
        for node in self.graph_data.get('nodes', []):
            label = node.get('label', node.get('id', ''))
            mermaid_code.append(f"    {node['id']}[{label}]")
            
        # Add edges
        for edge in self.graph_data.get('edges', []):
            mermaid_code.append(f"    {edge['source']} --> {edge['target']}")
            
        return "\n".join(mermaid_code)
        
    def generate_class_diagram(self) -> str:
        """Generate Mermaid class diagram"""
        mermaid_code = ["classDiagram"]
        
        # Add classes
        for node in self.graph_data.get('nodes', []):
            if node.get('type') == 'class':
                class_name = node.get('label', node.get('id', ''))
                mermaid_code.append(f"    class {class_name}{{")
                
                # Add methods if available
                # This would require more detailed class information from analysis
                mermaid_code.append("    }")
                
        # Add relationships
        for edge in self.graph_data.get('edges', []):
            if edge.get('type') == 'inherits':
                mermaid_code.append(f"    {edge['source']} <|-- {edge['target']}")
            elif edge.get('type') == 'contains':
                mermaid_code.append(f"    {edge['source']} *-- {edge['target']}")
            elif edge.get('type') == 'depends':
                mermaid_code.append(f"    {edge['source']} -- {edge['target']} : uses")
                
        return "\n".join(mermaid_code)