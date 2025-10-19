import tempfile
import os
from .database_schema_extractor import DatabaseSchemaExtractor

def test_database_schema_extractor():
    """Test the DatabaseSchemaExtractor with a sample models.py file"""
    
    # Create a temporary Django models.py file with sample models
    sample_models = '''
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users'

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'orders'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product_name = models.CharField(max_length=255)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        db_table = 'order_items'
'''
    
    # Create a temporary directory structure
    temp_dir = tempfile.mkdtemp()
    models_dir = os.path.join(temp_dir, 'myapp')
    os.makedirs(models_dir, exist_ok=True)
    
    # Write sample models to a temporary file
    models_file_path = os.path.join(models_dir, 'models.py')
    with open(models_file_path, 'w') as f:
        f.write(sample_models)
    
    try:
        # Test extracting database schema
        schema_extractor = DatabaseSchemaExtractor(temp_dir)
        result = schema_extractor.extract_schema()
        
        print("Database Schema Extraction Results:")
        print(f"Number of tables: {len(result['nodes'])}")
        print(f"Number of relationships: {len(result['edges'])}")
        
        # Print table information
        print("\nTables:")
        for node in result['nodes']:
            print(f"  {node['data']['label']}:")
            for field in node['data']['fields']:
                field_type = field['type']
                if field['is_primary_key']:
                    field_type += " (PK)"
                if field['is_foreign_key']:
                    field_type += f" (FK -> {field['foreign_key_target']})"
                if field['is_unique']:
                    field_type += " (UNIQUE)"
                print(f"    {field['name']}: {field_type}")
                
        # Print relationship information
        print("\nRelationships:")
        for edge in result['edges']:
            print(f"  {edge['data']['source_field']} -> {edge['data']['target_field']}")
            print(f"    From: {edge['data']['source_table']}")
            print(f"    To: {edge['data']['target_table']}")
            print(f"    Type: {edge['data']['type']}")
            print(f"    On Delete: {edge['data']['on_delete']}")
            
    finally:
        # Clean up temporary files
        os.unlink(models_file_path)
        os.rmdir(models_dir)
        os.rmdir(temp_dir)

if __name__ == "__main__":
    test_database_schema_extractor()