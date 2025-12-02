from django.urls import path
from . import views

urlpatterns = [
    path('test/', views.test_view, name='test'),
    path('test-template/', views.test_template, name='test_template'),
    path('upload/', views.upload_files, name='upload_files'),
    path('visualization/<int:project_id>/', views.visualization_view, name='visualization'),
    path('flowchart/<int:project_id>/<str:file_name>/<str:function_name>/', views.get_flowchart_data, name='flowchart_data'),
    path('erd/<int:project_id>/', views.get_erd_data, name='erd_data'),
    path('dependency/<int:project_id>/', views.get_dependency_data, name='dependency_data'),
    path('component/<int:project_id>/', views.get_component_data, name='component_data'),
    path('docs/', views.documentation_view, name='documentation'),
    path('', views.index_view, name='index'),
]