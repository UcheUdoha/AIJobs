-- Create job sources table
CREATE TABLE IF NOT EXISTS job_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(1024) NOT NULL,
    scraping_config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    last_scraped_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add source tracking to jobs table
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS source_id INTEGER REFERENCES job_sources(id);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS external_id VARCHAR(255);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS url VARCHAR(1024);
ALTER TABLE jobs ADD COLUMN IF NOT EXISTS posted_at TIMESTAMP;

-- Remove duplicate NULL records if any exist
DELETE FROM jobs a USING jobs b
WHERE a.id > b.id 
AND (a.source_id IS NULL AND b.source_id IS NULL)
AND (a.external_id IS NULL AND b.external_id IS NULL);

-- Create unique constraint excluding NULL values
CREATE UNIQUE INDEX IF NOT EXISTS unique_external_job 
ON jobs (source_id, external_id) 
WHERE source_id IS NOT NULL AND external_id IS NOT NULL;
