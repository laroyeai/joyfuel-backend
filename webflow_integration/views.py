from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BetaUserSerializer
from .models import BetaUser
from django.conf import settings
import requests
import os
import uuid
import base64
import logging
from mailjet_rest import Client
from utils.cloudinary_handler import get_cloudinary_url
from .google_groups import add_member_to_group
from django.middleware.csrf import get_token
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def send_mailjet_email(to_email, subject, html_content):
    """
    Send email using Mailjet API
    """
    mailjet = Client(auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET), version='v3.1')
    data = {
        'Messages': [{
            "From": {
                "Email": settings.MAILJET_FROM_EMAIL,
                "Name": "JOYfuel Team"
            },
            "Headers": {
                "List-Unsubscribe": "<mailto:analyze@laroye.ai>",
                "X-Entity-Ref-ID": "joyfuel-team"
            },
            "SenderEmail": settings.MAILJET_FROM_EMAIL,
            "To": [{
                "Email": to_email
            }],
            "Subject": subject,
            "HTMLPart": html_content,
            "CustomID": "JOYfuelBetaTest",
            "TemplateLanguage": True,
            "EventPayload": "JOYfuelTeamProfile",
            "CustomCampaign": "joyfuel-beta",
            "Variables": {
                "company_logo": "https://res.cloudinary.com/da15opquj/image/upload/v1743551130/laroye-logo-working-mark-a_ultihf.png"
            }
        }]
    }
    
    try:
        result = mailjet.send.create(data=data)
        if result.status_code == 200:
            return True, result.json()
        else:
            error_message = f"Mailjet API Error: {result.status_code} - {result.text}"
            logger.error(error_message)
            return False, error_message
    except Exception as e:
        error_message = f"Exception while sending email: {str(e)}"
        logger.error(error_message)
        return False, error_message

def generate_confirmation_token():
    return str(uuid.uuid4())

def get_base64_image(image_path):
    """Helper function to read and encode images as base64"""
    with open(os.path.join(settings.BASE_DIR, 'static/email_assets', image_path), 'rb') as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

def send_beta_invitation(email, platform):
    """
    Send beta invitation email
    """
    try:
        # Get template
        template_path = 'templates/base_email.html'
        with open(template_path, 'r') as file:
            template_content = file.read()

        # Ensure Android link is properly encoded
        android_link = settings.ANDROID_BETA_LINK.strip()
        if not android_link.startswith('http'):
            android_link = 'https://' + android_link

        # Replace placeholders with Cloudinary URLs
        html_content = template_content\
            .replace('{{ background_url }}', get_cloudinary_url('emailbackground.png'))\
            .replace('{{ logo_url }}', get_cloudinary_url('joyfuellogo.png'))\
            .replace('{{ laroye_url }}', get_cloudinary_url('laroye.png'))\
            .replace('{{ ios_link }}', settings.IOS_TESTFLIGHT_LINK)\
            .replace('{{ android_link }}', android_link)

        # Send email
        success, result = send_mailjet_email(
            email,
            "Welcome to JOYfuel Beta!",
            html_content
        )

        if success:
            # If platform is Android, add to Google Group
            if platform.lower() == 'android':
                try:
                    add_member_to_group(email, settings.GOOGLE_ANDROID_BETA_GROUP)
                except Exception as e:
                    logger.error(f"Failed to add member to Google Group: {str(e)}")
                    # Continue even if Google Group addition fails
                    pass
            return True, None
        else:
            return False, f"Failed to send beta invitation: {result}"
    except Exception as e:
        return False, f"Error sending beta invitation: {str(e)}"

