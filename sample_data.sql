-- Insert sample user
INSERT INTO users (email) VALUES ('demo@example.com');

-- Insert sample jobs
INSERT INTO jobs (title, company, location, description) VALUES
('Software Engineer', 'Tech Corp', 'San Francisco, CA', 'We are looking for a Software Engineer with experience in Python, JavaScript, and web development. Must have strong problem-solving skills and be familiar with agile methodologies.'),
('Data Scientist', 'Data Analytics Inc', 'New York, NY', 'Seeking a Data Scientist with expertise in machine learning, Python, and statistical analysis. Experience with NLP and deep learning frameworks is a plus.'),
('Frontend Developer', 'Web Solutions', 'Remote', 'Looking for a Frontend Developer skilled in React, TypeScript, and modern web technologies. Experience with responsive design and UI/UX principles required.'),
('DevOps Engineer', 'Cloud Systems', 'Seattle, WA', 'Seeking a DevOps Engineer with experience in AWS, Docker, and CI/CD pipelines. Knowledge of Kubernetes and infrastructure as code is essential.'),
('Full Stack Developer', 'Startup Hub', 'Austin, TX', 'Join our growing team as a Full Stack Developer. Experience with Node.js, React, and PostgreSQL required. Knowledge of microservices architecture is a plus.');
