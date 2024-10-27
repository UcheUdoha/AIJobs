import streamlit as st
from components.resume_upload import render_resume_upload
from components.job_search import render_job_search
from components.match_visualization import render_match_visualization
from utils.database import Database

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
page = st.sidebar.radio("Go to", ["Upload Resume", "Job Search", "Saved Jobs"])

if page == "Upload Resume":
    render_resume_upload()
    
elif page == "Job Search":
    render_job_search()
    
else:  # Saved Jobs
    st.header("Saved Jobs")
    db = Database()
    bookmarked_jobs = db.get_bookmarks(st.session_state['user_id'])
    
    for job in bookmarked_jobs:
        with st.expander(f"{job['title']} - {job['company']}"):
            st.write(f"**Location:** {job['location']}")
            st.write(f"**Description:**\n{job['description']}")
            
            # Show match score if resume is uploaded
            if 'resume_text' in st.session_state:
                render_match_visualization(job['description'])

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Made with ❤️ by Job Match Pro")