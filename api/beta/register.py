import os
import json
from django.core.wsgi import get_wsgi_application
from django.http import HttpResponse, JsonResponse
from django.conf import settings

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIProject.settings')
application = get_wsgi_application()

def handle_options(request):
    """Handle OPTIONS requests"""
    response = HttpResponse()
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type, Accept, Origin, Authorization"
    response["Access-Control-Allow-Credentials"] = "true"
    return response

def handler(request):
    """Handle serverless requests"""
    if request.method == 'OPTIONS':
        return handle_options(request)
    
    # For POST requests
    if request.method == 'POST':
        try:
            # Parse request body
            body = json.loads(request.body)
            email = body.get('email')
            platform = body.get('platform', 'web')
            
            if not email:
                return JsonResponse({
                    "message": "Email is required"
                }, status=400)
            
            # Import here to avoid circular imports
            from webflow_integration.views import send_beta_invitation
            from webflow_integration.models import BetaUser
            
            # Create or update beta user
            beta_user, created = BetaUser.objects.get_or_create(
                email=email,
                defaults={'platform': platform}
            )
            
            if not created:
                beta_user.platform = platform
                beta_user.save()
            
            # Send beta invitation
            success, message = send_beta_invitation(email, platform)
            
            if success:
                response_data = {
                    "message": "Successfully registered for beta testing!",
                    "email_sent": True
                }
                status_code = 200
            else:
                response_data = {
                    "message": "Registered for beta, but email failed to send",
                    "error": message
                }
                status_code = 500
            
            response = JsonResponse(response_data, status=status_code)
            response["Access-Control-Allow-Origin"] = "*"
            return response
            
        except Exception as e:
            response = JsonResponse({
                "message": "An error occurred while registering for beta",
                "error": str(e)
            }, status=500)
            response["Access-Control-Allow-Origin"] = "*"
            return response
    
    # For unsupported methods
    response = JsonResponse({
        "message": "Method not allowed"
    }, status=405)
    response["Access-Control-Allow-Origin"] = "*"
    return response 