import streamlit as st
from utils.database import Database
from utils.email_notifier import EmailNotifier
import re

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def render_email_preferences():
    st.header("Email Notification Settings")
    
    db = Database()
    user_id = st.session_state.get('user_id', 1)
    
    # Check SendGrid verification status
    try:
        notifier = EmailNotifier()
        is_verified, verification_message = notifier.get_verification_status()
        
        if not is_verified:
            st.warning(
                verification_message + "\n\n"
                "While verification is pending, email notifications will not be sent. "
                "This won't affect your ability to save preferences."
            )
    except Exception as e:
        st.error(f"Error connecting to email service: {str(e)}")
        return
    
    # Get current preferences
    preferences = db.get_email_preferences(user_id)
    
    # Email notification toggle
    is_enabled = st.toggle(
        "Enable email notifications for matching jobs",
        value=preferences['is_enabled'],
        help="Toggle email notifications on/off"
    )
    
    # Minimum match score slider
    min_match_score = st.slider(
        "Minimum match score for notifications",
        min_value=0,
        max_value=100,
        value=preferences['min_match_score'],
        step=5,
        help="You will receive notifications only for jobs with match scores above this threshold"
    )
    
    # Get current email
    user_email = db.get_user_email(user_id)
    
    # Email input field
    new_email = st.text_input(
        "Update Email Address",
        value=user_email if user_email else "",
        help="Enter your email address for job notifications"
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Preferences"):
            if new_email and not is_valid_email(new_email):
                st.error("Please enter a valid email address")
            else:
                # Update email if changed
                if new_email and new_email != user_email:
                    if db.update_user_email(user_id, new_email):
                        st.success("Email updated successfully!")
                    else:
                        st.error("Failed to update email address")
                
                # Update preferences
                db.update_email_preferences(user_id, is_enabled, min_match_score)
                st.success("Email preferences updated successfully!")
    
    with col2:
        if st.button("Send Test Email"):
            if not user_email:
                st.error("Please save your email address first")
                return
                
            if not is_valid_email(user_email):
                st.error("Invalid email address. Please update your email")
                return
            
            if not is_verified:
                st.error(
                    "Cannot send test email: SendGrid account needs verification. "
                    "Please check verification status above."
                )
                return
                
            with st.spinner("Sending test email..."):
                test_job = {
                    'title': 'Test Job Position',
                    'company': 'Test Company',
                    'location': 'Test Location',
                    'description': 'This is a test job notification.',
                    'match_score': min_match_score
                }
                
                success, message = notifier.send_job_match_notification(user_email, [test_job])
                if success:
                    st.success("Test email sent successfully! Please check your inbox.")
                else:
                    st.error(f"Failed to send test email: {message}")
    
    # Display verification and email status information
    st.markdown("---")
    st.subheader("Email System Status")
    
    if is_verified:
        st.success("✅ Email system is verified and ready to send notifications")
    else:
        st.warning(
            "⚠️ Email system verification pending\n\n"
            "Please follow these steps to complete verification:\n"
            "1. Check your email for verification instructions from SendGrid\n"
            "2. Click the verification link in the email\n"
            "3. If you haven't received the email, visit the [SendGrid Sender Verification](https://app.sendgrid.com/settings/sender_auth) page\n"
            "4. Complete the verification process\n"
            "5. Return to this page and refresh to update the status"
        )
    
    if user_email:
        st.info(f"Current notification email: {user_email}")
    else:
        st.warning("No email address set. Please add your email to receive notifications.")
