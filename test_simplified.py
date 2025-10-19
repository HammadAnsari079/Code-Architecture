import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "code_visualizer.settings")
    django.setup()
    
    # Test that our simplified views can be imported
    try:
        from analyzer import views_simplified
        print("SUCCESS: Simplified views imported correctly")
    except Exception as e:
        print(f"ERROR: Failed to import simplified views: {e}")
        
    # Test that our URL configuration can be imported
    try:
        from analyzer import urls_simplified
        print("SUCCESS: Simplified URLs imported correctly")
    except Exception as e:
        print(f"ERROR: Failed to import simplified URLs: {e}")
        
    # Test that our templates exist
    template_files = [
        'simple_upload.html',
        'analysis_results.html'
    ]
    
    for template in template_files:
        template_path = os.path.join('templates', template)
        if os.path.exists(template_path):
            print(f"SUCCESS: Template {template} found")
        else:
            print(f"ERROR: Template {template} not found")