"""
URL configuration for code_visualizer project.
"""
from django.contrib import admin
from django.urls import path, include
from analyzer.views import index_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('analyzer.urls')),
]