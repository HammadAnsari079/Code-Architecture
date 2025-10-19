from django.urls import path
from . import views_enhanced as views

urlpatterns = [
    path('enhanced-visualization/<int:project_id>/', views.enhanced_visualization_view, name='enhanced_visualization'),
    path('api/flowchart/<int:project_id>/<path:file_path>/<str:function_name>/', views.get_function_flowchart, name='get_function_flowchart'),
    path('api/erd/<int:project_id>/', views.get_database_erd, name='get_database_erd'),
    path('api/code-snippet/<path:file_path>/<int:line_number>/', views.get_code_snippet, name='get_code_snippet'),
    path('api/jump-to-code/', views.jump_to_code, name='jump_to_code'),
]