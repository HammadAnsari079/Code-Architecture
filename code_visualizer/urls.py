"""
URL configuration for code_visualizer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from analyzer.views_simple_fixed import index_view, test_view, visualization_view, documentation_view
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('analyzer.urls')),
    path('simple/', include('analyzer.urls_simplified')),
    path('enhanced/', include('analyzer.urls_enhanced')),
    path('test/', test_view, name='test'),
    path('visualization/<int:project_id>/', visualization_view, name='visualization'),
    path('docs/', documentation_view, name='documentation'),
    path('', RedirectView.as_view(url='/simple/', permanent=False)),
]