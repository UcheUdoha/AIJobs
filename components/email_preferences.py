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
    
    # Get current preferences
    preferences = db.get_email_preferences(user_id)
    
    # Email notification toggle
    is_enabled = st.toggle(
        "Enable email notifications for matching jobs",
        value=preferences['is_enabled']
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
                
            with st.spinner("Sending test email..."):
                notifier = EmailNotifier()
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
    
    # Display current email status
    if user_email:
        st.info(f"Current notification email: {user_email}")
    else:
        st.warning("No email address set. Please add your email to receive notifications.")
