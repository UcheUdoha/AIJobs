import os
import uuid
import magic
from datetime import datetime
from werkzeug.utils import secure_filename

class FileHandler:
    def __init__(self):
        self.upload_dir = "uploads"
        self.allowed_extensions = {'pdf', 'docx'}
        
        # Create uploads directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def allowed_file(self, filename):
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.allowed_extensions

    def save_file(self, file):
        if not file:
            return None, "No file provided"

        if not self.allowed_file(file.name):
            return None, "File type not allowed. Please upload PDF or DOCX files only."

        # Create a secure filename with timestamp and UUID
        original_filename = secure_filename(file.name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        
        file_path = os.path.join(self.upload_dir, filename)
        
        # Save the file
        with open(file_path, "wb") as f:
            f.write(file.getvalue())

        # Verify file type using python-magic
        file_type = magic.from_file(file_path, mime=True)
        allowed_mime_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
        
        if file_type not in allowed_mime_types:
            os.remove(file_path)
            return None, "Invalid file content. Please upload valid PDF or DOCX files only."

        return file_path, None
