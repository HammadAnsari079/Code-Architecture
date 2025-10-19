import json
from typing import Dict, List, Any

class EnhancedGraphGenerator:
    """Generate enhanced graph formats for interactive visualizations"""
    
    def __init__(self, analysis_data: Dict[str, Any]):
        self.analysis_data = analysis_data
        
    def to_cytoscape_format(self) -> Dict[str, List[Dict[str, Any]]]:
        """Convert to enhanced Cytoscape.js compatible format with interactive features"""
        nodes = []
        edges = []
        
        # Process nodes with enhanced properties for interactivity
        for node in self.analysis_data.get('nodes', []):
            cy_node = {
                'data': {
                    'id': node['id'],
                    'label': node['label'],
                    'type': node.get('type', 'default'),
                    # Add all additional properties for interactivity
                    **{k: v for k, v in node.items() if k not in ['id', 'label', 'type']}
                },
                # Add style information based on node type
                'classes': self._get_node_classes(node)
            }
            
            # Add parent if exists
            if 'parent' in node:
                cy_node['data']['parent'] = node['parent']
                
            nodes.append(cy_node)
            
        # Process edges with enhanced properties for interactivity
        for i, edge in enumerate(self.analysis_data.get('edges', [])):
            cy_edge = {
                'data': {
                    'id': edge.get('id', f"edge_{i}"),
                    'source': edge['source'],
                    'target': edge['target'],
                    'type': edge.get('type', 'default'),
                    # Add all additional properties for interactivity
                    **{k: v for k, v in edge.items() if k not in ['id', 'source', 'target', 'type']}
                },
                # Add style information based on edge type
                'classes': self._get_edge_classes(edge)
            }
            edges.append(cy_edge)
            
        return {
            'nodes': nodes,
            'edges': edges
        }
        
    def _get_node_classes(self, node: Dict[str, Any]) -> str:
        """Get CSS classes for a node based on its properties"""
        classes = [node.get('type', 'default')]
        
        # Add special classes for interactive features
        if node.get('type') == 'start':
            classes.append('start-node')
        elif node.get('type') == 'end':
            classes.append('end-node')
        elif node.get('type') == 'decision':
            classes.append('decision-node')
        elif node.get('type') == 'process':
            classes.append('process-node')
        elif node.get('type') == 'table':
            classes.append('table-node')
            
        # Add interactive classes
        classes.append('interactive-node')
        
        return ' '.join(classes)
        
    def _get_edge_classes(self, edge: Dict[str, Any]) -> str:
        """Get CSS classes for an edge based on its properties"""
        classes = [edge.get('type', 'default')]
        
        # Add special classes for interactive features
        if edge.get('type') == 'ForeignKey':
            classes.append('foreign-key-edge')
        elif edge.get('type') == 'depends':
            classes.append('dependency-edge')
        elif edge.get('type') == 'contains':
            classes.append('containment-edge')
            
        # Add interactive classes
        classes.append('interactive-edge')
        
        return ' '.join(classes)
        
    def generate_flowchart_style(self) -> List[Dict[str, Any]]:
        """Generate Cytoscape.js style for flowchart visualization"""
        return [
            # Base node style
            {
                'selector': 'node',
                'style': {
                    'width': 100,
                    'height': 40,
                    'background-color': '#ddd',
                    'label': 'data(label)',
                    'text-valign': 'center',
                    'text-halign': 'center',
                    'font-size': 12,
                    'color': '#333',
                    'border-width': 1,
                    'border-color': '#999'
                }
            },
            # Start node style (oval)
            {
                'selector': '.start-node, .end-node',
                'style': {
                    'shape': 'ellipse',
                    'background-color': '#4CAF50',
                    'color': 'white',
                    'font-weight': 'bold'
                }
            },
            # Process node style (rectangle)
            {
                'selector': '.process-node',
                'style': {
                    'shape': 'round-rectangle',
                    'background-color': '#2196F3',
                    'color': 'white'
                }
            },
            # Decision node style (diamond)
            {
                'selector': '.decision-node',
                'style': {
                    'shape': 'diamond',
                    'background-color': '#FF9800',
                    'color': 'white',
                    'width': 80,
                    'height': 80
                }
            },
            # Table node style (for ERD)
            {
                'selector': '.table-node',
                'style': {
                    'shape': 'round-rectangle',
                    'background-color': '#E91E63',
                    'color': 'white',
                    'width': 150,
                    'height': 100
                }
            },
            # Base edge style
            {
                'selector': 'edge',
                'style': {
                    'width': 2,
                    'line-color': '#666',
                    'target-arrow-color': '#666',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': 10,
                    'color': '#333',
                    'text-background-color': '#ffffff',
                    'text-background-opacity': 0.8
                }
            },
            # Foreign key edge style
            {
                'selector': '.foreign-key-edge',
                'style': {
                    'line-color': '#9C27B0',
                    'target-arrow-color': '#9C27B0',
                    'width': 2,
                    'line-style': 'dashed'
                }
            },
            # Dependency edge style
            {
                'selector': '.dependency-edge',
                'style': {
                    'line-color': '#FF5722',
                    'target-arrow-color': '#FF5722',
                    'line-style': 'dashed'
                }
            },
            # Hover effects
            {
                'selector': 'node:hover',
                'style': {
                    'overlay-color': '#4CAF50',
                    'overlay-opacity': 0.3,
                    'border-width': 2,
                    'border-color': '#4CAF50'
                }
            },
            {
                'selector': 'edge:hover',
                'style': {
                    'width': 4,
                    'line-color': '#4CAF50',
                    'target-arrow-color': '#4CAF50'
                }
            },
            # Selected node/edge styles
            {
                'selector': 'node:selected',
                'style': {
                    'border-width': 3,
                    'border-color': '#FF5722'
                }
            },
            {
                'selector': 'edge:selected',
                'style': {
                    'width': 4,
                    'line-color': '#FF5722',
                    'target-arrow-color': '#FF5722'
                }
            }
        ]
        
    def generate_erd_style(self) -> List[Dict[str, Any]]:
        """Generate Cytoscape.js style for ERD visualization"""
        return [
            # Table node style
            {
                'selector': '.table-node',
                'style': {
                    'shape': 'round-rectangle',
                    'background-color': '#FFFFFF',
                    'color': '#333',
                    'width': 200,
                    'height': 150,
                    'border-width': 2,
                    'border-color': '#333',
                    'label': 'data(label)',
                    'text-valign': 'top',
                    'text-halign': 'center',
                    'font-size': 14,
                    'font-weight': 'bold'
                }
            },
            # Foreign key edge style
            {
                'selector': '.foreign-key-edge',
                'style': {
                    'width': 2,
                    'line-color': '#9C27B0',
                    'target-arrow-color': '#9C27B0',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'line-style': 'solid'
                }
            },
            # Hover effects for tables
            {
                'selector': '.table-node:hover',
                'style': {
                    'overlay-color': '#2196F3',
                    'overlay-opacity': 0.2
                }
            },
            # Hover effects for relationships
            {
                'selector': '.foreign-key-edge:hover',
                'style': {
                    'width': 4,
                    'line-color': '#2196F3',
                    'target-arrow-color': '#2196F3'
                }
            },
            # Selected table style
            {
                'selector': '.table-node:selected',
                'style': {
                    'border-width': 3,
                    'border-color': '#FF5722',
                    'background-color': '#FFF3E0'
                }
            },
            # Selected relationship style
            {
                'selector': '.foreign-key-edge:selected',
                'style': {
                    'width': 4,
                    'line-color': '#FF5722',
                    'target-arrow-color': '#FF5722'
                }
            }
        ]
        
    def generate_layout_config(self, layout_type: str = 'flowchart') -> Dict[str, Any]:
        """Generate layout configuration for Cytoscape.js"""
        if layout_type == 'flowchart':
            return {
                'name': 'dagre',
                'rankDir': 'TB',
                'rankSep': 100,
                'nodeSep': 50,
                'edgeSep': 50,
                'animate': True,
                'animationDuration': 1000
            }
        elif layout_type == 'erd':
            return {
                'name': 'cose',
                'animate': True,
                'animationDuration': 1000,
                'nodeRepulsion': 400000,
                'idealEdgeLength': 100,
                'nodeOverlap': 20,
                'refresh': 20,
                'fit': True,
                'padding': 30,
                'randomize': False,
                'componentSpacing': 100,
                'nodeDimensionsIncludeLabels': True
            }
        else:
            return {
                'name': 'grid',
                'animate': True,
                'animationDuration': 1000
            }