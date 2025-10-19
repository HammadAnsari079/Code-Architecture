from django.urls import path
from . import views_simplified

urlpatterns = [
    path('', views_simplified.simple_upload_view, name='simple_upload'),
    path('results/<int:project_id>/', views_simplified.analysis_results_view, name='analysis_results'),
    path('api/process/', views_simplified.process_files_view, name='process_files'),
    path('api/flowchart/<int:project_id>/', views_simplified.flowchart_data_view, name='flowchart_data'),
    path('api/database/<int:project_id>/', views_simplified.database_data_view, name='database_data'),
]