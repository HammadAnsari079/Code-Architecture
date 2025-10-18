from django.db import models
from django.contrib.auth.models import User

class Project(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=500)
    status = models.CharField(max_length=50, default='uploaded')
    
    def __str__(self):
        return self.name

class AnalysisResult(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    analysis_type = models.CharField(max_length=100)  # architecture, dependency, dataflow
    result_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.name} - {self.analysis_type}"

class CodeFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=500)
    language = models.CharField(max_length=50)
    size = models.IntegerField()
    content = models.TextField()
    
    def __str__(self):
        return f"{self.project.name} - {self.file_path}"

class Dependency(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    source_module = models.CharField(max_length=255)
    target_module = models.CharField(max_length=255)
    dependency_type = models.CharField(max_length=50)  # import, function_call, etc.
    
    def __str__(self):
        return f"{self.source_module} -> {self.target_module}"

class Component(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    component_type = models.CharField(max_length=100)  # class, function, module, service
    file_path = models.CharField(max_length=500)
    line_number = models.IntegerField()
    relationships = models.JSONField(default=dict)  # Stores relationships with other components
    
    def __str__(self):
        return f"{self.project.name} - {self.name}"