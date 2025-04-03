import os
import cloudinary
import cloudinary.uploader
from django.conf import settings

def upload_images():
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET
    )
    
    # Path to email assets
    assets_dir = os.path.join(settings.BASE_DIR, 'static', 'email_assets')
    
    # List of images to upload
    images = ['joyfuellogo.png', 'laroye.png', 'emailbackground.png']
    
    results = {}
    for image_name in images:
        image_path = os.path.join(assets_dir, image_name)
        if os.path.exists(image_path):
            print(f"Uploading {image_name}...")
            try:
                # Upload the image
                result = cloudinary.uploader.upload(
                    image_path,
                    public_id=f"email_assets/{os.path.splitext(image_name)[0]}",  # Keep original name without extension
                    overwrite=True  # Update if already exists
                )
                results[image_name] = {
                    'status': 'success',
                    'url': result['secure_url']
                }
                print(f"✓ Successfully uploaded {image_name}")
                print(f"  URL: {result['secure_url']}")
            except Exception as e:
                results[image_name] = {
                    'status': 'error',
                    'error': str(e)
                }
                print(f"✗ Failed to upload {image_name}: {str(e)}")
        else:
            print(f"✗ Image not found: {image_path}")
            results[image_name] = {
                'status': 'error',
                'error': 'File not found'
            }
    
    return results

if __name__ == '__main__':
    # This allows running the script directly
    import django
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AIProject.settings')
    django.setup()
    upload_images() 