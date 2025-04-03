from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_google_groups_service():
    """
    Creates and returns an authorized Google Groups API service instance
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=['https://www.googleapis.com/auth/admin.directory.group',
                   'https://www.googleapis.com/auth/admin.directory.group.member']
        )
        
        # Create delegated credentials
        delegated_credentials = credentials.with_subject(settings.GOOGLE_ADMIN_EMAIL)
        
        # Build the service
        service = build('admin', 'directory_v1', credentials=delegated_credentials)
        return service
    except Exception as e:
        logger.error(f"Error creating Google Groups service: {str(e)}")
        raise

def add_user_to_group(email, group_email):
    """
    Adds a user to the specified Google Group
    
    Args:
        email (str): The email address of the user to add
        group_email (str): The email address of the Google Group
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        service = get_google_groups_service()
        
        # Prepare the member object
        member = {
            'email': email,
            'role': 'MEMBER'
        }
        
        # Add member to the group
        result = service.members().insert(
            groupKey=group_email,
            body=member
        ).execute()
        
        logger.info(f"Successfully added {email} to group {group_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding user {email} to group {group_email}: {str(e)}")
        return False

def remove_user_from_group(email, group_email):
    """
    Removes a user from the specified Google Group
    
    Args:
        email (str): The email address of the user to remove
        group_email (str): The email address of the Google Group
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        service = get_google_groups_service()
        
        # Remove member from the group
        service.members().delete(
            groupKey=group_email,
            memberKey=email
        ).execute()
        
        logger.info(f"Successfully removed {email} from group {group_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error removing user {email} from group {group_email}: {str(e)}")
        return False 