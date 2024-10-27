-- Create resume templates table
CREATE TABLE resume_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    template_structure JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create resume data blocks table
CREATE TABLE resume_data_blocks (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id),
    block_type VARCHAR(50) NOT NULL,
    block_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add template information to resumes table
ALTER TABLE resumes 
ADD COLUMN template_id INTEGER REFERENCES resume_templates(id),
ADD COLUMN parsed_data JSONB,
ADD COLUMN file_type VARCHAR(10),
ADD COLUMN file_url VARCHAR(255);

-- Insert some default resume templates
INSERT INTO resume_templates (name, template_structure) VALUES
('Professional', '{
    "sections": [
        {"name": "contact", "title": "Contact Information", "required": true},
        {"name": "summary", "title": "Professional Summary", "required": true},
        {"name": "experience", "title": "Work Experience", "required": true},
        {"name": "education", "title": "Education", "required": true},
        {"name": "skills", "title": "Skills", "required": true}
    ],
    "styling": {
        "font": "Arial",
        "fontSize": "11pt",
        "spacing": "1.15"
    }
}'::jsonb),
('Modern', '{
    "sections": [
        {"name": "header", "title": "Header", "required": true},
        {"name": "skills", "title": "Skills Overview", "required": true},
        {"name": "experience", "title": "Professional Experience", "required": true},
        {"name": "education", "title": "Education", "required": true},
        {"name": "projects", "title": "Projects", "required": false}
    ],
    "styling": {
        "font": "Helvetica",
        "fontSize": "10.5pt",
        "spacing": "1.2"
    }
}'::jsonb);
