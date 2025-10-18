import json
from typing import Dict, List, Any

class GraphGenerator:
    """Convert analysis results to graph formats for visualization"""
    
    def __init__(self, analysis_data: Dict[str, Any]):
        self.analysis_data = analysis_data
        
    def to_cytoscape_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to Cytoscape.js compatible format"""
        nodes = []
        edges = []
        
        # Process nodes
        for node in self.analysis_data.get('nodes', []):
            cy_node = {
                'data': {
                    'id': node['id'],
                    'label': node['label'],
                    'type': node['type']
                }
            }
            
            # Add parent if exists
            if 'parent' in node:
                cy_node['data']['parent'] = node['parent']
                
            nodes.append(cy_node)
            
        # Process edges
        for edge in self.analysis_data.get('edges', []):
            cy_edge = {
                'data': {
                    'id': f"{edge['source']}-{edge['target']}",
                    'source': edge['source'],
                    'target': edge['target'],
                    'type': edge['type']
                }
            }
            edges.append(cy_edge)
            
        return {
            'nodes': nodes,
            'edges': edges
        }
        
    def to_d3_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to D3.js compatible format"""
        nodes = []
        links = []
        
        # Create a map of node IDs to indices for D3
        node_map = {}
        for i, node in enumerate(self.analysis_data.get('nodes', [])):
            node_map[node['id']] = i
            
        # Process nodes
        for i, node in enumerate(self.analysis_data.get('nodes', [])):
            d3_node = {
                'id': node['id'],
                'name': node['label'],
                'type': node['type'],
                'group': node['type']
            }
            
            # Add additional properties
            if 'parent' in node:
                d3_node['parent'] = node['parent']
                
            nodes.append(d3_node)
            
        # Process edges
        for edge in self.analysis_data.get('edges', []):
            if edge['source'] in node_map and edge['target'] in node_map:
                d3_link = {
                    'source': node_map[edge['source']],
                    'target': node_map[edge['target']],
                    'type': edge['type']
                }
                links.append(d3_link)
                
        return {
            'nodes': nodes,
            'links': links
        }
        
    def to_sankey_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to Sankey diagram format for data flow visualization"""
        nodes = []
        links = []
        
        # For data flow, we focus on function calls and data transformations
        call_graph = self.analysis_data.get('call_graph', {})
        
        # Collect all unique functions/nodes
        all_nodes = set()
        for caller, callees in call_graph.items():
            all_nodes.add(caller)
            for callee in callees:
                all_nodes.add(callee)
                
        # Create nodes
        node_map = {}
        for i, node_name in enumerate(all_nodes):
            node_map[node_name] = i
            nodes.append({
                'name': node_name,
                'id': i
            })
            
        # Create links
        for caller, callees in call_graph.items():
            if caller in node_map:
                for callee in callees:
                    if callee in node_map:
                        links.append({
                            'source': node_map[caller],
                            'target': node_map[callee],
                            'value': 1  # Could be based on call frequency
                        })
                        
        return {
            'nodes': nodes,
            'links': links
        }