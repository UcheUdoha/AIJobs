from utils.database import Database
from utils.email_notifier import EmailNotifier

def process_notifications():
    """
    Process pending job match notifications
    """
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
        # Get unnotified matches above the minimum score
        matches = db.get_unnotified_matches(user_id, min_score)
        
        if matches:
            # Send email notification
            if email_notifier.send_job_match_notification(email, matches):
                # Mark matches as notified
                job_ids = [job['id'] for job in matches]
                db.mark_matches_as_notified(user_id, job_ids)

def setup_notification_worker():
    """
    Set up the notification worker to run periodically
    """
    import time
    import threading
    
    def worker():
        while True:
            try:
                process_notifications()
            except Exception as e:
                print(f"Error in notification worker: {str(e)}")
            time.sleep(3600)  # Run every hour
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
