import streamlit as st
from utils.nlp_processor import NLPProcessor
from utils.database import Database
from utils.file_handler import FileHandler
import io
import logging
import time
from typing import Tuple, Optional
import math
import magic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cache expensive operations with proper TTL
@st.cache_resource(ttl=3600)
def get_nlp_processor():
    return NLPProcessor()

@st.cache_resource(ttl=3600)
def get_db():
    return Database()

@st.cache_data(ttl=3600, max_entries=50)
def cache_file_content(file_content: bytes, file_name: str) -> str:
    """Cache file content with a unique key"""
    return f"{file_name}_{hash(file_content)}"

@st.cache_data(ttl=3600)
def extract_text_from_file(file_content: bytes, file_type: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract text from file with optimized chunked processing and caching"""
    try:
        # Process in chunks with a progress bar
        chunk_size = 1024 * 1024  # 1MB chunks
        total_size = len(file_content)
        chunks = math.ceil(total_size / chunk_size)
        
        extracted_text = ""
        for i in range(chunks):
            start = i * chunk_size
            end = min((i + 1) * chunk_size, total_size)
            chunk = file_content[start:end]
            
            # Process chunk based on file type
            if file_type == 'pdf':
                text_chunk = process_pdf_chunk(io.BytesIO(chunk))
            else:  # docx
                text_chunk = process_docx_chunk(io.BytesIO(chunk))
            
            extracted_text += text_chunk
            
        if not extracted_text.strip():
            return None, f"Could not extract text from {file_type.upper()} file."
            
        return extracted_text, None
            
    except Exception as e:
        logger.error(f"Error processing {file_type} file: {str(e)}")
        return None, f"Error processing file: {str(e)}"

@st.cache_data(ttl=3600)
def process_pdf_chunk(chunk):
    """Process a chunk of PDF data with caching"""
    try:
        import PyPDF2
        pdf_reader = PyPDF2.PdfReader(chunk)
        return " ".join(page.extract_text() for page in pdf_reader.pages)
    except Exception as e:
        logger.error(f"Error processing PDF chunk: {str(e)}")
        return ""

@st.cache_data(ttl=3600)
def process_docx_chunk(chunk):
    """Process a chunk of DOCX data with caching"""
    try:
        from docx import Document
        doc = Document(chunk)
        return " ".join(paragraph.text for paragraph in doc.paragraphs)
    except Exception as e:
        logger.error(f"Error processing DOCX chunk: {str(e)}")
        return ""

@st.cache_data(ttl=3600)
def validate_file_type(file_content: bytes, filename: str) -> Tuple[bool, Optional[str]]:
    """Validate file type using magic numbers with caching"""
    try:
        mime_type = magic.from_buffer(file_content, mime=True)
        allowed_mime_types = {
            'application/pdf': '.pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx'
        }
        
        file_ext = filename.lower().split('.')[-1]
        if mime_type not in allowed_mime_types:
            return False, "Invalid file type. Please upload a PDF or DOCX file."
            
        if allowed_mime_types[mime_type] != f'.{file_ext}':
            return False, "File extension does not match the actual file type."
            
        return True, None
    except Exception as e:
        logger.error(f"Error validating file type: {str(e)}")
        return False, f"Error validating file: {str(e)}"

def render_resume_preview(resume_text: str, container) -> None:
    """Render resume preview with optimized state management and chunking"""
    try:
        # Initialize preview state if not exists
        if 'preview_state' not in st.session_state:
            st.session_state.preview_state = {
                'chunk_size': 5000,
                'current_chunk': 0,
                'font_size': 'Medium',
                'dark_mode': False,
                'wrap_text': True,
                'show_line_numbers': False
            }
        
        # Chunk the text for better performance
        chunks = [resume_text[i:i + st.session_state.preview_state['chunk_size']] 
                 for i in range(0, len(resume_text), st.session_state.preview_state['chunk_size'])]
        
        # Preview controls in columns for better layout
        col1, col2, col3, col4 = container.columns(4)
        with col1:
            new_font_size = st.select_slider(
                "Font Size",
                options=["Small", "Medium", "Large"],
                value=st.session_state.preview_state['font_size']
            )
            if new_font_size != st.session_state.preview_state['font_size']:
                st.session_state.preview_state['font_size'] = new_font_size
                st.experimental_rerun()
        
        with col2:
            new_dark_mode = st.checkbox(
                "Dark Mode",
                value=st.session_state.preview_state['dark_mode']
            )
            if new_dark_mode != st.session_state.preview_state['dark_mode']:
                st.session_state.preview_state['dark_mode'] = new_dark_mode
                st.experimental_rerun()
        
        with col3:
            new_wrap_text = st.checkbox(
                "Wrap Text",
                value=st.session_state.preview_state['wrap_text']
            )
            if new_wrap_text != st.session_state.preview_state['wrap_text']:
                st.session_state.preview_state['wrap_text'] = new_wrap_text
                st.experimental_rerun()
        
        with col4:
            new_show_lines = st.checkbox(
                "Show Line Numbers",
                value=st.session_state.preview_state['show_line_numbers']
            )
            if new_show_lines != st.session_state.preview_state['show_line_numbers']:
                st.session_state.preview_state['show_line_numbers'] = new_show_lines
                st.experimental_rerun()
        
        # Pagination controls if needed
        if len(chunks) > 1:
            st.session_state.preview_state['current_chunk'] = st.slider(
                "Navigate Preview",
                0, len(chunks) - 1,
                st.session_state.preview_state['current_chunk']
            )
        
        # Apply styling
        font_sizes = {"Small": "0.8em", "Medium": "1em", "Large": "1.2em"}
        bg_color = "#1E1E1E" if st.session_state.preview_state['dark_mode'] else "#FFFFFF"
        text_color = "#FFFFFF" if st.session_state.preview_state['dark_mode'] else "#000000"
        
        # Display current chunk with styling
        current_text = chunks[st.session_state.preview_state['current_chunk']]
        
        container.markdown(
            f"""
            <style>
                .preview-container {{
                    font-family: monospace;
                    font-size: {font_sizes[st.session_state.preview_state['font_size']]};
                    background-color: {bg_color};
                    color: {text_color};
                    padding: 1rem;
                    border-radius: 4px;
                    white-space: {'pre-wrap' if st.session_state.preview_state['wrap_text'] else 'pre'};
                    max-height: 500px;
                    overflow-y: auto;
                }}
                .line-numbers {{
                    user-select: none;
                    text-align: right;
                    padding-right: 1em;
                    color: {text_color};
                    opacity: 0.5;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )
        
        if st.session_state.preview_state['show_line_numbers']:
            lines = current_text.split('\n')
            numbered_text = '\n'.join(
                f'<span class="line-numbers">{i + 1}</span> {line}'
                for i, line in enumerate(lines)
            )
            container.markdown(
                f'<div class="preview-container">{numbered_text}</div>',
                unsafe_allow_html=True
            )
        else:
            container.markdown(
                f'<div class="preview-container">{current_text}</div>',
                unsafe_allow_html=True
            )
            
    except Exception as e:
        logger.error(f"Error in resume preview: {str(e)}")
        container.error("Error displaying preview. Please try again.")

def render_resume_upload():
    """Main resume upload handler with optimized state management"""
    st.header("Resume Upload")
    
    # Initialize session state for upload
    if 'upload_state' not in st.session_state:
        st.session_state.upload_state = {
            'file_key': None,
            'resume_text': None,
            'processing_complete': False,
            'error': None
        }
    
    # File upload form
    with st.form("resume_upload_form"):
        uploaded_file = st.file_uploader(
            "Choose your resume file",
            type=['pdf', 'docx'],
            help="Upload your resume in PDF or DOCX format"
        )
        
        submit = st.form_submit_button("Process Resume")
        
        if submit and uploaded_file:
            try:
                # Check if this is a new file using cached content
                current_file_key = cache_file_content(uploaded_file.getvalue(), uploaded_file.name)
                
                if current_file_key != st.session_state.upload_state['file_key']:
                    # Validate file
                    is_valid, error = validate_file_type(
                        uploaded_file.getvalue(),
                        uploaded_file.name
                    )
                    
                    if not is_valid:
                        st.error(error)
                        return
                    
                    # Process file with progress tracking
                    with st.spinner("Processing resume..."):
                        # Extract text
                        file_type = uploaded_file.name.split('.')[-1].lower()
                        resume_text, error = extract_text_from_file(
                            uploaded_file.getvalue(),
                            file_type
                        )
                        
                        if error:
                            st.error(error)
                            return
                        
                        # Process with NLP (cached)
                        nlp = get_nlp_processor()
                        with st.spinner("Analyzing resume content..."):
                            processed_data = nlp.process_text(resume_text)
                            
                        # Save to database
                        db = get_db()
                        file_handler = FileHandler()
                        
                        with st.spinner("Saving resume..."):
                            file_path = file_handler.save_file(uploaded_file)
                            resume_id = db.save_resume(
                                st.session_state.get('user_id', 1),
                                resume_text,
                                list(processed_data['skills']),
                                processed_data['location'],
                                file_path,
                                file_type
                            )
                            
                            if not resume_id:
                                st.error("Failed to save resume to database")
                                return
                        
                        # Update session state
                        st.session_state.upload_state.update({
                            'file_key': current_file_key,
                            'resume_text': resume_text,
                            'processing_complete': True,
                            'error': None
                        })
                        
                        st.session_state.resume_text = resume_text
                        st.session_state.skills = processed_data['skills']
                        
                        st.success("Resume processed successfully!")
                        
            except Exception as e:
                logger.error(f"Error processing resume: {str(e)}")
                st.error(f"Error processing resume: {str(e)}")
                return
    
    # Show preview if processing is complete
    if st.session_state.upload_state['processing_complete']:
        st.subheader("Resume Preview")
        preview_container = st.container()
        render_resume_preview(
            st.session_state.upload_state['resume_text'],
            preview_container
        )
        
        # Show extracted information
        if 'skills' in st.session_state:
            st.subheader("Extracted Information")
            st.write("**Skills detected:**")
            st.write(", ".join(sorted(st.session_state.skills)))
