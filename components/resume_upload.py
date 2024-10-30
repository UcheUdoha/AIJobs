import streamlit as st
from utils.nlp_processor import NLPProcessor
from utils.database import Database
from utils.file_handler import FileHandler
import io
import logging
from typing import Tuple, Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import optional dependencies with error handling
PDF_SUPPORT = False
DOCX_SUPPORT = False

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    st.warning("PDF support is not available. Please install python-pdf2 package.")

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    st.warning("DOCX support is not available. Please install python-docx package.")

def extract_text_from_pdf(file) -> Tuple[Optional[str], Optional[str]]:
    """Extract text from PDF with enhanced error handling"""
    if not PDF_SUPPORT:
        return None, "PDF support is not available. Please upload a DOCX file instead."
    
    try:
        start_time = time.time()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.getvalue()))
        text = ""
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                text += page.extract_text() + "\n"
            except Exception as e:
                logger.error(f"Error extracting text from page {page_num}: {str(e)}")
                continue
        
        if not text.strip():
            return None, "Could not extract text from PDF. The file might be scanned or protected."
        
        logger.info(f"PDF text extraction completed in {time.time() - start_time:.2f} seconds")
        return text, None
        
    except Exception as e:
        logger.error(f"Error processing PDF file: {str(e)}")
        return None, f"Error processing PDF file: {str(e)}"

def extract_text_from_docx(file) -> Tuple[Optional[str], Optional[str]]:
    """Extract text from DOCX with enhanced error handling"""
    if not DOCX_SUPPORT:
        return None, "DOCX support is not available. Please upload a PDF file instead."
    
    try:
        start_time = time.time()
        doc = Document(io.BytesIO(file.getvalue()))
        text = ""
        
        for para in doc.paragraphs:
            try:
                text += para.text + "\n"
            except Exception as e:
                logger.error(f"Error extracting paragraph text: {str(e)}")
                continue
        
        if not text.strip():
            return None, "Could not extract text from DOCX. The file might be corrupted."
        
        logger.info(f"DOCX text extraction completed in {time.time() - start_time:.2f} seconds")
        return text, None
        
    except Exception as e:
        logger.error(f"Error processing DOCX file: {str(e)}")
        return None, f"Error processing DOCX file: {str(e)}"

def render_resume_upload():
    st.header("Upload Your Resume")
    
    # Show supported file types
    supported_types = []
    if PDF_SUPPORT:
        supported_types.append("PDF")
    if DOCX_SUPPORT:
        supported_types.append("DOCX")
    
    if not supported_types:
        st.error("No file type support available. Please contact the administrator.")
        return
    
    st.info(f"Supported file types: {', '.join(supported_types)}")
    
    # Add upload guidelines
    st.markdown("""
    ### Upload Guidelines:
    1. File must be in PDF or DOCX format
    2. Maximum file size: 10MB
    3. Text must be selectable (not scanned)
    4. File should not be password protected
    """)
    
    uploaded_file = st.file_uploader("Choose your resume", type=['pdf', 'docx'])
    
    if uploaded_file is not None:
        try:
            # Show upload status
            status_container = st.empty()
            status_container.info("Processing your resume...")
            
            # Validate file type before processing
            file_type = uploaded_file.name.split('.')[-1].lower()
            if file_type not in ['pdf', 'docx']:
                st.error("Invalid file type. Please upload a PDF or DOCX file.")
                return
                
            if file_type == 'pdf' and not PDF_SUPPORT:
                st.error("PDF support is not available. Please upload a DOCX file.")
                return
            elif file_type == 'docx' and not DOCX_SUPPORT:
                st.error("DOCX support is not available. Please upload a PDF file.")
                return
            
            # Check if preview is already cached
            cache_key = f"preview_{hash(uploaded_file.getvalue())}"
            if cache_key in st.session_state:
                resume_text = st.session_state[cache_key]
                logger.info("Using cached preview content")
            else:
                # Process file
                start_time = time.time()
                file_handler = FileHandler()
                file_path, error = file_handler.save_file(uploaded_file)
                
                if error:
                    st.error(error)
                    return
                
                # Extract text based on file type
                with st.spinner("Loading preview..."):
                    if file_type == 'pdf':
                        resume_text, error = extract_text_from_pdf(uploaded_file)
                    else:  # docx
                        resume_text, error = extract_text_from_docx(uploaded_file)
                
                if error:
                    st.error(error)
                    return
                
                if not resume_text or len(resume_text.strip()) == 0:
                    st.error("Could not extract text from the file. Please ensure the file contains selectable text.")
                    return
                
                # Cache the preview content
                st.session_state[cache_key] = resume_text
            
            # Process resume
            nlp_processor = NLPProcessor()
            processed_data = nlp_processor.process_text(resume_text)
            
            # Update status
            status_container.success("Resume processed successfully!")
            
            # Store in session state
            st.session_state['resume_text'] = resume_text
            st.session_state['skills'] = processed_data['skills']
            st.session_state['resume_location'] = processed_data['location']
            st.session_state['resume_file_path'] = file_path
            
            # Display extracted information
            st.subheader("Extracted Information")
            
            # Skills with confidence indicators
            if processed_data['skills']:
                st.write("**Skills Detected:**")
                for skill in sorted(processed_data['skills']):
                    st.markdown(f"- {skill}")
            else:
                st.warning("No skills were detected. Consider updating your resume with more technical terms.")
            
            # Location information
            if processed_data['location']:
                st.write("**Location:**", processed_data['location'])
            else:
                st.info("Location could not be automatically detected. You can specify it during job search.")
            
            # Processing time
            st.text(f"Processing time: {time.time() - start_time:.2f} seconds")
            
            # Preview uploaded resume with improved error handling
            with st.spinner("Loading preview..."):
                preview_container = st.empty()
                try:
                    preview_container.text_area(
                        "Resume Content Preview", 
                        resume_text,
                        height=300,
                        disabled=True
                    )
                except Exception as e:
                    st.error(f"Error displaying preview: {str(e)}")
            
            # Save to database
            if st.button("Save Resume"):
                try:
                    db = Database()
                    user_id = st.session_state.get('user_id', 1)  # Default user_id for demo
                    resume_id = db.save_resume(
                        user_id=user_id,
                        resume_text=resume_text,
                        extracted_skills=list(processed_data['skills']),
                        location=processed_data['location'],
                        file_path=file_path,
                        file_type=file_type
                    )
                    st.success(f"Resume saved successfully! ID: {resume_id}")
                    
                    # Additional feedback
                    if len(processed_data['skills']) < 5:
                        st.warning("Tip: Consider adding more technical skills to your resume for better job matches.")
                    
                except Exception as e:
                    logger.error(f"Error saving resume to database: {str(e)}")
                    st.error(f"Error saving resume to database. Please try again later.")
                
        except Exception as e:
            logger.error(f"Error processing resume: {str(e)}")
            st.error("An unexpected error occurred. Please try again or contact support if the issue persists.")
