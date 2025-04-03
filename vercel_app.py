import os
from django.core.wsgi import get_wsgi_application

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIProject.settings')
os.environ.setdefault('PYTHON_VERSION', '3.11')

# Initialize Django WSGI application
application = get_wsgi_application()

def handler(request):
    """
    Handle serverless requests
    """
    if request.method == 'OPTIONS':
        # Handle preflight requests
        response = application(request)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'X-Requested-With, Content-Type, Accept, Origin, Authorization'
        response['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    return application(request)

# Vercel serverless function handler
app = application 