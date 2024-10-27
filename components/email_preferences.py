import streamlit as st
from utils.database import Database

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
    
    if st.button("Save Preferences"):
        db.update_email_preferences(user_id, is_enabled, min_match_score)
        st.success("Email preferences updated successfully!")
