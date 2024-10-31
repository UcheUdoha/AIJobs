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
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_app():
    """Initialize application components with proper error handling"""
    try:
        with st.spinner("Initializing application..."):
            # Initialize database connection
            db = Database()
            if not db.test_connection():
                st.error("Failed to connect to database. Please check your database configuration.")
                return False

            # Apply schema updates
            try:
                apply_schema_updates()
            except Exception as e:
                logger.error(f"Schema update error: {str(e)}")
                st.warning("Schema updates encountered some issues but application can continue.")

            # Start background workers
            try:
                setup_notification_worker()
                setup_scraping_worker()
            except Exception as e:
                logger.error(f"Worker initialization error: {str(e)}")
                st.warning("Background workers failed to start but application can continue.")

            return True
    except Exception as e:
        st.error("Error initializing application. Please try again.")
        logger.error(f"Initialization error: {str(e)}")
        return False

def render_app():
    """Render main application with error boundaries"""
    try:
        # Page configuration
        st.set_page_config(
            page_title="Job Match Pro",
            page_icon="💼",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Load custom CSS
        try:
            with open("assets/style.css") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception as e:
            logger.error(f"Error loading CSS: {str(e)}")

        # Initialize session state
        if 'user_id' not in st.session_state:
            st.session_state['user_id'] = 1  # Default user for demo
        if 'page' not in st.session_state:
            st.session_state['page'] = "Upload Resume"
        if 'error_boundary' not in st.session_state:
            st.session_state['error_boundary'] = None

        # Sidebar navigation
        st.sidebar.title("Navigation")
        page = st.sidebar.radio(
            "Go to",
            ["Upload Resume", "Job Search", "Saved Jobs", "Interview Practice", "Analytics Dashboard", "Email Settings"],
            key="navigation"
        )

        # Error boundary for main content
        try:
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
                    
                    if not bookmarked_jobs:
                        st.info("No saved jobs found. Start bookmarking jobs you're interested in!")
                    else:
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

        except Exception as e:
            logger.error(f"Error in page rendering: {str(e)}")
            st.error("An error occurred while loading this page. Please try refreshing or contact support.")
            st.session_state['error_boundary'] = str(e)

    except Exception as e:
        logger.error(f"Critical error in application: {str(e)}")
        st.error("A critical error occurred. Please refresh the page or contact support.")

# Initialize and run application
if initialize_app():
    render_app()
else:
    st.stop()
