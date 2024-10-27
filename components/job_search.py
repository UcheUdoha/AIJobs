import streamlit as st
from utils.database import Database
from utils.text_similarity import TextSimilarity

def render_job_search():
    st.header("Job Search")
    
    # Search filters
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("Search by job title or keywords")
    with col2:
        location = st.text_input("Location")
        
    # Get jobs from database
    db = Database()
    jobs = db.get_jobs(search_query, location)
    
    # Calculate match scores if resume is uploaded
    if 'resume_text' in st.session_state:
        similarity = TextSimilarity()
        
        for job in jobs:
            match_score = similarity.calculate_match_score(
                st.session_state['resume_text'],
                job['description']
            )
            job['match_score'] = int(match_score * 100)
            
        # Sort jobs by match score
        jobs = sorted(jobs, key=lambda x: x['match_score'], reverse=True)
    
    # Display jobs
    for job in jobs:
        with st.expander(f"{job['title']} - {job['company']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Location:** {job['location']}")
                st.write(f"**Description:**\n{job['description']}")
                
            with col2:
                if 'match_score' in job:
                    st.metric("Match Score", f"{job['match_score']}%")
                
                if st.button("Save Job", key=f"save_{job['id']}"):
                    user_id = st.session_state.get('user_id', 1)  # Default user_id for demo
                    db.save_bookmark(user_id, job['id'])
                    st.success("Job saved to bookmarks!")
