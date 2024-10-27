import streamlit as st
from utils.nlp_processor import NLPProcessor
from utils.database import Database
from utils.file_handler import FileHandler
import PyPDF2
from docx import Document
import io

def extract_text_from_pdf(file):
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.getvalue()))
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_text_from_docx(file):
    doc = Document(io.BytesIO(file.getvalue()))
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    return text

def render_resume_upload():
    st.header("Upload Your Resume")
    
    uploaded_file = st.file_uploader("Choose your resume", type=['pdf', 'docx'])
    
    if uploaded_file is not None:
        file_handler = FileHandler()
        file_path, error = file_handler.save_file(uploaded_file)
        
        if error:
            st.error(error)
            return
            
        # Extract text based on file type
        if uploaded_file.name.lower().endswith('.pdf'):
            resume_text = extract_text_from_pdf(uploaded_file)
        else:  # docx
            resume_text = extract_text_from_docx(uploaded_file)
        
        # Process resume
        nlp_processor = NLPProcessor()
        skills = nlp_processor.extract_skills(resume_text)
        
        # Store in session state
        st.session_state['resume_text'] = resume_text
        st.session_state['skills'] = skills
        st.session_state['resume_file_path'] = file_path
        
        # Display extracted information
        st.subheader("Extracted Skills")
        st.write(", ".join(skills))
        
        # Preview uploaded resume
        with st.expander("Preview Resume Text"):
            st.text_area("Resume Content", resume_text, height=300)
        
        # Save to database
        if st.button("Save Resume"):
            db = Database()
            user_id = st.session_state.get('user_id', 1)  # Default user_id for demo
            resume_id = db.save_resume(
                user_id=user_id,
                resume_text=resume_text,
                extracted_skills=list(skills),
                file_path=file_path,
                file_type=uploaded_file.name.split('.')[-1].lower()
            )
            st.success(f"Resume saved successfully! ID: {resume_id}")
