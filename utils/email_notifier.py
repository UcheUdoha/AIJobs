import os
import logging
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self):
        try:
            self.sg = SendGridAPIClient(api_key=os.environ['SENDGRID_API_KEY'])
        except Exception as e:
            logger.error(f"Failed to initialize SendGrid client: {str(e)}")
            raise
        
    def send_job_match_notification(self, user_email: str, matched_jobs: List[Dict]) -> bool:
        """
        Send email notification for matching jobs
        
        Args:
            user_email (str): Recipient's email address
            matched_jobs (List[Dict]): List of matching jobs with their scores
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Input validation
            if not user_email or not matched_jobs:
                logger.error("Invalid input: missing email or matched jobs")
                return False

            # Create email content with HTML formatting
            job_listings = ""
            for job in matched_jobs:
                try:
                    job_listings += f"""
                    <div style="margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px;">
                        <h3 style="color: #0066cc; margin: 0;">{job['title']} - {job['company']}</h3>
                        <p style="color: #666;"><strong>Location:</strong> {job['location']}</p>
                        <p style="color: #666;"><strong>Match Score:</strong> {job['match_score']}%</p>
                        <p style="margin-top: 10px;">{job['description'][:200]}...</p>
                    </div>
                    """
                except KeyError as e:
                    logger.error(f"Missing required job field: {str(e)}")
                    continue

            email_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <h2 style="color: #0066cc;">New Job Matches Found!</h2>
                    <p>We found new job opportunities that match your profile:</p>
                    {job_listings}
                    <p style="margin-top: 20px;">
                        <a href="http://localhost:5000" style="background-color: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                            View All Matches
                        </a>
                    </p>
                </body>
            </html>
            """

            message = Mail(
                from_email='notifications@jobmatchpro.com',
                to_emails=user_email,
                subject='New Job Matches Found - Job Match Pro',
                html_content=email_content
            )
            
            response = self.sg.send(message)
            success = response.status_code == 202
            
            if success:
                logger.info(f"Email notification sent successfully to {user_email}")
            else:
                logger.error(f"Failed to send email: Status code {response.status_code}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending email notification to {user_email}: {str(e)}")
            return False
