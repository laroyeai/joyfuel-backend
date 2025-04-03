from utils.google_groups_handler import add_user_to_group
import logging

logger = logging.getLogger(__name__)

def add_member_to_group(email, group_email):
    """
    Add a member to a Google Group with error handling
    """
    try:
        success = add_user_to_group(email, group_email)
        if success:
            logger.info(f"Successfully added {email} to {group_email}")
            return True
        else:
            logger.error(f"Failed to add {email} to {group_email}")
            return False
    except Exception as e:
        logger.error(f"Error adding {email} to {group_email}: {str(e)}")
        return False 