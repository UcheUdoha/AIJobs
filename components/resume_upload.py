import streamlit as st
from utils.nlp_processor import NLPProcessor
from utils.database import Database
from utils.file_handler import FileHandler
import io
import logging
import time
from typing import Tuple, Optional
import math

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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def extract_text_from_pdf(file_content: bytes) -> Tuple[Optional[str], Optional[str]]:
    """Extract text from PDF with enhanced error handling and caching"""
    if not PDF_SUPPORT:
        return None, "PDF support is not available. Please upload a DOCX file instead."
    
    try:
        start_time = time.time()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
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

@st.cache_data(ttl=3600)  # Cache for 1 hour
def extract_text_from_docx(file_content: bytes) -> Tuple[Optional[str], Optional[str]]:
    """Extract text from DOCX with enhanced error handling and caching"""
    if not DOCX_SUPPORT:
        return None, "DOCX support is not available. Please upload a PDF file instead."
    
    try:
        start_time = time.time()
        doc = Document(io.BytesIO(file_content))
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

def chunk_text(text: str, chunk_size: int = 5000) -> list:
    """Split text into chunks for efficient rendering"""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def render_resume_preview(resume_text: str, container) -> None:
    """Render resume preview with improved state management and chunking"""
    try:
        # Initialize preview state in session state if not exists
        preview_state_key = 'preview_state'
        if preview_state_key not in st.session_state:
            st.session_state[preview_state_key] = {
                'text': resume_text,
                'font_size': 'Medium',
                'wrap_text': True,
                'dark_mode': False,
                'current_chunk': 0,
                'chunks': chunk_text(resume_text),
                'show_line_numbers': False
            }
        
        # Create preview container with customization options
        with container.expander("Resume Preview", expanded=True):
            # Add preview customization options in columns
            col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
            
            with col1:
                font_size = st.select_slider(
                    "Font Size",
                    options=["Small", "Medium", "Large"],
                    value=st.session_state[preview_state_key]['font_size'],
                    key='preview_font_size'
                )
            
            with col2:
                wrap_text = st.checkbox(
                    "Wrap Text",
                    value=st.session_state[preview_state_key]['wrap_text'],
                    key='preview_wrap_text'
                )
            
            with col3:
                dark_mode = st.checkbox(
                    "Dark Mode",
                    value=st.session_state[preview_state_key]['dark_mode'],
                    key='preview_dark_mode'
                )
                
            with col4:
                show_line_numbers = st.checkbox(
                    "Show Line Numbers",
                    value=st.session_state[preview_state_key]['show_line_numbers'],
                    key='preview_line_numbers'
                )
            
            # Update preview state
            st.session_state[preview_state_key].update({
                'font_size': font_size,
                'wrap_text': wrap_text,
                'dark_mode': dark_mode,
                'show_line_numbers': show_line_numbers
            })
            
            # Apply styling based on user preferences
            font_sizes = {
                "Small": "0.8em",
                "Medium": "1em",
                "Large": "1.2em"
            }
            
            background_color = "#1E1E1E" if dark_mode else "#FFFFFF"
            text_color = "#FFFFFF" if dark_mode else "#000000"
            
            # Pagination for chunks
            chunks = st.session_state[preview_state_key]['chunks']
            total_chunks = len(chunks)
            
            if total_chunks > 1:
                col1, col2 = st.columns([4, 1])
                with col1:
                    chunk_slider = st.slider(
                        "Navigate Preview",
                        0, total_chunks - 1,
                        st.session_state[preview_state_key]['current_chunk'],
                        format=f"Page %d of {total_chunks}"
                    )
                with col2:
                    st.markdown(f"<br>", unsafe_allow_html=True)
                    if st.button("Reset View"):
                        chunk_slider = 0
                
                st.session_state[preview_state_key]['current_chunk'] = chunk_slider
            
            # Create styled preview container with line numbers if enabled
            st.markdown(
                f"""
                <style>
                    .preview-container {{
                        font-family: 'Courier New', monospace;
                        font-size: {font_sizes[font_size]};
                        white-space: {("pre-wrap" if wrap_text else "pre")};
                        background-color: {background_color};
                        color: {text_color};
                        padding: 1rem;
                        border-radius: 4px;
                        border: 1px solid #ccc;
                        height: 400px;
                        overflow-y: auto;
                        margin: 1rem 0;
                        display: flex;
                    }}
                    .line-numbers {{
                        border-right: 1px solid #ccc;
                        padding-right: 10px;
                        margin-right: 10px;
                        color: {text_color};
                        opacity: 0.5;
                        text-align: right;
                        user-select: none;
                    }}
                    .preview-content {{
                        flex: 1;
                    }}
                </style>
                """,
                unsafe_allow_html=True
            )
            
            # Get current chunk of text
            current_text = chunks[st.session_state[preview_state_key]['current_chunk']]
            
            # Create preview content with optional line numbers
            if show_line_numbers:
                lines = current_text.split('\n')
                line_numbers = '<br>'.join(str(i) for i in range(1, len(lines) + 1))
                preview_content = f"""
                <div class="preview-container">
                    <div class="line-numbers">{line_numbers}</div>
                    <div class="preview-content">{current_text}</div>
                </div>
                """
            else:
                preview_content = f"""
                <div class="preview-container">
                    <div class="preview-content">{current_text}</div>
                </div>
                """
            
            st.markdown(preview_content, unsafe_allow_html=True)
            
            # Add download options
            col1, col2 = st.columns([1, 4])
            with col1:
                st.download_button(
                    "Download Preview",
                    resume_text,
                    file_name="resume_preview.txt",
                    mime="text/plain"
                )
            
    except Exception as e:
        logger.error(f"Error in resume preview: {str(e)}")
        container.error(f"Error displaying preview: {str(e)}")

