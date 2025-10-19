import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'analyzer'))

from analyzer.utils.analyzer import PythonAnalyzer

# Create a simple test file
test_code = '''
def hello_world():
    """A simple function"""
    print("Hello, World!")
    return True

class TestClass:
    """A test class"""
    
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        """Get the value"""
        return self.value

if __name__ == "__main__":
    hello_world()
'''

# Write test file
with open('test_file.py', 'w') as f:
    f.write(test_code)

# Test the analyzer
analyzer = PythonAnalyzer('test_file.py')
try:
    result = analyzer.analyze()
    print("Analysis successful!")
    print(f"Functions found: {len(result['functions'])}")
    print(f"Classes found: {len(result['classes'])}")
    for func in result['functions']:
        print(f"Function: {func['name']}")
    for cls in result['classes']:
        print(f"Class: {cls['name']}")
        for method in cls['methods']:
            print(f"  Method: {method['name']}")
except Exception as e:
    print(f"Analysis failed: {e}")

# Clean up
os.remove('test_file.py')