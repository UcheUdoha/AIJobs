-- Add indexes for frequently queried columns
CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);
CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_job_matches_user_score ON job_matches(user_id, match_score);
CREATE INDEX IF NOT EXISTS idx_interview_responses_user ON interview_responses(user_id);
CREATE INDEX IF NOT EXISTS idx_interview_questions_category ON interview_questions(category, difficulty);

-- Add index for full-text search
CREATE INDEX IF NOT EXISTS idx_jobs_description_gin ON jobs USING gin(to_tsvector('english', description));

-- Add composite indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_job_matches_notification ON job_matches(user_id, is_notified, match_score);
CREATE INDEX IF NOT EXISTS idx_bookmarks_user_job ON bookmarks(user_id, job_id);
