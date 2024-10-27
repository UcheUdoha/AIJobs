import streamlit as st
from utils.database import Database
from utils.advanced_matcher import AdvancedMatcher
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def render_job_search():
    st.header("Job Search")
    
    # Get user's resume location
    db = Database()
    user_id = st.session_state.get('user_id', 1)
    resume_location = None
    if 'resume_location' in st.session_state:
        resume_location = st.session_state['resume_location']
    
    # Search filters
    col1, col2 = st.columns(2)
    with col1:
        search_query = st.text_input("Search by job title or keywords")
    with col2:
        # Auto-fill location from resume if available
        default_location = resume_location if resume_location else ""
        location = st.text_input("Location", value=default_location)
        
    # Get jobs from database with location matching
    jobs = db.get_jobs(search_query, location, resume_location)
    
    # Calculate match scores if resume is uploaded
    if 'resume_text' in st.session_state:
        matcher = AdvancedMatcher()
        
        for job in jobs:
            match_results = matcher.calculate_match_score(
                st.session_state['resume_text'],
                job['description']
            )
            
            # Include location score in overall match calculation
            location_score = float(job['location_score'])
            match_results['location_score'] = round(location_score * 100, 2)
            
            # Update overall score to include location matching
            match_results['overall_score'] = round(
                (match_results['overall_score'] * 0.7 + location_score * 100 * 0.3), 2
            )
            
            job.update(match_results)
            
        # Sort jobs by overall match score
        jobs = sorted(jobs, key=lambda x: x['overall_score'], reverse=True)
    
    # Display jobs
    for job in jobs:
        with st.expander(f"{job['title']} - {job['company']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Location:** {job['location']}")
                st.write(f"**Description:**\n{job['description']}")
                
                if 'matching_skills' in job and job['matching_skills']:
                    st.write("**Matching Skills:**")
                    st.write(", ".join(job['matching_skills']))
                
            with col2:
                if 'overall_score' in job:
                    # Create gauge chart for overall score
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=job['overall_score'],
                        domain={'x': [0, 1], 'y': [0, 1]},
                        title={'text': "Overall Match"},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': "rgb(0, 102, 204)"},
                            'steps': [
                                {'range': [0, 40], 'color': "rgb(255, 230, 230)"},
                                {'range': [40, 70], 'color': "rgb(255, 255, 204)"},
                                {'range': [70, 100], 'color': "rgb(204, 255, 204)"}
                            ]
                        }
                    ))
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Create detailed scores visualization
                    categories = ['Semantic', 'Skills', 'Location']
                    scores = [
                        job['semantic_score'],
                        job['skill_score'],
                        job['location_score']
                    ]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Bar(
                        x=categories,
                        y=scores,
                        marker_color=['rgb(99, 110, 250)', 'rgb(239, 85, 59)', 'rgb(0, 204, 150)']
                    ))
                    
                    fig.update_layout(
                        title="Detailed Match Scores",
                        yaxis_range=[0, 100],
                        showlegend=False,
                        height=200
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                if st.button("Save Job", key=f"save_{job['id']}"):
                    db.save_bookmark(user_id, job['id'])
                    st.success("Job saved to bookmarks!")
