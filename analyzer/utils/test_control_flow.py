import tempfile
import os
from .control_flow_builder import ControlFlowGraphBuilder

def test_control_flow_builder():
    """Test the ControlFlowGraphBuilder with a sample function"""
    
    # Create a temporary Python file with a sample function
    sample_code = '''
def process_order(order_id):
    """Process an order"""
    order = Order.objects.get(id=order_id)
    if order.status != 'pending':
        return False
    if order.total > 1000:
        order.priority = 'high'
    else:
        order.priority = 'normal'
    order.status = 'processing'
    order.save()
    return True

def login(username, password):
    """User login function"""
    user = User.objects.get(username=username)
    if user.password == password:
        return user
    else:
        return None
'''
    
    # Write sample code to a temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_code)
        temp_file_path = f.name
    
    try:
        # Test building CFG for process_order function
        cfg_builder = ControlFlowGraphBuilder(temp_file_path)
        result = cfg_builder.build_cfg_for_function('process_order')
        
        print("Control Flow Graph for 'process_order' function:")
        print(f"Number of nodes: {len(result['nodes'])}")
        print(f"Number of edges: {len(result['edges'])}")
        
        # Print node information
        print("\nNodes:")
        for node in result['nodes']:
            print(f"  {node['data']['id']}: {node['data']['label']} (type: {node['data']['type']})")
            
        # Print edge information
        print("\nEdges:")
        for edge in result['edges']:
            print(f"  {edge['data']['source']} -> {edge['data']['target']} (label: {edge['data'].get('label', 'N/A')})")
            
        # Test building CFG for login function
        result2 = cfg_builder.build_cfg_for_function('login')
        
        print("\n\nControl Flow Graph for 'login' function:")
        print(f"Number of nodes: {len(result2['nodes'])}")
        print(f"Number of edges: {len(result2['edges'])}")
        
        # Print node information
        print("\nNodes:")
        for node in result2['nodes']:
            print(f"  {node['data']['id']}: {node['data']['label']} (type: {node['data']['type']})")
            
        # Print edge information
        print("\nEdges:")
        for edge in result2['edges']:
            print(f"  {edge['data']['source']} -> {edge['data']['target']} (label: {edge['data'].get('label', 'N/A')})")
            
    finally:
        # Clean up temporary file
        os.unlink(temp_file_path)

if __name__ == "__main__":
    test_control_flow_builder()