import streamlit as st
from utils.nlp_processor import NLPProcessor
from utils.database import Database

def render_resume_upload():
    st.header("Upload Your Resume")
    
    uploaded_file = st.file_uploader("Choose your resume (TXT format)", type=['txt'])
    
    if uploaded_file is not None:
        resume_text = uploaded_file.getvalue().decode("utf-8")
        
        # Process resume
        nlp_processor = NLPProcessor()
        skills = nlp_processor.extract_skills(resume_text)
        
        # Store in session state
        st.session_state['resume_text'] = resume_text
        st.session_state['skills'] = skills
        
        # Display extracted information
        st.subheader("Extracted Skills")
        st.write(", ".join(skills))
        
        # Save to database
        if st.button("Save Resume"):
            db = Database()
            user_id = st.session_state.get('user_id', 1)  # Default user_id for demo
            resume_id = db.save_resume(user_id, resume_text, list(skills))
            st.success(f"Resume saved successfully! ID: {resume_id}")
