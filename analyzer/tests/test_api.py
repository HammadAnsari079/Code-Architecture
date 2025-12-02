from django.test import TestCase, Client
from django.urls import reverse
from analyzer.models import Project, CodeFile
import json

class GraphApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.project = Project.objects.create(
            name="Test Project",
            description="Test Description"
        )
        
        # Create a sample model file for ERD testing
        self.model_code = """
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    total = models.DecimalField(max_digits=10, decimal_places=2)
"""
        CodeFile.objects.create(
            project=self.project,
            file_path="models.py",
            language="python",
            content=self.model_code,
            size=len(self.model_code)
        )
        
        # Create a sample view file for Dependency testing
        self.view_code = """
from .models import User, Order

def process_order(user_id):
    user = User.objects.get(id=user_id)
    return "Processed"
"""
        CodeFile.objects.create(
            project=self.project,
            file_path="views.py",
            language="python",
            content=self.view_code,
            size=len(self.view_code)
        )

    def test_get_erd_data(self):
        url = reverse('erd_data', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        # Should have nodes for User and Order tables
        elements = data['data']
        table_names = [e['data']['label'] for e in elements if 'table' in e.get('classes', '')]
        self.assertIn('User', table_names)
        self.assertIn('Order', table_names)

    def test_get_dependency_data(self):
        url = reverse('dependency_data', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        # Should have nodes for models.py and views.py
        elements = data['data']
        file_labels = [e['data']['label'] for e in elements if 'file' in e.get('classes', '')]
        self.assertIn('models.py', file_labels)
        self.assertIn('views.py', file_labels)

    def test_get_component_data(self):
        url = reverse('component_data', args=[self.project.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        # Should have component nodes (root folder in this case)
        elements = data['data']
        comp_labels = [e['data']['label'] for e in elements if 'component' in e.get('classes', '')]
        self.assertTrue(len(comp_labels) > 0)
