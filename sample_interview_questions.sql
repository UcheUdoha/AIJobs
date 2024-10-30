-- Add comprehensive interview questions
INSERT INTO interview_questions (category, question, difficulty) VALUES
-- Behavioral questions
('behavioral', 'Describe a situation where you had to work with a difficult team member. How did you handle it?', 'medium'),
('behavioral', 'Tell me about a time when you had to learn a new technology quickly. What was your approach?', 'medium'),
('behavioral', 'Share an example of when you had to make a difficult technical decision. What was your process?', 'hard'),
('behavioral', 'How do you handle competing priorities and deadlines?', 'medium'),
('behavioral', 'Tell me about a project that failed. What did you learn from it?', 'hard'),

-- Technical questions
('technical', 'Explain the differences between processes and threads.', 'medium'),
('technical', 'How would you improve the performance of a slow SQL query?', 'medium'),
('technical', 'Explain the concept of dependency injection and its benefits.', 'medium'),
('technical', 'What are the SOLID principles? Provide examples for each.', 'hard'),
('technical', 'Explain how HTTP works and the difference between HTTP/1.1 and HTTP/2.', 'medium'),
('technical', 'Describe the differences between TCP and UDP protocols.', 'medium'),
('technical', 'What is eventual consistency in distributed systems?', 'hard'),
('technical', 'Explain the CAP theorem and its implications in distributed systems.', 'hard'),
('technical', 'How does garbage collection work in modern programming languages?', 'medium'),
('technical', 'What are design patterns? Explain three patterns you commonly use.', 'hard'),

-- System Design questions
('system_design', 'Design a distributed job scheduling system.', 'hard'),
('system_design', 'How would you design Twitter''s tweet delivery system?', 'hard'),
('system_design', 'Design a real-time analytics dashboard that can handle millions of events per second.', 'hard'),
('system_design', 'How would you design a rate limiting system for an API?', 'medium'),
('system_design', 'Design a URL shortening service like bit.ly.', 'medium'),
('system_design', 'How would you design a notification system that can handle multiple channels (email, push, SMS)?', 'hard'),
('system_design', 'Design a distributed cache system.', 'hard'),
('system_design', 'How would you design a recommendation system for an e-commerce platform?', 'hard')

ON CONFLICT DO NOTHING;
