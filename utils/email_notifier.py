import os
import logging
import time
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import List, Dict
from sendgrid.base_interface import BaseInterface
from python_http_client import exceptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailNotifier:
    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        try:
            self.sg = SendGridAPIClient(api_key=os.environ['SENDGRID_API_KEY'])
            self.max_retries = max_retries
            self.retry_delay = retry_delay
        except Exception as e:
            logger.error(f"Failed to initialize SendGrid client: {str(e)}")
            raise

    def send_with_retry(self, message: Mail) -> tuple[bool, str]:
        """Send email with retry mechanism"""
        for attempt in range(self.max_retries):
            try:
                response = self.sg.send(message)
                if response.status_code == 202:
                    logger.info(f"Email sent successfully on attempt {attempt + 1}")
                    return True, "Email sent successfully"
                else:
                    logger.warning(f"Unexpected status code {response.status_code} on attempt {attempt + 1}")
                    
            except exceptions.BadRequestsError as e:
                error_msg = f"Bad request error: {str(e.body)}"
                logger.error(f"Attempt {attempt + 1}: {error_msg}")
                return False, error_msg
                
            except exceptions.UnauthorizedError:
                error_msg = "Invalid SendGrid API key"
                logger.error(f"Attempt {attempt + 1}: {error_msg}")
                return False, error_msg
                
            except exceptions.ForbiddenError:
                error_msg = "SendGrid account requires verification or has been blocked"
                logger.error(f"Attempt {attempt + 1}: {error_msg}")
                return False, error_msg
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1}: Unexpected error: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False, f"Failed to send email after {self.max_retries} attempts"
                
        return False, f"Failed to send email after {self.max_retries} attempts"

    def send_job_match_notification(self, user_email: str, matched_jobs: List[Dict]) -> tuple[bool, str]:
        """Send email notification for matching jobs with enhanced error handling"""
        try:
            # Input validation
            if not user_email or not matched_jobs:
                return False, "Invalid input: missing email or matched jobs"

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
            
            return self.send_with_retry(message)
            
        except Exception as e:
            error_msg = f"Error preparing email notification: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
