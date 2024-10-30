-- Drop and recreate interview-related tables
DROP TABLE IF EXISTS interview_responses CASCADE;
DROP TABLE IF EXISTS interview_questions CASCADE;

-- Create interview questions table
CREATE TABLE interview_questions (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    question TEXT NOT NULL,
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard')),
    skill_tags TEXT[] DEFAULT '{}',
    experience_level VARCHAR(20) CHECK (experience_level IN ('entry', 'mid', 'senior')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create user responses table
CREATE TABLE interview_responses (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    question_id INTEGER REFERENCES interview_questions(id),
    response TEXT NOT NULL,
    ai_feedback TEXT,
    score INTEGER CHECK (score >= 0 AND score <= 100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample interview questions
INSERT INTO interview_questions (category, question, difficulty, skill_tags, experience_level) VALUES
('technical', 'Explain how you would implement a REST API using Python and Flask. Include authentication and rate limiting in your response.', 'medium', ARRAY['python', 'flask', 'rest-api'], 'mid'),
('technical', 'Describe the differences between React hooks and class components. When would you use each?', 'medium', ARRAY['react', 'javascript', 'frontend'], 'mid'),
('technical', 'How would you optimize a PostgreSQL query that is running slowly? Walk through your debugging process.', 'hard', ARRAY['sql', 'postgresql', 'database'], 'senior'),
('technical', 'What are Python decorators and how do you use them? Provide examples.', 'medium', ARRAY['python'], 'mid'),
('behavioral', 'Tell me about a challenging project you worked on and how you overcame obstacles.', 'medium', ARRAY['problem-solving', 'project-management'], 'mid'),
('behavioral', 'How do you handle conflicts in a team setting?', 'medium', ARRAY['communication', 'teamwork'], 'mid'),
('system_design', 'Design a real-time chat application with support for group messaging.', 'hard', ARRAY['system-design', 'websockets', 'databases'], 'senior'),
('system_design', 'How would you design a URL shortening service?', 'medium', ARRAY['system-design', 'databases', 'api-design'], 'mid');
