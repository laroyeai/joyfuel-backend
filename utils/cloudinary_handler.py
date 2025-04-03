import cloudinary
import cloudinary.uploader
from django.conf import settings
import os

def upload_image_to_cloudinary(image_path):
    """Upload an image to Cloudinary and return its URL"""
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET
    )
    
    # Upload the image
    result = cloudinary.uploader.upload(image_path)
    
    # Return the secure URL
    return result['secure_url']

def get_cloudinary_url(image_name):
    """Get the Cloudinary URL for an image in the static/email_assets directory"""
    image_path = os.path.join(settings.BASE_DIR, 'static/email_assets', image_name)
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image {image_name} not found in static/email_assets")
    
    return upload_image_to_cloudinary(image_path) 