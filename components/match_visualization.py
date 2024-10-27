import streamlit as st
import plotly.graph_objects as go
from utils.text_similarity import TextSimilarity

def render_match_visualization(job_description: str):
    if 'resume_text' not in st.session_state:
        st.warning("Please upload your resume first to see match visualization")
        return
        
    similarity = TextSimilarity()
    
    # Calculate match score
    match_score = similarity.calculate_match_score(
        st.session_state['resume_text'],
        job_description
    )
    
    # Get matching keywords
    matching_keywords = similarity.get_matching_keywords(
        st.session_state['resume_text'],
        job_description
    )
    
    # Create gauge chart
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = match_score * 100,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Match Score"},
        gauge = {
            'axis': {'range': [0, 100]},
            'bar': {'color': "rgb(0, 102, 204)"},
            'steps': [
                {'range': [0, 33], 'color': "rgb(255, 230, 230)"},
                {'range': [33, 66], 'color': "rgb(255, 255, 204)"},
                {'range': [66, 100], 'color': "rgb(204, 255, 204)"}
            ]
        }
    ))
    
    st.plotly_chart(fig)
    
    # Display matching keywords
    st.subheader("Matching Keywords")
    st.write(", ".join(matching_keywords))
