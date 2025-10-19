from django.urls import path
from . import views_simple_fixed as views_simple

urlpatterns = [
    path('test/', views_simple.test_view, name='test'),
    path('test-template/', views_simple.test_template, name='test_template'),
    path('upload/', views_simple.upload_files, name='upload_files'),
    path('visualization/<int:project_id>/', views_simple.visualization_view, name='visualization'),
    path('flowchart/<int:project_id>/<str:file_name>/<str:function_name>/', views_simple.get_flowchart_data, name='flowchart_data'),
    path('docs/', views_simple.documentation_view, name='documentation'),
    path('', views_simple.index_view, name='index'),
]