@api_view(['POST'])
def register_beta(request):
    try:
        email = request.data.get('email')
        platform = request.data.get('platform', 'web')
        
        if not email:
            return Response({
                "message": "Email is required"
            }, status=status.HTTP_400_BAD_REQUEST)
            
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
            return Response({
                "message": "Successfully registered for beta testing!",
                "email_sent": True
            })
        else:
            return Response({
                "message": "Registered for beta, but email failed to send",
                "error": message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in register_beta: {str(e)}")
        return Response({
            "message": "An error occurred while registering for beta",
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def confirm_newsletter(request, token):
    try:
        beta_user = BetaUser.objects.get(confirmation_token=token)
        if not beta_user.newsletter_confirmed:
            beta_user.newsletter_confirmed = True
            beta_user.save()
            return redirect(f"{settings.BASE_URL}/newsletter-confirmed")
        return redirect(f"{settings.BASE_URL}/already-confirmed")
    except BetaUser.DoesNotExist:
        return redirect(f"{settings.BASE_URL}/invalid-token")

@api_view(['POST'])
def unsubscribe(request):
    email = request.data.get('email')
    if not email:
        return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        beta_user = BetaUser.objects.get(email=email)
        beta_user.is_subscribed = False
        beta_user.save()
        return Response({"message": "Successfully unsubscribed"})
    except BetaUser.DoesNotExist:
        return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def test_email(request):
    """
    Test endpoint for sending emails
    """
    try:
        platform = request.data.get('platform', 'android').lower()
        email = request.data.get('email', settings.GOOGLE_ANDROID_BETA_GROUP)
        
        success, message = send_beta_invitation(email, platform)
        
        if success:
            return Response({
                "message": "Test email sent successfully! Check your inbox."
            })
        else:
            return Response({
                "error": message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        return Response({
            "error": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def test_google_groups(request):
    """
    Test endpoint to verify Google Groups integration
    POST data should include:
    {
        "email": "user@example.com"
    }
    """
    try:
        email = request.data.get('email')
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to add the user to the Android beta group
        group_email = settings.GOOGLE_GROUPS['android_beta']
        success = add_user_to_group(email, group_email)
        
        if success:
            return Response({
                "message": f"Successfully added {email} to group {group_email}",
                "status": "success"
            })
        else:
            return Response({
                "message": f"Failed to add {email} to group {group_email}",
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Exception as e:
        logger.error(f"Error in test_google_groups: {str(e)}")
        return Response({
            "message": f"Error: {str(e)}",
            "status": "error"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def test_registration(request):
    email = request.data.get('email')
    platform = request.data.get('platform')
    
    if platform == 'android':
        try:
            # Get Cloudinary URLs for images
            logo_url = get_cloudinary_url('joyfuellogo.png')
            laroye_url = get_cloudinary_url('laroye.png')
            background_url = get_cloudinary_url('emailbackground.png')
            
            # Create HTML version of the email with direct Play Store link
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to JOYfuel Beta!</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body style="margin: 0; padding: 0; width: 100%; height: 100%; color: #ffffff; font-family: 'Poppins', Arial, sans-serif;">
    <table width="100%" height="100%" border="0" cellpadding="0" cellspacing="0" style="background-image: url('{background_url}'); background-size: cover; background-position: center; background-color: transparent;">
        <tr>
            <td align="center" valign="top">
                <table width="600" border="0" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%;">
                    <tr>
                        <td style="padding: 40px 20px;">
                            <!-- Logo and Title -->
                            <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <img src="{logo_url}" alt="JOYfuel" style="max-width: 180px; height: auto; margin-bottom: 30px; display: inline-block;">
                                        <h1 style="color: #ffffff; font-size: 32px; margin: 0; font-weight: 700; letter-spacing: 0.5px;">Welcome to JOYfuel Beta!</h1>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Content Box -->
                            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="margin: 40px 0;">
                                <tr>
                                    <td style="padding: 30px; background-color: rgba(0, 0, 0, 0.75); border-radius: 10px;">
                                        <p style="font-size: 18px; line-height: 1.6; margin-bottom: 40px;">Thank you for joining our beta testing program! We're excited to have you help us make JOYfuel even better.</p>
                                        
                                        <div style="background-color: rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 8px; margin-bottom: 30px;">
                                            <p style="margin-bottom: 25px;">Click the button below to start testing JOYfuel:</p>
                                            
                                            <a href="{settings.ANDROID_BETA_LINK}" style="display: inline-block; background-color: #FF6B2C; color: white; padding: 15px 30px; text-decoration: none; border-radius: 8px; margin: 10px 0 25px 0; font-weight: bold;">Join JOYfuel Beta Testing</a>
                                            
                                            <p style="margin-top: 25px;">Once you click the link, you'll be taken directly to the Play Store where you can download JOYfuel. Make sure to use the same email address ({email}) that you used to sign up for the beta program.</p>
                                        </div>
                                        
                                        <p style="font-size: 18px; line-height: 1.6; margin-bottom: 40px;">Your feedback is incredibly valuable to us and will help shape the future of JOYfuel. Feel free to share your thoughts and suggestions as you use the app!</p>
                                        
                                        <p style="font-size: 18px; line-height: 1.6; margin-bottom: 10px;">Best regards,</p>
                                        <p style="font-size: 18px; line-height: 1.6; margin-bottom: 40px;">The JOYfuel Team</p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Laroye Image -->
                            <table width="100%" border="0" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="right">
                                        <img src="{laroye_url}" alt="Laroye" style="width: 500px; height: auto; display: inline-block; margin-top: 20px;">
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
            
            # Send welcome email via Mailjet
            success, response = send_mailjet_email(
                email,
                "Welcome to JOYfuel Beta Testing!",
                html_content
            )
            
            if success:
                return Response({
                    "message": "Successfully sent welcome email",
                    "status": "success"
                })
            else:
                return Response({
                    "message": "Failed to send welcome email",
                    "error": response,
                    "status": "error"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            return Response({
                "message": "Error processing registration",
                "error": str(e),
                "status": "error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    return Response({"message": "Invalid platform specified"}, status=400)

@api_view(['GET'])
def get_csrf_token(request):
    """
    Get CSRF token for frontend
    """
    return JsonResponse({'csrfToken': get_token(request)}) 