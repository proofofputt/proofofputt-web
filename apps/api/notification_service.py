import data_manager
from email_utility import send_email
import logging
import json
import os

logger = logging.getLogger(__name__)

def _should_send_email(player_id, preference_key):
    """Checks if a user wants to receive a specific type of email."""
    try:
        prefs_json = data_manager.get_player_info(player_id).get('notification_preferences')
        if prefs_json:
            prefs = json.loads(prefs_json)
            # Default to True if the key is missing from their saved preferences
            return prefs.get(preference_key, True)
    except Exception as e:
        logger.error(f"Could not parse notification preferences for player {player_id}: {e}")
    # Default to sending the email if preferences are not set or invalid
    return True

def create_in_app_notification(player_id, notification_type, message, details=None, link_path=None):
    """Creates an in-app notification by calling the data manager."""
    data_manager.create_in_app_notification(player_id, notification_type, message, details, link_path)

def send_welcome_email(player_id):
    """Sends a welcome email to a new player."""
    if not _should_send_email(player_id, 'product_updates'):
        logger.info(f"Skipping welcome email for player {player_id} due to preferences.")
        return

    player = data_manager.get_player_info(player_id) # This should be get_player_info
    if not player:
        return

    subject = "Welcome to Proof of Putt!"
    body_html = f"""<p>Hi {player['name']},</p><p>Welcome to Proof of Putt! We're excited to have you on board.</p><p>To get started, calibrate your camera and start your first putting session from your dashboard.</p><p>Happy putting!</p><p>The Proof of Putt Team</p>"""
    body_text = f"Hi {player['name']},\n\nWelcome to Proof of Putt! We're excited to have you on board. To get started, calibrate your camera and start your first putting session from your dashboard.\n\nHappy putting!\nThe Proof of Putt Team"

    send_email(player['email'], subject, body_html, body_text)

def send_password_reset_email(to_email, player_name, token):
    """Sends a password reset email to the user."""
    # Password resets are critical and should ignore user preferences
    frontend_url = os.environ.get('FRONTEND_URL', 'https://www.proofofputt.com')
    reset_link = f"{frontend_url}/reset-password?token={token}"
    
    subject = "Your Proof of Putt Password Reset Request"
    body_html = f"""<p>Hello {player_name},</p><p>We received a request to reset your password for your Proof of Putt account.</p><p>Please click the link below to set a new password. This link will expire in one hour.</p><p><a href="{reset_link}" style="padding: 10px 15px; background-color: #d3ce34; color: #042B04; text-decoration: none; border-radius: 5px;">Reset Your Password</a></p><p>If you did not request a password reset, please ignore this email or contact support if you have concerns.</p><p>Thanks,<br>The Proof of Putt Team</p>"""
    body_text = f"Hello {player_name},\n\nWe received a request to reset your password for your Proof of Putt account.\nPlease visit the following link to set a new password. This link will expire in one hour:\n{reset_link}\n\nIf you did not request a password reset, please ignore this email.\n\nThanks,\nThe Proof of Putt Team"

    send_email(to_email, subject, body_html, body_text)
