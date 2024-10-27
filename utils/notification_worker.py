import logging
from utils.database import Database
from utils.email_notifier import EmailNotifier
import time
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_notifications():
    """
    Process pending job match notifications
    """
    try:
        db = Database()
        email_notifier = EmailNotifier()
        
        # Get all users with email notifications enabled
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT u.id, u.email, ep.min_match_score
                FROM users u
                JOIN email_preferences ep ON u.id = ep.user_id
                WHERE ep.is_enabled = true
            """)
            users = cur.fetchall()
        
        for user_id, email, min_score in users:
            try:
                # Get unnotified matches above the minimum score
                matches = db.get_unnotified_matches(user_id, min_score)
                
                if matches:
                    logger.info(f"Processing {len(matches)} matches for user {email}")
                    # Send email notification
                    if email_notifier.send_job_match_notification(email, matches):
                        # Mark matches as notified
                        job_ids = [job['id'] for job in matches]
                        db.mark_matches_as_notified(user_id, job_ids)
                        logger.info(f"Successfully processed notifications for user {email}")
                    else:
                        logger.error(f"Failed to send notifications to user {email}")
                        
            except Exception as e:
                logger.error(f"Error processing notifications for user {email}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error in notification processing: {str(e)}")

def setup_notification_worker():
    """
    Set up the notification worker to run periodically
    """
    def worker():
        logger.info("Starting notification worker")
        while True:
            try:
                process_notifications()
            except Exception as e:
                logger.error(f"Critical error in notification worker: {str(e)}")
            finally:
                time.sleep(3600)  # Run every hour
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    logger.info("Notification worker initialized")
