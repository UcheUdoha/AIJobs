import streamlit as st
from utils.database import Database
from utils.email_notifier import EmailNotifier

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
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Save Preferences"):
            db.update_email_preferences(user_id, is_enabled, min_match_score)
            st.success("Email preferences updated successfully!")
    
    with col2:
        if st.button("Send Test Email"):
            user_email = db.get_user_email(user_id)
            if user_email:
                notifier = EmailNotifier()
                test_job = {
                    'title': 'Test Job Position',
                    'company': 'Test Company',
                    'location': 'Test Location',
                    'description': 'This is a test job notification.',
                    'match_score': min_match_score
                }
                
                success = notifier.send_job_match_notification(user_email, [test_job])
                if success:
                    st.success("Test email sent successfully! Please check your inbox.")
                else:
                    st.error("Failed to send test email. Please try again later.")
            else:
                st.error("User email not found. Please make sure your email is set up correctly.")
    
    # Display current email
    user_email = db.get_user_email(user_id)
    if user_email:
        st.info(f"Notifications will be sent to: {user_email}")
    else:
        st.warning("No email address found. Please contact support to update your email.")
