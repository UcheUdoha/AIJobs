-- Add location field to resumes table
ALTER TABLE resumes 
ADD COLUMN location TEXT;

-- Add location_score field to store location match score
ALTER TABLE jobs 
ADD COLUMN location_score FLOAT DEFAULT 0.0;
