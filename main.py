import streamlit as st
from components.resume_upload import render_resume_upload
from components.job_search import render_job_search
from components.match_visualization import render_match_visualization
from components.email_preferences import render_email_preferences
from components.analytics_dashboard import render_analytics_dashboard
from components.interview_practice import render_interview_practice
from utils.database import Database
from utils.notification_worker import setup_notification_worker
from utils.scraping_worker import setup_scraping_worker
from apply_schema_updates import apply_schema_updates

# Apply schema updates
apply_schema_updates()

# Start workers
setup_notification_worker()
setup_scraping_worker()

# Page configuration
st.set_page_config(
    page_title="Job Match Pro",
    page_icon="💼",
    layout="wide"
)

# Load custom CSS
with open("assets/style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = 1  # Default user for demo

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Upload Resume", "Job Search", "Saved Jobs", "Interview Practice", "Analytics Dashboard", "Email Settings"]
)

# Main content
st.title("Job Match Pro")

# Render selected page with loading states
if page == "Upload Resume":
    with st.spinner("Loading resume upload..."):
        render_resume_upload()
        
elif page == "Job Search":
    with st.spinner("Loading job search..."):
        render_job_search()
        
elif page == "Email Settings":
    with st.spinner("Loading email preferences..."):
        render_email_preferences()
        
elif page == "Analytics Dashboard":
    with st.spinner("Loading analytics..."):
        render_analytics_dashboard()
        
elif page == "Interview Practice":
    with st.spinner("Loading interview practice..."):
        render_interview_practice()
        
else:  # Saved Jobs
    with st.spinner("Loading saved jobs..."):
        st.header("Saved Jobs")
        db = Database()
        bookmarked_jobs = db.get_bookmarks(st.session_state['user_id'])
        
        for job in bookmarked_jobs:
            with st.expander(f"{job['title']} - {job['company']}"):
                st.write(f"**Location:** {job['location']}")
                st.write(f"**Description:**\n{job['description']}")
                
                # Show match score if resume is uploaded
                if 'resume_text' in st.session_state:
                    with st.spinner("Calculating match score..."):
                        render_match_visualization(job['description'])

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by Job Match Pro")