def render_resume_upload():
    """Main resume upload handler with optimized state management"""
    st.header("Upload Your Resume")
    
    # Initialize session state for upload
    if 'upload_state' not in st.session_state:
        st.session_state.upload_state = {
            'file_key': None,
            'resume_text': None,
            'processing_complete': False,
            'error': None
        }
    
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
    
    # Create upload form with improved layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form(key='resume_upload_form', clear_on_submit=False):
            uploaded_file = st.file_uploader(
                "Choose your resume",
                type=['pdf', 'docx'],
                key="resume_uploader",
                help="Upload your resume in PDF or DOCX format"
            )
            
            submit_button = st.form_submit_button(
                "Upload Resume",
                help="Click to process your resume"
            )
            
            if submit_button and uploaded_file is not None:
                try:
                    # Check if this is a new file
                    current_file_key = f"{uploaded_file.name}_{hash(uploaded_file.getvalue())}"
                    
                    if st.session_state.upload_state['file_key'] != current_file_key:
                        with st.spinner("Processing resume..."):
                            # Process the file
                            file_handler = FileHandler()
                            file_path, error = file_handler.save_file(uploaded_file)
                            
                            if error:
                                st.error(error)
                                st.session_state.upload_state['error'] = error
                                return
                            
                            # Extract text based on file type
                            file_type = uploaded_file.name.split('.')[-1].lower()
                            if file_type == 'pdf':
                                resume_text, error = extract_text_from_pdf(uploaded_file.getvalue())
                            else:  # docx
                                resume_text, error = extract_text_from_docx(uploaded_file.getvalue())
                            
                            if error:
                                st.error(error)
                                st.session_state.upload_state['error'] = error
                                return
                            
                            # Process resume content with chunking
                            nlp_processor = NLPProcessor()
                            processed_data = nlp_processor.process_text(resume_text)
                            
                            # Update session states
                            st.session_state.upload_state.update({
                                'file_key': current_file_key,
                                'resume_text': resume_text,
                                'processing_complete': True,
                                'error': None
                            })
                            
                            st.session_state.resume_text = resume_text
                            st.session_state.skills = processed_data['skills']
                            st.session_state.resume_location = processed_data['location']
                            
                            # Save to database
                            db = Database()
                            resume_id = db.save_resume(
                                user_id=st.session_state.get('user_id', 1),
                                resume_text=resume_text,
                                extracted_skills=list(processed_data['skills']),
                                location=processed_data['location'],
                                file_path=file_path,
                                file_type=file_type
                            )
                            
                            st.success("Resume processed successfully!")
                            
                except Exception as e:
                    error_msg = f"An unexpected error occurred: {str(e)}"
                    logger.error(error_msg)
                    st.error(error_msg)
                    st.session_state.upload_state['error'] = error_msg
    
    # Show preview in second column with caching
    with col2:
        if st.session_state.upload_state.get('resume_text'):
            render_resume_preview(st.session_state.upload_state['resume_text'], st)
        else:
            st.info("Upload a resume to see the preview here.")
    
    # Display extracted information with improved layout
    if st.session_state.upload_state.get('processing_complete'):
        st.subheader("Extracted Information")
        
        # Display skills in a more organized layout
        if 'skills' in st.session_state and st.session_state['skills']:
            st.write("**Skills Detected:**")
            skills_cols = st.columns(3)
            for idx, skill in enumerate(sorted(st.session_state['skills'])):
                skills_cols[idx % 3].markdown(f"- {skill}")
        
        # Display location with icon
        if 'resume_location' in st.session_state and st.session_state['resume_location']:
            st.write("📍 **Location:**", st.session_state['resume_location'])
